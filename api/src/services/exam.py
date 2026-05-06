import logging
import random
import os
import shutil
import tempfile
import subprocess
import csv
import io
import json
import traceback
from typing import Tuple, List, Dict, Optional
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User
from src.models.exam_config import ExamConfig, GenerationStatus
from src.models.topic_config import TopicConfig
from src.models.topic import Topic
from src.models.exam import Exam
from src.models.question import Question
from src.models.question_option import QuestionOption
from src.models.subject import Subject
from src.models.email_options import EmailOptionsPayload
from src.services.subject import get_subject_by_id
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from src.core.config import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "latex_templates")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")


async def create_configs(
    session: AsyncSession,
    exam_specs: dict,
    student_tuples: List[tuple] = None,
    num_versions: int = 1
) -> Tuple[ExamConfig, List[TopicConfig]]:
    """Create ExamConfig and TopicConfigs."""
    
    # Using a dummy user ID since authentication is disabled
    dummy_user_id = "default_user"

    # Validate question counts before creating configs
    for topic_name in exam_specs["topics"]:
        result = await session.exec(select(Topic).where(Topic.name == topic_name))
        topic = result.first()
        if topic:
            # Count available questions for this topic
            count_result = await session.exec(
                select(func.count(Question.id)).where(Question.topic_id == topic.id)
            )
            available_questions = count_result.one_or_none() or 0
            requested_questions = exam_specs["number_questions"].get(topic_name, 0)
            
            if requested_questions > available_questions:
                raise ValueError(
                    f"Topic '{topic_name}' has only {available_questions} questions, "
                    f"but {requested_questions} were requested."
                )

    # Convert student_tuples to JSON string if provided
    nmec_name_list = None
    if student_tuples:
        import json
        student_dict = {str(nmec): {"name": name, "email": email} for nmec, name, email in student_tuples}
        nmec_name_list = json.dumps(student_dict)

    exam_config = ExamConfig(
        subject_id=exam_specs["subject_id"],
        fraction=exam_specs["fraction"],
        nmec_name_list=nmec_name_list,
        exam_name=exam_specs.get("exam_name") or exam_specs.get("exam_title", None),
        num_versions=num_versions
        #creator_keycloak_id=dummy_user_id
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    topic_configs = []
    for topic_name in exam_specs["topics"]:
        result = await session.exec(select(Topic).where(Topic.name == topic_name))
        topic = result.first()
        if topic:
            topic_config = TopicConfig(
                exam_config_id=exam_config.id,
                topic_id=topic.id,
                num_questions=exam_specs["number_questions"][topic_name],
                relative_weight=exam_specs["relative_quotations"][topic_name],
                #creator_keycloak_id=dummy_user_id
            )
            topic_configs.append(topic_config)

    session.add_all(topic_configs)
    await session.commit()

    return exam_config, topic_configs


def _compute_normalized_weights(topic_configs: List[TopicConfig]) -> Dict[int, float]:
    """Compute normalized weights (20-point scale) from topic configs."""
    total_mass = sum(tc.relative_weight * tc.num_questions for tc in topic_configs)
    if total_mass <= 0:
        return {tc.topic_id: 1.0 for tc in topic_configs}
    norm = 20.0 / total_mass
    return {tc.topic_id: tc.relative_weight * norm for tc in topic_configs}

# put the exam batch number rendered in the LaTeX
async def generate_exams_from_configs(
    session: AsyncSession,
    exam_config: ExamConfig,
    topic_configs: List[TopicConfig],
    num_variations: int = 1,
    exam_title: str = "Exame Época Normal",
    exam_date: str = None,
    semester: str = "1",
    academic_year: str = "2025/26",
    num_versions: int = None
) -> bytes:
    """Generate LaTeX exams and answer keys, return ZIP with PDFs. Saves a copy to disk."""
    zip_bytes, zip_path = await generate_exams_to_disk(
        session, exam_config, topic_configs, num_variations,
        exam_title, exam_date, semester, academic_year, num_versions
    )
    
    # Update exam_config with zip_path and status COMPLETED for backward compatibility
    exam_config.zip_path = zip_path
    exam_config.status = GenerationStatus.COMPLETED
    session.add(exam_config)
    await session.commit()
    
    return zip_bytes

async def generate_exams_to_disk(
    session: AsyncSession,
    exam_config: ExamConfig,
    topic_configs: List[TopicConfig],
    num_variations: int = 1,
    exam_title: str = "Exame Época Normal",
    exam_date: str = None,
    semester: str = "1",
    academic_year: str = "2025/26",
    num_versions: int = None
) -> Tuple[bytes, str]:
    """Generate LaTeX exams and answer keys, save to disk and return (bytes, path)."""
    import zipfile
    import io

    if num_versions is None:
        num_versions = num_variations

    if shutil.which("pdflatex") is None:
        raise RuntimeError("pdflatex is not installed. Please install it (e.g., 'sudo apt install texlive-latex-extra') or run the API via Docker.")
    if not topic_configs:
        raise ValueError("No topic configurations provided - cannot generate exams")

    # Get subject name
    subject_result = await session.exec(select(Subject).where(Subject.id == exam_config.subject_id))
    subject = subject_result.first()
    subject_name = subject.name if subject else "Unknown Subject"

    topic_weights = _compute_normalized_weights(topic_configs)
    zip_buffer = io.BytesIO()
    
    # Cache for unique versions (questions, answers, weights)
    versions_cache = {}
    # Mapping from version index to list of batch numbers (var_num)
    version_to_batches = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        exams_dir = os.path.join(tmpdir, "exams")
        keys_dir = os.path.join(tmpdir, "answer_keys")
        os.makedirs(exams_dir)
        os.makedirs(keys_dir)

        # Copy base templates
        for f in os.listdir(TEMPLATES_DIR):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(TEMPLATES_DIR, f), tmpdir)

        # Write custom date.tex
        if exam_date:
            from datetime import datetime
            date_obj = datetime.strptime(exam_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d de %B de %Y")
            # Portuguese month names
            pt_months = {
                "January": "janeiro", "February": "fevereiro", "March": "março",
                "April": "abril", "May": "maio", "June": "junho",
                "July": "julho", "August": "agosto", "September": "setembro",
                "October": "outubro", "November": "novembro", "December": "dezembro"
            }
            for en, pt in pt_months.items():
                formatted_date = formatted_date.replace(en, pt)
            with open(os.path.join(tmpdir, "date.tex"), "w") as f:
                f.write(formatted_date)

        for var_num in range(1, num_variations + 1):
            # Calculate version_idx with remainder distributed to earlier versions
            base_size = num_variations // num_versions
            remainder = num_variations % num_versions
            threshold = remainder * (base_size + 1)
            
            if var_num <= threshold:
                version_idx = (var_num - 1) // (base_size + 1)
            else:
                version_idx = remainder + (var_num - 1 - threshold) // base_size
            
            if version_idx not in version_to_batches:
                version_to_batches[version_idx] = []
            version_to_batches[version_idx].append(var_num)

            if version_idx in versions_cache:
                questions_latex, answers_map, answer_key, relative_weights, num_questions = versions_cache[version_idx]
            else:
                for f in os.listdir(TEMPLATES_DIR):
                    if f.endswith(".tex"):
                        shutil.copy(os.path.join(TEMPLATES_DIR, f), tmpdir)

                # Gather questions for this variation
                all_questions = []
                for t_conf in topic_configs:
                    result = await session.exec(
                        select(Question)
                        .where(Question.topic_id == t_conf.topic_id)
                        .order_by(func.random())
                        .limit(t_conf.num_questions)
                    )
                    all_questions.extend(result.all())
                
                # Load options for all questions
                q_ids = [q.id for q in all_questions]
                opts_by_q = {}
                if q_ids:
                    opts_result = await session.exec(
                        select(QuestionOption).where(QuestionOption.question_id.in_(q_ids))
                    )
                    all_opts = opts_result.all()
                    logger.info(f"Loaded {len(all_opts)} options for {len(q_ids)} questions")
                    for opt in all_opts:
                        opts_by_q.setdefault(opt.question_id, []).append(opt)
                
                random.shuffle(all_questions)

                # Generate T-variants.tex content and get answer positions
                questions_latex, answers_map = _generate_questions_latex(all_questions, topic_weights, opts_by_q)
                
                answer_key = dict()
                for k,v in answers_map.items():
                    val = ord(v)-65
                    k = k-1
                    answer_key[k] = val
                
                relative_weights = {}
                for i, q in enumerate(all_questions):
                    weight = topic_weights.get(q.topic_id, 1.0)
                    relative_weights[i] = weight
                
                num_questions = len(all_questions)
                versions_cache[version_idx] = (questions_latex, answers_map, answer_key, relative_weights, num_questions)

            # Write variant questions file
            with open(os.path.join(tmpdir, "T-variants.tex"), "w") as f:
                f.write(questions_latex)

            # Update Rules.tex with actual number of questions and fraction
            _update_rules(tmpdir, num_questions, exam_config.fraction / 100.0)

            # Save exam to DB
            new_exam = Exam(exam_config_id=exam_config.id, exam_xml=questions_latex, batch_number=var_num, answer_key=answer_key, relative_weights=relative_weights)
            session.add(new_exam)
            await session.commit()
            await session.refresh(new_exam)
            exam_id_str = str(new_exam.id)

            # Generate exam PDF (blank answer grid)
            _write_blank_answers(tmpdir, num_questions)
            # Pass var_num (Batch ID) to LaTeX so each paper is uniquely identified (e.g. Exame 12)
            exam_pdf = _compile_latex(tmpdir, "main_variants.tex", var_num, subject_name, exam_title, semester, academic_year, exam_id_str)
            if exam_pdf:
                with open(os.path.join(exams_dir, f"exam_var_{var_num}.pdf"), "wb") as f:
                    f.write(exam_pdf)

        # Generate single solutions PDF with all UNIQUE variations and their corresponding batch IDs
        unique_answers = []
        all_single = (num_versions == num_variations)
        
        for i in range(len(versions_cache)):
            v_num = i + 1
            batches = version_to_batches.get(i, [])
            if not batches:
                continue
            
            if all_single:
                label = f"{v_num}"
            else:
                if len(batches) > 1:
                    batch_range = f"{min(batches)} - {max(batches)}"
                else:
                    batch_range = f"{batches[0]}"
                label = f"{v_num} (Exams: {batch_range})"
                
            unique_answers.append((label, versions_cache[i][1]))

        _write_all_solutions(tmpdir, unique_answers, num_questions, exam_title)
        solutions_pdf = _compile_latex(tmpdir, "solutions.tex", 1, subject_name, exam_title, semester, academic_year)
        if solutions_pdf:
            with open(os.path.join(keys_dir, "all_solutions.pdf"), "wb") as f:
                f.write(solutions_pdf)

        if not os.listdir(exams_dir):
             raise RuntimeError("No exams were generated. LaTeX compilation likely failed. Check logs for details.")

        # Create ZIP
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(exams_dir):
                zf.write(os.path.join(exams_dir, f), f"exams/{f}")
            for f in os.listdir(keys_dir):
                zf.write(os.path.join(keys_dir, f), f"answer_keys/{f}")

        zip_bytes = zip_buffer.getvalue()
        
        # Save ZIP to persistent storage
        os.makedirs(os.path.join(STORAGE_DIR, "exams"), exist_ok=True)
        zip_filename = f"exams_config_{exam_config.id}.zip"
        zip_path = os.path.join(STORAGE_DIR, "exams", zip_filename)
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

    return zip_bytes, zip_path

async def generate_exams_task(
    session_factory,
    exam_config_id: int,
    num_variations: int,
    exam_specs: dict,
    num_versions: Optional[int] = None
):
    """Background task for generating exams."""
    if num_versions is None:
        num_versions = num_variations

    async with session_factory() as session:
        try:
            # Refresh exam_config and topic_configs
            exam_config = await get_exam_config_by_id(session, exam_config_id)
            if not exam_config:
                logger.error(f"ExamConfig {exam_config_id} not found in task")
                return

            exam_config.status = GenerationStatus.PROCESSING
            session.add(exam_config)
            await session.commit()

            topic_configs = exam_config.topic_configs
            exam_title = exam_specs.get("exam_name") or exam_specs.get("exam_title") or "Exame Época Normal"
            exam_date = exam_specs.get("exam_date")
            semester = exam_specs.get("semester", "1")
            academic_year = exam_specs.get("academic_year", "2025/26")

            _, zip_path = await generate_exams_to_disk(
                session, exam_config, topic_configs, num_variations,
                exam_title, exam_date, semester, academic_year, num_versions
            )

            exam_config.zip_path = zip_path
            exam_config.status = GenerationStatus.COMPLETED
            session.add(exam_config)
            await session.commit()
            logger.info(f"Async generation for ExamConfig {exam_config_id} completed successfully.")

        except Exception as e:
            logger.error(f"Async generation for ExamConfig {exam_config_id} failed: {e}")
            logger.error(traceback.format_exc())
            
            # Use a fresh session to ensure the status update succeeds even if the previous session is poisoned
            try:
                async with session_factory() as fail_session:
                    exam_config = await get_exam_config_by_id(fail_session, exam_config_id)
                    if exam_config:
                        exam_config.status = GenerationStatus.FAILED
                        fail_session.add(exam_config)
                        await fail_session.commit()
                        logger.info(f"ExamConfig {exam_config_id} status updated to FAILED")
            except Exception as e2:
                logger.error(f"Failed to set status to FAILED for ExamConfig {exam_config_id}: {e2}")

def _generate_questions_latex(questions: list, topic_weights: Dict[int, float], opts_by_q: Dict[int, list], num_options: int = 4) -> Tuple[str, Dict[int, str]]:
    """Generate LaTeX for questions and return answer map."""
    lines = []
    answers_map = {}
    
    for q_num, q in enumerate(questions, 1):
        weight = topic_weights.get(q.topic_id, 1.0)
        lines.append(f"\\question")
        lines.append(f"({weight:.2f} pts) {q.question_text}")
        lines.append("\\nopagebreak")
        lines.append("")
        
        all_opts = opts_by_q.get(q.id, [])
        logger.info(f"Question {q.id} has {len(all_opts)} options")
        correct_opts = [o for o in all_opts if o.value]
        wrong_opts = [o for o in all_opts if not o.value]
        
        # Pick one correct option
        correct = correct_opts[0] if correct_opts else None
        
        # Fill wrong options up to num_options - 1
        random.shuffle(wrong_opts)
        selected_wrong = wrong_opts[:num_options - 1]
        
        # Build final options list
        final_opts = ([correct] if correct else []) + selected_wrong
        random.shuffle(final_opts)
        
        lines.append("\\begin{choices}")
        for i, opt in enumerate(final_opts):
            if opt and opt.value:
                lines.append(f"  \\CorrectChoice {opt.option_text}")
                answers_map[q_num] = chr(ord('A') + i)
            elif opt:
                lines.append(f"  \\choice {opt.option_text}")
        lines.append("\\end{choices}")
        lines.append("")
    
    return "\n".join(lines), answers_map


def _get_answers_map(questions: list) -> Dict[int, str]:
    """Return dict mapping question number (1-indexed) to correct answer letter."""
    answers = {}
    for idx, q in enumerate(questions, 1):
        options = list(q.question_options)
        random.seed(q.id)
        random.shuffle(options)
        for i, opt in enumerate(options):
            if opt.value:
                answers[idx] = chr(ord('A') + i)
                break
    return answers


def _update_rules(workdir: str, num_questions: int, fraction: float):
    """Update Rules.tex with actual number of questions and fraction."""
    rules_path = os.path.join(workdir, "Rules.tex")
    with open(rules_path, "r") as f:
        content = f.read()
    content = content.replace("#NUM_QUESTIONS", str(num_questions))
    content = content.replace("#FRACTION", str(fraction))
    with open(rules_path, "w") as f:
        f.write(content)

def _write_blank_answers(workdir: str, num_questions: int):
    """Write blank T-answers.tex for student exam."""
    cols = num_questions
    header = " &".join([f"{i:02d}" for i in range(1, cols + 1)])
    
    rows = []
    for letter in ['A', 'B', 'C', 'D']:
        cells = [" " for _ in range(1, cols + 1)]
        rows.append(f"{letter}& " + " & ".join(cells) + " \\\\ \\hline")
    
    content = f"""\\renewcommand{{\\arraystretch}}{{1.5}}
\\begin{{center}}
\\qrcode[height=0.75in]{{\\qrcodecontent}}
\\end{{center}}
\\vspace{{0.3cm}}
\\begin{{center}}
\\begin{{tikzpicture}}
\\node[draw, dotted, thick, inner sep=1.5cm] {{
\\scriptsize
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\\end{{tabular}}
}};
\\end{{tikzpicture}}
\\end{{center}}
\\vspace{{0.25cm}}
"""
    with open(os.path.join(workdir, "T-answers.tex"), "w") as f:
        f.write(content)


def _write_answer_key(workdir: str, answers: Dict[int, str], num_questions: int):
    """Write T-answers.tex with X marks in correct cells."""
    cols = num_questions
    header = " &".join([f"{i:02d}" for i in range(1, cols + 1)])
    
    rows = []
    for letter in ['A', 'B', 'C', 'D']:
        cells = [("X" if answers.get(q) == letter else " ") for q in range(1, cols + 1)]
        rows.append(f"{letter}& " + " & ".join(cells) + " \\\\ \\hline")
    
    content = f"""\\renewcommand{{\\arraystretch}}{{1.5}}
\\begin{{center}}
\\qrcode[height=0.75in]{{\\qrcodecontent}}
\\end{{center}}
\\vspace{{0.3cm}}
\\begin{{center}}
\\begin{{tikzpicture}}
\\node[draw, dotted, thick, inner sep=1.5cm] {{
\\scriptsize
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\\end{{tabular}}
}};
\\end{{tikzpicture}}
\\end{{center}}
\\vspace{{0.25cm}}
"""
    with open(os.path.join(workdir, "T-answers.tex"), "w") as f:
        f.write(content)


def _write_all_solutions(workdir: str, all_answers: List[Tuple[str, Dict[int, str]]], num_questions: int, exam_title: str = "Exame Época Normal"):
    """Write solutions.tex with all variations in horizontal lines."""
    content = f"""\\documentclass[a4paper,10pt]{{exam}}
\\input{{H}}
\\begin{{document}}

\\begin{{center}}
\\huge
\\input{{UC}}

\\vspace{{0.3cm}}
\\normalsize
{exam_title}
\\\\
\\input{{date}}

\\vspace{{0.5cm}}
\\Large \\textbf{{Soluções}}
\\end{{center}}

\\vspace{{0.5cm}}

"""
    
    for label, answers in all_answers:
        cols = num_questions
        header = " &".join([f"{i:02d}" for i in range(1, cols + 1)])
        
        rows = []
        for letter in ['A', 'B', 'C', 'D']:
            cells = [("X" if answers.get(q) == letter else " ") for q in range(1, cols + 1)]
            rows.append(f"{letter}& " + " & ".join(cells) + " \\\\ \\hline")
        
        content += f"""\\noindent\\rule{{\\textwidth}}{{0.4pt}}

\\vspace{{0.3cm}}

\\begin{{center}}
\\textbf{{Version {label}}}

\\vspace{{0.2cm}}

\\renewcommand{{\\arraystretch}}{{1.5}}
\\scriptsize
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\\end{{tabular}}
\\end{{center}}

\\vspace{{0.3cm}}
"""
    
    content += "\\end{document}"
    
    with open(os.path.join(workdir, "solutions.tex"), "w") as f:
        f.write(content)


def _compile_latex(workdir: str, main_file: str, var_num: int, subject_name: str = None, exam_title: str = "Exame Época Normal", semester: str = "1", academic_year: str = "2025/26", qrcode_content: str = "0") -> bytes | None:
    """Compile LaTeX to PDF, return PDF bytes or None on failure."""
    main_path = os.path.join(workdir, main_file)
    with open(main_path, "r") as f:
        content = f.read()
    content = content.replace("\\newcommand\\tttnumber{0}", f"\\newcommand\\tttnumber{{{var_num}}}")
    content = content.replace("\\newcommand\\qrcodecontent{0}", f"\\newcommand\\qrcodecontent{{{qrcode_content}}}")
    content = content.replace("#FOOTER", "")
    content = content.replace("Exame Época Normal", exam_title)
    with open(main_path, "w") as f:
        f.write(content)

    # Create subject-specific UC.tex if subject_name is provided
    if subject_name:
        semester_text_en = f"{semester}st Semester" if semester == "1" else f"{semester}nd Semester"
        semester_text_pt = f"{semester}º Semestre"
        uc_content = f"""\\iftoggle{{english}}{{
{subject_name}\\\\
{semester_text_en}, {academic_year}\\\\
}}{{
{subject_name}\\\\
{semester_text_pt}, {academic_year}\\\\
}}"""
        with open(os.path.join(workdir, "UC.tex"), "w") as f:
            f.write(uc_content)
    
    # Modify H.tex to include variation number after UC.tex
    h_path = os.path.join(workdir, "H.tex")
    if os.path.exists(h_path):
        with open(h_path, "r") as f:
            h_content = f.read()
        # Only add if not already present (check for Versão pattern)
        if "Versão" not in h_content:
            h_content = h_content.replace(
                "\\input{UC}",
                f"\\input{{UC}}\n\t\\vspace{{0.2cm}}\n\t{{\\small \\textbf{{Versão {var_num}}}}}"
            )
        else:
            # Replace existing version number (Batch ID)
            import re
            h_content = re.sub(
                r"Versão \d+",
                f"Versão {var_num}",
                h_content
            )

        with open(h_path, "w") as f:
            f.write(h_content)

    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", main_file],
            cwd=workdir, capture_output=True, timeout=30
        )
        pdf_path = os.path.join(workdir, main_file.replace(".tex", ".pdf"))
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
    except Exception as e:
        logger.error(f"LaTeX compilation failed: {e}")
    return None


