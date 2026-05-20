from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
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
referrals = {}


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
        ],
        [
            KeyboardButton(
                text="👥 Do‘st taklif qilish"
            )
        ],
        [
            KeyboardButton(
                text="💸 Pul yechish"
                ),
        ],
        [
            KeyboardButton(
                text="☎️ Admin bilan bog‘lanish"
            )
]
    ],
    resize_keyboard=True
)


# ===== CONTACT ADMIN =====

@dp.message(
    lambda message:
    message.text == "☎️ Admin bilan bog‘lanish"
)
async def contact_admin(
    message: types.Message
):

    await message.answer(
        """
☎️ Admin bilan bog‘lanish

👨‍💼 Admin:
Bilolxon

📞 Telefon:
+998771814443
"""
    )

# ===== REFERRAL SYSTEM =====

@dp.message(
    lambda message:
    message.text == "👥 Do‘st taklif qilish"
)
async def referral_system(
    message: types.Message
):

    user_id = message.from_user.id

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{user_id}"
    )

    text = f"""
🏆 Mahorat Matematika Olimpiadasiga qatnashing!

🔗 Sizning referal linkingiz:

{referral_link}

📋 Agar "Do‘stga ulashish"
ishlamasa, yuqoridagi linkni
nusxalab do‘stlaringizga yuboring.

📚 Matematika olimpiadasi
📝 Online ro‘yxatdan o‘tish
🎁 Referal bonuslar mavjud
"""

    share_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Do‘stga ulashish",
                    url=f"https://t.me/share/url?url={referral_link}"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=share_keyboard
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

class WithdrawState(StatesGroup):

    karta = State()

# ===== WITHDRAW START =====

@dp.message(
    lambda message:
    message.text == "💸 Pul yechish"
)
async def withdraw_start(
    message: types.Message,
    state: FSMContext
):

    load_users()

    telegram_id = message.from_user.id

    current_user = None

    for reg_id, user in users_data.items():

        if int(user["telegram_user"]) == telegram_id:

            current_user = user
            break

    if current_user is None:

        await message.answer(
            "❌ Siz ro‘yxatdan o‘tmagansiz."
        )

        return

    balance = int(
        current_user.get(
            "balance",
            0
        )
    )

    if balance < 30000:

        await message.answer(
            f"""
❌ Minimal yechish summasi:

30 000 so‘m

💰 Sizning balans:
{balance} so‘m
"""
        )

        return

    await message.answer(
        """
💳 Pul tushadigan karta raqamingizni yuboring:

📌 Misol:
9860123412341234
"""
    )

    await state.set_state(
        WithdrawState.karta
    )


# ===== RECEIVE CARD =====

@dp.message(WithdrawState.karta)
async def receive_card(
    message: types.Message,
    state: FSMContext
):

    card = message.text.replace(
        " ",
        ""
    )

    if not (
        card.isdigit()
        and
        len(card) == 16
    ):

        await message.answer(
            "❌ Karta noto‘g‘ri."
        )

        return

    load_users()

    telegram_id = message.from_user.id

    for reg_id, user in users_data.items():

        if int(user["telegram_user"]) == telegram_id:

            balance = int(
                user.get(
                    "balance",
                    0
                )
            )

            for admin_id in ADMIN_IDS:

                await bot.send_message(
                    admin_id,
                    f"""
💸 PUL YECHISH SO‘ROVI

👤 {user['fish']}

🆔 {reg_id}

💰 Balans:
{balance} so‘m

💳 Karta:
{card}
""",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="✅ To‘landi",
                                    callback_data=f"withdraw_accept_{reg_id}"
                                )
                            ]
                        ]
                    )
                )

            await message.answer(
                """
✅ So‘rov adminga yuborildi.

📌 Tez orada tekshiriladi.
"""
            )

            break

    await state.clear()


# ===== START =====

@dp.message(CommandStart())
async def start(
    message: types.Message
):

    # ===== ADMIN =====

    if message.from_user.id in ADMIN_IDS:

        await message.answer(
            "👋 Assalomu alaykum admin!",
            reply_markup=admin_menu
        )

        return

    # ===== REFERRAL =====

    args = message.text.split()

    if len(args) > 1:

        ref_data = args[1]

        if ref_data.startswith("ref_"):

            referrer_id = ref_data.replace(
                "ref_",
                ""
            )

            if str(message.from_user.id) != referrer_id:

                referrals[
                    message.from_user.id
                ] = int(referrer_id)

    text = """
🏆 Mahorat Matematika Olimpiadasiga xush kelibsiz!

📅 Olimpiada sanasi:
06.06.2026

🕣 Boshlanish vaqti:
08:30

🏫 Manzil:
Mahorat Maktabi

📍 Mo‘ljal:
Turon Universiteti tepasi

💰 Ishtirok narxi:
50 000 so‘m

━━━━━━━━━━━━━━━

📚 Ushbu bot orqali siz:

✅ Olimpiadaga ro‘yxatdan o‘tasiz
✅ To‘lov chekini yuborasiz
✅ Referal havola orqali do‘stlarni taklif qilasiz
✅ Har bir tasdiqlangan do‘st uchun 5000 so‘m bonus olasiz
✅ Bonus 30 000 so‘mga yetganda yechib olasiz
✅ Natijalarni kuzatasiz

━━━━━━━━━━━━━━━

📌 Botdan foydalanish uchun
quyidagi kanallarga a’zo bo‘ling
va "✅ Tekshirish" tugmasini bosing.
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
    """
