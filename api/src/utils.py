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

        if q_type == "category":
            cat_text_tag = q.find('category').find('text') if q.find('category') else None
            if cat_text_tag:
                topic_name = clean_text(cat_text_tag.text).split('/')[-1].strip()
                if topic_name:
                    if topic_name not in topics:
                        topics[topic_name] = {"name": topic_name, "questions": []}
                    current_topic = topic_name
            continue

        if q_type in ["multichoice", "shortanswer"]:
            if not current_topic:
                # fallback if no topic found yet
                current_topic = "Default Topic"
                if current_topic not in topics:
                    topics[current_topic] = {"name": current_topic, "questions": []}

            question_text = q.find('questiontext')
            question_text_xml = question_text.text.strip() if question_text else ""
            question_text_plain = clean_text(question_text_xml)

            options = []
            for ans in q.find_all('answer'):
                ans_text = clean_text(ans.find('text').text) if ans.find('text') else ""
                fraction = float(ans.get('fraction', 0))
                options.append({"text": ans_text, "fraction": fraction})

            topics[current_topic]["questions"].append({
                "text": question_text_plain,
                "options": options
            })

    return {"topics": list(topics.values())}





