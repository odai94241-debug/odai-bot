import os
import time
import random
import telebot
from flask import Flask, request

# =========================================================
# ⚙️ الإعدادات والبيانات الخاصة بك
# =========================================================
API_TOKEN = '8734379872:AAFpX_ZqN0_mdJhZW2gj1yiNYJDIAVUqp18' 
AGENT_ID = "2826132-odai1@agents.nps"

SETTINGS = {
    "maintenance": False,
    "sham_cash": "يرجى التواصل مع الإدارة (أو ضبطه عبر /admin)",
    "syriatel_cash": "يرجى التواصل مع الإدارة (أو ضبطه عبر /admin)",
    "referral_url": "https://t.me/odairobertbot?start=",
    "deposit_bonus_active": False,
    "deposit_bonus_percentage": 10,
    "support_link": "https://t.me/odairobertbot"
}

MIN_DEPOSIT = 250        
MIN_WITHDRAW = 500       

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

USER_BALANCES = {}
USER_IDS = set()
TEMP_DEPOSIT_DATA = {} # لتخزين بيانات الشحن المؤقتة لكل مستخدم

def check_maintenance(message):
    if SETTINGS["maintenance"]:
        bot.send_message(
            message.chat.id, 
            "⚠️ **البوت قيد الصيانة حالياً!**\n\nنعمل على تحديث وتطوير النظام، يرجى المحاولة لاحقاً.",
            parse_mode="Markdown"
        )
        return True
    return False

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Bot is running perfectly!", 200

# =========================================================
# 👑 لوحة تحكم الإدارة التفاعلية
# =========================================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    show_admin_menu(message.chat.id)

def show_admin_menu(chat_id, message_id=None):
    m_status = "🔴 مفعّل (متوقف)" if SETTINGS["maintenance"] else "🟢 معطّل (يعمل)"
    b_status = f"🟢 مفعّل ({SETTINGS['deposit_bonus_percentage']}%)" if SETTINGS["deposit_bonus_active"] else "🔴 معطّل"
    
    text = (
        f"⚙️ **لوحة تحكم الإدارة التفاعلية:**\n\n"
        f"🛠 **وضع الصيانة:** {m_status}\n"
        f"🎯 **عرض بونص الإيداع:** {b_status}\n"
        f"👥 **عدد المستخدمين:** `{len(USER_IDS)}`\n"
        f"🎧 **رابط الدعم:** `{SETTINGS['support_link']}`\n"
        f"💳 **شام كاش:** `{SETTINGS['sham_cash']}`\n"
        f"📱 **سيرياتل كاش:** `{SETTINGS['syriatel_cash']}`\n\n"
        f"👇 **اختر الإجراء المطلوب:**"
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📢 إرسال إعلان/عرض لجميع المستخدمين", callback_data="admin_broadcast"),
        telebot.types.InlineKeyboardButton("🎧 تعيين/تعديل رابط أو معرف الدعم", callback_data="admin_set_support"),
        telebot.types.InlineKeyboardButton("🔄 تبديل وضع الصيانة", callback_data="admin_toggle_m"),
        telebot.types.InlineKeyboardButton("🎯 تفعيل/إيقاف بونص الإيداع (10%)", callback_data="admin_toggle_bonus"),
        telebot.types.InlineKeyboardButton("💳 تغيير عنوان شام كاش", callback_data="admin_set_sham"),
        telebot.types.InlineKeyboardButton("📱 تغيير رقم سيرياتل كاش", callback_data="admin_set_syriatel")
    )
    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الإعلان الآن (نص أو صورة مع نص):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, execute_broadcast)
    elif call.data == "admin_set_support":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🎧 أرسل رابط أو معرف الدعم الجديد:")
        bot.register_next_step_handler(msg, save_new_support)
    elif call.data == "admin_toggle_m":
        SETTINGS["maintenance"] = not SETTINGS["maintenance"]
        bot.answer_callback_query(call.id, "✅ تم التغيير!")
        show_admin_menu(call.message.chat.id, call.message.message_id)
    elif call.data == "admin_toggle_bonus":
        SETTINGS["deposit_bonus_active"] = not SETTINGS["deposit_bonus_active"]
        bot.answer_callback_query(call.id, "✅ تم التغيير!")
        show_admin_menu(call.message.chat.id, call.message.message_id)
    elif call.data == "admin_set_sham":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "💳 أرسل عنوان شام كاش الجديد:")
        bot.register_next_step_handler(msg, save_new_sham)
    elif call.data == "admin_set_syriatel":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📱 أرسل رقم سيرياتل كاش الجديد:")
        bot.register_next_step_handler(msg, save_new_syriatel)

