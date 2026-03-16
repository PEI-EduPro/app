import pytest
import json
from src.services import exam
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.topic_config import TopicConfig
from src.models.exam import Exam


@pytest.mark.asyncio
async def test_get_exam_configs_by_subject(session):
    """Test retrieving exam configurations by subject ID"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=75)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    topic_config = TopicConfig(
        exam_config_id=exam_config.id,
        topic_id=topic.id,
        num_questions=10,
        relative_weight=2.0
    )
    session.add(topic_config)
    await session.commit()
    
    # Test the service function
    configs = await exam.get_exam_configs_by_subject(session, subject.id)
    
    assert len(configs) == 1
    assert configs[0].id == exam_config.id
    assert configs[0].subject_id == subject.id
    assert configs[0].fraction == 75
    assert len(configs[0].topic_configs) == 1
    assert configs[0].topic_configs[0].topic.name == "Test Topic"


@pytest.mark.asyncio
async def test_get_exam_config_by_id(session):
    """Test retrieving exam configuration by ID"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=60)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Test the service function
    result = await exam.get_exam_config_by_id(session, exam_config.id)
    
    assert result is not None
    assert result.id == exam_config.id
    assert result.fraction == 60
    
    # Test with non-existent ID
    result = await exam.get_exam_config_by_id(session, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_store_student_list(session):
    """Test storing student list in exam configuration"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Test data
    student_data = json.dumps({"12345": "John Doe", "67890": "Jane Smith"})
    
    # Test the service function
    await exam.store_student_list(session, exam_config.id, student_data)
    
    # Verify data was stored
    await session.refresh(exam_config)
    assert exam_config.nmec_name_list == student_data
    
    # Verify we can parse the stored data
    parsed_data = json.loads(exam_config.nmec_name_list)
    assert parsed_data["12345"] == "John Doe"
    assert parsed_data["67890"] == "Jane Smith"


@pytest.mark.asyncio
async def test_get_subject_id_by_exam_config_id(session):
    """Test retrieving subject ID by exam config ID"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Test the service function
    result = await exam.get_subject_id_by_exam_config_id(exam_config.id, session)
    
    assert result == subject.id
    
    # Test with non-existent exam config
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await exam.get_subject_id_by_exam_config_id(99999, session)


@pytest.mark.asyncio
async def test_get_student_list(session):
    """Test retrieving student list from exam configuration"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    student_data = json.dumps({"12345": "John Doe", "67890": "Jane Smith"})
    exam_config = ExamConfig(
        subject_id=subject.id, 
        fraction=50,
        nmec_name_list=student_data
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Test the service function
    result = await exam.get_student_list(session, exam_config.id)
    
    assert result == student_data
    
    # Test with non-existent exam config
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await exam.get_student_list(session, 99999)


@pytest.mark.asyncio
async def test_get_exams_by_config_id(session):
    """Test retrieving exams by configuration ID"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Create multiple exams
    exam1 = Exam(exam_config_id=exam_config.id, exam_xml="<exam>test1</exam>")
    exam2 = Exam(exam_config_id=exam_config.id, exam_xml="<exam>test2</exam>")
    session.add_all([exam1, exam2])
    await session.commit()
    
    # Test the service function
    result = await exam.get_exams_by_config_id(session, exam_config.id)
    
    assert len(result) == 2
    assert all(e.exam_config_id == exam_config.id for e in result)
    
    # Test with non-existent exam config
    with pytest.raises(ValueError, match="No exams found for this configuration"):
        await exam.get_exams_by_config_id(session, 99999)


@pytest.mark.asyncio
async def test_store_student_list_nonexistent_config(session):
    """Test storing student list with non-existent exam configuration"""
    student_data = json.dumps({"12345": "John Doe"})
    
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await exam.store_student_list(session, 99999, student_data)
