import logging
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User
from src.models.topic_config import TopicConfig
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.question_option import QuestionOption, QuestionOptionPublic
from src.models.question import Question, QuestionCreate, QuestionPublic, QuestionUpdate
from typing import Optional, List

logger = logging.getLogger(__name__)

async def create_configs_and_exams(
    session: AsyncSession,
    exam_specs: dict,
    user_info: User
) -> str:
    """Create exam_config and topic_configs"""
    
    # Fix 1: Access dictionary correctly
    exam_config = ExamConfig(
        subject_id=exam_specs["subject_id"],
        fraction=exam_specs["fraction"],  # Changed from ["fraction"]
        creator_keycloak_id=user_info.user_id
    )
    session.add(exam_config)
    await session.commit()  # Fix 2: Add await
    await session.refresh(exam_config)  # Fix 3: Add await


    
    ex_conf_id = exam_config.id
    
    # Fix 4: Correct query syntax
    topic_configs = []
    for topic_name in exam_specs["topics"]:
        statement = select(Topic).where(Topic.name == topic_name)
        result = await session.exec(statement)
        topic = result.first()

        if topic:
            topic_config = TopicConfig(exam_config_id=ex_conf_id, # type: ignore
                                        topic_id=topic.id, # type: ignore
                                        num_questions=exam_specs["number_questions"][topic_name],
                                        relative_weight=exam_specs["relative_quotations"][topic_name],
                                        creator_keycloak_id=user_info.user_id
                                        ) 

            topic_configs.append(topic_config)
    
    session.add_all(topic_configs)
    await session.commit()
    
    return str(ex_conf_id)

