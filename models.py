from pydantic import BaseModel
from typing import List

class Lesson(BaseModel):
    date: str = ""
    day_of_week: str = ""
    time: str = ""
    subject: str = ""
    teacher: str = ""
    classroom: str = ""

class DaySchedule(BaseModel):
    date: str
    day_of_week: str
    lessons: List[Lesson]

class GroupSchedule(BaseModel):
    group: str
    group_number: str
    week_range: str
    days: List[DaySchedule]