async def create_configs_and_exams(
    session: AsyncSession,
    exam_specs: dict,
    num_versions: int = 1,
    student_tuples: List[tuple] = None,
    num_variations: int = None
) -> bytes:
    """Backward-compatible function combining config creation and exam generation."""
    if num_variations is None:
        num_variations = num_versions
        
    exam_config, topic_configs = await create_configs(session, exam_specs, student_tuples, num_versions)
    exam_title = exam_specs.get("exam_name") or exam_specs.get("exam_title") or "Exame Época Normal"
    exam_date = exam_specs.get("exam_date")
    semester = exam_specs.get("semester", "1")
    academic_year = exam_specs.get("academic_year", "2025/26")
    return await generate_exams_from_configs(session, exam_config, topic_configs, num_variations, exam_title, exam_date, semester, academic_year, num_versions)


async def get_exam_configs_by_subject(
    session: AsyncSession,
    subject_id: int
) -> List[ExamConfig]:
    """
    Get all exam configurations for a specific subject,
    including topic configurations and their topic details.
    """
    statement = (
        select(ExamConfig)
        .where(ExamConfig.subject_id == subject_id)
        .options(
            selectinload(ExamConfig.topic_configs).selectinload(TopicConfig.topic),
            selectinload(ExamConfig.exams)
        )
    )
    result = await session.exec(statement)
    return list(result.all())


