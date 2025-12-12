import logging
import random
import os
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Dict
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User
from src.models.topic_config import TopicConfig
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
from src.models.question import Question

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "latex_templates")


async def create_configs(
    session: AsyncSession,
    exam_specs: dict,
    user_info: User
) -> Tuple[ExamConfig, List[TopicConfig]]:
    """Create ExamConfig and TopicConfigs."""
    
    exam_config = ExamConfig(
        subject_id=exam_specs["subject_id"],
        fraction=exam_specs["fraction"],
        creator_keycloak_id=user_info.user_id
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
                creator_keycloak_id=user_info.user_id
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


async def generate_exams_from_configs(
    session: AsyncSession,
    exam_config: ExamConfig,
    topic_configs: List[TopicConfig],
    num_variations: int = 1
) -> bytes:
    """Generate LaTeX exams and answer keys, return ZIP with PDFs."""
    import zipfile
    import io

    if shutil.which("pdflatex") is None:
        raise RuntimeError("pdflatex is not installed. Please install it (e.g., 'sudo apt install texlive-latex-extra') or run the API via Docker.")

    topic_weights = _compute_normalized_weights(topic_configs)
    zip_buffer = io.BytesIO()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        exams_dir = os.path.join(tmpdir, "exams")
        keys_dir = os.path.join(tmpdir, "answer_keys")
        os.makedirs(exams_dir)
        os.makedirs(keys_dir)

        # Copy base templates
        for f in os.listdir(TEMPLATES_DIR):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(TEMPLATES_DIR, f), tmpdir)

        for var_num in range(1, num_variations + 1):
            # Gather questions for this variation
            all_questions = []
            for t_conf in topic_configs:
                result = await session.exec(
                    select(Question)
                    .where(Question.topic_id == t_conf.topic_id)
                    .options(selectinload(Question.question_options))
                    .order_by(func.random())
                    .limit(t_conf.num_questions)
                )
                all_questions.extend(result.all())
            
            random.shuffle(all_questions)

            # Generate T-variants.tex content and get answer positions
            questions_latex, answers_map = _generate_questions_latex(all_questions, topic_weights)
            num_questions = len(all_questions)

            # Write variant questions file
            with open(os.path.join(tmpdir, "T-variants.tex"), "w") as f:
                f.write(questions_latex)

            # Update Rules.tex with actual number of questions and fraction
            _update_rules(tmpdir, num_questions, exam_config.fraction / 100.0)

            # Generate exam PDF (blank answer grid)
            _write_blank_answers(tmpdir, num_questions)
            exam_pdf = _compile_latex(tmpdir, "main_variants.tex", var_num)
            if exam_pdf:
                with open(os.path.join(exams_dir, f"exam_var_{var_num}.pdf"), "wb") as f:
                    f.write(exam_pdf)

            # Generate answer key PDF (marked grid)
            _write_answer_key(tmpdir, answers_map, num_questions)
            key_pdf = _compile_latex(tmpdir, "main_variants.tex", var_num)
            if key_pdf:
                with open(os.path.join(keys_dir, f"answer_key_var_{var_num}.pdf"), "wb") as f:
                    f.write(key_pdf)

            # Save exam to DB
            new_exam = Exam(exam_config_id=exam_config.id, exam_xml=questions_latex)
            session.add(new_exam)
            await session.commit()

        if not os.listdir(exams_dir):
             raise RuntimeError("No exams were generated. LaTeX compilation likely failed. Check logs for details.")

        # Create ZIP
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(exams_dir):
                zf.write(os.path.join(exams_dir, f), f"exams/{f}")
            for f in os.listdir(keys_dir):
                zf.write(os.path.join(keys_dir, f), f"answer_keys/{f}")

    return zip_buffer.getvalue()


def _generate_questions_latex(questions: list, topic_weights: Dict[int, float]) -> Tuple[str, Dict[int, str]]:
    """Generate LaTeX for questions and return answer map."""
    lines = []
    answers_map = {}
    
    for q_num, q in enumerate(questions, 1):
        weight = topic_weights.get(q.topic_id, 1.0)
        lines.append(f"\\question")
        lines.append(f"({weight:.2f} pts) {q.question_text}")
        lines.append("")
        
        options = list(q.question_options)
        random.shuffle(options)
        
        lines.append("\\begin{choices}")
        for i, opt in enumerate(options):
            cmd = "\\CorrectChoice" if opt.value else "\\choice"
            lines.append(f"  {cmd} {opt.option_text}")
            if opt.value:
                answers_map[q_num] = chr(ord('A') + i)
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
\\qrcode[height=0.75in]{{\\tttnumber}}
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
\\qrcode[height=0.75in]{{\\tttnumber}}
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


def _compile_latex(workdir: str, main_file: str, var_num: int) -> bytes | None:
    """Compile LaTeX to PDF, return PDF bytes or None on failure."""
    main_path = os.path.join(workdir, main_file)
    with open(main_path, "r") as f:
        content = f.read()
    content = content.replace("\\newcommand\\tttnumber{0}", f"\\newcommand\\tttnumber{{{var_num}}}")
    content = content.replace("#FOOTER", "")
    with open(main_path, "w") as f:
        f.write(content)

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
    user_info: User,
    num_variations: int = 1
) -> bytes:
    """Backward-compatible function combining config creation and exam generation."""
    exam_config, topic_configs = await create_configs(session, exam_specs, user_info)
    return await generate_exams_from_configs(session, exam_config, topic_configs, num_variations)


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
            selectinload(ExamConfig.topic_configs).selectinload(TopicConfig.topic)
        )
    )
    result = await session.exec(statement)
    return list(result.all())