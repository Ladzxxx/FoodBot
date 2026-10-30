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
import aiohttp

router = Router()

# ---

async def get_our_product (product_id):
    url = f"https://fakestoreapi.com/products/{product_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


# ---

@router.message(Command("start"))
async def started(message: Message, state: FSMContext):
    await message.answer(f"Hello {message.from_user.full_name}! I am a market-bot!\n\nPlease enter the product ID command like this: <b>/product 1</b>",
        parse_mode="HTML")

@router.message(Command("product"), F.text)
async def get_product_info(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Invalid command format. Please use: /product <product_id>")
        return
    product_id = int(parts[1])
    await message.answer(f"Fetching product information with ID {product_id}...")

    try:
        product = await get_our_product(product_id)
    except Exception as e:
        await message.answer(f"Error fetching product information: {str(e)}")
        return

    if product is None:
        await message.answer(f"Product with ID {product_id} not found.")
        return

    title = product.get("title", "N/A")
    price = product.get("price", "N/A")
    description = product.get("description", "N/A")
    category = product.get("category", "N/A")
    image_url = product.get("image", None)

    text = (
        f"<b>Product Information:</b>\n" \
        f"<b>Title:</b> {title}\n" \
        f"<b>Price:</b> ${price}\n" \
        f"<b>Description:</b> {description}\n" \
        f"<b>Category:</b> {category}\n" \
        f"<b>Image URL:</b> {image_url}\n"
    )

    photo = FSInputFile("image.png")
    await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")

    # if image_url:
    #     await message.answer_photo(photo=image_url, caption=text, parse_mode="HTML")
    # else:
    #     await message.answer(text, parse_mode="HTML")