async def get_exam_by_id(
    session: AsyncSession,
    exam_id: int
) -> Exam | None:
    """
    Get a specific exam by ID.
    """
    statement = (
        select(Exam)
        .where(Exam.id == exam_id)
    )
    result = await session.exec(statement)
    return result.first()


async def get_exam_config_by_id(
    session: AsyncSession,
    exam_config_id: int
) -> ExamConfig | None:
    """
    Get a specific exam configuration by ID.
    """
    statement = (
        select(ExamConfig)
        .where(ExamConfig.id == exam_config_id)
        .options(
            selectinload(ExamConfig.exams),
            selectinload(ExamConfig.topic_configs).selectinload(TopicConfig.topic)
        )
    )
    result = await session.exec(statement)
    return result.first()


async def process_student_list_csv(
    session: AsyncSession,
    exam_config_id: int,
    file_contents: bytes
):
    """
    Parse the CSV file contents and store the student list.
    """
    csv_text = file_contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(csv_text))

    nmec_dict = {}

    for row in reader:
        nmec = row.get("nmec")
        name = row.get("name")
        email = row.get("email")
        if nmec and name:
            nmec_dict[nmec] = {"name": name, "email": email or ""}

    nmec_name_list = json.dumps(nmec_dict)

    await store_student_list(session, exam_config_id, nmec_name_list)


