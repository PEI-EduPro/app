from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
import xml.etree.ElementTree as ET
import io

def xml_to_pdf(xml_content: str, exam_id: int) -> bytes:
    """
    Converts Exam XML to a PDF file in memory.
    Returns the bytes of the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    # Custom styles
    title_style = styles["Heading1"]
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        spaceBefore=12,
        leading=14
    )
    option_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=2,
        leading=12
    )

    story = []
    
    # 1. Parse XML
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return b"Error parsing XML"

    # 2. Header
    story.append(Paragraph(f"Exam #{exam_id}", title_style))
    story.append(Spacer(1, 12))
    
    fraction = root.get('fraction', '0')
    story.append(Paragraph(f"Penalty for incorrect answer: {fraction}%", styles["Normal"]))
    story.append(Spacer(1, 24))

    # 3. Questions
    questions = root.findall("question")
    
    for idx, q in enumerate(questions, 1):
        # Question Text
        q_text_elem = q.find("text")
        q_text = q_text_elem.text if q_text_elem is not None else "No text"
        q_weight = q.get("weight", "1.0")
        
        full_q_text = f"<b>{idx}.</b> {q_text} <i>(Val: {q_weight})</i>"
        story.append(Paragraph(full_q_text, question_style))
        
        # Options
        options_elem = q.find("options")
        if options_elem is not None:
            options = options_elem.findall("option")
            
            # Create list items for options
            list_items = []
            for i, opt in enumerate(options):
                opt_text = opt.text if opt.text else ""
                
                # Checkbox style placeholder (e.g., "[ ]")
                item_content = Paragraph(f"{opt_text}", option_style)
                list_items.append(ListItem(item_content, bulletColor=colors.black))
            
            # Create the list flowable
            t_list = ListFlowable(
                list_items,
                bulletType='a',
                start=1,
                leftIndent=20
            )
            story.append(t_list)
        
        story.append(Spacer(1, 10))

    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