✅ Obuna tasdiqlandi!

🏆 Mahorat Matematika Olimpiadasiga
xush kelibsiz!

📅 Olimpiada sanasi:
06.06.2026

🕣 Boshlanish vaqti:
08:30

🏫 Manzil:
Mahorat Maktabi

📍 Mo‘ljal:
Turon Universiteti tepasi

💰 Ishtirok narxi:
50 000 so‘m

📚 Bot orqali:
• Ro‘yxatdan o‘tasiz
• To‘lov chekini yuborasiz
• Referal bonus yig‘asiz
• Natijalarni kuzatasiz

👇 Endi kerakli bo‘limni tanlang:
"""
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
        """
👤 F.I.SH kiriting:

✍️ Misol:
Ilyosjon Inamov
"""
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

            status_text = (
                "🟢 TO‘LOV TASDIQLANGAN"
                if data["status"] == "TOLOV TASDIQLANDI"
                else "🟡 TO‘LOV KUTILMOQDA"
            )

            result += f"""
━━━━━━━━━━━━━━━

🆔 ID:
{reg_id}

👤 Ishtirokchi:
{data['fish']}

📚 Sinf:
{data['sinf']}

🏫 Maktab:
{data['maktab']}

📌 Holat:
{status_text}

━━━━━━━━━━━━━━━
"""

    if result == "":

        result = """
❌ Siz hali ro‘yxatdan o‘tmagansiz.
"""

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
            """
❌ F.I.SH noto‘g‘ri.

✍️ Misol:
Ilyosjon Inamov
"""
        )

        return

    await state.update_data(
        fish=message.text
    )

    sinf_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="1-sinf"),
            KeyboardButton(text="2-sinf")
        ],
        [
            KeyboardButton(text="3-sinf"),
            KeyboardButton(text="4-sinf")
        ],
        [
            KeyboardButton(text="5-sinf"),
            KeyboardButton(text="6-sinf")
        ],
        [
            KeyboardButton(text="7-sinf"),
            KeyboardButton(text="8-sinf")
        ],
        [
            KeyboardButton(text="9-sinf"),
            KeyboardButton(text="10-sinf")
        ],
        [
            KeyboardButton(text="11-sinf")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

    await message.answer(
        "📚 Sinfni tanlang:",
        reply_markup=sinf_keyboard
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

    allowed_classes = [
        "1-sinf",
        "2-sinf",
        "3-sinf",
        "4-sinf",
        "5-sinf",
        "6-sinf",
        "7-sinf",
        "8-sinf",
        "9-sinf",
        "10-sinf",
        "11-sinf"
    ]

    if message.text not in allowed_classes:

        await message.answer(
            "❌ Tugmalardan birini tanlang."
        )

        return

    await state.update_data(
        sinf=message.text
    )

    await message.answer(
        """
📞 1-telefon raqami:

✍️ Misol:
+998901234567
""",
        reply_markup=ReplyKeyboardRemove()
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
            """
❌ Telefon noto‘g‘ri.

✍️ Misol:
+998901234567
"""
        )

        return

    await state.update_data(
        tel1=message.text
    )

    await message.answer(
        """
📞 2-telefon raqami:

✍️ Misol:
+998901234567
"""
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
            """
❌ Telefon noto‘g‘ri.

✍️ Misol:
+998901234567
"""
        )

        return

    await state.update_data(
        tel2=message.text
    )

    await message.answer(
        """
🏫 Maktab nomini kiriting:

✍️ Misol:
12-maktab
"""
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
            """
❌ Maktab nomi noto‘g‘ri.

✍️ Misol:
12-maktab
"""
        )

        return

    await state.update_data(
        maktab=message.text
    )

    data = await state.get_data()

    registration_id = (
        f"MM-{registration_counter:04d}"
    )

    registration_counter += 1

    users_data[registration_id] = {

        "telegram_user": message.from_user.id,

        "fish": data["fish"],

        "sinf": data["sinf"],

        "tel1": data["tel1"],

        "tel2": data["tel2"],

        "maktab": data["maktab"],

        "status": "KUTILMOQDA",

        "ref_bonus": 0
    }

    try:

        await asyncio.to_thread(
            requests.post,
            SCRIPT_URL,
            json={
                "id": registration_id,
                "telegram_user": message.from_user.id,
                "fish": data["fish"],
                "sinf": data["sinf"],
                "tel1": data["tel1"],
                "tel2": data["tel2"],
                "maktab": data["maktab"],
                
                "refer_id": referrals.get(
                message.from_user.id,
                    ""
                ),
            },
            timeout=10
        )

    except Exception as error:
        print(error)

    await message.answer(
    f"""
