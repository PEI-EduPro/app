import logging
import random
import os
import shutil
import tempfile
import subprocess
import csv
import io
import json
from typing import Tuple, List, Dict
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User
from src.models.exam_config import ExamConfig
from src.models.topic_config import TopicConfig
from src.models.topic import Topic
from src.models.exam import Exam
from src.models.question import Question
from src.models.question_option import QuestionOption
from src.models.subject import Subject
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


async def create_configs(
    session: AsyncSession,
    exam_specs: dict,
    student_tuples: List[tuple] = None
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
        exam_name=exam_specs.get("exam_name") or exam_specs.get("exam_title", None)
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
    academic_year: str = "2025/26"
) -> bytes:
    """Generate LaTeX exams and answer keys, return ZIP with PDFs."""
    import zipfile
    import io

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
    all_answers_maps = {}
    
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
            all_answers_maps[var_num] = answers_map
            answer_key = dict()
            for k,v in answers_map.items():
                val = ord(v)-65
                k = k-1
                answer_key[k] = val
            # Transform:
            # {
            #     1: 'C',
            #     2: 'A',
            #     3: 'D'
            # }
            # into:
            # {
            #     0: 2,
            #     1: 0,
            #     2: 3
            # }
            relative_weights = {}
            for i, q in enumerate(all_questions):
                weight = topic_weights.get(q.topic_id, 1.0)
                relative_weights[i] = weight
            # Associate questions with relative weights
            # {
            #     0: 1,
            #     1: 1,
            #     2: 2
            # }
            
            num_questions = len(all_questions)

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
            exam_pdf = _compile_latex(tmpdir, "main_variants.tex", var_num, subject_name, exam_title, semester, academic_year, exam_id_str)
            if exam_pdf:
                with open(os.path.join(exams_dir, f"exam_var_{var_num}.pdf"), "wb") as f:
                    f.write(exam_pdf)

            # Generate answer key PDF (marked grid)
            ''' Temporarily disable this because of the new all_solutions.pdf
            _write_answer_key(tmpdir, answers_map, num_questions)
            key_pdf = _compile_latex(tmpdir, "main_variants.tex", var_num, subject_name, exam_title, semester, academic_year, exam_id_str)
            if key_pdf:
                with open(os.path.join(keys_dir, f"answer_key_var_{var_num}.pdf"), "wb") as f:
                    f.write(key_pdf)
            '''

        # Generate single solutions PDF with all variations
        _write_all_solutions(tmpdir, all_answers_maps, num_questions, exam_title)
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

    return zip_buffer.getvalue()


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
\\begin{{minipage}}{{0.15\\textwidth}}
\\qrcode[height=0.75in]{{\\qrcodecontent}}
\\end{{minipage}}%
\\begin{{minipage}}{{0.80\\textwidth}}
\\scriptsize
\\begin{{center}}
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\end{{tabular}}
\end{{center}}
\\end{{minipage}}
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
\\begin{{minipage}}{{0.15\\textwidth}}
\\qrcode[height=0.75in]{{\\qrcodecontent}}
\\end{{minipage}}%
\\begin{{minipage}}{{0.80\\textwidth}}
\\scriptsize
\\begin{{center}}
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\end{{tabular}}
\end{{center}}
\\end{{minipage}}
\\end{{center}}
\\vspace{{0.25cm}}
"""
    with open(os.path.join(workdir, "T-answers.tex"), "w") as f:
        f.write(content)


def _write_all_solutions(workdir: str, all_answers: Dict[int, Dict[int, str]], num_questions: int, exam_title: str = "Exame Época Normal"):
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
    
    for var_num in sorted(all_answers.keys()):
        answers = all_answers[var_num]
        cols = num_questions
        header = " &".join([f"{i:02d}" for i in range(1, cols + 1)])
        
        rows = []
        for letter in ['A', 'B', 'C', 'D']:
            cells = [("X" if answers.get(q) == letter else " ") for q in range(1, cols + 1)]
            rows.append(f"{letter}& " + " & ".join(cells) + " \\\\ \\hline")
        
        content += f"""\\noindent\\rule{{\\textwidth}}{{0.4pt}}

\\vspace{{0.3cm}}

\\begin{{center}}
\\begin{{tabular}}{{c c}}
\\textbf{{Version {var_num}}} &
\\renewcommand{{\\arraystretch}}{{1.5}}
\\begin{{minipage}}{{0.75\\textwidth}}
\\scriptsize
\\begin{{center}}
\\begin{{tabular}}{{|l|{'l|' * cols}}}
\\hline
 &{header}\\\\ \\hline
{chr(10).join(rows)}
\\end{{tabular}}
\\end{{center}}
\\end{{minipage}}
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
            # Replace existing version number
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
    num_variations: int = 1,
    student_tuples: List[tuple] = None
) -> bytes:
    """Backward-compatible function combining config creation and exam generation."""
    exam_config, topic_configs = await create_configs(session, exam_specs, student_tuples)
    exam_title = exam_specs.get("exam_title", "Exame Época Normal")
    exam_date = exam_specs.get("exam_date")
    semester = exam_specs.get("semester", "1")
    academic_year = exam_specs.get("academic_year", "2025/26")
    return await generate_exams_from_configs(session, exam_config, topic_configs, num_variations, exam_title, exam_date, semester, academic_year)


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
    csv_text = file_contents.decode("utf-8")
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

