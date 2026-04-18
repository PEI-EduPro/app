# src/routers/exam.py
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.services import exam
from src.services.exam import build_exam_questions, get_exam_by_id, get_exam_config_by_id
from src.services.subject import get_subject_by_id
from src.services import waiting_room as waiting_room_service
from src.services.omr import evaluate_exam
from src.core.db import get_session
from src.models.user import User
from src.models.exam_config import ExamConfig, ExamConfigResponse, ExamGenerateRequest
from src.models.common import MessageResponse, StatusResponse
from src.models.topic_config import TopicConfigDTO
from src.core.deps import get_current_user_info, verify_permission
from src.core.keycloak import keycloak_client
import base64
import json
import logging
import os
import traceback
import cv2
from src import utils
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/subject/{subject_id}/configs", response_model=List[ExamConfigResponse])
async def get_subject_exam_configs(
    subject_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all exam configurations for a subject.
    """
    verify_permission(user_info, [f"/s{subject_id}"])
    configs = await exam.get_exam_configs_by_subject(session, subject_id)

    response = []
    for config in configs:
        topic_configs_dto = []
        for tc in config.topic_configs:
            # Safely access the topic name if it exists
            topic_name = tc.topic.name if tc.topic else "Unknown Topic"

            topic_configs_dto.append(TopicConfigDTO(
                id=tc.id,
                topic_id=tc.topic_id,
                topic_name=topic_name,
                num_questions=tc.num_questions,
                relative_weight=tc.relative_weight
            ))

        # Count exams using async query to avoid lazy loading
        num_variations = len(config.exams) if config.exams is not None else 0

        response.append(ExamConfigResponse(
            id=config.id,
            subject_id=config.subject_id,
            fraction=config.fraction,
            #creator_keycloak_id=config.creator_keycloak_id,
            topic_configs=topic_configs_dto,
            nmec_name_list=config.nmec_name_list,
            num_variations=num_variations
        ))

    return response

@router.post("/generate")
async def generate_exams(
    exam_specs: ExamGenerateRequest,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate exams based on specifications.
    Returns a ZIP file containing the generated exam PDFs.
    """
    verify_permission(user_info, [f"/s{exam_specs.subject_id}/generate_exams", f"/s{exam_specs.subject_id}/regent"])
    try:
        zip_bytes = await exam.create_configs_and_exams(
            session,
            exam_specs.model_dump(),
            exam_specs.num_variations,
            exam_specs.student_tuples
        )

        exam_config_id = await exam.get_latest_exam_config_id(session, exam_specs.subject_id)

        await waiting_room_service.create_waiting_room_service(
            session=session,
            exam_config_id=exam_config_id,
            regent_keycloak_id=user_info.user_id,
            vigilant_keycloak_ids=exam_specs.vigilant_keycloak_ids
        )

        logger.info(f"Successfully generated {exam_specs.num_variations} exam variations.")

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=exams.zip"}
        )

    except ValueError as ve:
        logger.warning(f"Validation error during config creation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to create configs: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/exam/{exam_config_id}/student_list", response_model=MessageResponse)
