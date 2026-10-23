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

# إعدادات قابلة للتعديل من لوحة الأدمن التفاعلية
SETTINGS = {
    "maintenance": False, # وضع الصيانة (True = مفعّل, False = معطّل)
    "sham_cash": "يرجى التواصل مع الإدارة",
    "syriatel_cash": "يرجى التواصل مع الإدارة",
    "referral_url": "https://t.me/odairobertbot?start=",
    "deposit_bonus_active": False, # حالة عرض بونص الإيداع
    "deposit_bonus_percentage": 10, # نسبة البونص
    "support_link": "https://t.me/odairobertbot" # رابط أو معرف الدعم
}

MIN_DEPOSIT = 250        
MIN_WITHDRAW = 500       

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# قواعد بيانات مؤقتة لتخزين الأرصدة وأيدي المستخدمين للإذاعة
USER_BALANCES = {}
USER_IDS = set()

# =========================================================
# 🛡️ فحص وضع الصيانة
# =========================================================
def check_maintenance(message):
    if SETTINGS["maintenance"]:
        bot.send_message(
            message.chat.id, 
            "⚠️ **البوت قيد الصيانة حالياً!**\n\nنعمل على تحديث وتطوير النظام، يرجى المحاولة لاحقاً.",
            parse_mode="Markdown"
        )
        return True
    return False

# =========================================================
# 🌐 مسار استقبال التحديثات من تليجرام (Webhook)
# =========================================================
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
        f"👥 **عدد المستخدمين المسجلين:** `{len(USER_IDS)}`\n"
        f"🎧 **رابط الدعم الحالي:** `{SETTINGS['support_link']}`\n"
        f"💳 **شام كاش الحالي:** `{SETTINGS['sham_cash']}`\n"
        f"📱 **سيرياتل كاش الحالي:** `{SETTINGS['syriatel_cash']}`\n\n"
        f"👇 **اختر الإجراء المطلوب بالضغط على الزر:**"
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📢 إرسال إعلان/عرض لجميع المستخدمين", callback_data="admin_broadcast"),
        telebot.types.InlineKeyboardButton("🎧 تعيين/تعديل رابط أو معرف الدعم", callback_data="admin_set_support"),
        telebot.types.InlineKeyboardButton("🔄 تبديل وضع الصيانة (تشغيل / إيقاف)", callback_data="admin_toggle_m"),
        telebot.types.InlineKeyboardButton("🎯 تفعيل/إيقاف عرض بونص الإيداع (10%)", callback_data="admin_toggle_bonus"),
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
        msg = bot.send_message(
            call.message.chat.id, 
            "📢 **قسم الإذاعة الشاملة**\n\n"
            "أرسل الآن الإعلان الذي تريد إرساله لجميع المستخدمين.\n"
            "*(يمكنك إرسال نص فقط، أو إرسال **صورة** مع نص مرفق كشرح للإعلان)*:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, execute_broadcast)

    elif call.data == "admin_set_support":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🎧 أرسل الآن **رابط أو معرف الدعم الجديد** (مثال: `@username` أو `https://t.me/...`):")
        bot.register_next_step_handler(msg, save_new_support)

    elif call.data == "admin_toggle_m":
        SETTINGS["maintenance"] = not SETTINGS["maintenance"]
        bot.answer_callback_query(call.id, "✅ تم تغيير وضع الصيانة بنجاح!")
        show_admin_menu(call.message.chat.id, call.message.message_id)
        
    elif call.data == "admin_toggle_bonus":
        SETTINGS["deposit_bonus_active"] = not SETTINGS["deposit_bonus_active"]
        state_txt = "تفعيل" if SETTINGS["deposit_bonus_active"] else "إيقاف"
        bot.answer_callback_query(call.id, f"✅ تم {state_txt} عرض بونص الإيداع بنجاح!")
        show_admin_menu(call.message.chat.id, call.message.message_id)
        
    elif call.data == "admin_set_sham":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "💳 أرسل الآن **عنوان شام كاش الجديد** في رسالة:")
        bot.register_next_step_handler(msg, save_new_sham)
        
    elif call.data == "admin_set_syriatel":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📱 أرسل الآن **رقم سيرياتل كاش الجديد** في رسالة:")
        bot.register_next_step_handler(msg, save_new_syriatel)

