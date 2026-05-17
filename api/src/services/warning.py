import json
import logging
from typing import List, Dict, Set

from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.exam import Exam
from src.models.exam_config import ExamConfig
from src.models.warning import Warning, WarningType, WarningAssignment, StudentSummary

logger = logging.getLogger(__name__)


def _get_nmec_name(nmec_str: str, nmec_to_name: dict) -> str:
    name = nmec_to_name.get(nmec_str, {})
    if isinstance(name, dict):
        name = name.get("name", "Unknown")
    elif not isinstance(name, str):
        name = "Unknown"
    return f"{nmec_str}:{name}"


async def calculate_and_persist_warnings(
    session: AsyncSession,
    exam_config_id: int,
    associations: List[str],
    nmec_to_name: dict
) -> None:
    """
    Delete all existing warnings for exam_config_id, then recalculate and persist
    new ones based on the provided associations list.
    Also writes exam.nmec for clean (conflict-free) 1:1 associations.
    Includes 'exam_correction_no_student' warnings for exams with photos but no student associated.
    """
    # Delete old warnings
    await session.exec(delete(Warning).where(Warning.exam_config_id == exam_config_id))

    student_to_exams: Dict[str, Set[int]] = {}
    exam_to_students: Dict[int, Set[str]] = {}

    for assoc in associations:
        if ":" not in assoc:
            continue
        try:
            exam_id_str, student_nmec = assoc.split(":", 1)
            exam_id = int(exam_id_str)
            student_to_exams.setdefault(student_nmec, set()).add(exam_id)
            exam_to_students.setdefault(exam_id, set()).add(student_nmec)
        except (ValueError, TypeError):
            continue

    conflict_students: Set[str] = set()
    conflict_exams: Set[int] = set()

    # 1. Multiple exams to one student
    for student_nmec, exams in student_to_exams.items():
        if len(exams) > 1:
            conflict_students.add(student_nmec)
            conflict_exams.update(exams)
            session.add(Warning(
                exam_config_id=exam_config_id,
                type=WarningType.multiple_exams_to_student,
                student_list=_get_nmec_name(student_nmec, nmec_to_name),
                exam_list=list(exams)
            ))

    # 2. Multiple students to one exam
    for exam_id, students in exam_to_students.items():
        if len(students) > 1:
            conflict_exams.add(exam_id)
            conflict_students.update(students)
            session.add(Warning(
                exam_config_id=exam_config_id,
                type=WarningType.multiple_students_to_exam,
                student_list="; ".join([_get_nmec_name(s, nmec_to_name) for s in students]),
                exam_list=[exam_id]
            ))

    # 3. Clean 1:1 associations: Write exam.nmec, student_name, student_email
    for exam_id, students in exam_to_students.items():
        if len(students) == 1:
            student_nmec = next(iter(students))
            if student_nmec not in conflict_students and exam_id not in conflict_exams:
                exam = await session.get(Exam, exam_id)
                if exam:
                    try:
                        exam.nmec = int(student_nmec)
                        student_data = nmec_to_name.get(student_nmec, {})
                        if isinstance(student_data, dict):
                            exam.student_name = student_data.get("name")
                            exam.student_email = student_data.get("email")
                        elif isinstance(student_data, str):
                            exam.student_name = student_data
                        session.add(exam)
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not set nmec on exam {exam_id}: "
                            f"'{student_nmec}' is not a valid integer."
                        )

    # 4. Exam correction without student association
    # Fetch all exams for this config to check who has a capture but no nmec
    all_exams_stmt = select(Exam).where(Exam.exam_config_id == exam_config_id)
    all_exams = (await session.exec(all_exams_stmt)).all()
    
    for exam in all_exams:
        if exam.capture_path is not None and exam.nmec is None:
            session.add(Warning(
                exam_config_id=exam_config_id,
                type=WarningType.exam_correction_no_student,
                student_list=None,
                exam_list=[exam.id]
            ))

