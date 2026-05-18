from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import (
    TOKEN,
    ADMIN_IDS,
    CHANNEL,
    CARD_NUMBER,
    PAYMENT,
    SCRIPT_URL
)

import asyncio
import requests
import re

bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())

registration_counter = 1

users_data = {}


# ===== LOAD LAST ID =====

def load_last_id():

    global registration_counter

    try:

        response = requests.get(
            SCRIPT_URL,
            timeout=10
        )

        ids = response.json()

        if len(ids) > 0:

            last_id = ids[-1]

            number = int(
                last_id.split("-")[1]
            )

            registration_counter = number + 1

    except Exception as error:
        print(error)


# ===== LOAD USERS =====

def load_users():

    global users_data

    try:

        response = requests.get(
            SCRIPT_URL + "?users=1",
            timeout=10
        )

        users_data = response.json()

    except Exception as error:
        print(error)


# ===== USER MENU =====

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📝 Ro‘yxatdan o‘tish"
            )
        ],
        [
            KeyboardButton(
                text="💳 Chek yuborish"
            )
        ],
        [
            KeyboardButton(
                text="📄 Mening IDlarim"
            )
        ]
    ],
    resize_keyboard=True
)


# ===== ADMIN MENU =====

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📋 Ro‘yxatdan o‘tganlar"
            )
        ],
        [
            KeyboardButton(
                text="✅ To‘lov tasdiqlanganlar"
            )
        ]
    ],
    resize_keyboard=True
)


# ===== STATES =====

class RegisterState(StatesGroup):

    fish = State()

    sinf = State()

    tel1 = State()

    tel2 = State()

    maktab = State()


class CheckState(StatesGroup):

    waiting_check = State()


# ===== START =====

@dp.message(CommandStart())
async def start(message: types.Message):

    # ADMIN
    if message.from_user.id in ADMIN_IDS:

        await message.answer(
            "👋 Assalomu alaykum admin!",
            reply_markup=admin_menu
        )

        return

    text = """
Assalomu alaykum!

Mahorat Matematika Olimpiadasiga xush kelibsiz.
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    url="https://www.instagram.com/mahorat_maktabi"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Telegram kanal",
                    url="https://t.me/mahorat_maktabi_namangan"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_sub"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard
    )


# ===== CHECK SUB =====

@dp.callback_query(
    lambda c: c.data == "check_sub"
)
async def check_sub(
    callback: types.CallbackQuery
):

    try:

        member = await bot.get_chat_member(
            CHANNEL,
            callback.from_user.id
        )

        if member.status in [
            "left",
            "kicked"
        ]:

            await callback.answer(
                "❌ Siz kanalga a'zo emassiz!",
                show_alert=True
            )

            return

    except Exception as error:

        print(error)

        await callback.answer(
            "❌ Kanal tekshirishda xatolik!",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "✅ Obuna tasdiqlandi!"
    )

    await callback.message.answer(
        "Kerakli bo‘limni tanlang:",
        reply_markup=menu
    )


# ===== ADMIN USERS =====

@dp.message(
    lambda message:
    message.text == "📋 Ro‘yxatdan o‘tganlar"
)
async def all_users(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    if len(users_data) == 0:

        await message.answer(
            "❌ Registratsiyalar yo‘q."
        )

        return

    result = ""

    for reg_id, data in users_data.items():

        result += f"""
🆔 {reg_id}

👤 {data['fish']}
📚 {data['sinf']}
🏫 {data['maktab']}

📞 {data['tel1']}
📞 {data['tel2']}

📌 {data['status']}

====================
"""

    await message.answer(result)


# ===== CONFIRMED USERS =====

@dp.message(
    lambda message:
    message.text == "✅ To‘lov tasdiqlanganlar"
)
async def confirmed_users(message: types.Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    result = ""

    for reg_id, data in users_data.items():

        if data["status"] == "TOLOV TASDIQLANDI":

            result += f"""
🆔 {reg_id}

👤 {data['fish']}
📚 {data['sinf']}
🏫 {data['maktab']}

📞 {data['tel1']}

