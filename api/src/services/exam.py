import anyio
import asyncio
import csv
import io
import json
import logging
import os
import random
import shutil
import smtplib
import subprocess
import tempfile
import traceback
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.keycloak import keycloak_client

from src.models.exam import Exam
from src.models.exam_config import (
    ExamConfig, 
    GenerationStatus, 
    ExamState, 
    ExamSessionInfoResponse, 
    ExamSessionMetricsResponse, 
    ProfessorExamSessionItem, 
    StudentInfo
)
from src.models.question import Question
from src.models.question_option import QuestionOption
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.topic_config import TopicConfig
from src.models.warning import Warning



logger = logging.getLogger(__name__)

LATEX_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates/latex")
HTML_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates/html")
jinja_env = Environment(loader=FileSystemLoader(HTML_TEMPLATES_DIR))
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")


async def create_configs(
    session: AsyncSession,
    exam_specs: dict,
    student_tuples: List[tuple] = None,
    num_versions: int = 1
) -> Tuple[ExamConfig, List[TopicConfig]]:
    """Create ExamConfig and TopicConfigs."""

    topic_ids = [int(tid) for tid in exam_specs["topics"]]

    # Fetch all topics in one query
    topics_result = await session.exec(select(Topic).where(Topic.id.in_(topic_ids)))
    topics_by_id = {t.id: t for t in topics_result.all()}

    # Validate question counts
    for topic_id in topic_ids:
        topic = topics_by_id.get(topic_id)
        if topic:
            count_result = await session.exec(
                select(func.count(Question.id)).where(Question.topic_id == topic.id)
            )
            available_questions = count_result.one_or_none() or 0
            requested_questions = exam_specs["number_questions"].get(str(topic_id), 0)
            if requested_questions > available_questions:
                raise ValueError(
                    f"Topic '{topic.name}' has only {available_questions} questions, "
                    f"but {requested_questions} were requested."
                )

    # Convert student_tuples to JSON string if provided
    nmec_name_list = None
    if student_tuples:
        student_dict = {str(nmec): {"name": name, "email": email} for nmec, name, email in student_tuples}
        nmec_name_list = json.dumps(student_dict)

    exam_config = ExamConfig(
        subject_id=exam_specs["subject_id"],
        fraction=exam_specs["fraction"],
        nmec_name_list=nmec_name_list,
        exam_name=exam_specs.get("exam_name") or exam_specs.get("exam_title", None),
        exam_date=exam_specs.get("exam_date", None),
        num_versions=num_versions
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    topic_configs = []
    for topic_id in topic_ids:
        topic = topics_by_id.get(topic_id)
        if topic:
            topic_configs.append(TopicConfig(
                exam_config_id=exam_config.id,
                topic_id=topic.id,
                num_questions=exam_specs["number_questions"][str(topic_id)],
                relative_weight=exam_specs["relative_quotations"][str(topic_id)],
            ))

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
async def generate_grades_report_pdf(
    session: AsyncSession,
    exam_config_id: int
) -> bytes:
    """Generate a PDF report of student grades using project standard templates."""
    if shutil.which("pdflatex") is None:
        raise RuntimeError("pdflatex is not installed.")

    # 1. Fetch data
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    subject_result = await session.exec(select(Subject).where(Subject.id == exam_config.subject_id))
    subject = subject_result.first()
    subject_name = subject.name if subject else "Unknown Subject"

    exams = await get_exams_by_config_id(session, exam_config_id)
    corrected_exams = [e for e in exams if e.grade is not None]
    corrected_exams.sort(key=lambda x: x.nmec if x.nmec else 0)

    # 2. Setup Temporary Directory and Templates
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy base templates if any were needed (though report is mostly self-contained)
        # For consistency, we'll write the specific files needed
        
        # Write UC.tex (following project pattern)
        # Defaulting to 1st Semester and 2025/26 as seen in other parts of the code
        semester_text_en = "1st Semester"
        semester_text_pt = "1º Semestre"
        academic_year = "2025/26"
        uc_content = f"""\\iftoggle{{english}}{{
{subject_name}\\\\
{semester_text_en}, {academic_year}\\\\
}}{{
{subject_name}\\\\
{semester_text_pt}, {academic_year}\\\\
}}"""
        async with await anyio.open_file(os.path.join(tmpdir, "UC.tex"), "w") as f:
            await f.write(uc_content)

        # Write date.tex (following project pattern)
        exam_date = exam_config.exam_date
        formatted_date = ""
        if exam_date:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(exam_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d de %B de %Y")
                pt_months = {
                    "January": "janeiro", "February": "fevereiro", "March": "março",
                    "April": "abril", "May": "maio", "June": "junho",
                    "July": "julho", "August": "agosto", "September": "setembro",
                    "October": "outubro", "November": "novembro", "December": "dezembro"
                }
                for en, pt in pt_months.items():
                    formatted_date = formatted_date.replace(en, pt)
            except Exception:
                formatted_date = exam_date
        async with await anyio.open_file(os.path.join(tmpdir, "date.tex"), "w") as f:
            await f.write(formatted_date)

        # Build ROWS
        rows = []
        for e in corrected_exams:
            nmec = str(e.nmec) if e.nmec else ""
            name = e.student_name or "Unknown Student"
            grade = f"{e.grade:.2f}"
            safe_name = name.replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")
            rows.append(f"{nmec} & {safe_name} & {grade} \\\\ \\hline")

        # Read Main Template
        template_path = os.path.join(LATEX_TEMPLATES_DIR, "grades_report.tex")
        async with await anyio.open_file(template_path, "r") as f:
            latex_content = await f.read()

        latex_content = latex_content.replace("__EXAM_NAME__", exam_config.exam_name or "Exame")
        latex_content = latex_content.replace("__ROWS__", "\n".join(rows))

        main_file = "report.tex"
        async with await anyio.open_file(os.path.join(tmpdir, main_file), "w") as f:
            await f.write(latex_content)

        # 3. Compile
        try:
            with anyio.fail_after(30):
                await anyio.run_process(
                    ["pdflatex", "-interaction=nonstopmode", main_file],
                    cwd=tmpdir,
                    check=False,
                )
            pdf_path = os.path.join(tmpdir, "report.pdf")
            if os.path.exists(pdf_path):
                async with await anyio.open_file(pdf_path, "rb") as f:
                    return await f.read()
            else:
                raise RuntimeError("LaTeX compilation failed - PDF not generated")
        except Exception as e:
            logger.error(f"LaTeX report compilation failed: {e}")
            raise RuntimeError(f"Failed to generate PDF report: {e}")


async def generate_exams_from_configs(
    session: AsyncSession,
    exam_config: ExamConfig,
    topic_configs: List[TopicConfig],
    total_exams: int = 1,
    exam_title: str = "Exame Época Normal",
    exam_date: str = None,
    semester: str = "1",
    academic_year: str = "2025/26",
    num_versions: int = None
) -> bytes:
    """Generate LaTeX exams and answer keys, return ZIP with PDFs. Saves a copy to disk."""
    zip_bytes, zip_path = await generate_exams_to_disk(
        session, exam_config, topic_configs, total_exams,
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
    total_exams: int = 1,
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
        num_versions = total_exams

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

        # Read template files once
        tex_files = [f for f in os.listdir(LATEX_TEMPLATES_DIR) if f.endswith(".tex")]

        # Copy base templates
        for f in os.listdir(LATEX_TEMPLATES_DIR):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(LATEX_TEMPLATES_DIR, f), tmpdir)

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
            async with await anyio.open_file(os.path.join(tmpdir, "date.tex"), "w") as f:
                await f.write(formatted_date)

        for var_num in range(1, total_exams + 1):
            # Calculate version_idx with remainder distributed to earlier versions
            base_size = total_exams // num_versions
            remainder = total_exams % num_versions
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
                for f in os.listdir(LATEX_TEMPLATES_DIR):
                    if f.endswith(".tex") and not (f == "date.tex" and exam_date):
                        shutil.copy(os.path.join(LATEX_TEMPLATES_DIR, f), tmpdir)

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
            async with await anyio.open_file(os.path.join(tmpdir, "T-variants.tex"), "w") as f:
                await f.write(questions_latex)

            # Update Rules.tex with actual number of questions and fraction
            await _update_rules(tmpdir, num_questions, exam_config.fraction / 100.0)

            # Save exam to DB
            new_exam = Exam(exam_config_id=exam_config.id, exam_xml=questions_latex, batch_number=var_num, answer_key=answer_key, relative_weights=relative_weights)
            session.add(new_exam)
            await session.commit()
            await session.refresh(new_exam)
            exam_id_str = str(new_exam.id)

            # Generate exam PDF (blank answer grid)
            await _write_blank_answers(tmpdir, num_questions)
            # Pass var_num (Batch ID) to LaTeX so each paper is uniquely identified (e.g. Exame 12)
            exam_pdf = await _compile_latex(tmpdir, "main_variants.tex", var_num, subject_name, exam_title, semester, academic_year, exam_id_str)
            if exam_pdf:
                async with await anyio.open_file(os.path.join(exams_dir, f"exam_var_{var_num}.pdf"), "wb") as f:
                    await f.write(exam_pdf)

        # Generate single solutions PDF with all UNIQUE variations and their corresponding batch IDs
        unique_answers = []
        all_single = (num_versions == total_exams)
        
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

        await _write_all_solutions(tmpdir, unique_answers, num_questions, exam_title)
        solutions_pdf = await _compile_latex(tmpdir, "solutions.tex", 1, subject_name, exam_title, semester, academic_year)
        if solutions_pdf:
            async with await anyio.open_file(os.path.join(keys_dir, "all_solutions.pdf"), "wb") as f:
                await f.write(solutions_pdf)

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
        async with await anyio.open_file(zip_path, "wb") as f:
            await f.write(zip_bytes)

    return zip_bytes, zip_path

async def generate_exams_task(
    session_factory,
    exam_config_id: int,
    total_exams: int,
    exam_specs: dict,
    num_versions: Optional[int] = None
):
    """Background task for generating exams."""
    if num_versions is None:
        num_versions = total_exams

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
                session, exam_config, topic_configs, total_exams,
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
                logger.critical(
                    f"ExamConfig {exam_config_id} is stuck in PENDING. "
                    f"Generation error: {e} | Status update error: {e2}"
                )

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


async def _update_rules(workdir: str, num_questions: int, fraction: float):
    """Update Rules.tex with actual number of questions and fraction."""
    rules_path = os.path.join(workdir, "Rules.tex")
    async with await anyio.open_file(rules_path, "r") as f:
        content = await f.read()
    content = content.replace("#NUM_QUESTIONS", str(num_questions))
    content = content.replace("#FRACTION", str(fraction))
    async with await anyio.open_file(rules_path, "w") as f:
        await f.write(content)

async def _write_blank_answers(workdir: str, num_questions: int):
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
    async with await anyio.open_file(os.path.join(workdir, "T-answers.tex"), "w") as f:
        await f.write(content)


async def _write_answer_key(workdir: str, answers: Dict[int, str], num_questions: int):
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
    async with await anyio.open_file(os.path.join(workdir, "T-answers.tex"), "w") as f:
        await f.write(content)


async def _write_all_solutions(workdir: str, all_answers: List[Tuple[str, Dict[int, str]]], num_questions: int, exam_title: str = "Exame Época Normal"):
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

    async with await anyio.open_file(os.path.join(workdir, "solutions.tex"), "w") as f:
        await f.write(content)

async def _compile_latex(workdir: str, main_file: str, var_num: int, subject_name: str = None, exam_title: str = "Exame Época Normal", semester: str = "1", academic_year: str = "2025/26", qrcode_content: str = "0") -> bytes | None:
    """Compile LaTeX to PDF, return PDF bytes or None on failure."""
    main_path = os.path.join(workdir, main_file)
    async with await anyio.open_file(main_path, "r") as f:
        content = await f.read()
    content = content.replace("\\newcommand\\tttnumber{0}", f"\\newcommand\\tttnumber{{{var_num}}}")
    content = content.replace("\\newcommand\\qrcodecontent{0}", f"\\newcommand\\qrcodecontent{{{qrcode_content}}}")
    content = content.replace("#FOOTER", "")
    content = content.replace("Exame Época Normal", exam_title)
    async with await anyio.open_file(main_path, "w") as f:
        await f.write(content)

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
        async with await anyio.open_file(os.path.join(workdir, "UC.tex"), "w") as f:
            await f.write(uc_content)
    
    # Modify H.tex to include variation number after UC.tex
    h_path = os.path.join(workdir, "H.tex")
    if os.path.exists(h_path):
        async with await anyio.open_file(h_path, "r") as f:
            h_content = await f.read()
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

        async with await anyio.open_file(h_path, "w") as f:
            await f.write(h_content)

    try:
        with anyio.fail_after(30):
            await anyio.run_process(
                ["pdflatex", "-interaction=nonstopmode", main_file],
                cwd=workdir,
                check=False,
            )
        pdf_path = os.path.join(workdir, main_file.replace(".tex", ".pdf"))
        if os.path.exists(pdf_path):
            async with await anyio.open_file(pdf_path, "rb") as f:
                return await f.read()
    except Exception as e:
        logger.error(f"LaTeX compilation failed: {e}")
    return None


async def create_configs_and_exams(
    session: AsyncSession,
    exam_specs: dict,
    num_versions: int = 1,
    student_tuples: List[tuple] = None,
    total_exams: int = None
) -> bytes:
    """Backward-compatible function combining config creation and exam generation."""
    if total_exams is None:
        total_exams = num_versions
        
    exam_config, topic_configs = await create_configs(session, exam_specs, student_tuples, num_versions)
    exam_title = exam_specs.get("exam_name") or exam_specs.get("exam_title") or "Exame Época Normal"
    exam_date = exam_specs.get("exam_date")
    semester = exam_specs.get("semester", "1")
    academic_year = exam_specs.get("academic_year", "2025/26")
    return await generate_exams_from_configs(session, exam_config, topic_configs, total_exams, exam_title, exam_date, semester, academic_year, num_versions)


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
    Get a specific exam configuration by ID, with computed metrics.
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
    exam_config = result.first()
    
    if not exam_config:
        return None

    return exam_config


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
    """
    Comprehensive deletion of an exam configuration and all related data.
    - Associated exams and their capture images.
    - Associated Keycloak groups.
    - Associated warnings.
    - The generated ZIP file.
    - The configuration itself and its topic configurations.
    """
    # 1. Fetch ExamConfig with related entities
    statement = (
        select(ExamConfig)
        .where(ExamConfig.id == exam_config_id)
        .options(selectinload(ExamConfig.exams))
    )
    result = await session.exec(statement)
    exam_config = result.first()
    
    if not exam_config:
        return False

    # 2. Fetch related Warnings
    warning_stmt = select(Warning).where(Warning.exam_config_id == exam_config_id)
    warning_result = await session.exec(warning_stmt)
    warnings = list(warning_result.all())

    # 3. Delete files from disk
    # Delete ZIP file
    if exam_config.zip_path and os.path.exists(exam_config.zip_path):
        try:
            os.remove(exam_config.zip_path)
            logger.info(f"Deleted ZIP file: {exam_config.zip_path}")
        except Exception as e:
            logger.error(f"Failed to delete ZIP file {exam_config.zip_path}: {e}")

    # Delete exam capture images
    for exam_item in exam_config.exams:
        if exam_item.capture_path and os.path.exists(exam_item.capture_path):
            try:
                os.remove(exam_item.capture_path)
                logger.info(f"Deleted exam capture: {exam_item.capture_path}")
            except Exception as e:
                logger.error(f"Failed to delete capture file {exam_item.capture_path}: {e}")

    # 4. Delete Keycloak groups for the exam session
    try:
        success = await keycloak_client.delete_exam_session_groups(exam_config.id)
        if success:
            logger.info(f"Deleted Keycloak groups for exam config {exam_config.id}")
        else:
            logger.warning(f"Failed to delete Keycloak groups for exam config {exam_config.id}")
    except Exception as e:
        logger.error(f"Error while deleting Keycloak groups for exam config {exam_config.id}: {e}")

    # 5. Delete database records in order
    # Delete Warnings
    for w in warnings:
        await session.delete(w)
    
    # Delete Exams
    for exam_item in exam_config.exams:
        await session.delete(exam_item)
    
    # Delete the configuration itself (cascades to topic_configs)
    await session.delete(exam_config)
    
    await session.commit()
    logger.info(f"Successfully deleted exam configuration {exam_config_id} and all related data.")
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

async def notify_student(session: AsyncSession, exam: Exam, email_options: Dict[str, Any]):
    """Notify student associated with the corresponding exam"""

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if not exam.student_email:
        raise HTTPException(status_code=422, detail=f"Exam {exam.id} has no student email")

    
    exam_config = await get_exam_config_by_id(session, exam.exam_config_id)
    subject = await session.get(Subject, exam_config.subject_id)

    # 1. PREPARE DATA FOR TEMPLATE
    has_capture = bool(exam.capture_path and os.path.exists(exam.capture_path))
    student_answers = json.loads(exam.results) if isinstance(exam.results, str) else (exam.results or {})
    
    # Pre-calculate the Answer Grid 
    answer_grid = []
    for row_idx, row_label in enumerate(['A', 'B', 'C', 'D']):
        row_cells = []
        for q_idx in range(len(exam.answer_key)):
            q_str = str(q_idx)
            is_selected = student_answers.get(q_str, {}).get(row_label, False)
            is_correct = (exam.answer_key.get(q_str) == row_idx) or (exam.answer_key.get(int(q_idx)) == row_idx)
            
            bg_class = ""
            if is_correct:
                bg_class = "bg-green"
            elif is_selected and not is_correct:
                bg_class = "bg-red"
                
            row_cells.append({
                "is_selected": is_selected,
                "bg_class": bg_class
            })
        answer_grid.append({"label": row_label, "cells": row_cells})

    # Pre-calculate Question Weights and Scores
    sorted_weight_indices = sorted([int(k) for k in exam.relative_weights.keys()])
    question_stats = []
    for idx in sorted_weight_indices:
        weight = exam.relative_weights[str(idx)]
        question_stats.append({
            "num": f"{idx + 1:02d}",
            "weight": weight,
            "penalty": weight * exam_config.fraction / 100
        })

    results_details = dict()
    for q in range(len(exam.answer_key)):
        results_details[str(q)] = {"correct": 0, "incorrect": 0}
        correct = chr(int(exam.answer_key[str(q)]) + 65)

        for letter, selected in student_answers.get(str(q), {}).items():
            if selected:
                if correct == letter:
                    results_details[str(q)]["correct"] += 1
                else:
                    results_details[str(q)]["incorrect"] += 1
    
    # Pre-calculate Cumulative Scores
    sorted_detail_indices = sorted([int(k) for k in results_details.keys()])
    score_details = []
    cumulative_score = 0.0

    for idx in sorted_detail_indices:
        correct = results_details[str(idx)]["correct"]
        incorrect = results_details[str(idx)]["incorrect"]
        weight = exam.relative_weights.get(str(idx), 0)
        penalty = weight * exam_config.fraction / 100
        score = correct * weight - incorrect * penalty
        
        cumulative_score += score

        score_class = ""
        if score > 0.001:
            score_class = "bg-green"
        elif score < -0.001:
            score_class = "bg-red"

        score_details.append({
            "num": f"{idx + 1:02d}",
            "correct": correct,
            "incorrect": incorrect,
            "score_display": f"{score:+.2f}",
            "score_class": score_class,
            "cumulative": cumulative_score
        })

    # 2. RENDER HTML FROM TEMPLATE
    template = jinja_env.get_template('email_to_student.html')
    html_body = template.render(
        options=email_options,
        student_name=exam.student_name,
        nmec=exam.nmec,
        grade=exam.grade,
        has_capture=has_capture,
        answer_key=exam.answer_key,
        answer_grid=answer_grid,
        question_stats=question_stats,
        score_details=score_details,
        fraction=exam_config.fraction,
        custom_description=email_options.get("custom_description", ""),
    )

    # 3. CONSTRUCT AND SEND EMAIL
    msg = MIMEMultipart()
    msg['From'] = os.getenv("SENDER_EMAIL")
    msg['To'] = exam.student_email
    msg['Subject'] = f"Nota de {exam_config.exam_name} de {subject.name}"

    msg.attach(MIMEText(html_body, 'html'))

    # Attach student capture
    if has_capture and email_options.get("exam_capture"):
        try:
            async with await anyio.open_file(exam.capture_path, "rb") as img:
                mime_image_capture = MIMEImage(await img.read())
                mime_image_capture.add_header("Content-ID", "<student_capture>")
                mime_image_capture.add_header("Content-Disposition", "inline", filename="student_capture.jpg")
                msg.attach(mime_image_capture)
        except Exception as e:
            logger.error(f"Failed to attach student capture image: {e}")

    # Attach signature
    img_path = os.path.join(os.path.dirname(__file__), "..", "img", "signature.jpg")
    try:
        async with await anyio.open_file(img_path, "rb") as img:
            mime_image = MIMEImage(await img.read())
            mime_image.add_header("Content-ID", "<signature_image>")
            mime_image.add_header("Content-Disposition", "inline", filename="signature.jpg")
            msg.attach(mime_image)
    except Exception as e:
        logger.error(f"Failed to attach signature image: {e}")

    # Send
    def send_email():
        server = smtplib.SMTP("smtp.gmail.com", int(os.getenv("EMAIL_NOTIFIER_PORT")))
        server.starttls()
        server.login(os.getenv("SENDER_EMAIL"), os.getenv("EMAIL_CODE"))
        server.send_message(msg)
        server.quit()

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_email)
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Falha no servidor de email: {type(e).__name__}: {e}")

    return {"message": "Email enviado com sucesso"}
async def transition_exam_config_state(
    session: AsyncSession, 
    exam_config_id: int, 
    target_state: ExamState
) -> ExamConfig:
    """
    Transition ExamConfig to a new state with business logic validation.
    """
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    current_state = exam_config.state

    # 1. Validation Logic for specific transitions
    if target_state == ExamState.VALIDATION:
        # Must resolve all warnings before moving to validation
        from src.models.warning import Warning
        warning_stmt = select(func.count(Warning.id)).where(Warning.exam_config_id == exam_config_id)
        warning_count = (await session.exec(warning_stmt)).one()
        if warning_count > 0:
            raise ValueError(f"Cannot transition to {target_state} because there are {warning_count} unresolved warnings.")

    elif target_state == ExamState.COMPLETED:
        # All exams with pictures must be validated
        unvalidated_pictured_exams = [e for e in exam_config.exams if e.capture_path is not None and not e.validated]
        if unvalidated_pictured_exams:
            raise ValueError(f"Cannot transition to {target_state} because there are {len(unvalidated_pictured_exams)} pictured exams that have not been validated.")

    # 2. Update state
    exam_config.state = target_state
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    return exam_config

async def create_exam_session_groups_service(
    session: AsyncSession,
    exam_config_id: int,
    regent_keycloak_id: str,
    vigilant_keycloak_ids: List[str]
):
    """
    Creates Keycloak groups for an exam session and assigns users.
    Now tied directly to ExamConfig ID.
    """
    await keycloak_client.create_exam_session_groups(
        exam_config_id=exam_config_id,
        regent_keycloak_id=regent_keycloak_id,
        vigilant_ids=vigilant_keycloak_ids
    )

async def get_exam_session_info_service(session: AsyncSession, exam_config_id: int, user_groups: List[str]) -> Optional[ExamSessionInfoResponse]:
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        return None

    # Get Subject to get the name
    subject = await session.get(Subject, exam_config.subject_id)
    if not subject:
        logger.warning(f"Subject not found for exam config {exam_config_id}")
        return None
        
    exams = await get_exams_by_config_id(session, exam_config_id)
    exam_ids = [exam.id for exam in exams]
    
    formatted_students = []
    if exam_config.nmec_name_list:
        try:
            raw_students = json.loads(exam_config.nmec_name_list)

            for nmec_key, student_data in raw_students.items():
                formatted_students.append(
                    StudentInfo(
                        nmec = str(nmec_key),
                        name = student_data.get("name", "Unknown")
                    )
                )
        except json.JSONDecodeError:
            logger.error(f"Failed to parse nmec_name_list for exam_config {exam_config.id}: invalid JSON")

    # Role extraction logic
    user_role = "Unknown"
    target_prefix = f"w{exam_config_id}/"
    for raw_group in user_groups:
        group = raw_group.lstrip("/")
        # Check if the group is for THIS specific exam session
        if group.startswith(target_prefix):
            parts = group.split("/", 1)
            if len(parts) == 2:
                extracted_role = parts[1]
                if extracted_role in ["regent", "vigilant"]:
                    user_role = extracted_role
                    break
            
    return ExamSessionInfoResponse(
        id=exam_config.id,
        subject_id=subject.id,
        subject_name=subject.name,
        state=exam_config.state,
        associations=exam_config.associations,
        student_list=formatted_students,
        exam_ids=exam_ids,
        total_students=len(formatted_students),
        total_exams=len(exam_ids),
        role = user_role
    )

async def associate_student_to_exam_service(
    session: AsyncSession,
    exam_config_id: int,
    exam_id: int,
    student_nmec: str
) -> Optional[ExamConfig]:
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        return None

    association_string = f"{exam_id}:{student_nmec}"
    if association_string not in exam_config.associations:
        exam_config.associations = [*exam_config.associations, association_string]
        session.add(exam_config)
        await session.commit()
        await session.refresh(exam_config)

    return exam_config

async def get_exam_session_metrics_service(
    session: AsyncSession,
    exam_config_id: int
) -> Optional[ExamSessionMetricsResponse]:
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        return None
        
    associated_exams = set()
    associated_students = set()
    
    for assoc in exam_config.associations:
        if ":" in assoc:
            exam_id, student_nmec = assoc.split(":", 1)
            associated_exams.add(exam_id)
            associated_students.add(student_nmec)
            
    return ExamSessionMetricsResponse(
        associated_exams_count=len(associated_exams),
        associated_students_count=len(associated_students)
    )

async def close_exam_session_service(session: AsyncSession, exam_config_id: int) -> ExamConfig:
    from src.services.warning import calculate_and_persist_warnings
    
    exam_config = await get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    if exam_config.state != ExamState.RUNNING:
        raise ValueError(f"Exam session must be in running state to be closed. Current state: {exam_config.state}")

    # 1. Update state to WARNING_HANDLING
    exam_config.state = ExamState.WARNING_HANDLING
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    # 2. Load nmec-name mapping for warnings
    nmec_to_name = {}
    if exam_config.nmec_name_list:
        try:
            nmec_to_name = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse nmec_name_list for exam_config {exam_config.id}: invalid JSON")

    # 3. Detect conflicts, persist warnings, and write clean exam.nmec values
    await calculate_and_persist_warnings(session, exam_config.id, exam_config.associations, nmec_to_name)

    await session.commit()
    await session.refresh(exam_config)

    return exam_config

async def get_professor_exam_sessions(
    session: AsyncSession,
    professor_keycloak_id: str,
    professor_groups: List[str]
) -> List[ProfessorExamSessionItem]:
    """
    Get all exam sessions where the professor is either a regent or vigilant.
    """
    # Extract exam config IDs and roles from groups
    exam_config_ids_with_roles: Dict[int, str] = {}
    
    for group in professor_groups:
        group = group.lstrip("/")

        if group.startswith("w") and "/" in group:
            parts = group.split("/", 1)
            if len(parts) == 2:
                wr_prefix, role = parts
                if role in ["regent", "vigilant"]:
                    try:
                        exam_config_id = int(wr_prefix[1:])
                        exam_config_ids_with_roles[exam_config_id] = role
                    except ValueError:
                        logger.warning(f"Invalid exam config ID in group: {group}")
                        continue
    
    if not exam_config_ids_with_roles:
        return []
    
    # Fetch all exam configs at once
    stmt = (
        select(ExamConfig)
        .where(ExamConfig.id.in_(list(exam_config_ids_with_roles.keys())))
        .options(selectinload(ExamConfig.exams))
    )
    results = await session.exec(stmt)
    exam_configs = results.all()
    
    result: List[ProfessorExamSessionItem] = []
    
    for ec in exam_configs:
        role = exam_config_ids_with_roles.get(ec.id)
        if not role:
            continue

        if role == "vigilant" and ec.state.value != "running":
            continue
        
        subject = await session.get(Subject, ec.subject_id)
        if not subject:
            continue
        
        result.append(ProfessorExamSessionItem(
            subject_id=subject.id,
            subject_name=subject.name,
            exam_config_id=ec.id,
            state=ec.state.value,
            role=role,
            exam_name=ec.exam_name,
            exam_date=ec.exam_date
        ))
    
    return result
