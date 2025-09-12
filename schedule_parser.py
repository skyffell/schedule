import httpx
from bs4 import BeautifulSoup
import logging
from typing import List, Optional
from models import Lesson, DaySchedule, GroupSchedule
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GroupScheduleParser:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def fetch_schedule(self) -> str:
        try:
            logger.info(f"Загружаем страницу: {self.base_url}")
            response = await self.client.get(self.base_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            raise

    async def get_group_schedule(self, group_number: str) -> Optional[GroupSchedule]:
        try:
            html = await self.fetch_schedule()
            soup = BeautifulSoup(html, 'html.parser')

            headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            target_header = None

            for header in headers:
                text = header.get_text().strip()
                if re.search(rf'Группа\s*[-–]?\s*{group_number}\b', text):
                    target_header = header
                    break

            if not target_header:
                raise Exception(f"Группа {group_number} не найдена")

            table = target_header.find_next('table')
            if not table:
                raise Exception("Таблица с расписанием не найдена")

            return self._parse_table(table, target_header.get_text().strip(), group_number)

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            raise

    def _parse_table(self, table: BeautifulSoup, full_group_name: str, group_number: str) -> GroupSchedule:
        rows = table.find_all('tr')
        if len(rows) < 3:
            raise Exception("Недостаточно строк в таблице")

        day_names_row = rows[0].find_all(['td', 'th'])
        date_row = rows[1].find_all(['td', 'th'])

        day_info = []
        for i in range(1, len(day_names_row)):
            day_name = day_names_row[i].get_text().strip()
            date_str = date_row[i].get_text().strip()
            if re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
                day_info.append((day_name, date_str))
            else:
                day_info.append((day_name, ""))

        lessons_by_day = {day[0]: [] for day in day_info}

        time_map = {
            "1": "8:00-9:30",
            "2": "9:40-11:10",
            "3": "11:20-12:50",
            "4": "13:30-15:00",
            "5": "15:10-16:40",
            "6": "16:50-18:20",
            "7": "18:30-20:00"
        }

        for row in rows[2:]:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 1 + len(day_info) * 2:
                continue

            lesson_number = cols[0].get_text().strip()
            if not lesson_number.isdigit():
                continue

            for i, (day_name, date_str) in enumerate(day_info):
                subject_raw = cols[1 + i * 2].get_text().strip()
                room_cell = cols[2 + i * 2].get_text().strip()

                if subject_raw and subject_raw != '-' and subject_raw != '--':
                    teacher = self._extract_teacher(subject_raw)

                    if "ФЗКиЗ" in subject_raw:
                        subject_clean = subject_raw
                    else:
                        subject_clean = subject_raw.replace(teacher, '').strip() if teacher else subject_raw

                    lesson = Lesson(
                        date=date_str,
                        day_of_week=day_name,
                        time=time_map.get(lesson_number, f"Пара {lesson_number}"),
                        subject=subject_clean,
                        teacher=teacher,
                        classroom=room_cell
                    )
                    lessons_by_day[day_name].append(lesson)

        days_schedule = []
        for day_name, lessons in lessons_by_day.items():
            days_schedule.append(DaySchedule(
                date=lessons[0].date if lessons else "",
                day_of_week=day_name,
                lessons=lessons
            ))

        return GroupSchedule(
            group=full_group_name,
            group_number=group_number,
            week_range="Неделя",
            days=days_schedule
        )

    def _extract_teacher(self, text: str) -> str:
        patterns = [
            r'([А-Я][а-я]+ [А-Я]\.[А-Я]\.)',
            r'([А-Я][а-я]+ [А-Я]\. [А-Я]\.)',
            r'([А-Я][а-я]+ [А-Я][а-я]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    async def get_available_groups(self) -> List[str]:
        try:
            html = await self.fetch_schedule()
            soup = BeautifulSoup(html, 'html.parser')

            groups = []
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])

            for header in headers:
                text = header.get_text().strip()
                match = re.search(r'Группа\s*[-–]?\s*(\d{2,3})', text)
                if match:
                    groups.append(match.group(1))

            return list(set(groups))
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return []

    async def close(self):
        await self.client.aclose()