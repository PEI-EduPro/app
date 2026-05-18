import pytest
import numpy as np
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.omr import evaluate_exam
from src.models.exam import Exam
from src.models.exam_config import ExamConfig

@pytest.fixture
def mock_image():
    return np.zeros((1000, 1000, 3), dtype=np.uint8)

@pytest.mark.asyncio
async def test_evaluate_exam_qr_not_found(session, mock_image):
    from src.models.subject import Subject
    sub = Subject(name="OMR Sub")
    session.add(sub)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=0)
    session.add(ec)
    await session.commit()
    
    exam = Exam(exam_config_id=ec.id, answer_key={}, relative_weights={})
    session.add(exam)
    await session.commit()
    
    with patch("src.services.omr.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = ec
        
        with patch("cv2.imread", return_value=mock_image), \
             patch("cv2.QRCodeDetector.detect", return_value=(False, None)):
            
            with pytest.raises(ValueError, match="Could not detect the QR code"):
                await evaluate_exam(session, exam, "fake_path.jpg")

@pytest.mark.asyncio
async def test_evaluate_exam_grid_not_found(session, mock_image):
    from src.models.subject import Subject
    sub = Subject(name="OMR Sub")
    session.add(sub)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=0)
    session.add(ec)
    await session.commit()
    
    exam = Exam(exam_config_id=ec.id, answer_key={}, relative_weights={})
    session.add(exam)
    await session.commit()
    
    with patch("src.services.omr.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = ec
        
        with patch("cv2.imread", return_value=mock_image), \
             patch("cv2.QRCodeDetector.detect", return_value=(True, np.array([[[10, 10], [50, 10], [50, 50], [10, 50]]]))), \
             patch("cv2.findContours", return_value=([], None)):
            
            with pytest.raises(Exception, match="could not locate the answer grid"):
                await evaluate_exam(session, exam, "fake_path.jpg")

@pytest.mark.asyncio
async def test_evaluate_exam_success(session, mock_image):
    from src.models.subject import Subject
    sub = Subject(name="OMR Sub")
    session.add(sub)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=10)
    session.add(ec)
    await session.commit()

    # Setup exam with 2 questions
    answer_key = {0: 1, 1: 2} # Q0: B, Q1: C
    relative_weights = {0: 1.0, 1: 1.0}
    exam = Exam(exam_config_id=ec.id, answer_key=answer_key, relative_weights=relative_weights)
    session.add(exam)
    await session.commit()
    
    with patch("src.services.omr.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = ec
        
        # Mock CV2 functions to simulate a successful detection and OMR process
        with patch("cv2.imread", return_value=mock_image), \
             patch("cv2.QRCodeDetector.detect", return_value=(True, np.array([[[10, 10], [100, 10], [100, 100], [10, 100]]]))), \
             patch("cv2.findContours") as mock_find_cnts, \
             patch("cv2.contourArea", side_effect=lambda c: 10000.0), \
             patch("cv2.boundingRect", return_value=(10, 200, 400, 400)), \
             patch("cv2.convexHull", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]]])), \
             patch("cv2.arcLength", return_value=1600.0), \
             patch("cv2.approxPolyDP", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]]])), \
             patch("cv2.warpPerspective", return_value=np.zeros((600, 600, 3), dtype=np.uint8)), \
             patch("cv2.threshold", return_value=(None, np.zeros((600, 600), dtype=np.uint8))), \
             patch("cv2.countNonZero") as mock_count, \
             patch("cv2.imwrite"), \
             patch("os.path.dirname", return_value="/tmp"), \
             patch("os.path.basename", return_value="exam.jpg"):
            
            # Mock findContours to return one candidate
            mock_find_cnts.return_value = ([np.zeros((4, 1, 2), dtype=np.int32)], None)
            
            # Mock countNonZero to simulate filled circles
            def count_side_effect(cell):
                if not hasattr(count_side_effect, 'counter'):
                    count_side_effect.counter = 0
                
                val = 0
                if count_side_effect.counter == 1: val = 100
                if count_side_effect.counter == 6: val = 100
                
                count_side_effect.counter += 1
                return val
                
            mock_count.side_effect = count_side_effect
            
            await evaluate_exam(session, exam, "fake_path.jpg")
            
            assert exam.grade > 0
            results = json.loads(exam.results)
            assert results["0"]["B"] is True
            assert results["1"]["C"] is True