async def notify_student(session: AsyncSession, exam: Exam):
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

    #message = f"A sua nota do <b>EXAM_NAME</b> da disciplina de <b>{subject_name}</b> foi de <b>{grade:.2f}</b> valores.<br><br>"
    message = "Identificação do aluno:"
    # Centering a table in email usually requires margin: auto and a specific width
    message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'
    message += '<tr style="background-color: #f2f2f2;">'
    message += '<th style="padding: 10px;">Nome</th>'
    message += '<th style="padding: 10px;">NMEC</th>'
    message += '<th style="padding: 10px;">Nota</th></tr>'

    message += f"<tr><td style='padding: 10px;'>{student_name}</td>"
    message += f"<td style='padding: 10px;'>{nmec}</td>"
    message += f"<td style='padding: 10px;'>{grade:.2f}</td></tr>"
    message += "</table><br>"

    message += "<br>Distribuição de cotações por questão:<br><br>"

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

    message += "A sua tabela de resposta:<br><br>"

    #message += "<p>METER AQUI FOTO DA TABELA DO ALUNO</p><br>"
    if exam.capture_path and os.path.exists(exam.capture_path):
        message += '<img src="cid:student_capture" style="max-width: 80%; height: auto; display: block; margin: auto; border: 1px solid #ccc;"><br>'
    else:
        message += '<p><i>[Imagem da tabela de resposta indisponível]</i></p><br>'

    # === CORRECT_TABLE_CORRECT_TABLE_CORRECT_TABLE ===

    message += "As respostas solução à sua versão do exame são:<br><br>"

    # Start the HTML table
    message += '<table border="1" style="border-collapse: collapse; margin-left: auto; margin-right: auto; width: 80%; text-align: center;">'

    # 1. Build the Header Row (Empty cell, then 01, 02, 03...)
    message += '<tr style="background-color: #f2f2f2;"><th></th>'
    for q in range(len(answer_key)):
        message += f"<th style='padding: 8px;'>{q + 1:02d}</th>"
    message += "</tr>"

    # 2. Build the Data Rows (A, B, C, D)
    for row_idx, row_label in enumerate(['A', 'B', 'C', 'D']):
        message += f"<tr><th style='padding: 8px;'>{row_label}</th>"
        
        for q_idx in range(len(answer_key)):
            # Mark 'X' if the answer matches the row index (0=A, 1=B, 2=C, 3=D)
            cell = "X" if answer_key.get(str(q_idx)) == row_idx else ""
            message += f"<td>{cell}</td>"
                
        message += "</tr>"

    message += "</table><br>"

    # === CORRECT_TABLE_CORRECT_TABLE_CORRECT_TABLE ===

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
        message += f"<td style='padding: 8px;'>{val}</td>"

    message += "</tr>"

    # Third row: Incorrect answers
    message += "<tr>"
    message += '<th style="padding: 8px;">Respostas incorretas</th>'

    for idx in sorted_indices:
        val = details[str(idx)]["incorrect"]
        message += f"<td style='padding: 8px;'>{val}</td>"

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

        message += f"<td style='padding: 8px;'>{score:.2f}</td>"

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
    #message += f"Sendo que a cada questão errada descontava {fraction}% da cotação dessa pergunta."

    message += f"<br>Em anexo encontram-se dois ficheiros, respetivamente a sua folha de resposta e a folha de resposta correspondente à versão do seu exame.<br>"
    message += f"<br>Se detetou alguma gralha na correção, deve comunicar ao regente responsável pela unidade curricular.<br>"
    message += "<br>Continuação de um bom ano letivo.<br>"
    message += "<b>EduPro @ UA</b>"

    # Imagem
    message += """
    <br><br>
    <img src="cid:signature_image"
        style="width:100%; height:auto; display:block; margin:auto;">
    """

    msg = MIMEMultipart()
    msg['From'] = os.getenv("SENDER_EMAIL")
    msg['To'] = student_email
    msg['Subject'] = f"Nota de {exam_name} de {subject_name} - {nmec} | {student_name}"

    html_body = f"""
    <html>
        <body>
            <p>{message}</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    # Attach signature image inline
    img_path = os.path.join(os.path.dirname(__file__), "..", "img", "signature.jpg")

    with open(img_path, "rb") as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header("Content-ID", "<signature_image>")
        mime_image.add_header("Content-Disposition", "inline", filename="signature.jpg")
        msg.attach(mime_image)

    # Attachments
    # Student answer grid
    '''Raw table (no omr coloring)'''

    # VER COM O PEDRO
    # if exam.capture_path and os.path.exists(exam.capture_path):
    #     with open(exam.capture_path, "rb") as f:
    #         part = MIMEApplication(f.read(), Name=os.path.basename(exam.capture_path))
    #         part['Content-Disposition'] = f'attachment; filename="{os.path.basename(exam.capture_path)}"'
    #         msg.attach(part)

    # Correct answer grid
    '''T.B.D (Talvez mande o PDF que os profs recebem para não ter de gerar um pdf só para o aluno)'''
    
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