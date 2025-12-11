import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path
from latex import build_pdf


def xml_to_pdf(xml_content: str, exam_id: int) -> bytes:
    """Converts Exam XML to PDF bytes."""
    root = ET.fromstring(xml_content)
    latex_content, t_variants_content = xml_to_latex(root, exam_id)
    return compile_latex_to_pdf(latex_content, t_variants_content)


def xml_to_latex(root: ET.Element, exam_id: int) -> tuple[str, str]:
    """Convert XML exam structure to LaTeX strings."""
    questions = root.findall("question")
    
    # Generate T-variants.tex content
    t_variants = ""
    for q in questions:
        q_text = q.findtext("text", "No text")
        q_weight = float(q.get("weight", "1"))
        t_variants += f"\\question ({q_weight:.1f} pts) {q_text}\n"
        
        options_elem = q.find("options")
        if options_elem is not None:
            t_variants += "\\begin{choices}\n"
            for opt in options_elem.findall("option"):
                opt_text = opt.text or ""
                cmd = "\\CorrectChoice" if opt.get("correct") == "true" else "\\choice"
                t_variants += f"{cmd} {opt_text}\n"
            t_variants += "\\end{choices}\n\n"
    
    # Build main document using template structure
    latex_doc = MAIN_TEMPLATE.replace("__EXAM_ID__", str(exam_id))
    
    return latex_doc, t_variants


MAIN_TEMPLATE = r"""\documentclass[a4paper,addpoints,10pt]{exam}

\input{H}
\newcommand\tttnumber{__EXAM_ID__}
\footer{}{Page \thepage\ of \numpages}{Exam ID: __EXAM_ID__}
\begin{document}

\Header{Exame Época Normal}{\Rules}{T-answers}{extra}

\begin{questions}
\input{T-variants}
\end{questions}

\end{document}
"""


def compile_latex_to_pdf(latex_content: str, t_variants_content: str) -> bytes:
    """Compile LaTeX string to PDF and return bytes."""
    templates_dir = Path(__file__).parent.parent / "latex_templates"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Copy template files
        for template_file in templates_dir.glob("*.tex"):
            (tmpdir_path / template_file.name).write_text(template_file.read_text())
        
        # Write generated T-variants.tex
        (tmpdir_path / "T-variants.tex").write_text(t_variants_content)
        
        # Build PDF
        pdf = build_pdf(latex_content, texinputs=[str(tmpdir_path), ''])
        return bytes(pdf)