async def store_student_list(
    session: AsyncSession,
    exam_config_id: int,
    nmec_name_list: str
):
    """
    Store the student list (nmec and names) for a given exam configuration.
     This will be used to associate generated exams with students.
     """
    # This function would typically update the ExamConfig with the provided nmec_dict
    # For example, you could add a new column to ExamConfig to store this information as JSON
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found.")
    
    exam_config.nmec_name_list = nmec_name_list
    session.add(exam_config)
    await session.commit()


async def get_subject_id_by_exam_config_id(
    exam_config_id:int,
    session: AsyncSession
):
    """Get subject's id by exam config id"""
    statement = select(ExamConfig).where(ExamConfig.id == exam_config_id)
    result = await session.exec(statement)
    exam_config = result.first()
    if not exam_config:
        raise ValueError("Exam configuration not found.")
    
    return exam_config.subject_id


async def get_student_list(
    session: AsyncSession,
    exam_config_id: int
):
    statement = select(ExamConfig).where(ExamConfig.id == exam_config_id)
    result = await session.exec(statement)
    exam_config = result.first()
    if not exam_config:
        raise ValueError("Exam configuration not found.")
    
    return exam_config.nmec_name_list


async def get_exams_by_config_id(
    session: AsyncSession,
    exam_config_id: int
):
    statement = select(Exam).where(Exam.exam_config_id == exam_config_id)
    result = await session.exec(statement)
    exams = result.all()
    
    if not exams:
        raise ValueError("No exams found for this configuration.")
    
    return exams


