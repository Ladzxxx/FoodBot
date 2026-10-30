from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    KeyboardButton, 
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)
from Forms.user import Form
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("start"))
async def started(message: Message, state: FSMContext):
    await message.answer(f"Hello {message.from_user.full_name}! Let's start to fill in your form!\n\nPlease enter your name")
    await state.set_state(Form.name)

@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Form filling canceled.")

@router.message(Form.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(f"Now fill in your age")
    await state.set_state(Form.age)

@router.message(Form.age, F.text)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Invalid age")
        return

    if int(message.text) < 1 or int(message.text) > 120:
        await message.answer("Invalid age")
        return

    await state.update_data(age=int(message.text))

    await message.answer(f"Now fill in your Email")
    await state.set_state(Form.mail)

@router.message(Form.mail, F.text)
async def process_mail(message: Message, state: FSMContext):
    email_text = message.text
    if "@" not in email_text or "." not in email_text:
        await message.answer("Invalid email")
        return
    await state.update_data(mail=email_text)

    data = await state.get_data()
    name = data.get("name")
    age = data.get("age")
    mail = data.get("mail")

    await message.answer(f"Your data:\n\nName: {name}\nAge: {age}\nEmail: {mail}")
    await state.clear()

@router.message(F.photo)
async def process_photo(message: Message):
    photo = message.photo[-1]
    id_photo = photo.file_id

    await message.answer(
        f"Your photo id: <code>{id_photo}</code>", 
        parse_mode="HTML"
        )
    await message.answer_photo(
        photo=id_photo,
        caption="Your photo"
        )

@router.message(F.video)
async def process_video(message: Message):
    video = message.video
    id_video = video.file_id
    duration = video.duration

    await message.answer(
        f"Your video id: <code>{id_video}</code>", 
        parse_mode="HTML"
        )
    await message.answer_video(
        video=id_video,
        caption=f"Your video (Duration: {duration} seconds)"
        )


@router.message(F.document)
async def process_document(message: Message, bot: Bot):
    document = message.document
    id_document = document.file_id
    file = await bot.get_file(file_id=id_document)
    file_path = file.file_path

    local_file_path = f"downloads/{document.file_name}"

    await bot.download_file(file_path=file_path, destination=local_file_path)

    await message.answer("Document downloaded successfully!")

@router.message(Command("file"))
async def send_file(message: Message, bot: Bot):
    file = FSInputFile("files/sample.txt")
    await message.answer_document(document=file, caption="Here is your file!")