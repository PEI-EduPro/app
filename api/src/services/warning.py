from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
from src.models.warning import Warning, WarningType
from src.models.exam import Exam

async def get_warnings_by_exam_config_id(session: AsyncSession, exam_config_id: int) -> List[dict]:
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
