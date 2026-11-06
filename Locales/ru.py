# CAN CHANGE TEXT: ru
TEXTS = {'calendar.day_summary': '<b>Выбранный день: {date:%d.%m.%Y}</b>\n'
                         'Время сна: {bedtime} – {wake_time}\n'
                         'Удовлетворённость сном: {sleep_satisfaction}\n'
                         'Стабильность настроения: {mood}\n'
                         'Боль в животе: {ache_text}',
 'calendar.edit_the_day': 'Заполнить день',
 'calendar.meals': '← Еда',
 'calendar.meals_2': 'Еда →',
 'calendar.month.1': 'Январь',
 'calendar.month.10': 'Октябрь',
 'calendar.month.11': 'Ноябрь',
 'calendar.month.12': 'Декабрь',
 'calendar.month.2': 'Февраль',
 'calendar.month.3': 'Март',
 'calendar.month.4': 'Апрель',
 'calendar.month.5': 'Май',
 'calendar.month.6': 'Июнь',
 'calendar.month.7': 'Июль',
 'calendar.month.8': 'Август',
 'calendar.month.9': 'Сентябрь',
 'calendar.month_date.1': 'января',
 'calendar.month_date.10': 'октября',
 'calendar.month_date.11': 'ноября',
 'calendar.month_date.12': 'декабря',
 'calendar.month_date.2': 'февраля',
 'calendar.month_date.3': 'марта',
 'calendar.month_date.4': 'апреля',
 'calendar.month_date.5': 'мая',
 'calendar.month_date.6': 'июня',
 'calendar.month_date.7': 'июля',
 'calendar.month_date.8': 'августа',
 'calendar.month_date.9': 'сентября',
 'calendar.month_title': '{month} {year}',
 'calendar.weekday.0': 'Пн',
 'calendar.weekday.1': 'Вт',
 'calendar.weekday.2': 'Ср',
 'calendar.weekday.3': 'Чт',
 'calendar.weekday.4': 'Пт',
 'calendar.weekday.5': 'Сб',
 'calendar.weekday.6': 'Вс',
 'calendar.weekday_full.0': 'Понедельник',
 'calendar.weekday_full.1': 'Вторник',
 'calendar.weekday_full.2': 'Среда',
 'calendar.weekday_full.3': 'Четверг',
 'calendar.weekday_full.4': 'Пятница',
 'calendar.weekday_full.5': 'Суббота',
 'calendar.weekday_full.6': 'Воскресенье',
 'command.callendar': '📅 Открыть календарь и сохранить черновик',
 'command.help': '❓ Как пользоваться Foodie',
 'command.language': '🌐 Изменить язык интерфейса',
 'command.makenote': '📝 Дневник и последние записи',
 'command.meal': '🍽 Записать приём пищи',
 'command.settings': '⚙️ Заново настроить профиль',
 'command.start': '🏠 Начать заново и открыть календарь',
 'command.statistics': '📊 Общая и месячная статистика',
 'command.timezone': '🌍 Изменить часовой пояс',
 'commands.help': '👋 Foodie — дневник сна, стабильности настроения, боли в животе и питания.\n'
                  '\n'
                  '📅 /callendar — посмотреть сегодня или прошлую дату; «Заполнить день» начинает опрос.\n'
                  '📝 /makenote — последние записи и переход к сегодня/вчера.\n'
                  '🍽 /meal [описание] — записать еду по текущему местному времени. Описание до 50 символов или '
                  '«Пропустить».\n'
                  '📊 /statistics — общая и месячная статистика; «Скачать Excel» выгружает все ответы.\n'
                  '⚙️ /settings — повторная настройка. Прежние параметры действуют до завершения.\n'
                  '🌍 /timezone — сменить UTC-смещение, сохранив настройки напоминаний.\n'
                  '🌐 /language — сменить русский/английский без потери данных и черновиков.\n'
                  '🏠 /start — выйти из диалога в календарь, сохранив ответы.\n'
                  '❓ /help — эта справка.\n'
                  '\n'
                  'Каждый ответ сохраняется сразу. «Отмена» оставляет прогресс. «Продолжить черновик» '
                  'возобновляет опрос; «Начать заново» заменяет только черновик и его препараты, сохраняя еду.\n'
                  '\n'
                  '🛏 Отход ко сну: от полудня предыдущего до полудня выбранного дня. Пробуждение: 00:00–24:00 '
                  'выбранного дня. Введите ЧЧ:ММ или нажмите время; отрицательная длительность не принимается. '
                  'Оценки — 1–10. Заметка о дне до 200 символов — последняя.\n'
                  '\n'
                  'Пять целей отметки: сон ≥7 часов, удовлетворённость сном ≥7, стабильность настроения ≥7, ≥2 '
                  'приёмов пищи, отход ко сну до 23:00 предыдущего дня.\n'
                  '✅ Все выполнены; 🟨 одна не выполнена; 🟧 две; 🟥 три и больше (🆘, если записана боль). 📝 Не '
                  'завершено; без отметки — нет ответов дневника.\n'
                  '\n'
                  '🔔 Напоминания: после выбранного местного часа, при 24 часах без завершённой записи, не чаще '
                  'раза за местный день. Еда таймер не сбрасывает. Утром — запись за вчера, вечером — за сегодня.',
 'commands.quick_commands': '📋 Быстрые команды',
 'common.a_little': 'Немного',
 'common.answered': 'Отвечено',
 'common.back': 'Назад',
 'common.calendar': 'Календарь',
 'common.cancel': 'Отмена',
 'common.done': 'Готово',
 'common.no': 'Нет',
 'common.no_comment': 'Без описания',
 'common.no_data': 'Пока нет данных',
 'common.none': 'Ничего из перечисленного',
 'common.none_trigger': 'Нет симптомов / нет явного триггера',
 'common.not_answered': 'Нет ответа',
 'common.not_sure': 'Не уверен(а)',
 'common.skip': 'Пропустить',
 'common.statistics': 'Статистика',
 'common.today': 'Сегодня',
 'common.yes': 'Да',
 'common.yesterday': 'Вчера',
 'day.all_recorded_medications': 'Все записанные препараты:',
 'day.am': 'ДП',
 'day.answer_recorded': '\n\nОтвет записан\n',
 'day.b_entry_saved_b': '<b>Запись сохранена!</b>\n\n',
 'day.b_headache_diary_b_you_can_create_a_new': '<b>Дневник самочувствия</b>\n'
                                                '\n'
                                                'Можно создать новую запись, изменить ответы за прошлые дни или '
                                                'открыть календарь.\n'
                                                '\n'
                                                '<b>Последние записи:</b>',
 'day.bedtime_is_outside_the_noon_to_noon_range': 'Время отхода ко сну должно быть между полуднем предыдущего и '
                                                  'полуднем выбранного дня',
 'day.bedtime_range_selected_date_d_m_y_12_00': '\n'
                                                'Отход ко сну: {selected_date:%d.%m.%Y} 12:00 – '
                                                '{selected_date_value:%d.%m.%Y} 12:00',
 'day.continue_draft': 'Продолжить черновик',
 'day.future_dates_are_not_available': 'Будущие даты недоступны.',
 'day.history_date': '{day} {month}',
 'day.index_medication_helped_effect': '{index}. {medication} — Помогло: {effect}',
 'day.invalid_answer': 'Неверный ответ',
 'day.invalid_date_open_callendar': 'Неверная дата. Откройте /callendar.',
 'day.invalid_time': 'Неверное время',
 'day.make_a_note_about_selected_date_d_m_y': 'Сделать запись за {selected_date:%d.%m.%Y}',
 'day.make_note_for_today_today_d_m_y': 'Запись за сегодня ({today:%d.%m.%Y})',
 'day.make_note_for_yesterday_yesterday_d_m_y': 'Запись за вчера ({yesterday:%d.%m.%Y})',
 'day.no_entries_yet': '\nЗаписей пока нет.',
 'day.open_callendar': 'Откройте /callendar.',
 'day.please_enter_a_valid_time_as_hh_mm': 'Введите корректное время в формате ЧЧ:ММ.',
 'day.please_finish_your_setup_with_start_first': 'Сначала завершите настройку через /start.',
 'day.please_use_the_buttons_for_this_question': 'Ответьте на этот вопрос кнопками.',
 'day.please_write_between_1_and_limit_characters': 'Введите от 1 до {limit} символов.',
 'day.pm': 'ПП',
 'day.question.ache': '🤕 Была ли боль в животе в этот день?',
 'day.question.bedtime': '🛏 Во сколько вы легли спать?\n'
                         'Выберите время от 12:00 предыдущего дня до 12:00 выбранного дня.\n'
                         'Нажмите время или введите ЧЧ:ММ. Время до полудня относится к выбранному дню, остальное '
                         '— к предыдущему.\n'
                         'Для полудня выбранного дня нажмите его кнопку или введите «сегодня 12:00».',
 'day.question.day_comment': '📝 Напишите короткую заметку о дне (до 200 символов).',
 'day.question.day_comment_wanted': '📝 Хотите добавить заметку о дне?',
 'day.question.medicine_details': '💊 Какой препарат и в какой дозировке вы приняли?\nНапишите название и дозу.',
 'day.question.medicine_relief': '💊 Помогло ли?',
 'day.question.mood_control': '🙂 Насколько стабильным было ваше настроение в течение дня?\n'
                              '1 — крайне нестабильным, 10 — очень стабильным.',
 'day.question.more_medicine': '➕ Принимали что-нибудь ещё?',
 'day.question.pain_comment': '📝 Напишите короткую заметку об эпизоде боли.',
 'day.question.pain_comment_wanted': '📝 Хотите добавить заметку об эпизоде боли?',
 'day.question.pain_description_requested': '🤕 Хотите описать, как именно болело?',
 'day.question.pain_intensity': '🌡 Насколько сильной была боль по сравнению с самой сильной болью в вашей жизни?\n'
                                '1 — очень слабая, 10 — самая сильная.',
 'day.question.painkillers': '💊 Принимали ли вы обезболивающее?',
 'day.question.sleep_satisfaction': '😴 Насколько вы удовлетворены своим сном?\n'
                                    '1 — совершенно не удовлетворён(а), 10 — полностью удовлетворён(а).',
 'day.question.wake_time': '🌅 Во сколько вы проснулись?\n'
                           'Выберите 00:00–24:00 выбранного дня. 24:00 — конец этого дня.\n'
                           'Нажмите целый час или введите ЧЧ:ММ.',
 'day.recorded_medications_continued': 'Записанные препараты (продолжение):',
 'day.sleep_time_cant_be_negative': 'Длительность сна не может быть отрицательной\n\n',
 'day.start_clean': 'Начать заново',
 'day.the_diary_questions_have_changed_open_callendar': 'Вопросы дневника изменились. Откройте /callendar.',
 'day.this_answer_is_invalid_or_the_question_has_expired': 'Неверный ответ или устаревший вопрос. Откройте '
                                                           '/callendar.',
 'day.this_draft_choice_has_expired_open_callendar': 'Этот выбор черновика устарел. Откройте /callendar.',
 'day.this_draft_has_changed_open_callendar': 'Черновик изменился. Откройте /callendar.',
 'day.this_edit_has_expired_open_callendar': 'Это редактирование устарело. Откройте /callendar.',
 'day.time_not_recorded': 'Время не записано',
 'day.use_hh_mm': 'Используйте ЧЧ:ММ',
 'day.view_the_calendar': 'Открыть календарь',
 'day.wake_up_date_selected_date_d_m_y': '\nДата пробуждения: {selected_date:%d.%m.%Y}',
 'day.you_have_an_unfinished_entry_for_selected_date_d': '📝 У вас есть незавершённая запись за '
                                                         '{selected_date:%d.%m.%Y}.\n'
                                                         'Продолжите её или начните заново, заменив этот '
                                                         'черновик. Записи еды сохранятся.',
 'day.your_previous_answer_is_already_saved_let_s_continue': 'Предыдущий ответ уже сохранён. Продолжим.',
 'day_export.answers': ' — ответы',
 'day_export.bedtime': 'Отход ко сну',
 'day_export.bedtime_date': 'Дата отхода ко сну',
 'day_export.completed': 'Завершена',
 'day_export.date': 'Дата',
 'day_export.diary_answers': 'Ответы дневника',
 'day_export.draft': 'Черновик',
 'day_export.entry_status': 'Статус записи',
 'day_export.header_continued_part': '{header} (продолжение {part})',
 'day_export.index_item_helped_relief_labels': '{index}. {item} — Помогло: {relief_labels}',
 'day_export.legacy_food_1_7': 'Прежнее питание (1–7)',
 'day_export.legacy_mood_1_7': 'Прежнее настроение (1–7)',
 'day_export.legacy_sleep_1_7': 'Прежний сон (1–7)',
 'day_export.legacy_yes_no': 'Прежний ответ Да/Нет',
 'day_export.meals_local_time_and_description': 'Приёмы пищи (местное время и описание)',
 'day_export.medications_and_effect': 'Препараты и эффект',
 'day_export.status': ' — статус',
 'diary.editing_day': 'Запись за {date:%d.%m.%Y}\n\n{question}',
 'export.answers': '{title} — ответы',
 'export.caption': 'Все сохранённые даты, от новых к старым. Черновики включены.',
 'export.field.ache': 'Боль в животе',
 'export.field.day_comment': 'Заметка о дне',
 'export.field.day_comment_wanted': 'Запрошена заметка о дне',
 'export.field.mood_control': 'Стабильность настроения (1–10)',
 'export.field.more_medicine': 'Другие препараты',
 'export.field.pain_comment': 'Заметка о боли',
 'export.field.pain_comment_wanted': 'Запрошена заметка о боли',
 'export.field.pain_description_requested': 'Запрошено описание боли',
 'export.field.pain_intensity': 'Интенсивность боли (1–10)',
 'export.field.painkillers': 'Приём обезболивающего',
 'export.field.sleep_satisfaction': 'Удовлетворённость сном (1–10)',
 'export.field.wake_time': 'Время пробуждения',
 'export.filename': 'foodbot_дневник.xlsx',
 'export.pain.0': 'Область боли',
 'export.pain.1': 'Характер боли',
 'export.pain.2': 'Сопутствующие симптомы',
 'export.pain.3': 'Предполагаемые пользователем триггеры',
 'export.status': '{title} — статус',
 'language.choose': 'Выберите язык.',
 'language.invalid': 'Используйте кнопки выбора языка.',
 'language.saved': 'Язык сохранён: {language}.',
 'meal.meal_saved_selected_date_d_m_y_at_data': '🍽 Приём пищи сохранён!\n'
                                                '{selected_date:%d.%m.%Y} в {data} — {description}',
 'meal.please_finish_your_setup_with_start_first': 'Сначала завершите настройку через /start.',
 'meal.please_write_between_1_and_50_characters_or_tap': 'Введите от 1 до 50 символов или нажмите «Пропустить».',
 'meal.prompt': '🍽 Приём пищи записан в {time}, дата — {day}.\n'
                'Добавьте описание (до 50 символов) или нажмите «Пропустить».',
 'meal.the_description_was_too_long_please_shorten_it_to': '\n'
                                                           'Описание слишком длинное. Сократите его до 50 '
                                                           'символов.',
 'meal.this_meal_is_already_recorded_open_callendar': 'Этот приём пищи уже записан. Откройте /callendar.',
 'pain.answer': '\nОтвет: ',
 'pain.answer_recorded': '\n\nОтвет записан\n',
 'pain.bedtime_date_bedtime_date_d_m_y': 'Дата отхода ко сну: {bedtime_date:%d.%m.%Y}\n\n',
 'pain.confirmed': 'Подтверждено',
 'pain.editing_day_selected_date_d_m_y': 'Запись за {selected_date:%d.%m.%Y}\n\n',
 'pain.error.choose_first': 'Сначала выберите ответ, «Не уверен(а)» или «Пропустить».',
 'pain.error.invalid_selection': 'Неверный выбор',
 'pain.error.invalid_text': 'Неверный текст',
 'pain.error.other_text': 'Для варианта «Другое» введите текст.',
 'pain.error.question_changed': 'Вопрос изменился. Откройте /callendar.',
 'pain.full_entry_selected_date_d_m_y': 'Полная запись за {selected_date:%d.%m.%Y}\n\n',
 'pain.intro': 'Опишите самый сильный эпизод боли за {date}.\n'
               'Можно выбрать несколько ответов.\n'
               '\n'
               'Если внезапная сильная боль происходит сейчас, срочно обратитесь за медицинской помощью. Не ждите '
               'завершения дневника.',
 'pain.invalid_entry': 'Неверная запись.',
 'pain.medication_item_helped_item_value': 'Препарат: {item}\nПомогло: {item_value}\n\n',
 'pain.next': 'Далее →',
 'pain.no_clear_trigger': 'Нет явного триггера',
 'pain.option.pain_character.burning': 'Жжение',
 'pain.option.pain_character.cramping': 'Схваткообразная',
 'pain.option.pain_character.dull': 'Тупая / ноющая',
 'pain.option.pain_character.other': 'Другое',
 'pain.option.pain_character.pressure': 'Давление / распирание',
 'pain.option.pain_character.sharp': 'Острая / колющая',
 'pain.option.pain_character.throbbing': 'Пульсирующая',
 'pain.option.pain_location.all_over': 'По всему животу',
 'pain.option.pain_location.lower_left': 'Внизу слева',
 'pain.option.pain_location.lower_middle': 'Внизу по центру',
 'pain.option.pain_location.lower_right': 'Внизу справа',
 'pain.option.pain_location.middle_left': 'Посередине слева',
 'pain.option.pain_location.middle_right': 'Посередине справа',
 'pain.option.pain_location.navel': 'Вокруг пупка',
 'pain.option.pain_location.other': 'Другая область',
 'pain.option.pain_location.upper_left': 'Вверху слева',
 'pain.option.pain_location.upper_middle': 'Вверху по центру',
 'pain.option.pain_location.upper_right': 'Вверху справа',
 'pain.option.pain_symptoms.black_stool': 'Чёрный липкий стул',
 'pain.option.pain_symptoms.bloating': 'Вздутие',
 'pain.option.pain_symptoms.blood_vomit': 'Кровь в рвоте',
 'pain.option.pain_symptoms.bowel_bleeding': 'Сильное кишечное кровотечение',
 'pain.option.pain_symptoms.breathing': 'Затруднение дыхания',
 'pain.option.pain_symptoms.constipation': 'Запор',
 'pain.option.pain_symptoms.diarrhoea': 'Диарея',
 'pain.option.pain_symptoms.fainting': 'Обморок',
 'pain.option.pain_symptoms.feverish': 'Повышенная температура / ощущение жара',
 'pain.option.pain_symptoms.heartburn': 'Изжога',
 'pain.option.pain_symptoms.nausea': 'Тошнота',
 'pain.option.pain_symptoms.other': 'Другое',
 'pain.option.pain_symptoms.vomiting': 'Рвота',
 'pain.option.pain_triggers.activity': 'Физическая активность',
 'pain.option.pain_triggers.food': 'Конкретная еда или напиток',
 'pain.option.pain_triggers.large_meal': 'Больше еды, чем обычно',
 'pain.option.pain_triggers.late_eating': 'Поздний приём пищи',
 'pain.option.pain_triggers.meal_gap': 'Длительный перерыв между едой',
 'pain.option.pain_triggers.medicine': 'Препарат или добавка',
 'pain.option.pain_triggers.other': 'Другое',
 'pain.option.pain_triggers.sleep': 'Плохой или короткий сон',
 'pain.option.pain_triggers.stress': 'Стресс или тревога',
 'pain.page_page_pages': 'Страница {page}/{pages}\n\n',
 'pain.pause_and_return': 'Приостановить и вернуться',
 'pain.please_type_a_short_description_1_limit_characters': 'Введите краткое описание (от 1 до {limit} символов).',
 'pain.please_use_the_buttons_or_select_other_to_enter': 'Используйте кнопки или выберите «Другое», чтобы ввести '
                                                         'текст.',
 'pain.please_write_between_1_and_limit_characters_or_reopen': 'Введите от 1 до {limit} символов. Если вопрос '
                                                               'изменился, откройте /callendar заново.\n'
                                                               '\n',
 'pain.previous': '← Назад',
 'pain.question.pain_character': 'Какой была боль? Выберите все подходящие варианты.',
 'pain.question.pain_location': 'Где вы чувствовали боль?\nСлева и справа — с вашей точки зрения.',
 'pain.question.pain_symptoms': 'Какие ещё симптомы вы заметили во время этого эпизода?\n'
                                'Выберите все подходящие варианты.',
 'pain.question.pain_triggers': 'Что, по вашему мнению, могло повлиять на боль?\n'
                                'Это ваши предположения, а не подтверждённые причины.',
 'pain.selections_saved_so_far': '\n\nСохранённый выбор\n',
 'pain.selections_saved_so_far_2': 'Сохранённый выбор',
 'pain.skipped': 'Пропущено',
 'pain.status_status': '\nСтатус: {status}\n',
 'pain.this_question_has_changed_open_callendar': 'Этот вопрос изменился. Откройте /callendar.',
 'pain.this_question_has_expired_open_callendar': 'Этот вопрос устарел. Откройте /callendar.',
 'pain.urgent_text': 'Если это происходит сейчас, срочно обратитесь за медицинской помощью.\n'
                     'Не ждите завершения дневника.',
 'pain.you_can_mention_a_specific_food_drink_or_other': '\n'
                                                        'Можно указать конкретную еду, напиток или другой фактор.',
 'profile.am': 'ДП',
 'profile.english': 'English',
 'profile.every_evening': 'Каждый вечер',
 'profile.every_morning': 'Каждое утро',
 'profile.excellent_i_ll_remind_you_of_my_presence_after': '👍 Напоминания — после {hour}:00 {suffix}.',
 'profile.first_choice': '🌐 Какой язык вы предпочитаете? / What language do you prefer?',
 'profile.gender.female': 'Женский',
 'profile.gender.male': 'Мужской',
 'profile.gender.secret': 'Не хочу говорить',
 'profile.hour': '{hour}:00 {period}',
 'profile.invalid_profile_answer': 'Неверный ответ настройки',
 'profile.let_s_update_your_settings_your_current_settings_stay': '⚙️ Обновим профиль. Прежние настройки '
                                                                  'действуют до завершения.\n'
                                                                  'Для выхода — /start.',
 'profile.moscow': ' (Москва)',
 'profile.moscow_3_00_utc': 'Москва (+3:00 UTC)',
 'profile.offset_d_00_utc': '{offset:+d}:00 UTC',
 'profile.please_answer_the_current_question_using_its_buttons': 'Ответьте на текущий вопрос его кнопками.',
 'profile.please_choose_a_time_zone_using_the_buttons': 'Выберите часовой пояс кнопками.',
 'profile.please_choose_a_time_zone_using_the_buttons_or': 'Выберите часовой пояс кнопками или используйте '
                                                           '/callendar для выхода.',
 'profile.please_enter_a_year_from_1900_to_date': 'Введите год от 1900 до {date}.',
 'profile.please_finish_your_setup_with_start_first': 'Сначала завершите настройку через /start.',
 'profile.please_open_a_private_chat_with_me_and_send': 'Откройте личный чат со мной и отправьте /start.',
 'profile.please_send_start_first': 'Сначала отправьте /start.',
 'profile.please_send_start_in_a_private_chat': 'Отправьте /start в личном чате.',
 'profile.please_use_the_buttons_for_the_current_question': 'Используйте кнопки текущего вопроса.',
 'profile.please_write_a_nickname_between_1_and_64_characters': 'Введите никнейм длиной от 1 до 64 символов.',
 'profile.pm': 'ПП',
 'profile.question.birth_year': '🎂 В каком году вы родились?',
 'profile.question.gender': '👤 Какой у вас пол?',
 'profile.question.language': '🌐 Какой язык вы предпочитаете?',
 'profile.question.nickname': '👋 Как к вам обращаться?\nВведите никнейм (1–64 символа).',
 'profile.question.reminder_hour': 'Запись можно сделать в любое время.\n'
                                   '\n'
                                   'После 24 часов без завершённой записи возможно одно напоминание за местный '
                                   'день.\n'
                                   'Выберите час, начиная с которого можно напоминать.',
 'profile.question.reminder_period': "Когда напоминать о дневнике?\n\nУтром — запись за вчера + сегодняшний сон\nВечером — запись за сегодня + сегодняшний сон",
 'profile.question.utc_offset': '🌍 В каком вы часовом поясе?',
 'profile.russian': 'Русский',
 'profile.time': '{hour:02d}:00',
 'profile.time_zone_saved_offset_d_00_utc_your_reminder': '🌍 Часовой пояс: {offset:+d}:00 UTC.\n'
                                                          '🔔 Час напоминания сохранён и теперь относится к этому '
                                                          'поясу.',
 'profile.value_d_00_utc': '{value:+d}:00 UTC',
 'profile.welcome': 'Привет! Я Foodie!\n'
                    'Я помогу вести дневник сна, питания, настроения и самочувствия.\n'
                    '\n'
                    'Выберите язык, чтобы продолжить.\n'
                    'Если мы уже общались, ваши записи сохранятся.',
 'profile.wrote_the_answer': 'Ответ записан\n',
 'profile.your_setup_is_already_complete_open_settings_to_change': 'Настройка уже завершена. Для изменения '
                                                                   'откройте /settings.',
 'reminders.could_not_check_reminders': 'Не удалось проверить напоминания',
 'reminders.hi_it_s_me': '— Привет, это я!',
 'reminders.reminder_failed_for_user_s_s': 'Не удалось отправить напоминание пользователю %s (%s)',
 'routes.b_day_comment_b': '\n\n<b>📝 Заметка о дне:</b>\n',
 'routes.b_meals_b': '\n\n<b>Приёмы пищи:</b>',
 'routes.future_dates_are_not_available': 'Будущие даты недоступны.',
 'routes.invalid_date_open_callendar': 'Неверная дата. Откройте /callendar.',
 'routes.invalid_meal_page_open_callendar': 'Неверная страница приёмов пищи. Откройте /callendar.',
 'routes.meal_index_meal_escape': '\nПриём пищи {index} - {meal} - {escape}',
 'routes.meals_page_meal_page_meals': '\nСтраница приёмов пищи {meal_page}/{meals}',
 'routes.no_meals_recorded': '\nПриёмы пищи не записаны.',
 'routes.open_the_calendar_with_callendar': 'Откройте календарь через /callendar.',
 'routes.please_finish_your_setup_with_start_first': 'Сначала завершите настройку через /start.',
 'routes.select_a_day_to_view_its_entry': 'Выберите дату, чтобы посмотреть запись.',
 'routes.this_button_is_no_longer_used_open_callendar': 'Эта кнопка больше не используется. Откройте /callendar.',
 'routes.today': ' (В выбранный день)',
 'statistics.all_time': 'Всё время',
 'statistics.b_all_time_statistics_b': '<b>📊 Статистика за всё время</b>\n\n',
 'statistics.b_previous_month_month_title_b': '\n\n<b>🗓 Предыдущий месяц: {month_title}</b>\n\n',
 'statistics.b_statistics_month_title_b': '<b>📊 Статистика: {month_title}</b>\n\n',
 'statistics.days_with_stomach_pain_pain_days_average_pain_intensity': 'Дней с болью в животе: {pain_days}\n'
                                                                       'Средняя интенсивность боли: {intensity}\n'
                                                                       '\n',
 'statistics.duration_h_duration_value_02d_min': '{duration} ч {duration_value:02d} мин',
 'statistics.future_dates_are_not_available': 'Будущие даты недоступны.',
 'statistics.get_excel_file': 'Скачать Excel',
 'statistics.in_progress': 'Не завершено',
 'statistics.invalid_date_open_callendar': 'Неверная дата. Откройте /callendar.',
 'statistics.invalid_period': 'Неверный период.',
 'statistics.invalid_statistics_page_use_statistics': 'Неверная страница статистики. Используйте /statistics.',
 'statistics.meal_statistics': 'Статистика питания',
 'statistics.months': '← Месяцы',
 'statistics.months_2': 'Месяцы →',
 'statistics.multiple_selections_are_allowed_percentages_may_total_more_than': '\n'
                                                                               '\n'
                                                                               'Можно выбрать несколько '
                                                                               'вариантов, поэтому сумма '
                                                                               'процентов может превышать 100%.\n'
                                                                               '«Ничего из перечисленного» входит '
                                                                               'в N, но не считается симптомом '
                                                                               'или триггером.',
 'statistics.n_valid_dates_confirmed_dates': '\nN = {valid_dates} дат с подтверждённым ответом\n',
 'statistics.no_answer_pain_days': 'Нет ответа: {pain_days}\n',
 'statistics.no_data_yet': '\nПока нет данных',
 'statistics.no_data_yet_0_below_7': 'Пока нет данных (0 оценок ниже 7)',
 'statistics.no_data_yet_n_0': 'Пока нет данных (N = 0)',
 'statistics.no_saved_notes_yet_make_a_note_with_makenote': 'Пока нет записей. Сначала создайте запись через '
                                                            '/makenote или /meal.',
 'statistics.other_original_user_text': '\nДругое — исходный текст пользователя:\n',
 'statistics.pain_statistics': 'Статистика боли',
 'statistics.pain_statistics_title_page_page_pages': 'Статистика боли: {title}\nСтраница {page}/{pages}\n\n',
 'statistics.preparing_your_excel_file': 'Готовлю файл Excel…',
 'statistics.skipped': 'Пропущено',
 'statistics.summary': '<b>Дней с записями: {days}</b>\n'
                       '\n'
                       'Средняя длительность сна: {sleep}\n'
                       'Средняя удовлетворённость сном: {satisfaction}\n'
                       'Средняя стабильность настроения: {mood}\n'
                       'Дней с болью в животе: {pain_days}\n'
                       '\n'
                       '<b>✅ Отличных дней: {green_days}</b>\n'
                       '<b>🍽 Записей о еде: {meals}</b>',
 'statistics.user_suspected_triggers': 'Предполагаемые пользователем триггеры',
 'statistics.values_2f_10_below_below_7': '{values:.2f}/10 (оценок ниже 7: {below})'}


