import pytest
import json
from src.services import exam
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.topic_config import TopicConfig
from src.models.exam import Exam
from src.models.question import Question


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


@pytest.mark.asyncio
async def test_create_configs_with_student_tuples(session):
    """Test create_configs function with student tuples"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    # Add questions to the topic
    for i in range(5):
        question = Question(topic_id=topic.id, question_text=f"Question {i+1}")
        session.add(question)
    await session.commit()
    
    # Test data
    exam_specs = {
        "subject_id": subject.id,
        "fraction": 75,
        "topics": [str(topic.id)],
        "number_questions": {str(topic.id): 5},
        "relative_quotations": {str(topic.id): 2.0}
    }
    
    student_tuples = [
        (12345, "John Doe", "john@example.com"),
        (67890, "Jane Smith", "jane@example.com")
    ]
    
    # Test the function
    exam_config, topic_configs = await exam.create_configs(session, exam_specs, student_tuples)
    
    # Verify exam config was created with student data
    assert exam_config.subject_id == subject.id
    assert exam_config.fraction == 75
    assert exam_config.nmec_name_list is not None
    
    # Verify student data was stored correctly
    student_data = json.loads(exam_config.nmec_name_list)
    assert "12345" in student_data
    assert student_data["12345"]["name"] == "John Doe"
    assert student_data["12345"]["email"] == "john@example.com"
    assert "67890" in student_data
    assert student_data["67890"]["name"] == "Jane Smith"
    assert student_data["67890"]["email"] == "jane@example.com"
    
    # Verify topic configs
    assert len(topic_configs) == 1
    assert topic_configs[0].topic_id == topic.id


@pytest.mark.asyncio
async def test_create_configs_without_student_tuples(session):
    """Test create_configs function without student tuples"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    # Add questions to the topic
    for i in range(3):
        question = Question(topic_id=topic.id, question_text=f"Question {i+1}")
        session.add(question)
    await session.commit()
    
    exam_specs = {
        "subject_id": subject.id,
        "fraction": 50,
        "topics": [str(topic.id)],
        "number_questions": {str(topic.id): 3},
        "relative_quotations": {str(topic.id): 1.5}
    }
    
    # Test the function without student tuples
    exam_config, topic_configs = await exam.create_configs(session, exam_specs)
    
    # Verify exam config was created without student data
    assert exam_config.subject_id == subject.id
    assert exam_config.fraction == 50
    assert exam_config.nmec_name_list is None


@pytest.mark.asyncio
async def test_get_latest_exam_config_id(session):
    """Test get_latest_exam_config_id function"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    # Create multiple exam configs
    config1 = ExamConfig(subject_id=subject.id, fraction=50)
    config2 = ExamConfig(subject_id=subject.id, fraction=75)
    session.add_all([config1, config2])
    await session.commit()
    await session.refresh(config1)
    await session.refresh(config2)
    
    # Test the function
    latest_id = await exam.get_latest_exam_config_id(session, subject.id)
    
    # Should return the ID of the most recently created config
    assert latest_id == config2.id
    
    # Test with non-existent subject
    with pytest.raises(ValueError, match="No exam config found for subject"):
        await exam.get_latest_exam_config_id(session, 99999)


@pytest.mark.asyncio
async def test_create_configs_with_empty_student_tuples(session):
    """Test create_configs function with empty student tuples list"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    # Add questions to the topic
    for i in range(4):
        question = Question(topic_id=topic.id, question_text=f"Question {i+1}")
        session.add(question)
    await session.commit()
    
    exam_specs = {
        "subject_id": subject.id,
        "fraction": 60,
        "topics": [str(topic.id)],
        "number_questions": {str(topic.id): 4},
        "relative_quotations": {str(topic.id): 1.8}
    }
    
    # Test with empty list
    exam_config, topic_configs = await exam.create_configs(session, exam_specs, [])
    
    # Should behave same as None
    assert exam_config.nmec_name_list is None


@pytest.mark.asyncio
async def test_create_configs_with_malformed_student_tuples(session):
    """Test create_configs function handles malformed student tuples gracefully"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    # Add questions to the topic
    for i in range(2):
        question = Question(topic_id=topic.id, question_text=f"Question {i+1}")
        session.add(question)
    await session.commit()
    
    exam_specs = {
        "subject_id": subject.id,
        "fraction": 80,
        "topics": [str(topic.id)],
        "number_questions": {str(topic.id): 2},
        "relative_quotations": {str(topic.id): 1.0}
    }
    
    # Test with malformed tuples - should raise ValueError
    malformed_tuples = [
        (12345, "John Doe"),  # Missing email
    ]
    
    # This should raise a ValueError due to unpacking mismatch
    with pytest.raises(ValueError, match="not enough values to unpack"):
        await exam.create_configs(session, exam_specs, malformed_tuples)