async def store_student_list(
    exam_config_id: int,
    file: UploadFile = File(...),
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Store information in csv file as a dict of nmec: student_name
    """
    group_name = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)

    verify_permission(user_info, [f"/s{group_name}/regent"])

    if file.content_type not in ("text/csv", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    
    # Read file contents asynchronously
    contents = await file.read()

    # Always release the file buffer when done
    await file.close()

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    await exam.process_student_list_csv(session, exam_config_id, contents)    
    return {"message": "Student list stored successfully."}

@router.get("/exam/{exam_config_id}/student_list",response_model=ExamConfigResponse)
async def retrieve_student_list(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    #correct to the waiting room id
    try:
        group_name = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    verify_permission(user_info, [f"/w{group_name}/vigilante", f"/w{group_name}/regent"])

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    if not exam_config:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")

    # Count exams using async query to avoid lazy loading
    num_variations = len(exam_config.exams) if exam_config.exams is not None else 0

    return ExamConfigResponse(
        id=exam_config.id,
        subject_id=exam_config.subject_id,
        fraction=exam_config.fraction,
        topic_configs=exam_config.topic_configs or [],
        nmec_name_list=exam_config.nmec_name_list,
        num_variations=num_variations
    )


@router.delete("/config/{exam_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam_config(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Remove an exam configuration. Only the regent of the subject can do this.
    """
    try:
        subject_id = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    verify_permission(user_info, [f"/s{subject_id}/regent"])

    success = await exam.delete_exam_config(session, exam_config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exam configuration not found.")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Deprecated: use POST /api/waiting-rooms/{waiting_room_id}/evaluate instead
# @router.post("/evaluate")
# async def evaluate_exam_omr(...)
    

    



@router.post("/{exam_id}/validate")
async def validate_exam(
    exam_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    The regent validates that an exam has been rightfully corrected.
    This is to help the regent understand the exams he has already validated.
    """

    exam_instance = await exam.get_exam_by_id(session, exam_id)
    if not exam_instance:
        raise HTTPException(status_code=404, detail="Exam not found.")

    subject_id = await exam.get_subject_id_by_exam_config_id(exam_instance.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    if exam_instance.grade is None or exam_instance.results is None or exam_instance.capture_path is None:
        raise HTTPException(status_code=400, detail="Exam has not been corrected yet.")

    exam_instance.validated = True
    session.add(exam_instance)
    await session.commit()

    return {"status": "success"}


@router.get("/{exam_config_id}/all_exams_info")
async def get_all_exams_info(
    exam_config_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get info for all exams in an exam configuration.
    Returns a list of exam info objects with grade, questions breakdown, capture (base64) and correction status.
    Only accessible by the regent of the subject.
    """
    subject_id = await exam.get_subject_id_by_exam_config_id(exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    try:
        exams = await exam.get_exams_by_config_id(session, exam_config_id)
    except ValueError:
        return []

    exam_config = await exam.get_exam_config_by_id(session, exam_config_id)
    fraction = exam_config.fraction if exam_config else 0

    result = []
    for e in exams:
        corrected = e.grade is not None and e.results is not None and e.capture_path is not None

        capture_b64 = None
        if corrected and os.path.exists(e.capture_path):
            with open(e.capture_path, "rb") as f:
                capture_b64 = base64.b64encode(f.read()).decode("utf-8")

        result.append({
            "corrected": corrected,
            "nmec": e.nmec,
            "validated": e.validated,
            "grade": e.grade,
            "exam_id": e.id,
            "capture": capture_b64,
            "questions": build_exam_questions(e, fraction),
        })

    return result


@router.get("/{exam_id}/exam_info")
async def get_exam_info(
    exam_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Get info for a single exam by ID.
    Returns grade, questions breakdown, capture (base64) and correction status.
    Returns 404 if the exam is not found. Only accessible by the regent of the subject.
    """
    e = await exam.get_exam_by_id(session, exam_id)
    if not e:
        raise HTTPException(status_code=404, detail="Exam not found.")

    subject_id = await exam.get_subject_id_by_exam_config_id(e.exam_config_id, session)
    verify_permission(user_info, [f"/s{subject_id}/regent"])

    corrected = e.grade is not None and e.results is not None and e.capture_path is not None

    capture_b64 = None
    if corrected and os.path.exists(e.capture_path):
        with open(e.capture_path, "rb") as f:
            capture_b64 = base64.b64encode(f.read()).decode("utf-8")

    questions = []
    if corrected:
        exam_config = await exam.get_exam_config_by_id(session, e.exam_config_id)
        fraction = exam_config.fraction if exam_config else 0
        questions = build_exam_questions(e, fraction)

    return {
        "corrected": corrected,
        "nmec": e.nmec,
        "validated": e.validated,
        "grade": e.grade,
        "exam_id": e.id,
        "capture": capture_b64,
        "questions": questions,
    }

@router.post("/{exam_id}/notify-student")
async def notify_student_via_email(
    exam_id: int,
    user_info: User = Depends(get_current_user_info),
    session: AsyncSession = Depends(get_session)
):
    """
    Notifies the associated student via email about their grade.
    The email consists of a message indicating the grade and 2 attachments (their answer grid, and the corresponding correction)
    """

    exam = await get_exam_by_id(session, exam_id)

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Check if exam has been manually validated
    if not exam.validated:
        raise HTTPException(status_code=400, detail="Exam has not been validated yet.")
    
    exam_config = await get_exam_config_by_id(session, exam.exam_config_id)

    # Verify user permissions
    verify_permission(user_info, [f"/s{exam_config.subject_id}/regent"])

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

    message += "<p>METER AQUI FOTO DA TABELA DO ALUNO</p><br>"

    # === CORRECT_TABLE_CORRECT_TABLE_CORRECT_TABLE ===

    message += "As respostas solução à sua versão do exame são:"

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