from pydantic import BaseModel

class EmailOptionsPayload(BaseModel):
    exam_capture: bool = False
    question_weights: bool = False
    red_green_cross_table: bool = False
    cumulative_score_table: bool = False
    custom_description: str = ""