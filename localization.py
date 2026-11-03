from Locales.en import TEXTS as EN
from Locales.ru import TEXTS as RU


def t(lang, key, **values):
    texts = EN if lang == "en" else RU
    text = texts.get(key, EN.get(key))
    if text is None:
        raise KeyError(f"Missing translation: {key}")
    return text.format(**values)


def language_of(profile):
    return (profile or {}).get("language") or "ru"


def first_language(user):
    # Имя — только подсказка для первого приветствия, не сохранённый выбор.
    name = " ".join(filter(None, (user.first_name, user.last_name)))
    if any("а" <= char.lower() <= "я" or char.lower() == "ё" for char in name):
        return "ru"
    if any("a" <= char.lower() <= "z" for char in name):
        return "en"
    return "ru"
