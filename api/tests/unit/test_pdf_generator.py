import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock
from src.services.pdf_generator import xml_to_latex, compile_latex_to_pdf, xml_to_pdf

def test_xml_to_latex():
    xml_string = """
    <exam>
        <question weight="2.5">
            <text>What is 2+2?</text>
            <options>
                <option correct="false">3</option>
                <option correct="true">4</option>
            </options>
        </question>
        <question weight="1.0">
            <text>Capital of France?</text>
            <options>
                <option correct="true">Paris</option>
                <option correct="false">London</option>
            </options>
        </question>
    </exam>
    """
    root = ET.fromstring(xml_string)
    
    latex_doc, t_variants = xml_to_latex(root, exam_id=123)
    
    # Check if exam ID is replaced
    assert "123" in latex_doc
    assert "__EXAM_ID__" not in latex_doc
    
    # Check if questions are formatted correctly
    assert "\\question (2.5 pts) What is 2+2?" in t_variants
    assert "\\question (1.0 pts) Capital of France?" in t_variants
    
    # Check options
    assert "\\choice 3" in t_variants
    assert "\\CorrectChoice 4" in t_variants
    assert "\\CorrectChoice Paris" in t_variants
    assert "\\choice London" in t_variants

def test_xml_to_latex_missing_options_and_weight():
    xml_string = """
    <exam>
        <question>
            <text>Open ended question?</text>
        </question>
    </exam>
    """
    root = ET.fromstring(xml_string)
    
    latex_doc, t_variants = xml_to_latex(root, exam_id=456)
    
    assert "\\question (1.0 pts) Open ended question?" in t_variants
    assert "\\begin{choices}" not in t_variants

@patch("src.services.pdf_generator.build_pdf")
def test_compile_latex_to_pdf(mock_build_pdf):
    # Mock the return of build_pdf to be some dummy bytes
    mock_pdf = MagicMock()
    mock_pdf.__bytes__ = lambda self: b"%PDF-1.4 dummy pdf"
    mock_pdf.__iter__ = lambda self: iter([b"%PDF-1.4 dummy pdf"]) # In case it's converted to bytes via list
    # The build_pdf returns an object that can be cast to bytes.
    # We can just make mock_build_pdf return a string or bytes.
    # Actually build_pdf usually returns a PDF object. 
    # Calling bytes(pdf) calls its __bytes__ method.
    class DummyPDF:
        def __bytes__(self):
            return b"dummy_pdf_content"
            
    mock_build_pdf.return_value = DummyPDF()
    
    latex_content = "\\documentclass{article}\\begin{document}Test\\end{document}"
    t_variants_content = "\\question (1.0 pts) Test"
    
    result = compile_latex_to_pdf(latex_content, t_variants_content, subject_name="Math 101")
    
    assert result == b"dummy_pdf_content"
    mock_build_pdf.assert_called_once()
    
    # Check the arguments to build_pdf
    args, kwargs = mock_build_pdf.call_args
    assert args[0] == latex_content
    assert "texinputs" in kwargs

@patch("src.services.pdf_generator.compile_latex_to_pdf")
@patch("src.services.pdf_generator.xml_to_latex")
def test_xml_to_pdf(mock_xml_to_latex, mock_compile_latex_to_pdf):
    mock_xml_to_latex.return_value = ("latex doc", "t variants")
    mock_compile_latex_to_pdf.return_value = b"pdf_bytes"
    
    xml_string = "<exam><question><text>Q1</text></question></exam>"
    
    result = xml_to_pdf(xml_string, exam_id=789, subject_name="History")
    
    assert result == b"pdf_bytes"
    
    mock_xml_to_latex.assert_called_once()
    # The first argument is an Element object
    root_arg = mock_xml_to_latex.call_args[0][0]
    assert root_arg.tag == "exam"
    assert mock_xml_to_latex.call_args[0][1] == 789
    
    mock_compile_latex_to_pdf.assert_called_once_with("latex doc", "t variants", "History")
