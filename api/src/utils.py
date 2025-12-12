from bs4 import BeautifulSoup



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





