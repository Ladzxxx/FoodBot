from localization import t
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Forms.pain import PAIN_OPTIONS, option_labels


def pain_keyboard(edit_id, key, options, lang="en"):
    selected = {item['option_code'] for item in options if item['is_selected']}
    labels = option_labels(key, lang=lang)
    rows = []
    width = 3 if key == 'pain_location' else 2
    choices = PAIN_OPTIONS[key]
    # Первые девять областей расположены как живот пользователя, а не наблюдателя.
    for index in range(0, len(choices), width):
        row = []
        for code, label in choices[index:index + width]:
            if key == 'pain_location' and index >= 9:
                if row:
                    rows.append(row)
                row = []
            row.append(InlineKeyboardButton(text=f"{'☑' if code in selected else '☐'} {labels[code]}", callback_data=f'pain:{edit_id}:{code}'))
        if row:
            rows.append(row)
    for code in ('none', 'unknown', 'skipped'):
        if code in labels:
            rows.append([InlineKeyboardButton(text=f"{'☑' if code in selected else '☐'} {labels[code]}", callback_data=f'pain:{edit_id}:{code}')])
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'common.done'), callback_data=f'pain:{edit_id}:done')])
    rows.append([InlineKeyboardButton(text=t(lang, 'pain.pause_and_return'), callback_data=f'pain:{edit_id}:pause')])
    return InlineKeyboardMarkup(inline_keyboard=rows)
