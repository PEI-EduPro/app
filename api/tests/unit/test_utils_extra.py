import pytest
import base64
import os
import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock
from src.utils import _detect_qr, decode_base64_image, clean_text, parse_moodle_xml, read_QR

def test_clean_text():
    assert clean_text("<p>Hello</p>") == "Hello"
    assert clean_text(None) == ""
    assert clean_text("<text>Just text</text>") == "Just text"

def test_detect_qr_multiple_strategies():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    with patch("cv2.QRCodeDetector.detectAndDecode") as mock_detect:
        # Strategy 1 fails, Strategy 2 fails, Strategy 3 succeeds
        mock_detect.side_effect = [("", None, None), ("", None, None), ("123", None, None)]
        assert _detect_qr(img) == "123"
        assert mock_detect.call_count == 3

def test_detect_qr_all_fail():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    with patch("cv2.QRCodeDetector.detectAndDecode", return_value=("", None, None)):
        assert _detect_qr(img) == ""

def test_decode_base64_image_invalid_base64():
    with pytest.raises(HTTPException) as exc:
        decode_base64_image("invalid-base64!!!")
    assert exc.value.status_code == 400
    assert "Invalid base64 encoding" in exc.value.detail

def test_decode_base64_image_fail_load():
    b64_img = base64.b64encode(b"not-an-image").decode()
    with patch("cv2.imread", return_value=None):
        with pytest.raises(HTTPException) as exc:
            decode_base64_image(b64_img)
        assert exc.value.status_code == 400
        assert "Failed to load" in exc.value.detail

def test_decode_base64_image_no_qr():
    # Valid transparent 1x1 PNG
    b64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BvAAnMAk8X8G6LAAAAAElFTkSuQmCC"
    with patch("cv2.imread", return_value=np.zeros((10,10,3), dtype=np.uint8)), \
         patch("src.utils._detect_qr", return_value=""):
        with pytest.raises(HTTPException) as exc:
            decode_base64_image(b64_img)
        assert exc.value.status_code == 400
        assert "Failed find an ID" in exc.value.detail

def test_decode_base64_image_not_digit_qr():
    b64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BvAAnMAk8X8G6LAAAAAElFTkSuQmCC"
    with patch("cv2.imread", return_value=np.zeros((10,10,3), dtype=np.uint8)), \
         patch("src.utils._detect_qr", return_value="abc"):
        with pytest.raises(HTTPException) as exc:
            decode_base64_image(b64_img)
        assert exc.value.status_code == 400
        assert "valid ID" in exc.value.detail

def test_parse_moodle_xml_empty_topic():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <quiz>
      <question type="multichoice">
        <name><text></text></name>
        <questiontext><text>Q1</text></questiontext>
        <answer fraction="100"><text>A1</text></answer>
      </question>
    </quiz>
    """
    result = parse_moodle_xml(xml)
    assert result["topics"][0]["name"] == "Default Topic"

@pytest.mark.asyncio
async def test_read_QR_invalid_type():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "text/plain"
    with pytest.raises(HTTPException) as exc:
        await read_QR(mock_file)
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_read_QR_fail_load():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"fake")
    mock_file.close = AsyncMock()
    
    with patch("cv2.imread", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await read_QR(mock_file)
        assert exc.value.status_code == 400
        assert "Failed to load" in exc.value.detail

@pytest.mark.asyncio
async def test_read_QR_no_id():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    mock_file.read = AsyncMock(return_value=b"fake")
    mock_file.close = AsyncMock()
    
    with patch("cv2.imread", return_value=np.zeros((10,10,3), dtype=np.uint8)), \
         patch("cv2.QRCodeDetector.detectAndDecode", return_value=("", None, None)):
        with pytest.raises(HTTPException) as exc:
            await read_QR(mock_file)
        assert exc.value.status_code == 400
        assert "Failed to decode" in exc.value.detail
