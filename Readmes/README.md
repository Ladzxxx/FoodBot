# FoodBot: запуск и места изменения

Подробное описание интерфейса и хранения данных: [основной README](../README.md).
Даты утреннего дневника и согласие: [MORNING_PRIVACY.md](MORNING_PRIVACY.md).

## Запуск

Нужен Python 3.12–3.14 и один процесс polling на токен.
Из папки проекта на Windows / PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Только при первой установке укажите BOT_TOKEN в .env.
.\.venv\Scripts\python.exe main.py
```

На Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Только при первой установке укажите BOT_TOKEN в .env.
python main.py
```

При обновлении сохраните существующие `.env` и `data/calendar.sqlite3`.
Не копируйте `.env.example` поверх настроенного `.env`. Бот добавляет недостающие
таблицы и столбцы при запуске; прежние записи и шкалы сохраняются.
Проверка через настоящий Telegram и Linux-сервер выполняется владельцем отдельно.
Серверные прокси, проверка здоровья и ночной бэкап в этой локальной копии
не представлены; перед загрузкой нужно сопоставить серверные доработки с кодом.

## Карта файлов и изменений

| Что менять | Файлы от корня проекта |
| --- | --- |
| Тексты вопросов, ошибки, подписи кнопок, месяцы | `Locales/ru.py`, `Locales/en.py`; одинаковые ключи и подстановки, `# CAN CHANGE TEXT`. |
| Порядок вопросов и переходы дневника | `Forms/day.py`, `Handlers/day.py`; описание боли — `Forms/pain.py`, `Handlers/pain.py`. |
| Кнопки | Модули по функционалу в `Keyboards/`; постоянное меню — `Keyboards/profile.py`. |
| Отображение выбранного дня и еды | `Handlers/routes.py`: `day_text()`, `calendar_text()`. |
| Отметка дня | `Forms/day.py`: `day_marker()`, общая для календаря и статистики. |
| Статистика и Excel | `Handlers/statistics.py`, `Keyboards/statistics.py`, `day_export.py`. |
| Профиль, язык, настройки и картинки | `Handlers/profile.py`, `Forms/profile.py`, `Keyboards/profile.py`, `Images/`. |
| Утренний дневник и восстановление двух дат | `Handlers/morning.py`, `morning_storage.py`, `Keyboards/morning.py`. |
| Согласие, доступ, удаление | `Handlers/privacy.py`, `privacy_access.py`, `privacy_storage.py`, `Keyboards/privacy.py`. |
| SQLite и сохранение ответов | `database.py`, `day_storage.py`, `pain_storage.py`. |
| Напоминания | `reminders.py`, `database.py`: 24 часа, выбранный час, актуальное согласие, максимум одна попытка за местный день. |
| Запуск, роутеры, остановка | `main.py`. |

Команда календаря — `/callendar`. Еда сохраняет местную дату при `/meal`;
исправление времени меняет ту же строку и не сбрасывает напоминания.
При первом входе язык политики временный; профиль создаётся после согласия.
Отказ удаляет активные данные пользователя, как указано рядом с кнопкой.

## Проверки

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py' -q
.\.venv\Scripts\python.exe -m pip check
```

Тесты используют временную SQLite и подменённый Telegram. В обычных сценариях
профиль уже имеет согласие; отсутствие согласия проверяется отдельно.
Новые сценарии сгруппированы в `test_privacy.py`, `test_morning.py`,
`test_meal.py` и `test_reminders.py`. Проверки и поиск ограничиваются рабочими
модулями и `tests`; `Archive` полностью исключён.

Локально 08.11.2026 прошёл **161 тест**, включая 30 новых. `pip check` не нашёл
конфликтов; синтаксис 48 активных Python-файлов проверен для Python 3.12.
В тесте ненадёжной доставки ожидается предупреждение `TelegramNetworkError`.
Тест запуска подменяет `getenv` по имени переменной: поддельный токен возвращается
только для `BOT_TOKEN`, другие переменные получают `None`. Это исключает подмену
адреса прокси токеном в этом тесте; серверный код прокси требует отдельной сверки.

`.env`, база, окружение и выгрузки исключены из Git. Коммит и загрузку
на сервер выполняет владелец после просмотра изменений.
