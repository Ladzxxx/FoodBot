from database import get_user_profile
from localization import t, language_of
from datetime import date, timedelta
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Forms.day import DayEdit
from Forms.pain import PAIN_QUESTIONS, URGENT_CODES, selected_labels
from Keyboards.pain import pain_keyboard
from pain_storage import get_pain_answers, save_pain_choice
from day_storage import get_day_entry
from day_storage import get_medications
from day_answers import previous_pain_answer, with_previous

router = Router()


async def safe_delete(bot, chat_id, message_id):
    if message_id is None:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramAPIError:
        pass


async def pain_screen(user_id, selected_date, key, lang="en", previous=None):
    _, options = await get_pain_answers(user_id, selected_date, selected_date)
    options = [item for item in options if item['question_key'] == key]
    # CAN CHANGE TEXT
    text = t(lang, 'pain.editing_day_selected_date_d_m_y', selected_date=selected_date)
    if key == 'pain_location':
        text += t(lang, 'pain.intro', date=selected_date.strftime('%d.%m.%Y')) + '\n\n'
    text += t(lang, "pain.question." + key)
    text = with_previous(text, previous, lang)
    text += t(lang, 'pain.selections_saved_so_far') + ('\n'.join(selected_labels(key, options, lang=lang)) or '___')
    if key == 'pain_symptoms' and any(item['is_selected'] and item['option_code'] in URGENT_CODES for item in options):
        text += '\n\n⚠️ ' + t(lang, 'pain.urgent_text')
    return text, options


async def send_pain_question(message, state, draft, selected_date, step, lang="en"):
    user_id = draft.get('user_id') or message.chat.id
    previous = previous_pain_answer(draft, selected_date, step, lang)
    text, options = await pain_screen(user_id, selected_date, step, lang=lang, previous=previous)
    question = await message.answer(text, reply_markup=pain_keyboard(draft['edit_id'], step, options, lang=lang))
    await state.update_data(step=step, message_id=question.message_id, user_id=user_id, other_pending=False, previous_pain_answer=previous)


async def refresh_question(message, state, draft, lang="en"):
    text, options = await pain_screen(draft['user_id'], date.fromisoformat(draft['date']), draft['step'], lang=lang, previous=draft.get("previous_pain_answer"))
    try:
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=draft['message_id'], text=text,
            reply_markup=pain_keyboard(draft['edit_id'], draft['step'], options, lang=lang))
    except TelegramBadRequest as error:
        if 'message is not modified' not in error.message:
            raise


