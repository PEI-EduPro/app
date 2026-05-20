import json
import logging
import cv2
import imutils
import json
import logging
import numpy as np
import os
from imutils.perspective import order_points
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.exam import Exam
from src.models.exam_config import ExamConfig, ExamState
from src.models.warning import Warning, WarningType
from src.services.exam import get_exam_config_by_id
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)

# Settings
NUM_OPTIONS = 4
MODEL_FILE = "src/cnn_models/15_05_2026.keras"
logger.info(f"Loading existing CNN model {MODEL_FILE}...")
model = load_model(MODEL_FILE)
classes = ['empty', 'erased', 'selected']

async def evaluate_exam(
    session: AsyncSession,
    exam: Exam,
    image_path: str
):
    """Evaluates Exam from given image using CNN."""

    exam_config_id = exam.exam_config_id
    exam_config = await get_exam_config_by_id(session, exam_config_id)

    fraction = exam_config.fraction
    answer_key = {int(k): v for k, v in exam.answer_key.items()}
    relative_weights = {int(k): v for k, v in exam.relative_weights.items()}
    num_questions = len(answer_key)

    # Extract Images via OpenCV
    cropped_table, padded_table, pad_x, pad_y, maxW, maxH = isolate_and_crop_table(image_path, num_questions)

    # Extract Cells & Run CNN 
    cells = extract_cells_math(cropped_table, num_questions)
    cells_array = np.array(cells).reshape(-1, 32, 32, 1) / 255.0
    
    predictions = model.predict(cells_array, verbose=0)
    predicted_classes = np.argmax(predictions, axis=1)

    # Base image for drawing
    padded_img = cv2.imread(padded_table)
    
    # Dynamically calculate cell size
    cell_h = maxH / (NUM_OPTIONS + 1.0)
    cell_w = maxW / (num_questions + 1.0)
    pad = 2 

    answers_details = dict()
    answered_dict = dict()

    # Grade the Exam and Draw Boxes
    for q in range(num_questions):
        answers_details[q] = {"erased": 0, "correct": 0, "incorrect": 0}
        answered_dict[str(q)] = dict()

        valid_selected = []
        erased_selected = []
        
        # Parse CNN predictions for this specific question
        for opt in range(NUM_OPTIONS):
            idx = (opt * num_questions) + q 
            pred_name = classes[predicted_classes[idx]]
            
            option_letter = chr(65 + opt)
            answered_dict[str(q)][option_letter] = (pred_name == "selected")
            
            if pred_name == "selected":
                valid_selected.append(opt)
            elif pred_name == "erased":
                erased_selected.append(opt)
                answers_details[q]["erased"] += 1

        k = answer_key.get(q)

        # Draw the boxes
        for opt in range(NUM_OPTIONS):
            y1 = int((opt + 1) * cell_h) + pad
            y2 = int((opt + 2) * cell_h) - pad
            x1 = int((q + 1) * cell_w) + pad
            x2 = int((q + 2) * cell_w) - pad
            
            # Shift the coordinates outward by pad_x and pad_y
            p_y1, p_y2 = y1 + pad_y, y2 + pad_y
            p_x1, p_x2 = x1 + pad_x, x2 + pad_x
            
            # Draw standard black box around the cell
            cv2.rectangle(padded_img, (p_x1 - 2, p_y1 - 2), (p_x2 + 2, p_y2 + 2), (0, 0, 0), 2)

            # Draw Colored status boxes
            if opt in erased_selected:
                cv2.rectangle(padded_img, (p_x1, p_y1), (p_x2, p_y2), (255, 0, 0), 2) # Blue (Erased)
            elif opt in valid_selected:
                if opt == k:
                    cv2.rectangle(padded_img, (p_x1, p_y1), (p_x2, p_y2), (30, 179, 0), 2) # Green (Correct)
                    answers_details[q]["correct"] += 1
                else:
                    cv2.rectangle(padded_img, (p_x1, p_y1), (p_x2, p_y2), (0, 0, 255), 2) # Red (Incorrect)
                    answers_details[q]["incorrect"] += 1

    # Calculate Final Score
    total_exam_score = 0.0
    sum_weights = sum(relative_weights.values())

    for q, info in answers_details.items():
        q_weight = relative_weights[q]
        q_value = (q_weight / sum_weights) * 20.0
        penalty_per_wrong = q_value * (fraction / 100.0)
        q_score = (info["correct"] * q_value) - (info["incorrect"] * penalty_per_wrong)
        total_exam_score += q_score

    total_exam_score = max(0.0, total_exam_score)
    print(f"\nFINAL EXAM SCORE: {total_exam_score:.2f} / 20.00")

    # Save Images & Update Database
    padded_table_path_corrected = image_path.replace(".", "_padded_table_corrected.") 
    cv2.imwrite(padded_table_path_corrected, padded_img)
    print(f"Saved padded visual annotation to: {padded_table_path_corrected}")

    exam.grade = total_exam_score
    exam.results = json.dumps(answered_dict)
    exam.capture_path = cropped_table          
    exam.correction_path = padded_table_path_corrected
    exam.validated = False

    session.add(exam)
    await session.commit()
    await session.refresh(exam)

