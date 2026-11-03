from localization import t
from datetime import date, timedelta
from io import BytesIO

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from Forms.pain import PAIN_QUESTIONS, option_labels

# CAN CHANGE TEXT: колонки основных ответов; прежняя шкала имеет отдельные колонки.
DAY_FIELDS = (
    "wake_time", "sleep_satisfaction", "mood_control", "ache", "pain_intensity",
    "painkillers", "more_medicine", "pain_description_requested",
    "pain_comment_wanted", "pain_comment", "day_comment_wanted", "day_comment",
)
YES_NO_FIELDS = {"ache", "painkillers", "more_medicine", "pain_description_requested",
                 "pain_comment_wanted", "day_comment_wanted"}


def yes_no(value, lang="en"):
    if value is None:
        return None
    # CAN CHANGE TEXT
    return t(lang, 'common.yes') if value else t(lang, 'common.no')


def export_rows(data, lang="en"):
    grouped = {}
    dates = set()
    for table, records in data.items():
        grouped[table] = {}
        for record in records:
            day = record["entry_date"]
            dates.add(day)
            grouped[table].setdefault(day, []).append(record)
    # CAN CHANGE TEXT
    headers = [t(lang, 'day_export.date'), t(lang, 'day_export.entry_status'), t(lang, 'day_export.bedtime_date'), t(lang, 'day_export.bedtime')]
    headers += [t(lang, "export.field." + field) for field in DAY_FIELDS]
    headers += [t(lang, 'day_export.medications_and_effect'), t(lang, 'day_export.meals_local_time_and_description')]
    for index, question in enumerate(PAIN_QUESTIONS):
        title = t(lang, f"export.pain.{index}")
        headers += [t(lang, "export.status", title=title), t(lang, "export.answers", title=title)]
    headers += [t(lang, 'day_export.legacy_yes_no'), t(lang, 'day_export.legacy_sleep_1_7'), t(lang, 'day_export.legacy_food_1_7'), t(lang, 'day_export.legacy_mood_1_7')]
    rows = []
    for day in sorted(dates, reverse=True):
        entry_records = grouped.get("diary_entries", {}).get(day, [])
        entry = entry_records[0] if entry_records else {}
        selected_date = date.fromisoformat(day)
        bedtime_date = None
        if entry.get("bedtime"):
            bedtime_date = selected_date + timedelta(days=entry.get("bedtime_day", -1))
        # CAN CHANGE TEXT
        status = (t(lang, 'day_export.completed') if entry.get("completed") else t(lang, 'day_export.draft')) if entry else None
        row = [selected_date, status, bedtime_date, entry.get("bedtime")]
        for field in DAY_FIELDS:
            value = entry.get(field)
            row.append(yes_no(value, lang=lang) if field in YES_NO_FIELDS else value)
        medicines = sorted(grouped.get("day_medications", {}).get(day, []), key=lambda item: item["id"])
        # CAN CHANGE TEXT: весь список лекарств и еды остаётся в строке своей даты.
        relief_labels = {"yes": t(lang, 'common.yes'), "no": t(lang, 'common.no'), "a_little": t(lang, 'common.a_little')}
        row.append("\n".join(t(lang, 'day_export.index_item_helped_relief_labels', index=index, item=item['description'], relief_labels=relief_labels.get(item['relief'], t(lang, 'common.not_answered')))
                             for index, item in enumerate(medicines, 1)))
        meals = sorted(grouped.get("meals", {}).get(day, []), key=lambda item: (item["created_at"], item["id"]))
        row.append("\n".join(f"{item['meal_time']} — {item['comment']}" for item in meals))
        answers = grouped.get("day_pain_answers", {}).get(day, [])
        options = grouped.get("day_pain_options", {}).get(day, [])
        for key in PAIN_QUESTIONS:
            status = next((item["status"] for item in answers if item["question_key"] == key), None)
            status_keys = {"in_progress":"statistics.in_progress", "answered":"common.answered", "none":"common.none_trigger", "unknown":"common.not_sure", "skipped":"statistics.skipped"}
            row.append(t(lang, status_keys[status]) if status in status_keys else status)
            labels = option_labels(key, lang=lang)
            selections = []
            for item in options:
                if item["question_key"] == key and item["is_selected"]:
                    label = labels.get(item["option_code"], item["option_code"])
                    if item["custom_text"]:
                        label += ": " + item["custom_text"]
                    selections.append(label)
            row.append("\n".join(selections))
        legacy = grouped.get("calendar_answers", {}).get(day, [])
        row.append(yes_no(legacy[0]["answer"], lang=lang) if legacy else None)
        ratings = grouped.get("day_ratings", {}).get(day, [])
        ratings = ratings[0] if ratings else {}
        row += [ratings.get(field) for field in ("sleep", "food", "mood")]
        rows.append(row)
    return headers, rows


def make_excel_file(data, lang="en") -> bytes | None:
    headers, rows = export_rows(data, lang=lang)
    if not rows:
        return None
    # Очень длинный список не обрезаем по лимиту одной ячейки Excel:
    # его продолжение помещаем в соседнюю колонку, сохраняя одну строку на дату.
    expanded_headers = []
    expanded_rows = [[] for row in rows]
    for column, header in enumerate(headers):
        parts = max(1, max((len(row[column]) + 31999) // 32000 if isinstance(row[column], str) else 1 for row in rows))
        for part in range(parts):
            # CAN CHANGE TEXT
            expanded_headers.append(header if part == 0 else t(lang, 'day_export.header_continued_part', header=header, part=part + 1))
            for index, row in enumerate(rows):
                value = row[column]
                if isinstance(value, str):
                    value = value[part * 32000:(part + 1) * 32000]
                elif part:
                    value = None
                expanded_rows[index].append(value)
    workbook = Workbook()
    sheet = workbook.active
    # CAN CHANGE TEXT
    sheet.title = t(lang, 'day_export.diary_answers')
    sheet.append(expanded_headers)
    for row in expanded_rows:
        sheet.append([ILLEGAL_CHARACTERS_RE.sub("", value) if isinstance(value, str) else value for value in row])
    for row in sheet:
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if isinstance(cell.value, str):
                # Текст пользователя, начинающийся с '=', не должен стать формулой.
                cell.data_type = "s"
            if isinstance(cell.value, date):
                cell.number_format = "dd.mm.yyyy"
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="245B45")
    sheet.row_dimensions[1].height = 42
    for index, header in enumerate(expanded_headers, 1):
        width = 42
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.column_dimensions["A"].width = 15
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = sheet.dimensions
    with BytesIO() as output:
        workbook.save(output)
        result = output.getvalue()
    workbook.close()
    return result
