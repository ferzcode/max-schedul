import re
from datetime import datetime, timedelta

from parser import parse_schedule

WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]

# Все падежи названий дней → именительный
DAY_FORMS = {
    "понедельник": "понедельник", "понедельника": "понедельник", "понедельнику": "понедельник",
    "понедельник ": "понедельник", "в понедельник": "понедельник", "по понедельникам": "понедельник",
    "вторник": "вторник", "вторника": "вторник", "вторнику": "вторник",
    "во вторник": "вторник", "по вторникам": "вторник",
    "среда": "среда", "среды": "среда", "среду": "среда", "среде": "среда",
    "в среду": "среда", "по средам": "среда",
    "четверг": "четверг", "четверга": "четверг", "четвергу": "четверг",
    "в четверг": "четверг", "по четвергам": "четверг",
    "пятница": "пятница", "пятницы": "пятница", "пятницу": "пятница", "пятнице": "пятница",
    "в пятницу": "пятница", "по пятницам": "пятница",
    "суббота": "суббота", "субботы": "суббота", "субботу": "суббота", "субботе": "суббота",
    "в субботу": "суббота", "по субботам": "суббота",
    "воскресенье": "воскресенье", "воскресенья": "воскресенье", "воскресенью": "воскресенье",
    "в воскресенье": "воскресенье", "по воскресеньям": "воскресенье",
}


def _day_header(dt: datetime) -> str:
    s = f"{WEEKDAYS[dt.weekday()].capitalize()}, {dt.day} {MONTHS[dt.month - 1]}"
    return s.replace(chr(0xA0), " ")


def _norm(s: str) -> str:
    return s.lower().replace(chr(0xA0), " ").strip()


def _week_parity(dt: datetime) -> str:
    iso_week = dt.isocalendar()[1]
    return "even" if iso_week % 2 == 0 else "odd"


def _filter_by_week(lessons: list, dt: datetime) -> list:
    parity = _week_parity(dt)
    return [l for l in lessons if l.get("week") in (parity, "all", "")]


def _end_time(start: str) -> str:
    try:
        h, m = map(int, start.split(":"))
        total = h * 60 + m + 90
        return f"{total // 60:02d}:{total % 60:02d}"
    except Exception:
        return "?"


