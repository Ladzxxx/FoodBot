from localization import t
from aiogram.fsm.state import State, StatesGroup

# CAN CHANGE TEXT: тексты дневных вопросов и объяснения шкал.
QUESTIONS = {
    'bedtime': t("en", 'day.question.bedtime'),
    'wake_time': t("en", 'day.question.wake_time'),
    'sleep_satisfaction': t("en", 'day.question.sleep_satisfaction'),
    'mood_control': t("en", 'day.question.mood_control'),
    'ache': t("en", 'day.question.ache'),
    'pain_intensity': t("en", 'day.question.pain_intensity'),
    'painkillers': t("en", 'day.question.painkillers'),
    'medicine_details': t("en", 'day.question.medicine_details'),
    'medicine_relief': t("en", 'day.question.medicine_relief'),
    'more_medicine': t("en", 'day.question.more_medicine'),
    'day_comment_wanted': t("en", 'day.question.day_comment_wanted'),
    'day_comment': t("en", 'day.question.day_comment'),
    'pain_description_requested': t("en", 'day.question.pain_description_requested'),
    'pain_comment_wanted': t("en", 'day.question.pain_comment_wanted'),
    'pain_comment': t("en", 'day.question.pain_comment'),
}

RATING_STEPS = ("sleep_satisfaction", "mood_control", "pain_intensity")
TIME_STEPS = ("bedtime", "wake_time")
TEXT_STEPS = ("medicine_details", "day_comment", "pain_comment")
YES_NO_STEPS = (
    "ache", "painkillers", "more_medicine", "day_comment_wanted",
    "pain_description_requested", "pain_comment_wanted",
)


def next_day_step(step: str, value, entry: dict) -> str:
    if step == "bedtime":
        return "wake_time"
    if step == "wake_time":
        return "sleep_satisfaction"
    if step == "sleep_satisfaction":
        return "mood_control"
    if step == "mood_control":
        return "ache"
    if step == "ache":
        return "pain_intensity" if value else "day_comment_wanted"
    if step == "pain_intensity":
        return "painkillers"
    if step == "painkillers":
        return "medicine_details" if value else "pain_description_requested"
    if step == "medicine_details":
        return "medicine_relief"
    if step == "medicine_relief":
        return "more_medicine"
    if step == "more_medicine":
        return "medicine_details" if value else "pain_description_requested"
    # Общая заметка — последний вопрос, после всех подробностей боли.
    if step == "day_comment_wanted":
        return "day_comment" if value else "complete"
    if step == "day_comment":
        return "complete"
    if step == "pain_description_requested":
        return "pain_location" if value else "pain_comment_wanted"
    if step == "pain_comment_wanted":
        return "pain_comment" if value else "day_comment_wanted"
    if step == "pain_comment":
        return "day_comment_wanted"
    return "complete"


class DayEdit(StatesGroup):
    answer = State()
    choose = State()


def sleep_minutes(entry: dict) -> int | None:
    try:
        bed_hour, bed_minute = map(int, entry.get("bedtime", "").split(":"))
        wake_hour, wake_minute = map(int, entry.get("wake_time", "").split(":"))
    except (ValueError, AttributeError):
        return None
    if not (0 <= bed_hour < 24 and 0 <= wake_hour <= 24 and 0 <= bed_minute < 60 and 0 <= wake_minute < 60):
        return None
    if wake_hour == 24 and wake_minute != 0:
        return None
    bedtime_day = entry.get("bedtime_day", -1)
    if bedtime_day not in (-1, 0):
        return None
    # Считаем относительно начала выбранного дня, без остатка от суток.
    # Отрицательный результат используется для отказа в сохранении ответа.
    return wake_hour * 60 + wake_minute - (bedtime_day * 1440 + bed_hour * 60 + bed_minute)


def day_marker(entry: dict, meal_count: int = 0) -> str:
    if not entry:
        return ""
    if not entry.get("completed"):
        # CAN CHANGE TEXT: отметка незавершённой записи.
        return "📝"
    duration = sleep_minutes(entry)
    # CAN CHANGE TEXT / RULE: пять условий и отметки по числу нарушений.
    requirements = (
        duration is not None and duration >= 7 * 60,
        (entry.get("sleep_satisfaction") or 0) >= 7,
        (entry.get("mood_control") or 0) >= 7,
        meal_count >= 2,
        entry.get("bedtime_day", -1) == -1 and (entry.get("bedtime") or "24:00") < "23:00",
    )
    failed = requirements.count(False)
    # CAN CHANGE TEXT: заменяем только красную отметку завершённого дня с болью.
    if failed >= 3 and entry.get("ache") == 1:
        return "🆘"
    return ("✅", "🟨", "🟧", "🟥")[min(failed, 3)]


def has_green_marker(entry: dict, meal_count: int = 0) -> bool:
    return day_marker(entry, meal_count) == "✅"