def execute_broadcast(message):
    success_count = 0
    fail_count = 0
    
    bot.send_message(message.chat.id, "⏳ جاري إرسال الإذاعة لجميع المستخدمين، يرجى الانتظار...")

    for uid in USER_IDS:
        try:
            if message.photo:
                photo_id = message.photo[-1].file_id
                caption = message.caption or ""
                bot.send_photo(uid, photo_id, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(uid, message.text, parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1

    bot.send_message(
        message.chat.id, 
        f"📊 **تقرير الإذاعة:**\n\n"
        f"✅ تم الإرسال بنجاح إلى: `{success_count}` مستخدم\n"
        f"❌ فشل الإرسال إلى: `{fail_count}` مستخدم",
        parse_mode="Markdown"
    )
    show_admin_menu(message.chat.id)

def save_new_support(message):
    new_val = message.text.strip()
    SETTINGS["support_link"] = new_val
    bot.send_message(message.chat.id, f"✅ تم تحديث رابط/معرف الدعم بنجاح إلى:\n`{new_val}`", parse_mode="Markdown")
    show_admin_menu(message.chat.id)

def save_new_sham(message):
    new_val = message.text.strip()
    SETTINGS["sham_cash"] = new_val
    bot.send_message(message.chat.id, f"✅ تم تحديث شام كاش بنجاح إلى:\n`{new_val}`", parse_mode="Markdown")
    show_admin_menu(message.chat.id)

def save_new_syriatel(message):
    new_val = message.text.strip()
    SETTINGS["syriatel_cash"] = new_val
    bot.send_message(message.chat.id, f"✅ تم تحديث سيرياتل كاش بنجاح إلى:\n`{new_val}`", parse_mode="Markdown")
    show_admin_menu(message.chat.id)

# =========================================================
# 📱 القائمة الرئيسية للأزرار
# =========================================================
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("👤 إنشاء حساب")
    btn2 = telebot.types.KeyboardButton("💳 شحن الرصيد")
    btn3 = telebot.types.KeyboardButton("💸 سحب الرصيد")
    btn4 = telebot.types.KeyboardButton("🎰 عجلة الفرصة")
    btn5 = telebot.types.KeyboardButton("🎁 إهداء صديق")
    btn6 = telebot.types.KeyboardButton("👥 نظام الإحالات")
    btn7 = telebot.types.KeyboardButton("🎁 قسم الهدايا")
    btn8 = telebot.types.KeyboardButton("📊 حسابي والمعلومات")
    btn9 = telebot.types.KeyboardButton("📜 شروط الاستخدام")
    btn10 = telebot.types.KeyboardButton("🎧 خدمة الدعم")
    btn11 = telebot.types.KeyboardButton("🗑 طلب حذف الحساب")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9, btn10)
    markup.add(btn11)
    return markup

# =========================================================
# 🚀 الترحيب ورسالة الشروط والأحكام
# =========================================================
@bot.message_handler(commands=['start'])
def send_terms(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    
    markup = telebot.types.InlineKeyboardMarkup()
    btn_accept = telebot.types.InlineKeyboardButton("✅ موافقة على الشروط", callback_data="accept_terms")
    markup.add(btn_accept)
    
    terms_text = (
        "عند الضغط على زر موافقة فأنت توافق على الشروط القائمة ضمن البوت ويحق لك الإعتراض في حال مواجهة أي مشكلة خارجة عن شروط وقوانين البوت.\n"
        "يرجى قراءة هذه الشّروط قبل استخدام البوت لضمان تجربة آمنة وسلسة.\n\n"
        "البوت مخصّص لإنشاء الحسابات، والسّحب، والتعبئة الفورية لحسابات موقع Ichancy.\n\n"
        "⚠️ **الشـروط والأحكام:**\n\n"
        "1️⃣ **منع الحسابات المتعدّدة:** إنشاء أكثر من حساب للشّخص الواحد مخالف للقوانين.\n"
        "2️⃣ **تبديل طرق الدفع غير مسموح:** لا يُسمح بشحن رصيد وسحبه بغرض التبديل بين وسائل الدفع.\n"
        "3️⃣ **شروط أرباح الإحالات:** تُحتسب بعد تسجيل 3 إحالات نشطة أو أكثر.\n"
        "4️⃣ **نسب عمولة السحب المعتمدة:**\n"
        " • 10% على العمليات حتى 50 مليون ليرة سورية.\n"
        " • 15% من 50 مليون حتى 150 مليون ليرة سورية.\n"
        "
        