# CAN CHANGE TEXT: утренний опрос, политика и отдельное согласие.
TEXTS.update({
    "privacy.welcome": "Добро пожаловать в FoodBot. Сначала выберите язык и ознакомьтесь с обработкой данных.",
    "privacy.choose_language": "Выберите язык / Choose your language",
    "privacy.policy": "Политика конфиденциальности FoodBot\nВерсия {version}\n\nОператор: Лозовский Владислав Александрович.\nКонтакты: Telegram @ooosila; loz_vlad@icloud.com.\n\nFoodBot хранит Telegram ID и ID личного чата, язык, настройки профиля и ваши записи о сне, питании, настроении, боли, симптомах, лекарствах и заметки. Ранее сохранённые пол и год рождения также могут оставаться в профиле. Данные используются для дневника, напоминаний и статистики. Выгрузка Excel создаётся в памяти и отправляется вам в личный чат.\n\nПо информации владельца, бот размещён у российского хостинг-провайдера. Сообщения также проходят через Telegram и обрабатываются по его правилам. Оператор может иметь доступ к данным для поддержки и обслуживания.\n\nЗаписи хранятся до удаления вами или прекращения сервиса. /delete_me отзывает согласие и удаляет данные из действующей базы бота. По информации владельца, резервные копии базы удаляются еженедельно. До очередного удаления в них могут сохраняться прежние данные. Это не удаляет автоматически историю сообщений и уже скачанные файлы в Telegram.\n\nПолитика: /privacy. Бот предназначен для личного дневника совершеннолетних и не ставит диагнозы.",
    "privacy.consent": "Разрешаете FoodBot обрабатывать введённые вами данные, включая сведения о здоровье, для ведения дневника, напоминаний и статистики? Согласие можно отозвать через /delete_me.\n\nПри выборе «Не согласен» все ваши данные будут удалены из действующей базы бота.",
    "privacy.agree": "Согласен",
    "privacy.decline": "Не согласен",
    "privacy.accepted": "Выбор сохранён. Продолжим настройку.",
    "privacy.expired": "Эта кнопка устарела. Отправьте /start.",
    "privacy.start_required": "Для начала работы или согласия отправьте /start.",
    "privacy.declined": "Вы не дали согласие. Ваши данные удалены из действующей базы бота. Чтобы начать заново, отправьте /start. История Telegram и резервные копии удаляются отдельно по правилам политики.",
    "privacy.deleted": "Ваши данные удалены из действующей базы бота. Чтобы начать заново, отправьте /start. История Telegram и резервные копии удаляются отдельно по правилам политики.",
    "privacy.delete_question": "Удалить все ваши данные из действующей базы FoodBot и отозвать согласие? Это нельзя отменить. История Telegram и резервные копии удаляются отдельно по правилам политики.",
    "privacy.delete_confirm": "Удалить мои данные",
    "privacy.delete_cancelled": "Удаление отменено.",
    "privacy.delete_failed": "Не удалось завершить удаление. Доступ к дневнику и напоминания отключены. Повторите /delete_me или обратитесь к оператору через контакт в /privacy.",
    "command.privacy": "Политика конфиденциальности",
    "command.delete_me": "Удалить мои данные",
    "morning.open": "Сон за {date:%d.%m.%Y} и вчерашний день",
    "morning.intro": "Утренняя запись\n\nСон: ночь {bedtime_date:%d.%m.%Y}–{sleep_date:%d.%m.%Y}.\nОстальные ответы: {other_date:%d.%m.%Y}.\n\nУже сохранённые ответы останутся. Изменить их можно отдельными кнопками.\n",
    "morning.sleep_values": "\nСон: {bedtime} → {wake}\nУдовлетворённость сном: {satisfaction}\n",
    "morning.other_values": "\nСтабильность настроения вчера: {mood}\nБоль вчера: {ache}\n",
    "morning.continue": "Заполнить пропуски",
    "morning.resume": "Продолжить сохранённый утренний опрос",
    "morning.edit_sleep": "Изменить сон",
    "morning.edit_other": "Изменить ответы за вчера",
    "morning.view_other": "Посмотреть все ответы за вчера",
    "morning.saved": "Запись сделана!\nСон — {sleep_date:%d.%m.%Y}.\nОстальные ответы — {other_date:%d.%m.%Y}.",
    "morning.stale": "Это утреннее напоминание устарело. Начните запись за текущие даты или продолжите ранее начатую запись с указанными датами.",
    "morning.expired": "Этот утренний опрос устарел. Откройте актуальное напоминание или /callendar."
})

