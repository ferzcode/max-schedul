# MAX Schedule Bot — ИРНИТУ

Голосовой и текстовый чат-бот MAX для получения расписания ИРНИТУ с интеграцией YandexGPT (RAG) и Yandex SpeechKit.

## Возможности

- 📅 Расписание для **любой группы** по названию (АСУб-23-1, ИСИб-23-1 и т.д.)
- 🔍 Фильтр по дате: сегодня, завтра, день недели, конкретное число
- 👨‍🏫 Фильтр по преподавателю (на день или на всю неделю)
- ⏰ Ближайшая пара, во сколько начинается/заканчивается
- 📆 Учёт чётности/нечётности недели
- 🎤 **Голосовой ввод** через Yandex SpeechKit
- 🤖 **YandexGPT (RAG)** для сложных вопросов
- 💾 PostgreSQL + SQLAlchemy (пользователи, логи)
- 🎛 Inline-кнопки в MAX

## Стек

- Python 3.14
- maxapi — SDK для бота MAX
- PostgreSQL + SQLAlchemy
- Yandex Cloud: YandexGPT, SpeechKit
- aiohttp, BeautifulSoup4

## Установка

```bash
git clone https://github.com/ferzcode/max-schedul.git
cd max-schedul
cd max-schedule-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
