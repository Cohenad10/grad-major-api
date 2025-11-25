from pydantic import BaseModel


class SurveySchema(BaseModel):
    q1: int
    q2: int
    q3: str
    q4: int
    q5: str

    q6: int
    q7: str
    q8: int
    q9: bool
    q10: int

    q11: int
    q12: int
    q13: int
    q14: int
    q15: int
