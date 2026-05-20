import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services import exam
from src.models.subject import Subject
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
import os

@pytest.mark.asyncio
async def test_generate_grades_report_pdf_no_pdflatex(session):
    """Test error handling when pdflatex is missing"""
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="pdflatex is not installed"):
            await exam.generate_grades_report_pdf(session, 1)

@pytest.mark.asyncio
async def test_generate_grades_report_pdf_success(session):
    """Test successful report generation (mocking pdflatex)"""
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(
        subject_id=subject.id, 
        exam_name="Midterm", 
        exam_date="2024-05-20"
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    exam_instance = Exam(
        exam_config_id=exam_config.id,
        nmec=12345,
        student_name="John Doe",
        grade=18.5,
        answer_key={"0": 0}, # To avoid issues with other functions if they check this
        relative_weights={"0": 1.0}
    )
    session.add(exam_instance)
    await session.commit()
    
    # We need to mock os.path.exists specifically for the report.pdf file
    original_exists = os.path.exists
    def side_effect_exists(path):
        if "report.pdf" in str(path):
            return True
        return original_exists(path)

    with patch("shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("anyio.run_process") as mock_run, \
         patch("os.path.exists", side_effect=side_effect_exists):
        
        # Mock anyio.open_file
        mock_file = MagicMock()
        # Reads: 1. template
        # Other calls are writes: UC.tex, date.tex, report.tex
        # Final read: report.pdf
        mock_file.__aenter__.return_value.read.side_effect = [
            "__EXAM_NAME__ __ROWS__",
            b"fake pdf content"
        ]
        mock_file.__aenter__.return_value.write = AsyncMock()
        
        with patch("anyio.open_file", return_value=mock_file):
            pdf_bytes = await exam.generate_grades_report_pdf(session, exam_config.id)
            assert pdf_bytes == b"fake pdf content"
            
            # Verify that pdflatex was "called"
            mock_run.assert_called_once()
            args, _ = mock_run.call_args
            assert args[0][0] == "pdflatex"
