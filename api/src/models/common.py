from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class StatusResponse(BaseModel):
    status: str


class XMLImportResponse(BaseModel):
    topics_created: int
    questions_created: int
    options_created: int