@pytest.mark.asyncio
async def test_evaluate_exam_success(session, mock_image):
    from src.models.subject import Subject
    sub = Subject(name="OMR Sub")
    session.add(sub)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=10)
    session.add(ec)
    await session.commit()

    # Setup exam with 2 questions
    answer_key = {0: 1, 1: 2} # Q0: B, Q1: C
    relative_weights = {0: 1.0, 1: 1.0}
    exam = Exam(exam_config_id=ec.id, answer_key=answer_key, relative_weights=relative_weights)
    session.add(exam)
    await session.commit()
    
    with patch("src.services.omr.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = ec
        
        # Mock CV2 functions and the new Keras model
        with patch("cv2.imread", return_value=mock_image), \
             patch("cv2.QRCodeDetector.detect", return_value=(True, np.array([[[10, 10], [100, 10], [100, 100], [10, 100]]]))), \
             patch("cv2.findContours") as mock_find_cnts, \
             patch("cv2.contourArea", side_effect=lambda c: 10000.0), \
             patch("cv2.boundingRect", return_value=(10, 200, 400, 400)), \
             patch("cv2.convexHull", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]]])), \
             patch("cv2.arcLength", return_value=1600.0), \
             patch("cv2.approxPolyDP", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]]])), \
             patch("cv2.warpPerspective", return_value=np.zeros((600, 600, 3), dtype=np.uint8)), \
             patch("cv2.imwrite"), \
             patch("os.path.dirname", return_value="/tmp"), \
             patch("os.path.basename", return_value="exam.jpg"), \
             patch("src.services.omr.model.predict") as mock_predict:
            
            # Mock findContours to return one candidate
            mock_find_cnts.return_value = ([np.zeros((4, 1, 2), dtype=np.int32)], None)
            
            # Mock the Keras CNN predictions
            # 2 questions * 4 options = 8 cells.
            # Classes: 0='empty', 1='erased', 2='selected'
            mock_preds = np.array([[1.0, 0.0, 0.0]] * 8) # Set all to 'empty' initially
            
            mock_preds[2] = [0.0, 0.0, 1.0] # Select Q0_B
            mock_preds[5] = [0.0, 0.0, 1.0] # Select Q1_C
            
            mock_predict.return_value = mock_preds
            
            await evaluate_exam(session, exam, "fake_path.jpg")
            
            assert exam.grade > 0
            results = json.loads(exam.results)
            assert results["0"]["B"] is True
            assert results["1"]["C"] is True

@pytest.mark.asyncio
async def test_evaluate_exam_fallback_bounding_box(session, mock_image):
    from src.models.subject import Subject
    sub = Subject(name="OMR Sub")
    session.add(sub)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=0)
    session.add(ec)
    await session.commit()

    # Setup exam with 1 question
    answer_key = {0: 0}
    relative_weights = {0: 1.0}
    exam = Exam(exam_config_id=ec.id, answer_key=answer_key, relative_weights=relative_weights)
    session.add(exam)
    await session.commit()
    
    with patch("src.services.omr.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = ec
        
        with patch("cv2.imread", return_value=mock_image), \
             patch("cv2.QRCodeDetector.detect", return_value=(True, np.array([[[10, 10], [100, 10], [100, 100], [10, 100]]]))), \
             patch("cv2.findContours", return_value=([np.zeros((5, 1, 2), dtype=np.int32)], None)), \
             patch("cv2.contourArea", return_value=10000.0), \
             patch("cv2.boundingRect", return_value=(200, 200, 400, 400)), \
             patch("cv2.convexHull", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]], [[400,400]]])), \
             patch("cv2.arcLength", return_value=1600.0), \
             patch("cv2.approxPolyDP", return_value=np.array([[[200,200]], [[600,200]], [[600,600]], [[200,600]], [[400,400]]])), \
             patch("cv2.warpPerspective", return_value=np.zeros((600, 600, 3), dtype=np.uint8)), \
             patch("cv2.threshold", return_value=(None, np.zeros((600, 600), dtype=np.uint8))), \
             patch("cv2.countNonZero", return_value=0), \
             patch("cv2.imwrite"), \
             patch("os.path.dirname", return_value="/tmp"), \
             patch("os.path.basename", return_value="exam.jpg"):
            
            # approxPolyDP returns 5 points, triggering the fallback to boundingRect
            await evaluate_exam(session, exam, "fake_path.jpg")
            assert exam.grade == 0
