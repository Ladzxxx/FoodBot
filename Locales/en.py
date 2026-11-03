# CAN CHANGE TEXT: en
TEXTS = {'calendar.day_summary': '<b>Selected day: {date:%d.%m.%Y}</b>\n'
                         'Sleep time: {bedtime} – {wake_time}\n'
                         'Sleep satisfaction: {sleep_satisfaction}\n'
                         'Mood stability: {mood}\n'
                         'Stomach pain: {ache_text}',
 'calendar.edit_the_day': 'Edit the day',
 'calendar.meals': '← Meals',
 'calendar.meals_2': 'Meals →',
 'calendar.month.1': 'January',
 'calendar.month.10': 'October',
 'calendar.month.11': 'November',
 'calendar.month.12': 'December',
 'calendar.month.2': 'February',
 'calendar.month.3': 'March',
 'calendar.month.4': 'April',
 'calendar.month.5': 'May',
 'calendar.month.6': 'June',
 'calendar.month.7': 'July',
 'calendar.month.8': 'August',
 'calendar.month.9': 'September',
 'calendar.month_date.1': 'January',
 'calendar.month_date.10': 'October',
 'calendar.month_date.11': 'November',
 'calendar.month_date.12': 'December',
 'calendar.month_date.2': 'February',
 'calendar.month_date.3': 'March',
 'calendar.month_date.4': 'April',
 'calendar.month_date.5': 'May',
 'calendar.month_date.6': 'June',
 'calendar.month_date.7': 'July',
 'calendar.month_date.8': 'August',
 'calendar.month_date.9': 'September',
 'calendar.month_title': '{month} {year}',
 'calendar.weekday.0': 'Mon',
 'calendar.weekday.1': 'Tue',
 'calendar.weekday.2': 'Wed',
 'calendar.weekday.3': 'Thu',
 'calendar.weekday.4': 'Fri',
 'calendar.weekday.5': 'Sat',
 'calendar.weekday.6': 'Sun',
 'calendar.weekday_full.0': 'Monday',
 'calendar.weekday_full.1': 'Tuesday',
 'calendar.weekday_full.2': 'Wednesday',
 'calendar.weekday_full.3': 'Thursday',
 'calendar.weekday_full.4': 'Friday',
 'calendar.weekday_full.5': 'Saturday',
 'calendar.weekday_full.6': 'Sunday',
 'command.callendar': '📅 Open the calendar; keep unfinished notes',
 'command.help': '❓ How to use Foodie',
 'command.language': '🌐 Change interface language',
 'command.makenote': '📝 Open your diary and recent entries',
 'command.meal': '🍽 Record a meal now',
 'command.settings': '⚙️ Set up your profile again',
 'command.start': '🏠 Restart the conversation and open the calendar',
 'command.statistics': '📊 All-time and monthly statistics',
 'command.timezone': '🌍 Change your time zone',
 'commands.help': '👋 Foodie is your diary of sleep, mood stability, stomach pain and meals.\n'
                  '\n'
                  '📅 /callendar — view today or a past date; Edit the day starts the questions.\n'
                  '📝 /makenote — recent entries and shortcuts for today/yesterday.\n'
                  '🍽 /meal [description] — record a meal at your current local time. Description: up to 50 '
                  'characters, or Skip.\n'
                  '📊 /statistics — all-time and monthly summaries; Get Excel file downloads all saved answers.\n'
                  '⚙️ /settings — repeat setup. Current settings stay active until you finish.\n'
                  '🌍 /timezone — change the UTC offset; keep reminder settings.\n'
                  '🌐 /language — switch Russian/English without losing data or drafts.\n'
                  '🏠 /start — leave the dialogue and open the calendar; keep saved answers.\n'
                  '❓ /help — show this guide.\n'
                  '\n'
                  'Answers save immediately. Cancel keeps progress. Continue draft resumes it; Start clean '
                  'replaces only that draft and its medications, keeping meals.\n'
                  '\n'
                  '🛏 Bedtime: yesterday noon to noon on the selected day. Wake-up: 00:00–24:00 on that day. Type '
                  'HH:MM or tap a time; negative duration is rejected. Ratings: 1–10. The final day comment '
                  'allows 200 characters.\n'
                  '\n'
                  'Day markers check five targets: sleep ≥7 hours, sleep satisfaction ≥7, mood stability ≥7, ≥2 '
                  'meals, bedtime before 23:00 yesterday.\n'
                  '✅ All met; 🟨 one unmet; 🟧 two; 🟥 three or more (🆘 if pain was recorded). 📝 Unfinished; no '
                  'marker means no diary answers.\n'
                  '\n'
                  '🔔 Reminders start after your chosen local hour, after 24 hours without a completed entry, at '
                  'most once per local day. Meals do not reset the timer. Morning reminders ask about yesterday; '
                  'evening reminders ask about today.',
 'commands.quick_commands': '📋 Quick commands',
 'common.a_little': 'A little',
 'common.answered': 'Answered',
 'common.back': 'Back',
 'common.calendar': 'Calendar',
 'common.cancel': 'Cancel',
 'common.done': 'Done',
 'common.no': 'No',
 'common.no_comment': 'No comment',
 'common.no_data': 'No data yet',
 'common.none': 'None',
 'common.none_trigger': 'None / No clear trigger',
 'common.not_answered': 'Not answered',
 'common.not_sure': 'Not sure',
 'common.skip': 'Skip',
 'common.statistics': 'Statistics',
 'common.today': 'Today',
 'common.yes': 'Yes',
 'common.yesterday': 'Yesterday',
 'day.all_recorded_medications': 'All recorded medications:',
 'day.am': 'AM',
 'day.answer_recorded': '\n\nAnswer recorded\n',
 'day.b_entry_saved_b': '<b>Entry saved!</b>\n\n',
 'day.b_headache_diary_b_you_can_create_a_new': '<b>Headache Diary</b>\n'
                                                '\n'
                                                'You can create a new entry, edit information for previous days, '
                                                'or view the calendar.\n'
                                                '\n'
                                                '<b>Latest entries:</b>',
 'day.bedtime_is_outside_the_noon_to_noon_range': 'Bedtime is outside the noon-to-noon range',
 'day.bedtime_range_selected_date_d_m_y_12_00': '\n'
                                                'Bedtime range: {selected_date:%d.%m.%Y} 12:00 – '
                                                '{selected_date_value:%d.%m.%Y} 12:00',
 'day.continue_draft': 'Continue draft',
 'day.future_dates_are_not_available': 'Future dates are not available.',
 'day.history_date': '{month} {day}',
 'day.index_medication_helped_effect': '{index}. {medication} — Helped: {effect}',
 'day.invalid_answer': 'Invalid answer',
 'day.invalid_date_open_callendar': 'Invalid date. Open /callendar.',
 'day.invalid_time': 'Invalid time',
 'day.make_a_note_about_selected_date_d_m_y': 'Make a note about {selected_date:%d.%m.%Y}',
 'day.make_note_for_today_today_d_m_y': 'Make note for today ({today:%d.%m.%Y})',
 'day.make_note_for_yesterday_yesterday_d_m_y': 'Make note for yesterday ({yesterday:%d.%m.%Y})',
 'day.no_entries_yet': '\nNo entries yet.',
 'day.open_callendar': 'Open /callendar.',
 'day.please_enter_a_valid_time_as_hh_mm': 'Please enter a valid time as HH:MM.',
 'day.please_finish_your_setup_with_start_first': 'Please finish your setup with /start first.',
 'day.please_use_the_buttons_for_this_question': 'Please use the buttons for this question.',
 'day.please_write_between_1_and_limit_characters': 'Please write between 1 and {limit} characters.',
 'day.pm': 'PM',
 'day.question.ache': '🤕 Did you have stomach pain today?',
 'day.question.bedtime': '🛏 When did you go to bed?\n'
                         'Range: noon yesterday to noon on the selected day.\n'
                         'Tap a time or type HH:MM: before noon means the selected day; noon or later means '
                         'yesterday.\n'
                         'For noon on the selected day, tap its Today button or type today 12:00.',
 'day.question.day_comment': '📝 Please write a short note about the day (up to 200 characters).',
 'day.question.day_comment_wanted': '📝 Would you like to add a note about the day?',
 'day.question.medicine_details': '💊 Which medication did you take, and at what dose?\n'
                                  'Please type the name and dosage.',
 'day.question.medicine_relief': '💊 Did it help?',
 'day.question.mood_control': '🙂 How stable was your mood throughout the day?\n'
                              '1 = extremely unstable, 10 = very stable.',
 'day.question.more_medicine': '➕ Did you take anything else?',
 'day.question.pain_comment': '📝 Please write a short note about the pain episode.',
 'day.question.pain_comment_wanted': '📝 Would you like to add a note about the pain episode?',
 'day.question.pain_description_requested': '🤕 Would you like to describe what the pain felt like?',
 'day.question.pain_intensity': '🌡 How intense was the pain compared with the worst pain you have ever felt?\n'
                                '1 = very mild, 10 = the worst pain.',
 'day.question.painkillers': '💊 Did you take any painkillers?',
 'day.question.sleep_satisfaction': '😴 How satisfied were you with your sleep?\n'
                                    '1 = very dissatisfied, 10 = very satisfied.',
 'day.question.wake_time': '🌅 What time did you wake up today?\n'
                           'Choose 00:00–24:00 today. 24:00 means the end of today.\n'
                           'Tap a full hour, or type HH:MM.',
 'day.recorded_medications_continued': 'Recorded medications (continued):',
 'day.sleep_time_cant_be_negative': 'Sleep duration cannot be negative.\n\n',
 'day.start_clean': 'Start clean',
 'day.the_diary_questions_have_changed_open_callendar': 'The diary questions have changed. Open /callendar.',
 'day.this_answer_is_invalid_or_the_question_has_expired': 'This answer is invalid or the question has expired. '
                                                           'Open /callendar.',
 'day.this_draft_choice_has_expired_open_callendar': 'This draft choice has expired. Open /callendar.',
 'day.this_draft_has_changed_open_callendar': 'This draft has changed. Open /callendar.',
 'day.this_edit_has_expired_open_callendar': 'This edit has expired. Open /callendar.',
 'day.time_not_recorded': 'Time not recorded',
 'day.use_hh_mm': 'Use HH:MM',
 'day.view_the_calendar': 'View the calendar',
 'day.wake_up_date_selected_date_d_m_y': '\nWake-up date: {selected_date:%d.%m.%Y}',
 'day.you_have_an_unfinished_entry_for_selected_date_d': '📝 You have an unfinished entry for '
                                                         '{selected_date:%d.%m.%Y}.\n'
                                                         'Continue it, or start clean and replace this draft. '
                                                         'Meals will stay.',
 'day.your_previous_answer_is_already_saved_let_s_continue': "Your previous answer is already saved. Let's "
                                                             'continue.',
 'day_export.answers': ' answers',
 'day_export.bedtime': 'Bedtime',
 'day_export.bedtime_date': 'Bedtime date',
 'day_export.completed': 'Completed',
 'day_export.date': 'Date',
 'day_export.diary_answers': 'Diary answers',
 'day_export.draft': 'Draft',
 'day_export.entry_status': 'Entry status',
 'day_export.header_continued_part': '{header} (continued {part})',
 'day_export.index_item_helped_relief_labels': '{index}. {item} — Helped: {relief_labels}',
 'day_export.legacy_food_1_7': 'Legacy food (1–7)',
 'day_export.legacy_mood_1_7': 'Legacy mood (1–7)',
 'day_export.legacy_sleep_1_7': 'Legacy sleep (1–7)',
 'day_export.legacy_yes_no': 'Legacy Yes/No',
 'day_export.meals_local_time_and_description': 'Meals (local time and description)',
 'day_export.medications_and_effect': 'Medications and effect',
 'day_export.status': ' status',
 'diary.editing_day': 'Editing day: {date:%d.%m.%Y}\n\n{question}',
 'export.answers': '{title} answers',
 'export.caption': 'All saved dates, newest first. Includes drafts.',
 'export.field.ache': 'Stomach pain',
 'export.field.day_comment': 'Day comment',
 'export.field.day_comment_wanted': 'Day comment requested',
 'export.field.mood_control': 'Mood stability (1–10)',
 'export.field.more_medicine': 'More medication taken',
 'export.field.pain_comment': 'Pain note',
 'export.field.pain_comment_wanted': 'Pain note requested',
 'export.field.pain_description_requested': 'Pain description requested',
 'export.field.pain_intensity': 'Pain intensity (1–10)',
 'export.field.painkillers': 'Painkillers taken',
 'export.field.sleep_satisfaction': 'Sleep satisfaction (1–10)',
 'export.field.wake_time': 'Wake-up time',
 'export.filename': 'foodbot_answers.xlsx',
 'export.pain.0': 'Pain location',
 'export.pain.1': 'Pain character',
 'export.pain.2': 'Accompanying symptoms',
 'export.pain.3': 'User-suspected triggers',
 'export.status': '{title} status',
 'language.choose': 'Choose your language.',
 'language.invalid': 'Please use the language buttons.',
 'language.saved': 'Language saved: {language}.',
 'meal.meal_saved_selected_date_d_m_y_at_data': '🍽 Meal saved!\n'
                                                '{selected_date:%d.%m.%Y} at {data} — {description}',
 'meal.please_finish_your_setup_with_start_first': 'Please finish your setup with /start first.',
 'meal.please_write_between_1_and_50_characters_or_tap': 'Please write between 1 and 50 characters, or tap Skip.',
 'meal.prompt': '🍽 Meal recorded at {time} on {day}.\n'
                'Add an optional description (up to 50 characters), or tap Skip.',
 'meal.the_description_was_too_long_please_shorten_it_to': '\n'
                                                           'The description was too long. Please shorten it to 50 '
                                                           'characters.',
 'meal.this_meal_is_already_recorded_open_callendar': 'This meal is already recorded. Open /callendar.',
 'pain.answer': '\nAnswer: ',
 'pain.answer_recorded': '\n\nAnswer recorded\n',
 'pain.bedtime_date_bedtime_date_d_m_y': 'Bedtime date: {bedtime_date:%d.%m.%Y}\n\n',
 'pain.confirmed': 'Confirmed',
 'pain.editing_day_selected_date_d_m_y': 'Editing day: {selected_date:%d.%m.%Y}\n\n',
 'pain.error.choose_first': 'Choose an answer, Not sure or Skip first.',
 'pain.error.invalid_selection': 'Invalid selection',
 'pain.error.invalid_text': 'Invalid text',
 'pain.error.other_text': 'Other needs text',
 'pain.error.question_changed': 'Question has changed',
 'pain.full_entry_selected_date_d_m_y': 'Full entry: {selected_date:%d.%m.%Y}\n\n',
 'pain.intro': 'Describe the worst pain episode on {date}.\n'
               'You can select several answers.\n'
               '\n'
               'If sudden severe pain is happening now, seek urgent medical help. Do not wait to finish this '
               'diary.',
 'pain.invalid_entry': 'Invalid entry.',
 'pain.medication_item_helped_item_value': 'Medication: {item}\nHelped: {item_value}\n\n',
 'pain.next': 'Next →',
 'pain.no_clear_trigger': 'No clear trigger',
 'pain.option.pain_character.burning': 'Burning',
 'pain.option.pain_character.cramping': 'Cramping',
 'pain.option.pain_character.dull': 'Dull/aching',
 'pain.option.pain_character.other': 'Other',
 'pain.option.pain_character.pressure': 'Pressure',
 'pain.option.pain_character.sharp': 'Sharp/stabbing',
 'pain.option.pain_character.throbbing': 'Throbbing',
 'pain.option.pain_location.all_over': 'All over the abdomen',
 'pain.option.pain_location.lower_left': 'Lower left',
 'pain.option.pain_location.lower_middle': 'Lower middle',
 'pain.option.pain_location.lower_right': 'Lower right',
 'pain.option.pain_location.middle_left': 'Middle left',
 'pain.option.pain_location.middle_right': 'Middle right',
 'pain.option.pain_location.navel': 'Around navel',
 'pain.option.pain_location.other': 'Other area',
 'pain.option.pain_location.upper_left': 'Upper left',
 'pain.option.pain_location.upper_middle': 'Upper middle',
 'pain.option.pain_location.upper_right': 'Upper right',
 'pain.option.pain_symptoms.black_stool': 'Black, sticky stool',
 'pain.option.pain_symptoms.bloating': 'Bloating',
 'pain.option.pain_symptoms.blood_vomit': 'Blood in vomit',
 'pain.option.pain_symptoms.bowel_bleeding': 'Heavy bleeding from the bowel',
 'pain.option.pain_symptoms.breathing': 'Trouble breathing',
 'pain.option.pain_symptoms.constipation': 'Constipation',
 'pain.option.pain_symptoms.diarrhoea': 'Diarrhoea',
 'pain.option.pain_symptoms.fainting': 'Fainting',
 'pain.option.pain_symptoms.feverish': 'Fever / felt feverish',
 'pain.option.pain_symptoms.heartburn': 'Heartburn',
 'pain.option.pain_symptoms.nausea': 'Nausea',
 'pain.option.pain_symptoms.other': 'Other',
 'pain.option.pain_symptoms.vomiting': 'Vomiting',
 'pain.option.pain_triggers.activity': 'Physical activity',
 'pain.option.pain_triggers.food': 'Particular food or drink',
 'pain.option.pain_triggers.large_meal': 'Larger meal than usual',
 'pain.option.pain_triggers.late_eating': 'Eating late',
 'pain.option.pain_triggers.meal_gap': 'Long gap between meals',
 'pain.option.pain_triggers.medicine': 'Medicine or supplement',
 'pain.option.pain_triggers.other': 'Other',
 'pain.option.pain_triggers.sleep': 'Poor or short sleep',
 'pain.option.pain_triggers.stress': 'Stress or anxiety',
 'pain.page_page_pages': 'Page {page}/{pages}\n\n',
 'pain.pause_and_return': 'Pause and return',
 'pain.please_type_a_short_description_1_limit_characters': 'Please type a short description (1–{limit} '
                                                            'characters).',
 'pain.please_use_the_buttons_or_select_other_to_enter': 'Please use the buttons, or select Other to enter text.',
 'pain.please_write_between_1_and_limit_characters_or_reopen': 'Please write between 1 and {limit} characters, or '
                                                               'reopen /callendar if the question has changed.\n'
                                                               '\n',
 'pain.previous': '← Previous',
 'pain.question.pain_character': 'What did the pain feel like? Select all that apply.',
 'pain.question.pain_location': 'Where did you feel the pain?\nLeft and right mean your own left and right.',
 'pain.question.pain_symptoms': 'What other symptoms did you notice during this episode?\nSelect all that apply.',
 'pain.question.pain_triggers': 'What do you think may have contributed to the pain?\n'
                                'These are your suspicions, not confirmed causes.',
 'pain.selections_saved_so_far': '\n\nSelections saved so far\n',
 'pain.selections_saved_so_far_2': 'Selections saved so far',
 'pain.skipped': 'Skipped',
 'pain.status_status': '\nStatus: {status}\n',
 'pain.this_question_has_changed_open_callendar': 'This question has changed. Open /callendar.',
 'pain.this_question_has_expired_open_callendar': 'This question has expired. Open /callendar.',
 'pain.urgent_text': 'If this is happening now, seek urgent medical help.\nDo not wait to finish this diary.',
 'pain.you_can_mention_a_specific_food_drink_or_other': '\n'
                                                        'You can mention a specific food, drink or other factor.',
 'profile.am': 'AM',
 'profile.english': 'English',
 'profile.every_evening': 'Every evening',
 'profile.every_morning': 'Every morning',
 'profile.excellent_i_ll_remind_you_of_my_presence_after': '👍 Reminders start after {hour}:00 {suffix}.',
 'profile.first_choice': '🌐 What language do you prefer? / Какой язык вы предпочитаете?',
 'profile.gender.female': 'Female',
 'profile.gender.male': 'Male',
 'profile.gender.secret': 'Secret',
 'profile.hour': '{hour}:00 {period}',
 'profile.invalid_profile_answer': 'Invalid profile answer',
 'profile.let_s_update_your_settings_your_current_settings_stay': '⚙️ Update your profile. Current settings stay '
                                                                  'active until you finish.\n'
                                                                  'Use /start to leave.',
 'profile.moscow': ' (Moscow)',
 'profile.moscow_3_00_utc': 'Moscow (+3:00 UTC)',
 'profile.offset_d_00_utc': '{offset:+d}:00 UTC',
 'profile.please_answer_the_current_question_using_its_buttons': 'Please answer the current question using its '
                                                                 'buttons.',
 'profile.please_choose_a_time_zone_using_the_buttons': 'Please choose a time zone using the buttons.',
 'profile.please_choose_a_time_zone_using_the_buttons_or': 'Please choose a time zone using the buttons, or use '
                                                           '/callendar to leave.',
 'profile.please_enter_a_year_from_1900_to_date': 'Please enter a year from 1900 to {date}.',
 'profile.please_finish_your_setup_with_start_first': 'Please finish your setup with /start first.',
 'profile.please_open_a_private_chat_with_me_and_send': 'Please open a private chat with me and send /start.',
 'profile.please_send_start_first': 'Please send /start first.',
 'profile.please_send_start_in_a_private_chat': 'Please send /start in a private chat.',
 'profile.please_use_the_buttons_for_the_current_question': 'Please use the buttons for the current question.',
 'profile.please_write_a_nickname_between_1_and_64_characters': 'Please write a nickname between 1 and 64 '
                                                                'characters.',
 'profile.pm': 'PM',
 'profile.question.birth_year': '🎂 What is your year of birth?',
 'profile.question.gender': '👤 What gender are you?',
 'profile.question.language': '🌐 What language do you prefer?',
 'profile.question.nickname': '👋 What should I call you?\nEnter a nickname (1–64 characters).',
 'profile.question.reminder_hour': 'You can write at any time.\n'
                                   '\n'
                                   'After 24 hours without a completed entry, I can send one reminder per local '
                                   'day.\n'
                                   'Choose the earliest reminder hour.',
 'profile.question.reminder_period': 'When should I remind you?\n'
                                     '\n'
                                     'Morning — write about yesterday.\n'
                                     'Evening — review today before bed.',
 'profile.question.utc_offset': '🌍 What time zone are you in?',
 'profile.russian': 'Russian',
 'profile.time': '{hour:02d}:00',
 'profile.time_zone_saved_offset_d_00_utc_your_reminder': '🌍 Time zone: {offset:+d}:00 UTC.\n'
                                                          '🔔 Your reminder hour is unchanged and now uses this '
                                                          'time zone.',
 'profile.value_d_00_utc': '{value:+d}:00 UTC',
 'profile.welcome': "Hi, I'm Foodie!\n"
                    'I help you keep a diary of sleep, meals, mood and well-being.\n'
                    '\n'
                    'Choose your language so I can tell you more.\n'
                    "If we've already communicated, your saved data stays.",
 'profile.wrote_the_answer': 'Wrote the answer\n',
 'profile.your_setup_is_already_complete_open_settings_to_change': 'Your setup is already complete. Open '
                                                                   '/settings to change it.',
 'reminders.could_not_check_reminders': 'Could not check reminders',
 'reminders.hi_it_s_me': "— Hi, it's Me!",
 'reminders.reminder_failed_for_user_s_s': 'Reminder failed for user %s (%s)',
 'routes.b_day_comment_b': '\n\n<b>📝 Day comment:</b>\n',
 'routes.b_meals_b': '\n\n<b>Meals:</b>',
 'routes.future_dates_are_not_available': 'Future dates are not available.',
 'routes.invalid_date_open_callendar': 'Invalid date. Open /callendar.',
 'routes.invalid_meal_page_open_callendar': 'Invalid meal page. Open /callendar.',
 'routes.meal_index_meal_escape': '\nMeal {index} - {meal} - {escape}',
 'routes.meals_page_meal_page_meals': '\nMeals page {meal_page}/{meals}',
 'routes.no_meals_recorded': '\nNo meals recorded.',
 'routes.open_the_calendar_with_callendar': 'Open the calendar with /callendar.',
 'routes.please_finish_your_setup_with_start_first': 'Please finish your setup with /start first.',
 'routes.select_a_day_to_view_its_entry': 'Select a day to view its entry.',
 'routes.this_button_is_no_longer_used_open_callendar': 'This button is no longer used. Open /callendar.',
 'routes.today': ' (Today)',
 'statistics.all_time': 'All time',
 'statistics.b_all_time_statistics_b': '<b>📊 All-time statistics</b>\n\n',
 'statistics.b_previous_month_month_title_b': '\n\n<b>🗓 Previous month: {month_title}</b>\n\n',
 'statistics.b_statistics_month_title_b': '<b>📊 Statistics: {month_title}</b>\n\n',
 'statistics.days_with_stomach_pain_pain_days_average_pain_intensity': 'Days with stomach pain: {pain_days}\n'
                                                                       'Average pain intensity: {intensity}\n'
                                                                       '\n',
 'statistics.duration_h_duration_value_02d_min': '{duration} h {duration_value:02d} min',
 'statistics.future_dates_are_not_available': 'Future dates are not available.',
 'statistics.get_excel_file': 'Get Excel file',
 'statistics.in_progress': 'In progress',
 'statistics.invalid_date_open_callendar': 'Invalid date. Open /callendar.',
 'statistics.invalid_period': 'Invalid period.',
 'statistics.invalid_statistics_page_use_statistics': 'Invalid statistics page. Use /statistics.',
 'statistics.meal_statistics': 'Meal statistics',
 'statistics.months': '← Months',
 'statistics.months_2': 'Months →',
 'statistics.multiple_selections_are_allowed_percentages_may_total_more_than': '\n'
                                                                               '\n'
                                                                               'Multiple selections are allowed; '
                                                                               'percentages may total more than '
                                                                               '100%.\n'
                                                                               'None is included in N, not '
                                                                               'counted as a symptom or trigger.',
 'statistics.n_valid_dates_confirmed_dates': '\nN = {valid_dates} confirmed dates\n',
 'statistics.no_answer_pain_days': 'No answer: {pain_days}\n',
 'statistics.no_data_yet': '\nNo data yet',
 'statistics.no_data_yet_0_below_7': 'No data yet (0 below 7)',
 'statistics.no_data_yet_n_0': 'No data yet (N = 0)',
 'statistics.no_saved_notes_yet_make_a_note_with_makenote': 'No saved notes yet. Make a note with /makenote or '
                                                            '/meal first.',
 'statistics.other_original_user_text': '\nOther — original user text:\n',
 'statistics.pain_statistics': 'Pain statistics',
 'statistics.pain_statistics_title_page_page_pages': 'Pain statistics: {title}\nPage {page}/{pages}\n\n',
 'statistics.preparing_your_excel_file': 'Preparing your Excel file…',
 'statistics.skipped': 'Skipped',
 'statistics.summary': '<b>Days with notes: {days}</b>\n'
                       '\n'
                       'Average sleep duration: {sleep}\n'
                       'Average sleep satisfaction: {satisfaction}\n'
                       'Average mood stability: {mood}\n'
                       'Days with stomach pain: {pain_days}\n'
                       '\n'
                       '<b>✅ Excellent days: {green_days}</b>\n'
                       '<b>🍽 Meal notes: {meals}</b>',
 'statistics.user_suspected_triggers': 'User-suspected triggers',
 'statistics.values_2f_10_below_below_7': '{values:.2f}/10 ({below} below 7)'}