@router.callback_query(F.data.startswith('pain:'))
async def pain_button(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    draft = await state.get_data()
    parts = callback.data.split(':')
    if (len(parts) != 3 or await state.get_state() != DayEdit.answer.state
        or parts[1] != draft.get('edit_id') or draft.get('step') not in PAIN_QUESTIONS
        or not isinstance(callback.message, Message) or callback.message.chat.type != 'private'
        or callback.message.chat.id != callback.from_user.id
        or callback.message.message_id != draft.get('message_id')
        or callback.from_user.id != draft.get('user_id')):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'pain.this_question_has_expired_open_callendar'), show_alert=True)
        return
    selected_date = date.fromisoformat(draft['date'])
    entry = await get_day_entry(callback.from_user.id, selected_date)
    if not entry or entry['completed'] or entry['next_step'] != draft['step']:
        await callback.answer(t(lang, 'pain.this_question_has_changed_open_callendar'), show_alert=True)
        return
    action = parts[2]
    if action == 'pause':
        from Handlers.routes import show_month
        await state.clear()
        await show_month(callback, selected_date, lang=lang, profile=language_profile or {})
        return
    if action == 'other':
        _, options = await pain_screen(callback.from_user.id, selected_date, draft['step'], lang=lang, previous=draft.get("previous_pain_answer"))
        if not any(item['option_code'] == 'other' and item['is_selected'] for item in options):
            limit = 300 if draft['step'] == 'pain_triggers' else 200
            # CAN CHANGE TEXT
            prompt = t(lang, 'pain.please_type_a_short_description_1_limit_characters', limit=limit)
            if limit == 300:
                prompt += t(lang, 'pain.you_can_mention_a_specific_food_drink_or_other')
            current_text, _ = await pain_screen(callback.from_user.id, selected_date, draft['step'], lang=lang, previous=draft.get("previous_pain_answer"))
            try:
                await callback.message.edit_text(prompt + '\n\n' + current_text,
                    reply_markup=pain_keyboard(draft['edit_id'], draft['step'], options, lang=lang))
            except TelegramBadRequest as error:
                if 'message is not modified' not in error.message:
                    raise
            await state.update_data(other_pending=True)
            await callback.answer()
            return
    try:
        next_step = await save_pain_choice(callback.from_user.id, selected_date, draft['step'], action, morning_id=draft.get('morning_id'))
    except ValueError as error:
        await callback.answer(t(lang, str(error)), show_alert=True)
        return
    await state.update_data(other_pending=False)
    await callback.answer()
    if action != 'done':
        await refresh_question(callback.message, state, draft, lang=lang)
        return
    _, options = await pain_screen(callback.from_user.id, selected_date, draft['step'], lang=lang, previous=draft.get("previous_pain_answer"))
    # CAN CHANGE TEXT: подтверждение содержит все выбранные подписи, включая Other.
    text = with_previous(t(lang, 'pain.question.' + draft['step']),
        draft.get("previous_pain_answer"), lang, receipt=True)
    text += t(lang, 'pain.answer_recorded') + '\n'.join(selected_labels(draft['step'], options, lang=lang))
    if draft['step'] == 'pain_symptoms' and any(item['is_selected'] and item['option_code'] in URGENT_CODES for item in options):
        text += '\n\n⚠️ ' + t(lang, 'pain.urgent_text')
    await callback.message.edit_text(text, reply_markup=None)
    for user_message in draft.get('pain_user_messages', []):
        # Не удаляем текст, который пользователь снял с выбора или заменил другим.
        if any(item['is_selected'] and item['custom_text'] == user_message['text'] for item in options):
            await safe_delete(callback.bot, callback.message.chat.id, user_message['message_id'])
    await state.update_data(pain_user_messages=[])
    # Предыдущее подтверждение удаляем только после успешного показа нового.
    await safe_delete(callback.bot, callback.message.chat.id, draft.get('pain_confirmation_id'))
    await state.update_data(pain_confirmation_id=callback.message.message_id)
    draft = await state.get_data()
    # Локальный импорт позволяет вернуться к обычному вопросу без отдельного слоя диалога.
    from Handlers.day import send_question
    if draft.get("morning"):
        from morning_storage import get_morning_session
        session = await get_morning_session(callback.from_user.id)
        from Handlers.morning import continue_morning
        await continue_morning(callback.message, state, session, lang)
    else:
        await send_question(callback.message, state, draft, selected_date, next_step, lang=lang)


@router.message(DayEdit.answer, F.text & ~F.text.startswith('/'))
async def pain_text(message: Message, state: FSMContext):
    draft = await state.get_data()
    # Этот роутер подключён перед дневником, поэтому чужие шаги пропускаем.
    from aiogram.dispatcher.event.bases import SkipHandler
    if draft.get('step') not in PAIN_QUESTIONS:
        raise SkipHandler
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    if message.chat.type != 'private' or message.from_user.id != draft.get('user_id'):
        return
    if not draft.get('other_pending'):
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'pain.please_use_the_buttons_or_select_other_to_enter'))
        return
    try:
        await save_pain_choice(message.from_user.id, date.fromisoformat(draft['date']), draft['step'], 'other', message.text.strip(), morning_id=draft.get('morning_id'))
    except ValueError:
        # CAN CHANGE TEXT
        limit = 300 if draft['step'] == 'pain_triggers' else 200
        text, options = await pain_screen(message.from_user.id, date.fromisoformat(draft['date']), draft['step'], lang=lang, previous=draft.get("previous_pain_answer"))
        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=draft['message_id'],
            text=t(lang, 'pain.please_write_between_1_and_limit_characters_or_reopen', limit=limit) + text,
            reply_markup=pain_keyboard(draft['edit_id'], draft['step'], options, lang=lang))
        return
    await refresh_question(message, state, draft, lang=lang)
    await state.update_data(other_pending=False)
    # Текст удалится после Done и успешного показа полного подтверждения.
    pending = draft.get('pain_user_messages', [])
    await state.update_data(pain_user_messages=pending + [{'message_id': message.message_id, 'text': message.text.strip()}])


