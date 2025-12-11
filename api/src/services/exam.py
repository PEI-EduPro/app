import logging
import random
import xml.etree.ElementTree as ET
import zipfile
import io
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User
from src.models.topic_config import TopicConfig
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
from src.models.question_option import QuestionOption, QuestionOptionPublic
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from src.services.pdf_generator import xml_to_pdf
from typing import Optional, List

logger = logging.getLogger(__name__)

async def create_configs_and_exams(
    session: AsyncSession,
    exam_specs: dict,
    num_variations: int = 1
) -> bytes:
    """
    Create exam_config, topic_configs.
    Then generate 'num_variations' unique exams, save them, 
    render them to PDFs, and return a ZIP containing all PDFs.
    """
    
    # 1. Create ExamConfig (Shared parent for all variations)
    exam_config = ExamConfig(
        subject_id=exam_specs["subject_id"],
        fraction=exam_specs["fraction"],
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    ex_conf_id = exam_config.id
    
    # 2. Create TopicConfigs
    topic_configs = []
    topic_weights = {} 
    total_relative_mass = 0.0

    for topic_id in exam_specs["topics"]:
        statement = select(Topic).where(Topic.id == topic_id)
        result = await session.exec(statement)
        topic = result.first()

        if topic:
            weight = exam_specs["relative_quotations"][topic_id]
            num_q = exam_specs["number_questions"][topic_id]
            
            topic_config = TopicConfig(
                exam_config_id=ex_conf_id,
                topic_id=topic.id,
                num_questions=num_q,
                relative_weight=weight,
            )
            topic_configs.append(topic_config)
            
            total_relative_mass += (weight * num_q)
            topic_weights[topic.id] = weight

    session.add_all(topic_configs)
    await session.commit()
    
    # Calculate Normalization Factor (Scale to 20)
    if total_relative_mass > 0:
        normalization_factor = 20.0 / total_relative_mass
    else:
        normalization_factor = 1.0 # Default fallback if no questions or zero weights

    # Update weights to be actual values (0-20 scale)
    for tid in topic_weights:
        topic_weights[tid] = topic_weights[tid] * normalization_factor
    
    # Prepare ZIP buffer
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        
        # 3. Loop to generate variations
        for i in range(num_variations):
            all_questions = []

            # Re-select random questions for this variation
            for t_conf in topic_configs:
                statement = (
                    select(Question)
                    .where(Question.topic_id == t_conf.topic_id)
                    .options(selectinload(Question.question_options))
                    .order_by(func.random())
                    .limit(t_conf.num_questions)
                )
                result = await session.exec(statement)
                questions = result.all()
                
                if len(questions) < t_conf.num_questions:
                    logger.warning(f"Variation {i+1}: Topic {t_conf.topic_id} requested {t_conf.num_questions} but found {len(questions)}")
                
                all_questions.extend(questions)

            # Scramble questions
            random.shuffle(all_questions)

            # Build XML
            root = ET.Element("exam")
            root.set("fraction", str(exam_config.fraction))
            root.set("subject_id", str(exam_config.subject_id))
            root.set("variation", str(i + 1)) # Add variation number to XML

            for q in all_questions:
                q_elem = ET.SubElement(root, "question")
                q_elem.set("id", str(q.id))
                weight = topic_weights.get(q.topic_id, 1.0)
                q_elem.set("weight", str(weight))
                
                text_elem = ET.SubElement(q_elem, "text")
                text_elem.text = q.question_text
                
                # Debug logging
                options_list = list(q.question_options)
                logger.info(f"Processing Q {q.id} (Topic {q.topic_id}) - Found {len(options_list)} options")

                opts_elem = ET.SubElement(q_elem, "options")
                
                # Scramble options
                random.shuffle(options_list)

                for opt in options_list:
                    opt_elem = ET.SubElement(opts_elem, "option")
                    opt_elem.set("id", str(opt.id))
                    opt_elem.set("correct", str(opt.value).lower())
                    opt_elem.text = opt.option_text

            exam_xml_str = ET.tostring(root, encoding='unicode')

            # 4. Save Exam Variation
            new_exam = Exam(
                exam_config_id=ex_conf_id, # type: ignore
                exam_xml=exam_xml_str
            )
            session.add(new_exam)
            await session.commit()
            await session.refresh(new_exam) # Get ID

            # 5. Generate PDF
            pdf_bytes = xml_to_pdf(exam_xml_str, new_exam.id)
            
            # 6. Add to ZIP
            filename = f"exam_{new_exam.id}_var_{i+1}.pdf"
            zip_file.writestr(filename, pdf_bytes)

    # Return ZIP bytes
    return zip_buffer.getvalue()

