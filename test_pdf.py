#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/vasco/EduPro/app/api/src')

from services.pdf_generator import xml_to_pdf

test_xml = """<exam fraction="25" subject_id="1" variation="1">
  <question id="1" weight="2.0">
    <text>What is 2+2?</text>
    <options>
      <option id="1" correct="true">4</option>
      <option id="2" correct="false">3</option>
      <option id="3" correct="false">5</option>
    </options>
  </question>
</exam>"""

try:
    pdf_bytes = xml_to_pdf(test_xml, 999)
    print(f"SUCCESS: Generated PDF with {len(pdf_bytes)} bytes")
    with open("/tmp/test_exam.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("Saved to /tmp/test_exam.pdf")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