def isolate_and_crop_table(image_path, num_questions):
    """
    Locates the answer grid using the QR code as an anchor, flattens it, 
    and saves a cleanly cropped image of just the grid.
    """
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Could not load image at {image_path}")
        raise FileNotFoundError(f"Could not load image at {image_path}")

    # Detect QR Code using the robust multi-pass method
    bbox = get_robust_qr_bbox(image)

    if bbox is None:
        logger.error("Could not detect the QR code")
        raise ValueError("Could not detect the QR code")

    # Naming conventions
    cropped_table_path = image_path.replace(".", "_cropped_table.")                     
    padded_table_path = image_path.replace(".", "_padded_table.")                       

    # Extract QR Code bounding box geometry
    qr_pts = bbox[0]
    qr_x_min = int(min(qr_pts[:, 0]))
    qr_x_max = int(max(qr_pts[:, 0]))
    qr_y_min = int(min(qr_pts[:, 1]))
    qr_y_max = int(max(qr_pts[:, 1]))
    qr_w = qr_x_max - qr_x_min
    qr_h = qr_y_max - qr_y_min
    qr_cx = qr_x_min + (qr_w / 2.0)

    # Preprocess the image for Grid Extraction
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    # Use a small kernel (3x3 or 5x5) so we ONLY fix minor breaks in the solid grid lines.
    # The widely spaced dots of the outer border will remain disconnected, 
    # preventing the algorithm from detecting it as the largest contour.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)) 
    
    # Apply the close operation
    closed_image = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    # Find contours on the CLOSED image
    cnts = cv2.findContours(closed_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # A 1-question grid is very tall (ratio ~ 0.3)
    # A 20-question grid is very wide (ratio ~ 5.0)
    min_ratio = 0.2
    max_ratio = 8.0

    # Dynamically find the target box (The solid grid)
    targetCnt = None
    for c in cnts:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h) if h > 0 else 0
        c_cx = x + (w / 2.0)
        c_cy = y + (h / 2.0)
        x_diff = abs(qr_cx - c_cx)
        
        # 1. Is it physically located below the QR code?
        is_below = c_cy > (qr_y_max - (qr_h * 0.5))
        
        # 2. Is it horizontally aligned with the QR code?
        is_aligned_horizontally = x_diff < (qr_w * 2.5) # Relaxed to 2.5 just in case
        
        # 3. Is it a substantial block on the page? (Relaxed to 0.8x QR size)
        is_larger_than_qr = area > (qr_w * qr_h * 0.8)
        
        # 4. Does the shape make remote sense?
        is_valid_shape = min_ratio < aspect_ratio < max_ratio
        
        if is_below and is_aligned_horizontally and is_larger_than_qr and is_valid_shape:
            # Wrap the grid in a tight polygon to ignore inner lines/noise
            hull = cv2.convexHull(c)
            pts = hull.reshape(-1, 2)
            
            # Find the absolute 4 corners mathematically
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            
            tl = pts[np.argmin(s)]       # Top-Left
            br = pts[np.argmax(s)]       # Bottom-Right
            tr = pts[np.argmin(diff)]    # Top-Right
            bl = pts[np.argmax(diff)]    # Bottom-Left
            
            # Use these exact corners for the perfect perspective warp
            targetCnt = np.array([tl, tr, br, bl], dtype="float32")
            break

    if targetCnt is None:
        logger.error("Found the QR Code, but could not locate the answer grid below it.")
        raise Exception("Found the QR Code, but could not locate the answer grid below it.")

    # Perspective Transform (Tight Crop & Flatten)
    rect = order_points(targetCnt.reshape(4, 2))
    (tl, tr, br, bl) = rect

    # Calculate width and height of the inner grid
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # TIGHT CROP (For the CNN to read)
    dst_tight = np.array([
        [0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]
    ], dtype="float32")
    M_tight = cv2.getPerspectiveTransform(rect, dst_tight)
    clean_grid = cv2.warpPerspective(image, M_tight, (maxWidth, maxHeight))
    cv2.imwrite(cropped_table_path, clean_grid)

    # PADDED CROP (For the Visual Annotation)
    pad_x = int(maxWidth * 0.15)
    pad_y = int(maxHeight * 0.60)
    dst_padded = np.array([
        [pad_x, pad_y],
        [maxWidth - 1 + pad_x, pad_y],
        [maxWidth - 1 + pad_x, maxHeight - 1 + pad_y],
        [pad_x, maxHeight - 1 + pad_y]
    ], dtype="float32")

    warped_w = maxWidth + (2 * pad_x)
    warped_h = maxHeight + (2 * pad_y)
    M_padded = cv2.getPerspectiveTransform(rect, dst_padded)
    padded_grid = cv2.warpPerspective(image, M_padded, (warped_w, warped_h))
    
    cv2.imwrite(padded_table_path, padded_grid)

    print(f"Successfully saved crops to {cropped_table_path} and {padded_table_path}")
    
    # Return EVERYTHING for the exact coordinate mapping
    return cropped_table_path, padded_table_path, pad_x, pad_y, maxWidth, maxHeight