async def get_filtered_students(
    session: AsyncSession,
    exam_config_id: int,
) -> List[StudentSummary]:
    """
    Returns students that either:
    - have no association in the exam session, OR
    - are involved in any warning (any type)
    """
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    nmec_to_info: dict = {}
    if exam_config.nmec_name_list:
        try:
            nmec_to_info = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse nmec_name_list for exam_config {exam_config.id}: invalid JSON")

    # Build set of nmecs that have at least one association
    associated_nmecs: Set[str] = set()
    for assoc in exam_config.associations:
        if ":" in assoc:
            _, nmec = assoc.split(":", 1)
            associated_nmecs.add(nmec)

    # Build set of nmecs involved in any warning
    stmt = select(Warning).where(Warning.exam_config_id == exam_config_id)
    result = await session.exec(stmt)
    warnings = result.all()

    warned_nmecs: Set[str] = set()
    for w in warnings:
        if not w.student_list:
            continue
        for part in w.student_list.split(";"):
            part = part.strip()
            if ":" in part:
                nmec = part.split(":", 1)[0]
                warned_nmecs.add(nmec)

    students = []
    for nmec, info in nmec_to_info.items():
        if isinstance(info, dict):
            name = info.get("name", "")
            email = info.get("email", "")
        else:
            name = str(info)
            email = ""

        if nmec not in associated_nmecs or nmec in warned_nmecs:
            students.append(StudentSummary(nmec=nmec, name=name, email=email))

    return students


async def get_warnings_by_exam_config_id(session: AsyncSession, exam_config_id: int) -> List[dict]:
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    statement = select(Warning).where(Warning.exam_config_id == exam_config_id)
    result = await session.exec(statement)
    warnings = result.all()

    response_list = []

    # We will need batch numbers for exams. Let's fetch them efficiently
    # by grabbing all exams for this config.
    exam_stmt = select(Exam).where(Exam.exam_config_id == exam_config_id)
    exams_result = await session.exec(exam_stmt)
    exams = exams_result.all()
    exam_batch_map = {exam.id: exam.batch_number for exam in exams}

    def parse_student_list(student_list_str: str) -> List[dict]:
        if not student_list_str:
            return []
        students = []
        # Expecting format: "123:Name; 456:Name2"
        for s in student_list_str.split(";"):
            s = s.strip()
            if not s:
                continue
            parts = s.split(":", 1)
            if len(parts) == 2:
                try:
                    nmec = int(parts[0])
                except ValueError:
                    nmec = 0
                name = parts[1]
            else:
                nmec = 0
                name = parts[0]
            students.append({
                "nmec": nmec,
                "name": name,
                "email": "placeholder@example.com"
            })
        return students

    for warning in warnings:
        students = parse_student_list(warning.student_list)
        
        if warning.type == WarningType.multiple_students_to_exam:
            # 1 exam, multiple students
            if warning.exam_list:
                exam_id = warning.exam_list[0]
                response_list.append({
                    "exam_id": exam_id,
                    "batch_number": exam_batch_map.get(exam_id),
                    "students": students
                })
        
        elif warning.type == WarningType.multiple_exams_to_student:
            # Multiple exams, 1 student
            for exam_id in warning.exam_list:
                response_list.append({
                    "exam_id": exam_id,
                    "batch_number": exam_batch_map.get(exam_id),
                    "students": students
                })
                
        elif warning.type == WarningType.exam_correction_no_student:
            # 1 exam, 0 students
            if warning.exam_list:
                exam_id = warning.exam_list[0]
                response_list.append({
                    "exam_id": exam_id,
                    "batch_number": exam_batch_map.get(exam_id),
                    "students": []
                })

    return response_list


async def resolve_warnings_service(
    session: AsyncSession,
    exam_config_id: int,
    assignments: List[WarningAssignment]
) -> List[dict]:
    exam_config = await session.get(ExamConfig, exam_config_id)
    if not exam_config:
        raise ValueError("Exam configuration not found")

    # Build set of exam_ids being resolved
    incoming_exam_ids = {a.exam_id for a in assignments}

    # Remove existing associations for those exams, keep the rest
    kept = [a for a in exam_config.associations if ":" in a and int(a.split(":", 1)[0]) not in incoming_exam_ids]

    # Add new assignments
    new_associations = kept + [f"{a.exam_id}:{a.student_nmec}" for a in assignments]
    exam_config.associations = new_associations
    session.add(exam_config)

    # Load nmec->name map
    nmec_to_name = {}
    if exam_config.nmec_name_list:
        try:
            nmec_to_name = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse nmec_name_list for exam_config {exam_config_id}: invalid JSON")

    await calculate_and_persist_warnings(session, exam_config_id, new_associations, nmec_to_name)
    await session.commit()

    return await get_warnings_by_exam_config_id(session, exam_config_id)