====================
"""

    if result == "":

        result = "❌ Tasdiqlanganlar yo‘q."

    await message.answer(result)


# ===== REGISTER START =====

@dp.message(
    lambda message:
    message.text == "📝 Ro‘yxatdan o‘tish"
)
async def register_start(
    message: types.Message,
    state: FSMContext
):

    await message.answer(
        "👤 F.I.SH kiriting:"
    )

    await state.set_state(
        RegisterState.fish
    )


# ===== MY IDS =====

@dp.message(
    lambda message:
    message.text == "📄 Mening IDlarim"
)
async def my_ids(message: types.Message):

    telegram_id = message.from_user.id

    result = ""

    for reg_id, data in users_data.items():

        if int(data["telegram_user"]) == telegram_id:

            result += f"""
🆔 {reg_id}

👤 {data['fish']}

📌 {data['status']}

"""

    if result == "":

        result = "❌ Registratsiyalar topilmadi."

    await message.answer(result)


# ===== SEND CHECK MENU =====

@dp.message(
    lambda message:
    message.text == "💳 Chek yuborish"
)
async def send_check_menu(
    message: types.Message
):

    telegram_id = message.from_user.id

    keyboard_buttons = []

    for reg_id, data in users_data.items():

        if int(data["telegram_user"]) == telegram_id:

            if data["status"] != "TOLOV TASDIQLANDI":

                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=reg_id,
                            callback_data=f"sendcheck_{reg_id}"
                        )
                    ]
                )

    if len(keyboard_buttons) == 0:

        await message.answer(
            "❌ Aktiv registratsiyalar yo‘q."
        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_buttons
    )

    await message.answer(
        "ID tanlang:",
        reply_markup=keyboard
    )


# ===== SEND CHECK SELECT =====

@dp.callback_query(
    lambda c:
    c.data.startswith("sendcheck_")
)
async def sendcheck_select(
    callback: types.CallbackQuery,
    state: FSMContext
):

    registration_id = callback.data.split("_")[1]

    await state.update_data(
        registration_id=registration_id
    )

    await callback.message.answer(
        f"""
🆔 {registration_id}

💳 To‘lov:
{PAYMENT}

💳 Karta:
{CARD_NUMBER}

Chekni yuboring.
"""
    )

    await state.set_state(
        CheckState.waiting_check
    )


# ===== FISH =====

@dp.message(RegisterState.fish)
async def get_fish(
    message: types.Message,
    state: FSMContext
):

    if len(message.text) < 5:

        await message.answer(
            "❌ F.I.SH noto‘g‘ri."
        )

        return

    await state.update_data(
        fish=message.text
    )

    await message.answer(
        "📚 Sinfingiz:"
    )

    await state.set_state(
        RegisterState.sinf
    )


# ===== SINF =====

@dp.message(RegisterState.sinf)
async def get_sinf(
    message: types.Message,
    state: FSMContext
):

    if message.text not in [
        "1", "2", "3", "4", "5",
        "6", "7", "8", "9",
        "10", "11"
    ]:

        await message.answer(
            "❌ Sinfni to‘g‘ri kiriting."
        )

        return

    await state.update_data(
        sinf=message.text
    )

    await message.answer(
        "📞 1-telefon:\n\n+998901234567"
    )

    await state.set_state(
        RegisterState.tel1
    )


# ===== TEL1 =====

@dp.message(RegisterState.tel1)
async def get_tel1(
    message: types.Message,
    state: FSMContext
):

    pattern = r'^\+998\d{9}$'

    if not re.match(
        pattern,
        message.text
    ):

        await message.answer(
            "❌ Telefon noto‘g‘ri."
        )

        return

    await state.update_data(
        tel1=message.text
    )

    await message.answer(
        "📞 2-telefon:\n\n+998901234567"
    )

    await state.set_state(
        RegisterState.tel2
    )


# ===== TEL2 =====

@dp.message(RegisterState.tel2)
async def get_tel2(
    message: types.Message,
    state: FSMContext
):

    pattern = r'^\+998\d{9}$'

    if not re.match(
        pattern,
        message.text
    ):

        await message.answer(
            "❌ Telefon noto‘g‘ri."
        )

        return

    await state.update_data(
        tel2=message.text
    )

    await message.answer(
        "🏫 Maktab nomi:"
    )

    await state.set_state(
        RegisterState.maktab
    )


# ===== SCHOOL =====

@dp.message(RegisterState.maktab)
async def get_maktab(
    message: types.Message,
    state: FSMContext
):

    global registration_counter

    if len(message.text) < 3:

        await message.answer(
            "❌ Maktab nomi noto‘g‘ri."
        )

        return

    await state.update_data(
        maktab=message.text
    )

    data = await state.get_data()

    registration_id = (
        f"MM-{registration_counter:03d}"
    )

    registration_counter += 1

    users_data[registration_id] = {

        "telegram_user": message.from_user.id,

        "fish": data["fish"],

        "sinf": data["sinf"],

        "tel1": data["tel1"],

        "tel2": data["tel2"],

        "maktab": data["maktab"],

        "status": "KUTILMOQDA"
    }

    try:

        requests.post(
            SCRIPT_URL,
            json={
                "id": registration_id,
                "telegram_user": message.from_user.id,
                "fish": data["fish"],
                "sinf": data["sinf"],
                "tel1": data["tel1"],
                "tel2": data["tel2"],
                "maktab": data["maktab"]
            },
            timeout=10
        )

    except Exception as error:
        print(error)

    await message.answer(
        f"""
