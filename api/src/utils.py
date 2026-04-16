import base64
import os
import cv2
from fastapi import File, HTTPException, UploadFile
from bs4 import BeautifulSoup

IMAGES_DIR = os.getenv("IMAGES_DIR", "/tmp")



def decode_base64_image(base64_str: str) -> tuple[int, str]:
    """Decode a base64 image, save it temporarily, and read its QR code.

    Returns:
        Tuple of (exam_id, temp_file_path)
    """
    # Extract MIME type and strip data URI prefix if present
    mime_type = "image/jpeg"  # default
    if "," in base64_str:
        header, base64_str = base64_str.split(",", 1)
        # Extract MIME type from header like "data:image/jpeg;base64"
        if "data:" in header:
            mime_part = header.split(";")[0]  # "data:image/jpeg"
            if "/" in mime_part:
                mime_type = mime_part.split("/")[1]  # "image/jpeg"

    # Map MIME type to file extension
    ext_map = {"jpeg": ".jpg", "jpg": ".jpg", "png": ".png"}
    ext = ext_map.get(mime_type.split("/")[1] if "/" in mime_type else mime_type, ".jpg")

    try:
        image_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {e}")

    os.makedirs(IMAGES_DIR, exist_ok=True)
    temp_file_path = os.path.join(IMAGES_DIR, f"exam_{os.urandom(8).hex()}{ext}")
    with open(temp_file_path, "wb") as buffer:
        buffer.write(image_bytes)

    img = cv2.imread(temp_file_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Failed to load the uploaded image.")

    detector = cv2.QRCodeDetector()
    id_str, _, _ = detector.detectAndDecode(img)


    if not id_str:
        raise HTTPException(status_code=400, detail="Failed find an ID from the QR code.")

    if not id_str.isdigit():
        raise HTTPException(status_code=400, detail=f"Failed to decode a valid ID from the QR code. (I.E, the QR code that was read did not have only digits). We read: {id_str}")

    return int(id_str), temp_file_path


def clean_text(xml_text: str) -> str:
    """Remove XML tags (like <p>) and return plain text."""
    if not xml_text:
        return ""
    return BeautifulSoup(xml_text, "xml").get_text().strip()

def parse_moodle_xml(xml_content):
    soup = BeautifulSoup(xml_content, 'xml')
    topics = {}
    current_topic = None

    for q in soup.find_all('question'):
        q_type = q.get('type')

        if q_type in ["multichoice", "shortanswer"]:
            current_topic = q.find("name").find("text").get_text(strip=True)
            
            if not current_topic:
                # fallback if no topic found yet
                current_topic = "Default Topic"

            if current_topic not in topics:
                topics[current_topic] = {"name": current_topic, "questions": []}

            dirty_question_text = q.find('questiontext').text.replace("<br>", " / ") if q.find('text') else ""
            question_text_plain = clean_text(dirty_question_text)

            options = []
            for ans in q.find_all('answer'):
                dirty_ans_text = ans.find('text').text.replace("<br>", " / ") if ans.find('text') else ""
                ans_text = clean_text(dirty_ans_text)
                fraction = float(ans.get('fraction', 0))
                options.append({"text": ans_text, "fraction": fraction})

            topics[current_topic]["questions"].append({
                "text": question_text_plain,
                "options": options
            })

    return {"topics": list(topics.values())}

async def read_QR(file: UploadFile = File(...)):
    """Read QR code from the uploaded image and return the decoded data."""
    
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only PNG and JPEG files are accepted.")

    # Save the uploaded file to the captures directory
    os.makedirs(IMAGES_DIR, exist_ok=True)
    temp_file_path = os.path.join(IMAGES_DIR, file.filename)
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Always release the file buffer when done
    await file.close()

    # Load image and decode QR
    img = cv2.imread(temp_file_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Failed to load the uploaded image.")
    
    detector = cv2.QRCodeDetector()
    id_str, _, _ = detector.detectAndDecode(img)

    if not id_str or not id_str.isdigit():
        raise HTTPException(status_code=400, detail="Failed to decode a valid ID from the QR code.")

    id = int(id_str)

    return id, temp_file_path


