from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import os

from schedule_parser import GroupScheduleParser
from models import GroupSchedule

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.parser = GroupScheduleParser(
        "https://mgkct.minskedu.gov.by/персоналии/учащимся/расписание-занятий-на-неделю"
    )
    app.state.last_update = None
    app.state.cached_schedule = None
    yield
    await app.state.parser.close()

app = FastAPI(title="Schedule for Group 99", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

templates = Jinja2Templates(directory="templates")

def parse_date(date_str: str):
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y")
    except:
        return None

def sort_schedule_days(days):
    return sorted(days, key=lambda d: parse_date(d.date) or datetime.max)

def get_lessons_by_date(schedule, target_date: datetime):
    for day in schedule.days:
        day_date = parse_date(day.date)
        if day_date and day_date.date() == target_date.date():
            return day.lessons
    return []

def get_reference_dates(schedule):
    today = datetime.now().date()
    available_dates = sorted([
        parse_date(day.date).date()
        for day in schedule.days
        if parse_date(day.date)
    ])
    for date in available_dates:
        if date >= today:
            return date, date + timedelta(days=1)
    return None, None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        group_number = "99"
        if app.state.cached_schedule is None:
            app.state.cached_schedule = await app.state.parser.get_group_schedule(group_number)

        schedule = app.state.cached_schedule
        sorted_days = sort_schedule_days(schedule.days)

        today_date, tomorrow_date = get_reference_dates(schedule)
        today_lessons = get_lessons_by_date(schedule, today_date) if today_date else []
        tomorrow_lessons = get_lessons_by_date(schedule, tomorrow_date) if tomorrow_date else []

        return templates.TemplateResponse("index.html", {
            "request": request,
            "schedule": schedule,
            "group_number": group_number,
            "current_date": datetime.now().strftime("%d %B %Y"),
            "current_day": datetime.now().strftime("%A"),
            "today_lessons": today_lessons,
            "tomorrow_lessons": tomorrow_lessons,
            "sorted_days": sorted_days,
            "today_label": today_date.strftime("%A, %d.%m.%Y") if today_date else "Сегодня",
            "tomorrow_label": tomorrow_date.strftime("%A, %d.%m.%Y") if tomorrow_date else "Завтра",
            "current_time": datetime.now().strftime("%H:%M"),
            "now": datetime.now
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "schedule": None,
            "group_number": "99",
            "current_date": datetime.now().strftime("%d %B %Y"),
            "current_day": datetime.now().strftime("%A"),
            "today_lessons": [],
            "tomorrow_lessons": [],
            "sorted_days": [],
            "today_label": "Сегодня",
            "tomorrow_label": "Завтра",
            "current_time": datetime.now().strftime("%H:%M"),
            "error": f"Ошибка загрузки расписания: {str(e)}",
            "now": datetime.now
        })

@app.get("/css/main.css")
async def get_css():
    return FileResponse("static/css/main.css")

@app.get("/js/main.js")
async def get_js():
    return FileResponse("static/js/main.js")