def execute_broadcast(message):
    success, fail = 0, 0
    bot.send_message(message.chat.id, "⏳ جاري إرسال الإذاعة...")
    for uid in USER_IDS:
        try:
            if message.photo:
                bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "", parse_mode="Markdown")
            else:
                bot.send_message(uid, message.text, parse_mode="Markdown")
            success += 1
        except Exception:
            fail += 1
    bot.send_message(message.chat.id, f"📊 تم الإرسال بنجاح إلى: {success} | فشل: {fail}")
    show_admin_menu(message.chat.id)

def save_new_support(message):
    SETTINGS["support_link"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ تم تحديث الدعم بنجاح.")
    show_admin_menu(message.chat.id)

def save_new_sham(message):
    SETTINGS["sham_cash"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ تم تحديث شام كاش بنجاح.")
    show_admin_menu(message.chat.id)

def save_new_syriatel(message):
    SETTINGS["syriatel_cash"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ تم تحديث سيرياتل كاش بنجاح.")
    show_admin_menu(message.chat.id)

def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("👤 إنشاء حساب"),
        telebot.types.KeyboardButton("💳 شحن الرصيد"),
        telebot.types.KeyboardButton("💸 سحب الرصيد"),
        telebot.types.KeyboardButton("🎰 عجلة الفرصة"),
        telebot.types.KeyboardButton("🎁 إهداء صديق"),
        telebot.types.KeyboardButton("👥 نظام الإحالات"),
        telebot.types.KeyboardButton("🎁 قسم الهدايا"),
        telebot.types.KeyboardButton("📊 حسابي والمعلومات"),
        telebot.types.KeyboardButton("📜 شروط الاستخدام"),
        telebot.types.KeyboardButton("🎧 خدمة الدعم"),
        telebot.types.KeyboardButton("🗑 طلب حذف الحساب")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_terms(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ موافقة على الشروط", callback_data="accept_terms"))
    terms_text = (
        "مرحباً بك. يرجى قراءة الشروط والأحكام قبل البدء:\n\n"
        "1️⃣ منع الحسابات المتعددة.\n"
        "2️⃣ تبديل طرق الدفع غير مسموح.\n"
        "3️⃣ نسب عمولة السحب: 10% حتى 50M، 15% حتى 150M، 20% فوق 150M.\n"
        "4️⃣ تأكد من عناوين الدفع بدقة وعدم إرسال ملاحظات في شام كاش."
    )
    bot.send_message(message.chat.id, terms_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "accept_terms")
def terms_accepted(call):
    USER_IDS.add(call.message.chat.id)
    bot.answer_callback_query(call.id, "تم قبول الشروط!")
    bot.send_message(call.message.chat.id, "أهلاً بك!", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎧 خدمة الدعم")
def support_contact(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💬 تواصل مع الدعم الفني", url=SETTINGS["support_link"]))
    bot.send_message(message.chat.id, "🎧 للتواصل مع الدعم الفني:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 إنشاء حساب")
def ask_username(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    msg = bot.send_message(message.chat.id, "👤 أرسل اسم المستخدم (Username) الذي ترغب به:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_username)

def process_username(message):
    if message.text in ["👤 إنشاء حساب", "💳 شحن الرصيد", "💸 سحب الرصيد", "🎰 عجلة الفرصة", "📊 حسابي والمعلومات", "📜 شروط الاستخدام", "🎧 خدمة الدعم"]:
        bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=main_keyboard())
        return
    username = message.text.strip()
    if len(username) < 3:
        msg = bot.send_message(message.chat.id, "❌ اسم المستخدم قصير جداً. أعد المحاولة:")
        bot.register_next_step_handler(msg, process_username)
        return
    password = f"Pass_{message.from_user.id}!2026"
    text = f"🎉 **تم إنشاء حسابك بنجاح!**\n\n🔗 https://ichancy.com\n👤 `{username}`\n🔑 `{password}`"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎰 عجلة الفرصة")
def spin_wheel(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    msg = bot.send_message(message.chat.id, "🌀 جاري تدوير العجلة...")
    time.sleep(1.5)
    won = random.choice([0, 10, 25, 50, 100])
    if won > 0:
        bot.edit_message_text(f"🎉 مبروك! ربحت: +{won} ليرة جديدة", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.edit_message_text("🌀 حظاً أوفراً في المرة القادمة!", chat_id=message.chat.id, message_id=msg.message_id)

# =========================================================
# 💳 نظام شحن الرصيد التفاعلي (رقم العملية ثم القيمة فقط)
# =========================================================
@bot.message_handler(func=lambda message: message.text == "💳 شحن الرصيد")
def deposit_info(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("💳 شام كاش (Sham Cash)", callback_data="dep_sham"),
        telebot.types.InlineKeyboardButton("📱 سيرياتل كاش (Syriatel Cash)", callback_data="dep_syriatel")
    )
    
    bot.send_message(
        message.chat.id, 
        "📥 **قسم شحن الرصيد**\n\nالرجاء اختيار **طريقة الدفع** التي تريد الشحن من خلالها:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data in ["dep_sham", "dep_syriatel"])
def deposit_method_chosen(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    
    method = "شام كاش" if call.data == "dep_sham" else "سيرياتل كاش"
    details = SETTINGS['sham_cash'] if call.data == "dep_sham" else SETTINGS['syriatel_cash']
    
    TEMP_DEPOSIT_DATA[user_id] = {"method": method}
    
    bonus = f"🎉 **عرض الشحن:** بونص {SETTINGS['deposit_bonus_percentage']}% مفعّل حالياً!\n\n" if SETTINGS["deposit_bonus_active"] else ""
    warning_note = "🛑 **تنبيه شام كاش:** لا تقم أبداً بإرسال ملاحظات تجنباً للحظر.\n\n" if method == "شام كاش" else ""
    
    text = (
        f"📥 **شحن الرصيد عبر {method}**\n\n"
        f"{bonus}"
        f"📍 **العنوان / الكود المخصص للتحويل:** `{details}`\n"
        f"⚠️ **الحد الأدنى للشحن:** {MIN_DEPOSIT} ليرة جديدة.\n\n"
        f"{warning_note}"
        f"الرجاء إرسال **رقم العملية (Transaction ID)** الخاصة بالتحويل الآن:"
    )
    
    msg = bot.send_message(user_id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_trx)

def process_deposit_trx(message):
    if message.text and message.text.startswith('/'):
        return

    user_id = message.chat.id
    if user_id in TEMP_DEPOSIT_DATA:
        TEMP_DEPOSIT_DATA[user_id]["trx_id"] = message.text.strip()
    
    msg = bot.send_message(user_id, "💰 ممتاز.الآن أرسل **قيمة المبلغ المرسل** (بالعملة الجديدة):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    if message.text and message.text.startswith('/'):
        return

    user_id = message.chat.id
    amount = message.text.strip()
    
    data = TEMP_DEPOSIT_DATA.get(user_id, {"method": "غير معروف", "trx_id": "غير معروف"})
    
    bot.send_message(
        user_id, 
        f"✅ **تم إرسال طلب الشحن بنجاح!**\n\n"
        f"💳 طريقة الدفع: `{data['method']}`\n"
        f"🔢 رقم العملية: `{data['trx_id']}`\n"
        f"💰 المبلغ المرسل: `{amount}` ليرة جديدة\n\n"
        f"⏳ **طلبك قيد المراجعة، بانتظار موافقة الإدارة وإضافة الرصيد لحسابك.**",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    if user_id in TEMP_DEPOSIT_DATA:
        del TEMP_DEPOSIT_DATA[user_id]

@bot.message_handler(func=lambda message: message.text == "💸 سحب الرصيد")
def withdraw_info(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    bot.send_message(message.chat.id, f"📤 **سحب الرصيد**\nالحد الأدنى: {MIN_WITHDRAW} ليرة جديدة.\nأرسل المبلغ المطلوب:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👥 نظام الإحالات")
def referral_info(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    link = f"{SETTINGS['referral_url']}{message.from_user.id}"
    bot.send_message(message.chat.id, f"👥 رابط الدعوة الخاص بك:\n`{link}`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 حسابي والمعلومات")
def show_account_info(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    bal = USER_BALANCES.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"📊 **حسابك:**\nID: `{message.from_user.id}`\nالرصيد: {bal} ليرة", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📜 شروط الاستخدام")
def show_terms_only(message):
    USER_IDS.add(message.chat.id)
    send_terms(message)

if __name__ == '__main__':
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{API_TOKEN}")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    
