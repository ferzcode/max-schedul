from maxapi import Dispatcher
from maxapi.filters import F
from maxapi.types import MessageCreated, MessageCallback, CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from datetime import datetime

from db import get_session
from models import User, RequestLog
from assistant import answer as get_answer
from groups import find_group_id

user_states = {}


def make_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="📅 На сегодня", payload="day_today"),
        CallbackButton(text="📅 На завтра", payload="day_tomorrow"),
    )
    builder.row(
        CallbackButton(text="📅 Пн", payload="day_1"),
        CallbackButton(text="📅 Вт", payload="day_2"),
        CallbackButton(text="📅 Ср", payload="day_3"),
    )
    builder.row(
        CallbackButton(text="📅 Чт", payload="day_4"),
        CallbackButton(text="📅 Пт", payload="day_5"),
        CallbackButton(text="📅 Сб", payload="day_6"),
    )
    builder.row(
        CallbackButton(text="⏰ Сейчас", payload="now"),
        CallbackButton(text="👨‍🏫 По преподавателю", payload="by_teacher"),
    )
    builder.row(
        CallbackButton(text="🔄 Сменить группу", payload="change_group"),
    )
    return builder.as_markup()


def _end_time(start: str) -> str:
    try:
        h, m = map(int, start.split(":"))
        total = h * 60 + m + 90
        return f"{total // 60:02d}:{total % 60:02d}"
    except Exception:
        return "?"


def _build_context(lessons: list, target_date=None) -> str:
    now = datetime.now()
    iso_week = now.isocalendar()[1]
    current_parity = "чётная" if iso_week % 2 == 0 else "нечётная"

    if target_date is not None:
        target_iso = target_date.isocalendar()[1]
        target_parity = "чётная" if target_iso % 2 == 0 else "нечётная"
        header = (
            f"Вопрос про {target_date.strftime('%d.%m.%Y')} — это {target_parity} неделя. "
            f"Ниже только пары, которые подходят под эту неделю. "
            f"Отвечай строго на основе этих данных."
        )
    else:
        header = (
            f"Сегодня {now.strftime('%d.%m.%Y')}. Текущая неделя — {current_parity}. "
            f"Ниже полное расписание на две недели. Учти чётность при ответе."
        )

    lines = [header, ""]
    for l in lessons:
        start = l["time"]
        end = _end_time(start)
        w = l.get("week", "all")
        if w == "even":
            week_label = "чёт"
        elif w == "odd":
            week_label = "нечёт"
        else:
            week_label = "всегда"
        line = f"[{week_label}] {l['day']} {start}–{end} — {l['subject']}"
        if l.get("type"):
            line += f" ({l['type']})"
        if l.get("teacher"):
            line += f", {l['teacher']}"
        if l.get("room"):
            line += f", ауд. {l['room']}"
        lines.append(line)
    return "\n".join(lines)


