from html import escape
from datetime import timedelta

from day_storage import get_day_entry, get_medications
from Forms.day import YES_NO_STEPS
from Forms.pain import selected_labels
from localization import t
from pain_storage import get_pain_answers


async def snapshot_answers(user_id, dates):
    # Снимок нужен только для показа прежних значений внутри текущего редактирования.
    result = {}
    for selected_date in dates:
        answers, options = await get_pain_answers(user_id, selected_date, selected_date)
        result[selected_date.isoformat()] = {
            "entry": await get_day_entry(user_id, selected_date) or {},
            "medications": await get_medications(user_id, selected_date),
            "pain_answers": answers, "pain_options": options,
        }
    return result


def medication_index(snapshot, selected_date, step):
    saved = snapshot.get(selected_date.isoformat(), {})
    medications = saved.get("medications", [])
    entry = saved.get("entry", {})
    if step in ("medicine_relief", "more_medicine"):
        return max(0, len(medications) - 1)
    if step == "medicine_details" and entry.get("more_medicine") == 1:
        return len(medications)
    return 0


def previous_answer(draft, selected_date, step, lang):
    saved = draft.get("previous_values", {}).get(selected_date.isoformat(), {})
    entry = saved.get("entry", {})
    if step in ("medicine_details", "medicine_relief"):
        index = draft.get("medicine_index", 0)
        medications = saved.get("medications", [])
        if not 0 <= index < len(medications):
            return None
        medication = medications[index]
        value = medication["description"] if step == "medicine_details" else medication["relief"]
        if step == "medicine_relief" and value is not None:
            return t(lang, {"yes": "common.yes", "no": "common.no", "a_little": "common.a_little"}[value])
        return value
    if step == "more_medicine" and saved.get("medications"):
        index = draft.get("medicine_index", 0)
        medications = saved["medications"]
        if index >= len(medications):
            return None
        return t(lang, "common.yes" if index + 1 < len(medications) else "common.no")
    value = entry.get(step)
    if value is None:
        return None
    if step == "bedtime":
        bedtime_date = selected_date + timedelta(days=entry.get("bedtime_day", -1))
        return f"{value} ({bedtime_date:%d.%m.%Y})"
    if step in YES_NO_STEPS:
        return t(lang, "common.yes" if value else "common.no")
    return str(value) if value != "" else t(lang, "common.no_comment")


def previous_pain_answer(draft, selected_date, step, lang):
    saved = draft.get("previous_values", {}).get(selected_date.isoformat(), {})
    answers = saved.get("pain_answers", [])
    if not any(item["question_key"] == step for item in answers):
        return None
    options = [item for item in saved.get("pain_options", []) if item["question_key"] == step]
    labels = selected_labels(step, options, lang=lang)
    return "\n".join(labels) if labels else None


def with_previous(text, value, lang, *, receipt=False, html=False):
    if value is None:
        return text
    value = str(value)
    if len(value) > 1500:
        # Старые длинные заметки сокращаем только на экране, в базе они остаются.
        value = value[:1500] + t(lang, "day.previous_shortened")
    if html:
        value = escape(value)
    key = "day.previous_answer" if receipt else "day.already_recorded"
    return text + t(lang, key, value=value)
