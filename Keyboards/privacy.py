from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization import t


def privacy_language_keyboard(token):
    # CAN CHANGE TEXT: названия языков всегда на собственном языке.
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Русский", callback_data=f"privacy:lang:{token}:ru"),
        InlineKeyboardButton(text="English", callback_data=f"privacy:lang:{token}:en"),
    ]])


def consent_keyboard(token, lang):
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "privacy.agree"), callback_data=f"privacy:agree:{token}")],
        [InlineKeyboardButton(text=t(lang, "privacy.decline"), callback_data=f"privacy:decline:{token}")],
    ])


def delete_keyboard(token, lang):
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "privacy.delete_confirm"), callback_data=f"privacy:delete:{token}"),
        InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data=f"privacy:cancel:{token}"),
    ]])
