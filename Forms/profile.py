from localization import t
from aiogram.fsm.state import State, StatesGroup

# CAN CHANGE TEXT / IMAGE: имена картинок из папки Images для сообщений настройки.
PROFILE_IMAGES = {
    "welcome": "helloimage.png",
    "gender": "gender.png",
    "birth_year": "bdayyear.png",
    "utc_offset": "timezones.png",
    "complete": "seeyousoon.png",
}

# CAN CHANGE TEXT / IMAGE: русские версии; остальные картинки общие для двух языков.
PROFILE_IMAGES_RU = {
    "welcome": "RU-helloimage.png",
    "complete": "RU-seeyousoon.png",
}

# CAN CHANGE TEXT: приветствие и вопросы настройки профиля.
WELCOME_TEXT = (
    t("en", 'profile.welcome')
)

# CAN CHANGE TEXT
PROFILE_QUESTIONS = {
    'language': t("en", 'profile.question.language'),
    'nickname': t("en", 'profile.question.nickname'),
    # Временно отключены. Для возврата вопросов раскомментируйте эти две строки.
    # 'gender': t("en", 'profile.question.gender'),
    # 'birth_year': t("en", 'profile.question.birth_year'),
    'utc_offset': t("en", 'profile.question.utc_offset'),
    'reminder_period': t("en", 'profile.question.reminder_period'),
    'reminder_hour': t("en", 'profile.question.reminder_hour'),
}


def next_profile_field(profile: dict) -> str | None:
    for field in PROFILE_QUESTIONS:
        if profile[field] is None:
            return field
    return None


class ProfileEdit(StatesGroup):
    settings = State()
    timezone = State()