def extract_cells_math(clean_grid_path, num_questions):
    """
    Slices a perfectly flattened grid image into individual cells using math.
    Dynamically adapts columns based on num_questions from the database!
    """
    img = cv2.imread(clean_grid_path)
    if img is None:
        logger.error(f"Could not load image at {clean_grid_path}")
        raise ValueError(f"Could not load image at {clean_grid_path}")

    h, w = img.shape[:2]
    
    total_rows = NUM_OPTIONS + 1
    total_cols = num_questions + 1
    
    cell_h = h / total_rows
    cell_w = w / total_cols

    cells = []
    margin_h = int(cell_h * 0.15)
    margin_w = int(cell_w * 0.15)

    for row in range(total_rows):
        if row == 0: continue
            
        for col in range(total_cols):
            if col == 0: continue
                
            y1, y2 = int(row * cell_h), int((row + 1) * cell_h)
            x1, x2 = int(col * cell_w), int((col + 1) * cell_w)
            
            cell_crop = img[y1 + margin_h : y2 - margin_h, x1 + margin_w : x2 - margin_w]
            cell_gray = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2GRAY)
            cell_ready = cv2.resize(cell_gray, (32, 32))
            
            cells.append(cell_ready)

    return cells

def get_robust_qr_bbox(image):
    """
    Attempts to detect a QR code using multiple image processing techniques.
    """
    detector = cv2.QRCodeDetector()
    
    # Original
    retval, bbox = detector.detect(image)
    if retval and bbox is not None: return bbox

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    retval, bbox = detector.detect(gray)
    if retval and bbox is not None: return bbox

    # Simple Thresh
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    retval, bbox = detector.detect(thresh)
    if retval and bbox is not None: return bbox

    # Adaptive Thresh
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    retval, bbox = detector.detect(adaptive)
    if retval and bbox is not None: return bbox
    
    # Blurred Adaptive
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    adaptive_blur = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5)
    retval, bbox = detector.detect(adaptive_blur)
    if retval and bbox is not None: return bbox

    return None
