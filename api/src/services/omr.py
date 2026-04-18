from src.models.exam import Exam
from src.services.exam import get_exam_config_by_id
from sqlmodel.ext.asyncio.session import AsyncSession

from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2
import json

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

    # Detect QR Code to use as an anchor
    qr_detector = cv2.QRCodeDetector()
    retval, bbox = qr_detector.detect(image)

    if not retval or bbox is None:
        raise Exception("Could not detect the QR code. Please check image clarity.")

    # Extract QR Code bounding box geometry
    qr_pts = bbox[0]
    qr_x_min = int(min(qr_pts[:, 0]))
    qr_x_max = int(max(qr_pts[:, 0]))
    qr_y_min = int(min(qr_pts[:, 1]))
    qr_y_max = int(max(qr_pts[:, 1]))
    qr_w = qr_x_max - qr_x_min
    qr_h = qr_y_max - qr_y_min
    
    # Calculate the horizontal center line of the QR code
    qr_cy = qr_y_min + (qr_h / 2.0)

    # 2. Preprocess the image for Grid Extraction
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    # Sort contours by area (largest first)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # 3. Dynamically find the target box using relative spatial constraints
    targetCnt = None

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # We are looking for a quadrilateral (4 points)
        if len(approx) == 4:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # Center of the current contour
            c_cy = y + (h / 2.0)
            y_diff = abs(qr_cy - c_cy)
            
            # SPATIAL LOGIC: 
            # 1. To the right: Grid's X starts after the QR code (allowing slight margin of error)
            # 2. Aligned: Grid's center Y is roughly aligned with the QR code's center Y
            # 3. Size: Grid is strictly larger than the QR code (replaces brittle image_area % check)
            # 4. Shape: Grid is horizontally wide
            
            is_to_the_right = x > (qr_x_max - (qr_w * 0.5)) 
            is_aligned_horizontally = y_diff < (qr_h * 2.0)
            is_larger_than_qr = area > (qr_w * qr_h * 2.0)
            
            if is_to_the_right and is_aligned_horizontally and is_larger_than_qr and aspect_ratio > 3.0:
                targetCnt = approx
                break

    if targetCnt is None:
        raise Exception("Found the QR Code, but could not locate the adjacent answer grid.")

    # 4. Apply the perspective transform (Bird's-eye view) directly on the grid
    paper = four_point_transform(image, targetCnt.reshape(4, 2))
    warped = four_point_transform(gray, targetCnt.reshape(4, 2))

    # 3. Apply Thresholding
    thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    grid_paper = paper.copy()
    grid_thresh = thresh.copy()

    # divide the grid into 4 rows x 13 columns (Now 5 rows x 18 cols for the new format)
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
        
        # Initialize the sub-dictionary for the current question ---
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
            
            # CROP WITH MARGINS
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
                
        # Populate answered_dict based on valid_selected ---
        for opt in range(NUM_OPTIONS):
            option_letter = chr(65 + opt) # Converts 0->A, 1->B, 2->C, 3->D
            # True if the option is in valid_selected, False otherwise (including erased)
            answered_dict[str(q)][option_letter] = (opt in valid_selected)
        
        # draw all cells in black (using original outer coordinates for visual precision)
        for opt in range(NUM_OPTIONS):
            x1, y1, x2, y2 = cell_coords[opt]
            cv2.rectangle(grid_paper, (x1, y1), (x2, y2), (0, 0, 0), 2)
        
        k = answer_key[q]
        
        # draw all selected cells
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
            
            # Draw the rectangle slightly inset so it doesn't overlap the black grid lines
            cv2.rectangle(grid_paper, (x1+2, y1+2), (x2-2, y2-2), color, 3)

        answers_details[q]["erased"] = erased
        answers_details[q]["correct"] = correct
        answers_details[q]["incorrect"] = incorrect

    # Scoring logic
    total_exam_score = 0.0
    sum_weights = sum(relative_weights.values())

    for q, info in answers_details.items():
        q_weight = relative_weights[q]
        
        # Calculate base value of the question
        q_value = (q_weight / sum_weights) * 20.0
        
        # Calculate the penalty for an incorrect option
        penalty_per_wrong = q_value * (fraction / 100.0)
        
        # Calculate final score for this specific question
        q_score = (info["correct"] * q_value) - (info["incorrect"] * penalty_per_wrong)
        
        total_exam_score += q_score

    # Floor the total score at 0 to prevent negative exam results (optional)
    total_exam_score = max(0.0, total_exam_score)
    print(f"\nFINAL EXAM SCORE: {total_exam_score:.2f} / 20.00")

    # Persist results to the database
    exam.grade = total_exam_score
    exam.results = json.dumps(answered_dict)
    exam.results_details = answers_details
    exam.capture_path = image_path

    session.add(exam)
    await session.commit()
    await session.refresh(exam)

    # I am assuming this save is for debug. 
    # I would urge my colleagues to leave debugs in writting for future reference thought. Something like:
    # Debug => saving image to check it out.
    new_name = image_path.rsplit(".", 1)
    new_name = f"{new_name[0]}_omr_correction.{new_name[1]}"
    cv2.imwrite(new_name, grid_paper)