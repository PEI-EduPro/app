import pytest
from src.utils import clean_text, parse_moodle_xml

def test_clean_text_basic():
    text = "<p>This is a test.</p>"
    assert clean_text(text) == "This is a test."

def test_clean_text_empty():
    assert clean_text(None) == ""
    assert clean_text("") == ""

def test_clean_text_nested_tags():
    text = "<div><p>Some <b>bold</b> text</p></div>"
    assert clean_text(text) == "Some bold text"

def test_parse_moodle_xml_multichoice():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name>
      <text>Math Variables</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>What is x if 2x = 4?</p>]]></text>
    </questiontext>
    <answer fraction="100" format="html">
      <text><![CDATA[<p>2</p>]]></text>
    </answer>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>4</p>]]></text>
    </answer>
  </question>
</quiz>
    """
    
    result = parse_moodle_xml(xml_content)
    
    assert "topics" in result
    assert len(result["topics"]) == 1
    
    topic = result["topics"][0]
    assert topic["name"] == "Math Variables"
    assert len(topic["questions"]) == 1
    
    question = topic["questions"][0]
    assert question["text"] == "What is x if 2x = 4?"
    assert len(question["options"]) == 2
    
    # Check option 1
    assert question["options"][0]["text"] == "2"
    assert question["options"][0]["fraction"] == 100.0
    
    # Check option 2
    assert question["options"][1]["text"] == "4"
    assert question["options"][1]["fraction"] == 0.0

def test_parse_moodle_xml_shortanswer():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="shortanswer">
    <name>
      <text>Geography</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>What is the capital of France?</p>]]></text>
    </questiontext>
    <answer fraction="100" format="moodle_auto_format">
      <text>Paris</text>
    </answer>
  </question>
</quiz>
    """
    
    result = parse_moodle_xml(xml_content)
    
    assert len(result["topics"]) == 1
    topic = result["topics"][0]
    assert topic["name"] == "Geography"
    
    question = topic["questions"][0]
    assert question["text"] == "What is the capital of France?"
    assert len(question["options"]) == 1
    assert question["options"][0]["text"] == "Paris"
    assert question["options"][0]["fraction"] == 100.0

def test_parse_moodle_xml_ignore_other_types():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="category">
    <category>
      <text>$course$/top/Default for Course</text>
    </category>
  </question>
  <question type="description">
    <name>
      <text>Info</text>
    </name>
    <questiontext>
      <text>Read this first.</text>
    </questiontext>
  </question>
</quiz>
    """
    
    result = parse_moodle_xml(xml_content)
    # Both "category" and "description" types should be ignored by the parser
    assert len(result["topics"]) == 0

def test_parse_moodle_xml_br_replacement():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name>
      <text>Formatting</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Line 1<br>Line 2</p>]]></text>
    </questiontext>
    <answer fraction="100" format="html">
      <text><![CDATA[<p>Ans 1<br>Ans 2</p>]]></text>
    </answer>
  </question>
</quiz>
    """
    
    result = parse_moodle_xml(xml_content)
    question = result["topics"][0]["questions"][0]
    
    assert question["text"] == "Line 1 / Line 2"
    assert question["options"][0]["text"] == "Ans 1 / Ans 2"
