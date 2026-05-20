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
from src.services.warning import calculate_and_persist_warnings

logger = logging.getLogger(__name__)

# Settings (tune if needed)
NOISE_THRESHOLD = 30
NUM_OPTIONS = 4

async def evaluate_exam(
    session: AsyncSession,
    exam: Exam,
    image_path: str
):
    """Evaluates Exam from given image."""

    exam_config_id = exam.exam_config_id
    exam_config = await get_exam_config_by_id(session, exam_config_id)

    fraction = exam_config.fraction
    answer_key = {int(k): v for k, v in exam.answer_key.items()}
    relative_weights = {int(k): v for k, v in exam.relative_weights.items()}
    num_questions = len(answer_key)
    image = cv2.imread(image_path)

    # 1. Detect QR Code to use as an anchor
    qr_detector = cv2.QRCodeDetector()
    retval, bbox = qr_detector.detect(image)

    if not retval or bbox is None:
        raise ValueError("Could not detect the QR code. Please check image clarity.")

    # Extract QR Code bounding box geometry
    qr_pts = bbox[0]
    qr_x_min = int(min(qr_pts[:, 0]))
    qr_x_max = int(max(qr_pts[:, 0]))
    qr_y_min = int(min(qr_pts[:, 1]))
    qr_y_max = int(max(qr_pts[:, 1]))
    qr_w = qr_x_max - qr_x_min
    qr_h = qr_y_max - qr_y_min
    qr_cx = qr_x_min + (qr_w / 2.0)

    # 2. Preprocess the image for Grid Extraction
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # 3. Dynamically find the target box (The solid grid)
    candidates = []
    for c in cnts:
        area = cv2.contourArea(c)
        
        # Calculate bounding box and aspect ratio
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h) if h > 0 else 0
        
        c_cx = x + (w / 2.0)
        x_diff = abs(qr_cx - c_cx)
        
        # Flexible location checks: Grid should be near the QR code
        # We allow it to be below or side-by-side
        is_vertically_near = y > (qr_y_min - qr_h)
        is_horizontally_near = x_diff < (qr_w * 10.0) # Lenient alignment
        
        # Area check: must be at least comparable to the QR code
        is_significant = area > (qr_w * qr_h * 0.5)
        
        if is_vertically_near and is_horizontally_near and is_significant and aspect_ratio > 0.5:
            # Solidity check to ensure it's a solid-ish block (like a grid)
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            if solidity > 0.3: # Grids are relatively solid, but allow for noise/marks
                candidates.append(c)

    if not candidates:
        raise Exception("Found the QR Code, but could not locate the answer grid near it.")

    # Sort candidates by area and pick the largest one that is below/beside the QR
    candidates = sorted(candidates, key=cv2.contourArea, reverse=True)
    best_c = candidates[0]
    
    # Try to approximate to 4 points for perspective transform
    # Use the convex hull to smooth out any "X" marks that might protrude
    hull = cv2.convexHull(best_c)
    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, 0.02 * peri, True)
    
    if len(approx) == 4:
        target_cnt = approx
    else:
        # Fallback: use the bounding box corners if approximation fails
        # This ensures we always have 4 points for the perspective transform
        x, y, w, h = cv2.boundingRect(hull)
        target_cnt = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])

    # Capture dotted line area
    # Order the points of the solid grid
    rect = order_points(target_cnt.reshape(4, 2))
    (tl, tr, br, bl) = rect

    # Calculate width and height of the inner grid
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Calculate padding based on the LaTeX "inner sep=1.5cm"
    # 1.5cm is approx 60% of the grid height, and 15% of the grid width
    pad_x = int(maxWidth * 0.15)
    pad_y = int(maxHeight * 0.60)

    # Destination points: The grid corners inside a LARGER padded canvas
    dst = np.array([
        [pad_x, pad_y],
        [maxWidth - 1 + pad_x, pad_y],
        [maxWidth - 1 + pad_x, maxHeight - 1 + pad_y],
        [pad_x, maxHeight - 1 + pad_y]
    ], dtype="float32")

    # The size of our final capture_path image
    warped_w = maxWidth + (2 * pad_x)
    warped_h = maxHeight + (2 * pad_y)

    # Execute the padded transform
    M = cv2.getPerspectiveTransform(rect, dst)
    outer_paper = cv2.warpPerspective(image, M, (warped_w, warped_h))
    outer_gray = cv2.warpPerspective(gray, M, (warped_w, warped_h))

    clean_crop = outer_paper.copy()

    # Apply Thresholding to the entire padded area
    outer_thresh = cv2.threshold(outer_gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # Extract strictly the inner grid for OMR pixel counting
    grid_thresh = outer_thresh[pad_y : pad_y + maxHeight, pad_x : pad_x + maxWidth]

    # divide the grid into 5 rows x 21 columns
    h, w = grid_thresh.shape
    cell_h = h / 5.0  
    cell_w = w / (num_questions + 1.0)

    # Define a margin (e.g., 15%) to ignore the thick grid borders
    margin_h = int(cell_h * 0.15)
    margin_w = int(cell_w * 0.15)

    answers_details = dict()
    answered_dict = dict()

    # iterate through each column (question) - skip first column
    for q in range(num_questions):
        cell_coords = []
        cell_totals = []
        answers_details[q] = dict()
        answered_dict[str(q)] = dict()
        
        erased = 0
        correct = 0
        incorrect = 0
        
        # iterate through each row (option) - skip first row
        for opt in range(NUM_OPTIONS):
            y1 = int((opt + 1) * cell_h)
            y2 = int((opt + 2) * cell_h)
            x1 = int((q + 1) * cell_w)
            x2 = int((q + 2) * cell_w)
            
            # CROP WITH MARGINS inside the grid_thresh
            cell = grid_thresh[y1 + margin_h : y2 - margin_h, x1 + margin_w : x2 - margin_w]
            total = cv2.countNonZero(cell)
            
            if total <= NOISE_THRESHOLD:
                total = 0
            
            cell_coords.append((x1, y1, x2, y2))
            cell_totals.append(total)
        
        max_fill = max(cell_totals) if max(cell_totals) > 0 else 1
        threshold = max(max_fill * 0.2, NOISE_THRESHOLD)
        
        selected = [i for i, total in enumerate(cell_totals) if total > threshold]
        
        valid_selected = []
        for opt in selected:
            x1, y1, x2, y2 = cell_coords[opt]
            eval_area = (x2 - x1 - (2 * margin_w)) * (y2 - y1 - (2 * margin_h))
            fill_ratio = cell_totals[opt] / eval_area if eval_area > 0 else 0
            
            if fill_ratio <= 0.85:  # not fully filled (not erased)
                valid_selected.append(opt)
                
        # Populate answered_dict based on valid_selected
        for opt in range(NUM_OPTIONS):
            option_letter = chr(65 + opt) 
            answered_dict[str(q)][option_letter] = (opt in valid_selected)
        
        k = answer_key[q]

        # Draw all cells in black on the OUTER PAPER (shifting by pad_x and pad_y)
        for opt in range(NUM_OPTIONS):
            x1, y1, x2, y2 = cell_coords[opt]
            cv2.rectangle(outer_paper, (x1 + pad_x, y1 + pad_y), (x2 + pad_x, y2 + pad_y), (0, 0, 0), 2)
        
        # Draw selected colored cells on the OUTER PAPER
        for opt in selected:
            x1, y1, x2, y2 = cell_coords[opt]
            eval_area = (x2 - x1 - (2 * margin_w)) * (y2 - y1 - (2 * margin_h))
            fill_ratio = cell_totals[opt] / eval_area if eval_area > 0 else 0
            
            if fill_ratio > 0.6:  # fully filled (blue)
                color = (255, 0, 0)
                erased += 1
            elif opt == k:  # correct (green)
                color = (0, 255, 0)
                correct += 1
            else:  # wrong (red)
                color = (0, 0, 255)
                incorrect += 1
            
            # Apply padding offset to position the color box directly over the inner grid
            p_x1, p_y1 = x1 + pad_x, y1 + pad_y
            p_x2, p_y2 = x2 + pad_x, y2 + pad_y
            
            # Draw inset rectangle
            cv2.rectangle(outer_paper, (p_x1 + 2, p_y1 + 2), (p_x2 - 2, p_y2 - 2), color, 3)

        answers_details[q]["erased"] = erased
        answers_details[q]["correct"] = correct
        answers_details[q]["incorrect"] = incorrect

    # Scoring logic
    total_exam_score = 0.0
    sum_weights = sum(relative_weights.values())

    for q, info in answers_details.items():
        q_weight = relative_weights[q]
        q_value = (q_weight / sum_weights) * 20.0
        penalty_per_wrong = q_value * (fraction / 100.0)
        q_score = (info["correct"] * q_value) - (info["incorrect"] * penalty_per_wrong)
        total_exam_score += q_score

    total_exam_score = max(0.0, total_exam_score)
    logger.info(f"FINAL EXAM SCORE: {total_exam_score:.2f} / 20.00")

    # Save the padded image as the final capture path
    dir_name = os.path.dirname(image_path)
    base_name = os.path.basename(image_path)
    name_parts = base_name.rsplit(".", 1)
    safe_correction_name = f"{name_parts[0]}_omr_correction.{name_parts[1]}"
    safe_clean_name = f"{name_parts[0]}_clean.{name_parts[1]}"
    clean_path = os.path.join(dir_name, safe_clean_name)
    cv2.imwrite(clean_path, clean_crop)
    correction_path = os.path.join(dir_name, safe_correction_name)
    cv2.imwrite(correction_path, outer_paper)

    # Persist results to the database
    exam.grade = total_exam_score
    exam.results = json.dumps(answered_dict)
    exam.validated = True

    exam.capture_path = clean_path          
    exam.correction_path = correction_path
    session.add(exam)
    await session.commit()
    await session.refresh(exam)

    # 2. Re-calculate all warnings (including the new one if nmec is missing)
    # This automatically transitions the state between WARNING_HANDLING and VALIDATION
    nmec_to_name = {}
    if exam_config.nmec_name_list:
        try:
            nmec_to_name = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse nmec_name_list for exam_config {exam_config.id}: invalid JSON")

    await calculate_and_persist_warnings(session, exam_config.id, exam_config.associations, nmec_to_name)

    await session.commit()
    await session.refresh(exam_config)