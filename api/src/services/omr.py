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
    exam_config = get_exam_config_by_id(session, exam_config_id)

    fraction = exam_config.fraction
    answer_key = exam.answer_key
    relative_weights = exam.relative_weights
    num_questions = len(answer_key)
    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # 1. Dynamically find the target box contour (Directly looking for the grid now)
    targetCnt = None
    image_area = image.shape[0] * image.shape[1]

    for c in cnts:
        # Approximate the contour's shape
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # We are looking for a quadrilateral (4 points)
        if len(approx) == 4:
            area = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # INCREASE the minimum aspect ratio to bypass the taller instruction box.
            # The actual grid is much wider (approx 4.5 to 6.0)
            if area > 0.01 * image_area and 4.0 < aspect_ratio < 7.0:
                targetCnt = approx
                break

    if targetCnt is None:
        raise Exception("Could not find the target box contour. Please check image clarity or thresholds.")

    # 2. Apply the perspective transform (Bird's-eye view)
    paper = four_point_transform(image, targetCnt.reshape(4, 2))
    warped = four_point_transform(gray, targetCnt.reshape(4, 2))

    #cv2.imwrite("4.jpg", paper)
    #cv2.imwrite("5.jpg", warped)

    # 3. Apply Thresholding
    thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    #cv2.imwrite("6.jpg", thresh)

    # --- NEW SECTION: ISOLATE THE INNER ANSWER GRID ---
    # We skip the second inner contour search because we already warped directly 
    # to the grid above. We just assign variables to match your original flow.

    grid_paper = paper.copy()
    grid_thresh = thresh.copy()

    #cv2.imwrite("grid_only.jpg", grid_paper)

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
        
        # --- NEW: Initialize the sub-dictionary for the current question ---
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
                
        # --- NEW: Populate answered_dict based on valid_selected ---
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

    print("--- Answers Accuracy Details (Usado para fazer as somas e multiplicações com as cotações relativas) ---")
    print(json.dumps(answers_details, indent=2))

    print("--- Selected Options Dictionary (Usado para popular a grelha do frontend para ajustes manuais) ---")
    print(json.dumps(answered_dict, indent=2))

    for q, info in answers_details.items():
        total_detected = info["correct"] + info["incorrect"]
        if total_detected > 2:
            print(f"⚠️  Detector might have glitched on question {q+1}, detected {total_detected} options! ⚠️")

    #cv2.imwrite(f"exam_var_{version}.jpg", grid_paper)
    cv2.waitKey(0)

    # --- NEW: MATH & SCORING LOGIC ---
    total_exam_score = 0.0
    sum_weights = sum(relative_weights.values())

    print("\n--- Scoring Breakdown ---")
    for q, info in answers_details.items():
        q_weight = relative_weights[q]
        
        # Calculate base value of the question
        q_value = (q_weight / sum_weights) * 20.0
        
        # Calculate the penalty for an incorrect option
        penalty_per_wrong = q_value * (fraction / 100.0)
        
        # Calculate final score for this specific question
        q_score = (info["correct"] * q_value) - (info["incorrect"] * penalty_per_wrong)
        
        total_exam_score += q_score
        print(f"Q{q+1:02d}: Weight={q_weight} | Value={q_value:.2f} | Correct={info['correct']}, Wrong={info['incorrect']} | Score={q_score:.3f}")

    # Floor the total score at 0 to prevent negative exam results (optional)
    total_exam_score = max(0.0, total_exam_score)

    print(f"\n✅ FINAL EXAM SCORE: {total_exam_score:.2f} / 20.00")
    #cv2.imwrite(f"exam_var_{version}.jpg", grid_paper)
    new_name = image_path.split(".")
    new_name[0] = new_name[0]+"_omr_correction"
    new_name = "".join(new_name)
    cv2.imwrite(f"{new_name}", grid_paper)

    '''
    # --- BEGINNING: FOOTER ---
    # 1. Get current warped grid dimensions
    h, w = grid_paper.shape[:2]

    # Define generic styling based on image width to keep it consistent
    # even if images are varying resolutions
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.7, w / 1600.0)    # Dynamic font scaling based on width
    thickness = max(2, int(w / 1000.0))  # Dynamic thickness based on width

    # Define color constants (BGR format)
    COLOR_GREEN = (0, 255, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_BLUE = (255, 0, 0)
    COLOR_BLACK = (0, 0, 0)

    # Define lines and their associated colors
    # We use standard letters here. NOTE: If your system font 
    # struggles with portuguese accents (ã, ê, à), you can replace
    # them with standard letters (e.g., Nao contabilizada).
    lines = [
        ("Verde - Resposta Assinalada Correta", COLOR_GREEN),
        ("", COLOR_BLACK),
        ("Vermelho - Resposta Assinalada Incorreta", COLOR_RED),
        ("", COLOR_BLACK),
        ("Azul - Resposta Rasurada (Nao contabilizada)", COLOR_BLUE),
        ("", COLOR_BLACK),
        (f"Nota: {total_exam_score:.2f}/20", COLOR_BLACK)
    ]

    # 2. Define Footer Height
    # Estimate the height needed based on line spacing and margin
    # 4 lines + margin top/bottom
    line_height_padding = int(50 * (w / 1920.0)) # Scale spacing based on width
    footer_height = (len(lines) + 1) * line_height_padding

    # 3. Create a clean white footer canvas
    footer = np.full((footer_height, w, 3), 255, dtype=np.uint8)

    # 4. Draw the text lines onto the white footer
    x_pos = int(w * 0.05) # 5% indent from the left edge
    y_start = line_height_padding + 10 # Start coordinate for first line

    for i, (text, color) in enumerate(lines):
        y_pos = y_start + (i * line_height_padding)
        cv2.putText(footer, text, (x_pos, y_pos), font, font_scale, color, thickness)

    # 5. Join the graded grid and the new footer vertically
    final_graded_image = cv2.vconcat([grid_paper, footer])

    print(f"[INFO] Footer legend and score applied to image.")

    # --- NOW UPDATE YOUR EXISTING SAVE LINE BELOW THIS ---
    # Change the variable you are saving from `grid_paper` to `final_graded_image`

    # In your original script, replace the existing:
    # cv2.imwrite(f"exam_var_{version}.jpg", grid_paper)
    # with the line below:
    cv2.imwrite(f"exam_var_{version}.jpg", final_graded_image)
    '''