def text_pages(text, limit=3400):
    # Разбиваем по символам: даже длинные старые заметки полностью доступны.
    return [text[index:index + limit] for index in range(0, len(text), limit)] or ['___']


def page_keyboard(prefix, page, count, back, lang="en"):
    rows = []
    navigation = []
    # CAN CHANGE TEXT
    if page > 0:
        navigation.append(InlineKeyboardButton(text=t(lang, 'pain.previous'), callback_data=f'{prefix}:{page - 1}'))
    if page + 1 < count:
        navigation.append(InlineKeyboardButton(text=t(lang, 'pain.next'), callback_data=f'{prefix}:{page + 1}'))
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith('painview:'))
async def full_entry(callback: CallbackQuery):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    if not isinstance(callback.message, Message) or callback.message.chat.type != 'private':
        await callback.answer()
        return
    try:
        _, day, raw_page = callback.data.split(':')
        selected_date = date.fromisoformat(day)
        page = int(raw_page)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'pain.invalid_entry'), show_alert=True)
        return
    from Forms.day import QUESTIONS
    entry = await get_day_entry(callback.from_user.id, selected_date) or {}
    # CAN CHANGE TEXT: полный просмотр ничего не сохраняет и не закрывает опрос.
    text = t(lang, 'pain.full_entry_selected_date_d_m_y', selected_date=selected_date)
    for key in QUESTIONS:
        if key in entry and entry[key] is not None:
            value = entry[key]
            if key in ('ache', 'painkillers', 'more_medicine', 'day_comment_wanted', 'pain_description_requested', 'pain_comment_wanted'):
                value = t(lang, 'common.yes') if value else t(lang, 'common.no')
            text += t(lang, "day.question." + key) + t(lang, 'pain.answer') + str(value) + '\n\n'
    if entry.get('bedtime'):
        bedtime_date = selected_date - timedelta(days=1) if entry.get('bedtime_day', -1) == -1 and selected_date > date.min else selected_date
        text += t(lang, 'pain.bedtime_date_bedtime_date_d_m_y', bedtime_date=bedtime_date)
    medications = await get_medications(callback.from_user.id, selected_date)
    for item in medications:
        text += t(lang, 'pain.medication_item_helped_item_value', item=item['description'], item_value={'yes':t(lang, 'common.yes'), 'no':t(lang, 'common.no'), 'a_little':t(lang, 'common.a_little')}.get(item['relief'], '___'))
    answers, options = await get_pain_answers(callback.from_user.id, selected_date, selected_date)
    for key in PAIN_QUESTIONS:
        # CAN CHANGE TEXT: статусы показываем понятными словами.
        statuses = {'in_progress': t(lang, 'pain.selections_saved_so_far_2'), 'answered': t(lang, 'pain.confirmed'), 'none': t(lang, 'pain.confirmed'), 'unknown': t(lang, 'common.not_sure'), 'skipped': t(lang, 'pain.skipped')}
        status = next((statuses[item['status']] for item in answers if item['question_key'] == key), '___')
        labels = selected_labels(key, [item for item in options if item['question_key'] == key], lang=lang)
        text += t(lang, "pain.question." + key) + t(lang, 'pain.status_status', status=status) + ('\n'.join(labels) or '___') + '\n\n'
    pages = text_pages(text)
    page = max(0, min(page, len(pages) - 1))
    await callback.message.edit_text(t(lang, 'pain.page_page_pages', page=page + 1, pages=len(pages)) + pages[page],
        reply_markup=page_keyboard(f'painview:{day}', page, len(pages), f'calendar:day:{day}', lang=lang))
    await callback.answer()