✅ Registratsiya qilindi

🆔 {registration_id}

💳 To‘lov:
{PAYMENT}

💳 Karta:
{CARD_NUMBER}

Chek yuborish tugmasidan foydalaning.
""",
        reply_markup=menu
    )

    await state.clear()


# ===== RECEIVE CHECK =====

@dp.message(CheckState.waiting_check)
async def receive_check(
    message: types.Message,
    state: FSMContext
):

    data = await state.get_data()

    registration_id = data["registration_id"]

    user = users_data[registration_id]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"accept_{registration_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"reject_{registration_id}"
                )
            ]
        ]
    )

    text = f"""
🆕 YANGI CHEK

🆔 {registration_id}

👤 {user['fish']}
🏫 {user['maktab']}
📚 {user['sinf']}

📞 {user['tel1']}
📞 {user['tel2']}
"""

    for admin_id in ADMIN_IDS:

        if message.photo:

            await bot.send_photo(
                admin_id,
                photo=message.photo[-1].file_id,
                caption=text,
                reply_markup=keyboard
            )

        elif message.document:

            await bot.send_document(
                admin_id,
                document=message.document.file_id,
                caption=text,
                reply_markup=keyboard
            )

    await message.answer(
        "✅ Adminga yuborildi."
    )

    await state.clear()


# ===== ACCEPT =====

@dp.callback_query(
    lambda c:
    c.data.startswith("accept_")
)
async def accept_payment(
    callback: types.CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        await callback.answer(
            "❌ Siz admin emassiz!",
            show_alert=True
        )

        return

    registration_id = callback.data.split("_")[1]

    user = users_data[registration_id]

    user["status"] = "TOLOV TASDIQLANDI"

    try:

        requests.post(
            SCRIPT_URL,
            json={
                "action": "update_status",
                "id": registration_id
            },
            timeout=10
        )

    except Exception as error:
        print(error)

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await bot.send_message(
        user["telegram_user"],
        f"""
✅ To‘lov tasdiqlandi

🆔 {registration_id}

🕘 Olimpiada:
Yakshanba 09:00
"""
    )

    await callback.answer(
        "Tasdiqlandi!"
    )


# ===== REJECT =====

@dp.callback_query(
    lambda c:
    c.data.startswith("reject_")
)
async def reject_payment(
    callback: types.CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        await callback.answer(
            "❌ Siz admin emassiz!",
            show_alert=True
        )

        return

    registration_id = callback.data.split("_")[1]

    user = users_data[registration_id]

    user["status"] = "QAYTA CHEK"

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await bot.send_message(
        user["telegram_user"],
        f"""
❌ To‘lov tasdiqlanmadi

🆔 {registration_id}

Iltimos chekni qayta yuboring.
"""
    )

    await callback.answer(
        "Bekor qilindi!"
    )


# ===== MAIN =====

async def main():

    load_last_id()

    load_users()

    print("✅ Bot ishga tushdi...")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())

# TEST