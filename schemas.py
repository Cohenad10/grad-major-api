from pydantic import BaseModel


class SurveySchema(BaseModel):
    # Section 1
    q1: int
    q2: int
    q3: str
    q4: int
    q5: str

    # Section 2
    q6: int
    q7: str
    q8: int
    q9: bool
    q10: int

    # Section 3
    q11: int
    q12: int
    q13: int
    q14: int
    q15: int

    # Section 4 — RIASEC personality items
    r1: int
    i1: int
    a1: int
    s1: int
    e1: int
    c1: int