def register_handlers(dp: Dispatcher):

    @dp.message_created()
    async def on_message(event: MessageCreated):
        body = event.message.body
        text = (body.text or "").strip()
        attachments = body.attachments or []
        user_id = event.message.sender.user_id

        print(f"=== MSG: text={text!r}, attachments={len(attachments)} ===")

        if attachments and not text:
            att = attachments[0]
            if att.type in ("audio", "voice"):
                from voice_handler import download_audio, recognize_audio
                url = getattr(att.payload, "url", None)
                if url:
                    audio_bytes = await download_audio(url)
                    recognized = await recognize_audio(audio_bytes)
                    if recognized:
                        text = recognized
                    else:
                        await event.message.answer("🎤 Не удалось распознать голосовое.")
                        return
                else:
                    await event.message.answer("Не нашёл URL аудио.")
                    return
            else:
                await event.message.answer(f"Получил вложение типа: {att.type}")
                return

        for att in attachments:
            print(f"    att.type={att.type}")
            print(f"    att.payload={att.payload}")

        if attachments and not text:
            await event.message.answer(
                f"Голосовое/медиа получил. Тип: {attachments[0].type}. "
                f"Скоро научусь распознавать."
            )
            return

        if not text:
            return

        session = get_session()
        try:
            user = session.query(User).filter_by(max_user_id=user_id).first()
            if not user:
                user = User(max_user_id=user_id)
                session.add(user)
                session.commit()
                user_states[user_id] = "waiting_group"
                await event.message.answer(
                    "Привет! Напиши название своей группы (например, АСУб-23-1):"
                )
                return

            state = user_states.get(user_id, "idle")
            reply = get_answer(text, group_id=user.group_id, group_name=user.group_name, state=state)

            if reply == "__WAIT_GROUP__":
                user_states[user_id] = "waiting_group"
                await event.message.answer("Напиши название новой группы (например, ИСИб-23-1):")
                return

            if reply.startswith("__SET_GROUP__:"):
                new_name = reply.split(":", 1)[1].strip()
                new_id = find_group_id(new_name)
                if new_id is None:
                    await event.message.answer(f"Не нашёл группу «{new_name}». Попробуй ещё раз:")
                    return
                user.group_id = new_id
                user.group_name = new_name
                session.commit()
                user_states[user_id] = "idle"
                await event.message.answer(f"Ок! Твоя группа — {new_name}.")
                return

            if reply.startswith("__FILTER_TEACHER__:"):
                teacher_name = reply.split(":", 1)[1].strip()
                user_states[user_id] = "idle"
                reply = get_answer(
                    f"расписание преподавателя {teacher_name}",
                    group_id=user.group_id,
                    group_name=user.group_name,
                )
                await event.message.answer(reply, attachments=[make_keyboard()])
                return

            if reply.startswith("__YANDEX_ASK__:"):
                question_for_yandex = reply.split(":", 1)[1].strip()
                from yandex_assistant import ask as yandex_ask
                from parser import parse_schedule
                from assistant import _parse_date, _day_specified, _day_header, _norm, _filter_by_week

                lessons = parse_schedule(user.group_id)
                q_lower = question_for_yandex.lower()
                now = datetime.now()

                if _day_specified(q_lower):
                    target = _parse_date(q_lower, now)
                    header = _day_header(target)
                    lessons = [l for l in lessons if _norm(header) in _norm(l["day"])]
                    lessons = _filter_by_week(lessons, target)
                    context = _build_context(lessons, target_date=target)
                else:
                    context = _build_context(lessons)

                answer_text = await yandex_ask(question_for_yandex, context=context)
                log = RequestLog(max_user_id=user_id, query=f"yandex:{question_for_yandex}")
                session.add(log)
                session.commit()
                await event.message.answer(answer_text, attachments=[make_keyboard()])
                return

            log = RequestLog(max_user_id=user_id, query=text[:2000])
            session.add(log)
            session.commit()
        finally:
            session.close()

        await event.message.answer(reply, attachments=[make_keyboard()])

    @dp.message_callback()
    async def on_callback(event: MessageCallback):
        payload = event.callback.payload
        user_id = event.callback.user.user_id

        await event.answer()

        session = get_session()
        try:
            user = session.query(User).filter_by(max_user_id=user_id).first()
            if not user:
                await event.message.answer("Сначала напиши /start")
                return

            if payload == "change_group":
                user_states[user_id] = "waiting_group"
                await event.message.answer("Напиши название новой группы:")
                return

            if payload == "by_teacher":
                user_states[user_id] = "waiting_teacher"
                await event.message.answer(
                    "Напиши фамилию преподавателя (например, Гутгарц):"
                )
                return

            if payload == "now":
                reply = get_answer("какая пара сейчас", user.group_id, user.group_name)
            elif payload == "day_today":
                reply = get_answer("расписание на сегодня", user.group_id, user.group_name)
            elif payload == "day_tomorrow":
                reply = get_answer("что завтра", user.group_id, user.group_name)
            elif payload.startswith("day_"):
                day_num = int(payload.split("_")[1])
                weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
                day_name = weekdays[day_num - 1]
                reply = get_answer(f"расписание на {day_name}", user.group_id, user.group_name)
            else:
                reply = "Неизвестная команда"

            log = RequestLog(max_user_id=user_id, query=f"callback:{payload}")
            session.add(log)
            session.commit()
        finally:
            session.close()

        await event.message.answer(reply, attachments=[make_keyboard()])
