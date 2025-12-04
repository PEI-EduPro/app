import re
from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup

@dataclass
class ParsedOption:
    option_text: str
    value: bool

@dataclass
class ParsedQuestion:
    name: str
    question_text: str
    topic_name: str
    options: List[ParsedOption]

def parse_moodle_xml(xml_path: str) -> List[ParsedQuestion]:
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    root = BeautifulSoup(content, 'lxml-xml')
    
    questions = []
    current_topic = ""
    
    for q in root.find_all('question'):
        qtype = q.get('type')
        
        if qtype == 'category':
            cat_el = q.find('category')
            cat_text = cat_el.find('text').get_text() if cat_el else ""
            current_topic = cat_text.split('/')[-1]
            continue
        
        if qtype != 'multichoice':
            continue
        
        name_el = q.find('name')
        name = name_el.find('text').get_text() if name_el else ""
        qtext_el = q.find('questiontext')
        qtext = qtext_el.find('text').get_text() if qtext_el else ""
        
        options = []
        for i, ans in enumerate(q.find_all('answer')):
            fraction = int(float(ans.get('fraction', '0')))
            opt_text = ans.find('text').get_text() if ans.find('text') else ""
            options.append(ParsedOption(
                option_text=opt_text,
                value=(fraction == 100)
            ))
        
        questions.append(ParsedQuestion(
            name=name,
            question_text=qtext,
            topic_name=current_topic,
            options=options
        ))
    
    return questions

def to_db_models(parsed: List[ParsedQuestion], topic_id: int) -> List[dict]:
    """Returns dicts ready for QuestionCreate + QuestionOptionCreate"""
    return [{
        'question': {'topic_id': topic_id, 'question_text': pq.question_text},
        'options': [
            {'option_text': o.option_text, 'value': o.value}
            for o in pq.options
        ]
    } for pq in parsed]

if __name__ == "__main__":
    # Test with the XML file
    questions = parse_moodle_xml("perguntas-40384-IES-Q1.3_Software_process_large-20250929-1305.xml")
    for q in questions:
        print(f"Topic: {q.topic_name}")
        print(f"Question: {q.question_text}")
        for o in q.options:
            print(f"  [{o.value}] {o.option_text}")
        print("---")