✅ Registratsiya muvaffaqiyatli yakunlandi!

━━━━━━━━━━━━━━━

👤 ISHTIROKCHI

🆔 ID:
{registration_id}

👨‍🎓 F.I.SH:
{data['fish']}

📚 Sinf:
{data['sinf']}

🏫 Maktab:
{data['maktab']}

📱 1-telefon:
{data['tel1']}

📱 2-telefon:
{data['tel2']}

━━━━━━━━━━━━━━━

💰 50 000 so‘m to‘lovni
quyidagi kartaga o‘tkazing:

💳 9860 0401 1490 7971

👤 Bilolxon M

━━━━━━━━━━━━━━━

📤 To‘lovdan so‘ng
"💳 Chek yuborish"
tugmasi orqali chekni yuboring.

📌 Holat:
KUTILMOQDA
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

    load_users()

    if registration_id not in users_data:

        await callback.answer(
            "❌ Registratsiya topilmadi!",
            show_alert=True
        )

        return

    user = users_data[registration_id]

    if user["status"] == "TOLOV TASDIQLANDI":

        await callback.answer(
        "⚠️ Bu to‘lov avval tasdiqlangan!",
        show_alert=True
    )

    return

    user["status"] = "TOLOV TASDIQLANDI"

    telegram_user = user["telegram_user"]

    # ===== REFERRAL BONUS =====

    referrer_id = user.get(
        "refer_id",
        ""
    )

    if str(referrer_id) != "":

        for reg_id, ref_user in users_data.items():

            if str(
                ref_user["telegram_user"]
            ) == str(referrer_id):

                current_balance = int(
                    ref_user.get(
                        "balance",
                        0
                    )
                )

                current_balance += 5000

                ref_user["balance"] = current_balance

                try:

                    await asyncio.to_thread(
                        requests.post,
                        SCRIPT_URL,
                        json={
                            "action": "update_referral",
                            "telegram_user": referrer_id
                        },
                        timeout=10
                    )

                except Exception as error:
                    print(error)

                try:

                    await bot.send_message(
                        referrer_id,
                        f"""
🎉 Sizning taklifingiz orqali
bir foydalanuvchi to‘lov qildi!

💰 Sizga 5000 so‘m bonus yozildi.

🏦 Jami balans:
{current_balance} so‘m

💸 30 000 so‘m bo‘lganda
pul yechib olishingiz mumkin.
"""
                    )

                except:
                    pass

                break

    # ===== UPDATE STATUS =====

    try:

        await asyncio.to_thread(
            requests.post,
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

    # ===== SEND USER MESSAGE =====

    await bot.send_message(
        telegram_user,
        f"""
✅ To‘lov tasdiqlandi!

🆔 ID:
{registration_id}

👨‍🎓 Ishtirokchi:
{user['fish']}

━━━━━━━━━━━━━━━

🏆 OLIMPIADA MA’LUMOTI

📅 Sana:
06.06.2026

🕣 Boshlanish vaqti:
08:30

📍 Manzil:
Mahorat Maktabi

📌 Mo‘ljal:
Turon Universiteti tepasi

━━━━━━━━━━━━━━━

📚 Olimpiadaga
o‘z vaqtida kelishingizni so‘raymiz.
"""
    )

    await callback.answer(
        "✅ Tasdiqlandi!"
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

    load_users()

    if registration_id not in users_data:

        await callback.answer(
            "❌ Registratsiya topilmadi!",
            show_alert=True
        )

        return

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

# ===== WITHDRAW ACCEPT =====

@dp.callback_query(
    lambda c:
    c.data.startswith(
        "withdraw_accept_"
    )
)
async def withdraw_accept(
    callback: types.CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        return

    registration_id = callback.data.replace(
        "withdraw_accept_",
        ""
    )

    load_users()

    if registration_id not in users_data:

        return

    user = users_data[registration_id]

    balance = int(
        user.get(
            "balance",
            0
        )
    )

    if balance < 30000:

        await callback.answer(
            "❌ Balans yetarli emas.",
            show_alert=True
        )

        return

    new_balance = balance - 30000

    user["balance"] = new_balance

    try:

        await asyncio.to_thread(
            requests.post,
            SCRIPT_URL,
            json={
                "action": "withdraw_done",
                "telegram_user": user["telegram_user"],
                "balance": new_balance
            },
            timeout=10
        )

    except Exception as error:
        print(error)

    await bot.send_message(
        user["telegram_user"],
        f"""
✅ Pul yechish tasdiqlandi.

💰 30 000 so‘m
kartangizga tashlandi.

🏦 Qolgan balans:
{new_balance} so‘m
"""
    )

    await callback.message.edit_reply_markup()

    await callback.answer(
        "Tasdiqlandi!"
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