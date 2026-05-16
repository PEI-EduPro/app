import base64
import numpy as np
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from src.utils import decode_base64_image


@pytest.mark.asyncio
async def test_decode_base64_image_invalid_base64():
    with pytest.raises(HTTPException) as exc:
        await decode_base64_image("invalid-base64!!!")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_decode_base64_image_fail_load():
    b64_img = base64.b64encode(b"not-an-image").decode()
    with patch("cv2.imread", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await decode_base64_image(b64_img)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_decode_base64_image_no_qr():
    b64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BvAAnMAk8X8G6LAAAAAElFTkSuQmCC"
    with patch("cv2.imread", return_value=np.zeros((10, 10, 3), dtype=np.uint8)), \
         patch("src.utils._detect_qr", return_value=""):
        with pytest.raises(HTTPException) as exc:
            await decode_base64_image(b64_img)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_decode_base64_image_not_digit_qr():
    b64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BvAAnMAk8X8G6LAAAAAElFTkSuQmCC"
    with patch("cv2.imread", return_value=np.zeros((10, 10, 3), dtype=np.uint8)), \
         patch("src.utils._detect_qr", return_value="abc"):
        with pytest.raises(HTTPException) as exc:
            await decode_base64_image(b64_img)
        assert exc.value.status_code == 400