def _format_lessons(lessons: list) -> str:
    if not lessons:
        return "На этот день занятий нет."
    lines = []
    for l in lessons:
        start = l["time"]
        end = _end_time(start)
        parts = [f"{start}–{end} — {l['subject']}"]
        if l.get("type"):
            parts.append(f"({l['type']})")
        if l.get("room"):
            parts.append(f"ауд. {l['room']}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _format_by_day(lessons: list) -> str:
    if not lessons:
        return "Занятий не найдено."
    by_day = {}
    for l in lessons:
        by_day.setdefault(l["day"], []).append(l)
    lines = []
    for day in by_day:
        lines.append(f"\n📅 {day}")
        for l in by_day[day]:
            start = l["time"]
            end = _end_time(start)
            parts = [f"  {start}–{end} — {l['subject']}"]
            if l.get("type"):
                parts.append(f"({l['type']})")
            if l.get("room"):
                parts.append(f"ауд. {l['room']}")
            lines.append(" ".join(parts))
    return "\n".join(lines)


def _detect_weekday(q: str):
    """Возвращает индекс дня недели (0–6) или None."""
    for form, base in DAY_FORMS.items():
        if form in q:
            return WEEKDAYS.index(base)
    return None


def _parse_date(q: str, now: datetime) -> datetime:
    if "послезавтра" in q:
        return now + timedelta(days=2)
    if "завтра" in q:
        return now + timedelta(days=1)

    m = re.search(r"\b(\d{1,2})[.\s](\d{1,2})\b", q)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        try:
            return now.replace(day=day, month=month)
        except ValueError:
            pass

    wd_idx = _detect_weekday(q)
    if wd_idx is not None:
        delta = (wd_idx - now.weekday()) % 7
        if delta == 0 and "прошл" not in q:
            delta = 7
        return now + timedelta(days=delta)

    return now


def _day_specified(q: str) -> bool:
    if any(w in q for w in ["сегодня", "завтра", "послезавтра"]):
        return True
    if _detect_weekday(q) is not None:
        return True
    if re.search(r"\b\d{1,2}[.\s]\d{1,2}\b", q):
        return True
    return False


def _find_teacher(lessons: list, query: str):
    words = re.findall(r"[А-ЯЁа-яё]{4,}", query)
    if not words:
        return None, None
    words_lower = [w.lower() for w in words]
    for lesson in lessons:
        if not lesson.get("teacher"):
            continue
        parts = lesson["teacher"].split()
        if not parts:
            continue
        last_name = parts[0].lower().rstrip(".")
        if last_name in words_lower:
            return last_name, lesson["teacher"]
    return None, None


def answer(question: str, group_id: int, group_name: str, state: str = "idle") -> str:
    q = question.lower().strip()
    now = datetime.now()

    if state == "waiting_group":
        return "__SET_GROUP__:" + question
    if state == "waiting_teacher":
        return "__FILTER_TEACHER__:" + question

    if any(w in q for w in ["привет", "здравствуй", "хай", "help", "помощь", "/start"]):
        return (f"Привет! Я бот расписания ИРНИТУ.\n"
                f"Твоя группа: {group_name}.\n"
                "Что умею:\n"
                "• «расписание на сегодня» / «что завтра»\n"
                "• «какая пара сейчас» / «во сколько заканчивается последняя пара»\n"
                "• «пары в среду»\n"
                "• «расписание преподавателя Гутгарц»\n"
                "• «смени группу» — выбери другую группу")

    if re.search(r"(смени|поменяй).*групп\w*", q):
        return "__WAIT_GROUP__"

    yandex_keywords = [
        "где проходит", "где будет", "где находится", "какой корпус",
        "как добраться", "как найти", "когда экзамен", "расписание сессии",
    ]
    if any(kw in q for kw in yandex_keywords):
        return "__YANDEX_ASK__:" + question

    lessons = parse_schedule(group_id)

    last_name, teacher_display = _find_teacher(lessons, q)

    if teacher_display:
        teacher_lessons = [l for l in lessons if l["teacher"] == teacher_display]

        if _day_specified(q):
            target = _parse_date(q, now)
            header = _day_header(target)
            filtered = _filter_by_week(teacher_lessons, target)
            filtered = [l for l in filtered if _norm(header) in _norm(l["day"])]
            return f"Занятия {teacher_display} на {header}:\n{_format_lessons(filtered)}"

        target = _parse_date(q, now)
        filtered = _filter_by_week(teacher_lessons, target)
        return f"Занятия {teacher_display} на неделю:\n{_format_by_day(filtered)}"

    target = _parse_date(q, now)
    header = _day_header(target)
    day_lessons = [l for l in lessons if _norm(header) in _norm(l["day"])]
    day_lessons = _filter_by_week(day_lessons, target)

    if "какая пара" in q or "ближайшая" in q or "сейчас" in q:
        now_time = now.strftime("%H:%M")
        upcoming = [l for l in day_lessons if l["time"] >= now_time]
        if upcoming:
            first = upcoming[0]
            end = _end_time(first["time"])
            return (f"Ближайшая пара:\n{first['time']}–{end} — {first['subject']}"
                    + (f" ({first['type']})" if first.get("type") else "")
                    + (f"\nауд. {first['room']}" if first.get("room") else ""))
        return "На сегодня пар больше нет."

    if "во сколько заканчивается" in q or "когда заканчивается" in q or "конец пары" in q:
        if not day_lessons:
            return f"На {header} занятий нет."
        last = day_lessons[-1]
        end = _end_time(last["time"])
        return (f"Последняя пара на {header} заканчивается в {end}.\n"
                f"({last['time']}–{end} — {last['subject']}"
                + (f", ауд. {last['room']}" if last.get("room") else "") + ")")

    if "во сколько начинается" in q or "когда начинается" in q:
        if not day_lessons:
            return f"На {header} занятий нет."
        first = day_lessons[0]
        end = _end_time(first["time"])
        return (f"Первая пара на {header} начинается в {first['time']}.\n"
                f"({first['time']}–{end} — {first['subject']}"
                + (f", ауд. {first['room']}" if first.get("room") else "") + ")")

    return f"Расписание группы {group_name} на {header}:\n{_format_lessons(day_lessons)}"