TEXTS["commands.help"] += "\n\n/privacy — политика конфиденциальности.\n/delete_me — удалить данные и отозвать согласие."

TEXTS.update({
    "morning.question.ache": "🤕 Была ли боль в животе {date:%d.%m.%Y}?",
    "morning.question.wake_time": "🌅 Во сколько вы проснулись {date:%d.%m.%Y}?\nВыберите 00:00–24:00 указанной даты или введите ЧЧ:ММ."
})

# CAN CHANGE TEXT: сохранённые ответы, утренние пересечения и время еды.
TEXTS.update({
    "day.already_recorded": "\n\nУже записано:\n{value}",
    "day.previous_answer": "\n\nУже было записано:\n{value}",
    "day.previous_shortened": "… (сокращено для показа)",
    "profile.every_evening_recommended": "Вечером (рекомендуем)",
    "reminders.friend": "друг",
    "reminders.morning_greeting": "Доброе утро, {nickname}! Сделаем запись?",
    "reminders.evening_greeting": "Добрый вечер, {nickname}! Сделаем запись?",
    "morning.only_sleep": "Записать только сегодняшний сон",
    "morning.continue_day": "Продолжить вчерашний день",
    "morning.resume_dates": "Продолжить: сон {sleep_date}, день {other_date}",
    "morning.yesterday_done": "\nЗа {date:%d.%m.%Y} остальные ответы уже заполнены. Запишем только сегодняшний сон?",
    "morning.continue_yesterday": "\nПродолжим запись за {date:%d.%m.%Y}, заполнив недостающие ответы.",
    "morning.yesterday_sleep_saved": "\nСон за {date:%d.%m.%Y} уже записан и останется без изменений.",
    "morning.today_sleep_saved": "\nСон за {date:%d.%m.%Y} уже записан. Повторно спрашивать его не будем.",
    "morning.already_complete": "\nОбе части уже заполнены. Можно посмотреть запись или явно выбрать редактирование.",
    "meal.time_hint": "\nМожно отправить ЧЧ:ММ, чтобы изменить время этого приёма пищи, или ЧЧ:ММ и описание. Дата останется прежней.",
    "meal.change_time": "Изменить время",
    "meal.invalid_time": "Укажите время в формате ЧЧ:ММ от 00:00 до 23:59. Например: 13:45.",
    "meal.not_found": "Эта запись недоступна или кнопка устарела. Откройте /callendar или начните новую запись через /meal.",
    "meal.time_question": "Приём пищи за {date:%d.%m.%Y}.\nУже записанное время: {time}.\n\nВведите новое время ЧЧ:ММ. Дата и описание не изменятся.",
    "meal.time_changed": "Уже было записано: {old}.\nНовое время: {new}.\n\n"
})

# CAN CHANGE TEXT: краткие даты утренней записи.
TEXTS["morning.short_dates"] = "Сон: {sleep_date:%d.%m.%Y}.\nОстальные ответы: {other_date:%d.%m.%Y}.\n"