async def delete_exam_config(
    session: AsyncSession,
    exam_config_id: int
) -> bool:
    statement = select(ExamConfig).where(ExamConfig.id == exam_config_id)
    result = await session.exec(statement)
    exam_config = result.first()
    
    if not exam_config:
        return False
        
    await session.delete(exam_config)
    await session.commit()
    return True


async def get_latest_exam_config_id(session: AsyncSession, subject_id: int) -> int:
    """Get the ID of the most recently created exam config for a subject."""
    stmt = select(ExamConfig).where(ExamConfig.subject_id == subject_id).order_by(ExamConfig.id.desc()).limit(1)
    result = await session.exec(stmt)
    exam_config = result.first()
    if not exam_config:
        raise ValueError(f"No exam config found for subject {subject_id}")
    return exam_config.id


async def correct_by_hand(
    session: AsyncSession,
    exam_id: int,
    grid: dict,
) -> Exam:
    """
    Update exam results from a manually-provided grid and recompute the grade server-side.
    `grid` is a dict like {"0": {"A": false, "B": true, ...}, ...}
    """
    exam_instance = await get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise ValueError("Exam not found.")

    exam_config = await get_exam_config_by_id(session, exam_instance.exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found.")

    answer_key = {int(k): v for k, v in exam_instance.answer_key.items()}
    relative_weights = {int(k): v for k, v in exam_instance.relative_weights.items()}
    fraction = exam_config.fraction
    sum_weights = sum(relative_weights.values()) or 1

    # Normalise grid keys to uppercase option letters
    normalised_grid = {
        str(q_idx): {opt.upper(): val for opt, val in opts.items()}
        for q_idx, opts in grid.items()
    }

    total_score = 0.0
    for q_idx, correct_opt_idx in answer_key.items():
        q_weight = relative_weights.get(q_idx, 0)
        q_value = (q_weight / sum_weights) * 20.0
        penalty_per_wrong = q_value * (fraction / 100.0)

        opts = normalised_grid.get(str(q_idx), {})
        correct_letter = chr(ord('A') + correct_opt_idx)

        num_correct = 1 if opts.get(correct_letter, False) else 0
        num_wrong = sum(1 for letter, marked in opts.items() if marked and letter != correct_letter)

        total_score += (num_correct * q_value) - (num_wrong * penalty_per_wrong)

    exam_instance.results = json.dumps(normalised_grid)
    exam_instance.grade = max(0.0, total_score)

    session.add(exam_instance)
    await session.commit()
    await session.refresh(exam_instance)
    return exam_instance



def build_exam_questions(exam: Exam, fraction: float) -> list:
    """Build the questions list for exam info responses."""
    if not (exam.results and exam.answer_key and exam.relative_weights):
        return []

    answered_dict = json.loads(exam.results)
    answer_key = {int(k): v for k, v in exam.answer_key.items()}
    relative_weights = {int(k): v for k, v in exam.relative_weights.items()}
    sum_weights = sum(relative_weights.values()) or 1

    questions = []
    for q_idx in sorted(answer_key.keys()):
        q_weight = relative_weights.get(q_idx, 0)
        q_value = round((q_weight / sum_weights) * 20.0, 4)
        correct_answer = chr(ord('a') + answer_key[q_idx])
        answers = {k.lower(): v for k, v in answered_dict.get(str(q_idx), {}).items()}

        questions.append({
            "question_number": q_idx,
            "correct_answer": correct_answer,
            "discount": fraction,
            "value": q_value,
            "answers": answers,
        })

    return questions

async def notify_student(session: AsyncSession, exam: Exam, email_options: Dict[str, bool]):
    """Notify student associated with the corresponding exam"""

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam_config = await get_exam_config_by_id(session, exam.exam_config_id)

    exam_name = exam_config.exam_name
    subject = await get_subject_by_id(session, exam_config.subject_id)

    subject_name = subject.name
    
    nmec = exam.nmec
    student_email = exam.student_email
    student_name = exam.student_name
    grade = exam.grade
    fraction = exam_config.fraction
    relative_weights = exam.relative_weights
    details = exam.results_details
    answer_key = exam.answer_key

    message = ""

    # Student Identification Table (Name, NMEC, and Grade)
    if email_options.get("student_identification", False):
        message += "Identificação do aluno:"
        
        message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'
        message += '<tr style="background-color: #f2f2f2;">'
        message += '<th style="padding: 10px;">Nome</th>'
        message += '<th style="padding: 10px;">NMEC</th></tr>'

        message += f"<tr><td style='padding: 10px;'>{student_name}</td>"
        message += f"<td style='padding: 10px;'>{nmec}</td></tr>"
        message += "</table><br>"

    # Student Answer Grid (Real Image taken by the regent when correcting the exam)
    if email_options.get("exam_capture", False):
        message += "Foto da sua tabela de resposta:<br><br>"

        if exam.capture_path and os.path.exists(exam.capture_path):
            message += '<img src="cid:student_capture" style="max-width: 80%; height: auto; display: block; margin: auto; border: 1px solid #ccc;"><br>'
        else:
            message += '<p><i>[Imagem da tabela de resposta indisponível]</i></p><br>'

    # Student Answer Grid (clean)
    if email_options.get("red_green_cross_table", False):
        # Parse the student's results from the JSON string
        student_answers = json.loads(exam.results) if isinstance(exam.results, str) else (exam.results or {})
        
        message += "A sua tabela digitalizada:<br><br>"

        message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'

        # Create the header row (01, 02, 03, ...)
        message += '<tr style="background-color: #f2f2f2;"><th></th>'
        for q in range(len(answer_key)):
            message += f"<th style='padding: 8px;'>{q + 1:02d}</th>"
        message += "</tr>"

        # Create the rows for options A, B, C, D
        for row_idx, row_label in enumerate(['A', 'B', 'C', 'D']):
            message += f"<tr><th style='padding: 8px;'>{row_label}</th>"
            
            for q_idx in range(len(answer_key)):
                q_str = str(q_idx)
                
                # Check selection
                is_selected = student_answers.get(q_str, {}).get(row_label, False)
                
                # Check correctness
                is_correct = (answer_key.get(q_str) == row_idx) or (answer_key.get(int(q_idx)) == row_idx)
                
                cell_text = "<b>X</b>" if is_selected else ""
                
                # Cell background color
                bg_color = ""
                if is_correct:
                    # Green if it's the correct answer (whether the student marked it or not)
                    bg_color = "background-color: #a8e6cf;" 
                elif is_selected and not is_correct:
                    # Red if the student marked it, but it's wrong
                    bg_color = "background-color: #ff8b94;" 
                    
                message += f"<td style='padding: 8px; {bg_color}'>{cell_text}</td>"
                    
            message += "</tr>"

        message += "</table><br>"

        # Table Color Scheme Legend
        message += "<table style='margin-left: 10%; border-collapse: separate; border-spacing: 0 5px; text-align: left; font-size: 14px;'>"
        message += "<tr>"
        message += "<td style='width: 25px; height: 25px; background-color: #a8e6cf; border: 1px solid black;'></td>"
        message += "<td style='padding-left: 10px;'>- Resposta correta</td>"
        message += "</tr>"

        message += "<tr>"
        message += "<td style='width: 25px; height: 25px; background-color: #a8e6cf; border: 1px solid black; text-align: center;'><b>X</b></td>"
        message += "<td style='padding-left: 10px;'>- Resposta correta selecionada</td>"
        message += "</tr>"

        message += "<tr>"
        message += "<td style='width: 25px; height: 25px; background-color: #ff8b94; border: 1px solid black; text-align: center;'><b>X</b></td>"
        message += "<td style='padding-left: 10px;'>- Resposta incorreta selecionada</td>"
        message += "</tr>"
        message += "</table><br>"

    # Exam Score Distribution Table (Question Value, and Penalty)
    if email_options.get("question_weights", False):
        message += "Distribuição de cotações por questão:<br><br>"

        message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'

        sorted_indices = sorted([int(k) for k in relative_weights.keys()])

        # First row: Question numbers
        message += '<tr style="background-color: #f2f2f2;">'
        message += '<th style="padding: 8px;">Pergunta</th>'

        for idx in sorted_indices:
            q_num = f"{idx + 1:02d}"
            message += f"<th style='padding: 8px;'>{q_num}</th>"

        message += "</tr>"

        # Second row: Values
        message += "<tr>"
        message += '<th style="padding: 8px;">Cotação</th>'

        for idx in sorted_indices:
            val = relative_weights[str(idx)]
            message += f"<td style='padding: 8px;'>{val:.2f}</td>"

        message += "</tr>"

        # Third row: Penalties
        message += "<tr>"
        message += f'<th style="padding: 8px;">Desconto por questão errada ({fraction}%)</th>'

        for idx in sorted_indices:
            val = relative_weights[str(idx)]*fraction/100
            message += f"<td style='padding: 8px;'>{val:.2f}</td>"

        message += "</tr>"

        message += "</table><br>"

    # Details regarding comparison between the student's actual answer and the correct exam answers
    if email_options.get("cumulative_score_table", False):
        message += "Das suas respostas resultaram as seguintes cotações:<br><br>"

        message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'

        sorted_indices = sorted([int(k) for k in details.keys()])

        # First row: Question numbers
        message += '<tr style="background-color: #f2f2f2;">'
        message += '<th style="padding: 8px;">Pergunta</th>'

        for idx in sorted_indices:
            q_num = f"{idx + 1:02d}"
            message += f"<th style='padding: 8px;'>{q_num}</th>"

        message += "</tr>"

        # Second row: Correct answers
        message += "<tr>"
        message += '<th style="padding: 8px;">Respostas corretas</th>'

        for idx in sorted_indices:
            val = details[str(idx)]["correct"]
            bg_color = "background-color: #a8e6cf;" if val == 1 else ""
            message += f"<td style='padding: 8px; {bg_color}'>{val}</td>"

        message += "</tr>"

        # Third row: Incorrect answers
        message += "<tr>"
        message += '<th style="padding: 8px;">Respostas incorretas</th>'

        for idx in sorted_indices:
            val = details[str(idx)]["incorrect"]
            bg_color = "background-color: #ff8b94;" if val > 0 else ""
            message += f"<td style='padding: 8px; {bg_color}'>{val}</td>"

        message += "</tr>"

        # Fourth row: Resulting score (optional but useful)
        message += "<tr>"
        message += '<th style="padding: 8px;">Cotação obtida</th>'

        for idx in sorted_indices:
            correct = details[str(idx)]["correct"]
            incorrect = details[str(idx)]["incorrect"]

            weight = relative_weights.get(str(idx), 0)

            penalty = weight * fraction / 100

            score = correct * weight - incorrect * penalty

            # Determine the background color based on the score
            bg_color = ""
            if score > 0.001:
                bg_color = "background-color: #a8e6cf;" # Green for positive
            elif score < -0.001:
                bg_color = "background-color: #ff8b94;" # Red for negative
                
            # Add a '+' sign for non negative numbers
            score_display = f"{score:+.2f}"
                
            message += f"<td style='padding: 8px; {bg_color}'>{score_display}</td>"

        message += "</tr>"

        # Fifth row: Cumulative score
        message += "<tr>"
        message += '<th style="padding: 8px;">Cotação acumulada</th>'

        cumulative_score = 0.0
        for idx in sorted_indices:
            correct = details[str(idx)]["correct"]
            incorrect = details[str(idx)]["incorrect"]

            weight = relative_weights.get(str(idx), 0)
            penalty = weight * fraction / 100
            score = correct * weight - incorrect * penalty
            
            cumulative_score += score

            message += f"<td style='padding: 8px;'>{cumulative_score:.2f}</td>"

        message += "</tr>"

        message += "</table>"
    
    # Student Grade
    message += f"""
    <div style="text-align: center; margin: 30px 0; font-family: Arial, sans-serif;">
        <div style="font-size: 25px; font-weight: bold; color: #555;">Nota</div>
        <div style="font-size: 45px; font-weight: bold; color: #000; margin-top: 5px;">{grade:.2f}/20</div>
    </div>
    """

    # Grading Disclosure
    if email_options.get("exam_capture", False) and email_options.get("red_green_cross_table", False):
        message += "Se detetou alguma gralha na correção, deve comunicar ao regente responsável pela unidade curricular.<br>"

    # Greeting
    message += "<br>Continuação de um bom ano letivo.<br>"
    message += "<b>EduPro @ UA</b><br>"

    # No Reply Notice
    message += """
    <div style="text-align: center; color: #888888; font-size: 15px;">
        Email enviado automaticamente.<br>
        Por favor não responda a este email.
    </div>
    """
    ""
    # EduPro Signatura Image
    message += """
    <br><br>
    <img src="cid:signature_image"
        style="width:100%; height:auto; display:block; margin:auto;">
    """

    msg = MIMEMultipart()
    msg['From'] = os.getenv("SENDER_EMAIL")
    msg['To'] = student_email
    msg['Subject'] = f"Nota de {exam_name} de {subject_name}"

    html_body = f"""
    <html>
        <body>
            <p>{message}</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    # Attach the student capture image inline
    image_to_send = exam.capture_path # Change to exam.capture_path if preferred

    if image_to_send and os.path.exists(image_to_send):
        try:
            with open(image_to_send, "rb") as img:
                mime_image_capture = MIMEImage(img.read())
                # The Content-ID must perfectly match the cid: in the HTML above
                mime_image_capture.add_header("Content-ID", "<student_capture>")
                mime_image_capture.add_header("Content-Disposition", "inline", filename="student_capture.jpg")
                msg.attach(mime_image_capture)
        except Exception as e:
            logger.error(f"Failed to attach student capture image: {e}")

    # Attach signature image inline
    img_path = os.path.join(os.path.dirname(__file__), "..", "img", "signature.jpg")

    with open(img_path, "rb") as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header("Content-ID", "<signature_image>")
        mime_image.add_header("Content-Disposition", "inline", filename="signature.jpg")
        msg.attach(mime_image)

    # Send via SMTP
    try:
        server = smtplib.SMTP("smtp.gmail.com", int(os.getenv("EMAIL_NOTIFIER_PORT")))
        server.starttls() # Segurança
        server.login(os.getenv("SENDER_EMAIL"), os.getenv("EMAIL_CODE"))
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Falha no servidor de email: {type(e).__name__}: {e}")

    return {"message": "Email enviado com sucesso"}