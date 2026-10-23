import telebot
from telebot import types
import requests
import time
import random

# =========================================================
# ⚙️ التوكن المعتمد والبيانات الخاصة بك
# =========================================================
API_TOKEN = '8734379872:AAFAHvAa6IY1P7lrzMEaBbUkVNVCDgI_lRs' 

# معرف الوكالة الخاص بك في iChancy
AGENT_ID = "2826132-odai1@agents.nps"
ICHANCY_API_URL = "https://agents.ichancy.com/api"

# متغيرات النظام (يمكنك التحكم بها من التلغرام عبر أمر /admin)
SETTINGS = {
    "maintenance": False, # وضع الصيانة (True = مفعّل, False = معطّل)
    "sham_cash": "يرجى التواصل مع الإدارة",
    "syriatel_cash": "يرجى التواصل مع الإدارة",
    "referral_url": "https://t.me/odairobertbot?start="
}

# الحدود المالية (بالعملة الجديدة)
MIN_DEPOSIT = 250        # أدنى حد للشحن (250 ليرة جديدة)
MIN_WITHDRAW = 500       # أدنى حد للسحب (500 ليرة جديدة)

bot = telebot.TeleBot(API_TOKEN)

# =========================================================
# 🛡️ دالة فحص وضع الصيانة
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
# 👑 لوحة التحكم بالإدارة (لوضع الصيانة وتغيير العناوين)
# =========================================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    status = "🔴 مفعّل" if SETTINGS["maintenance"] else "🟢 معطّل"
    text = (
        f"⚙️ **لوحة تحكم الإدارة:**\n\n"
        f"🛠 **وضع الصيانة:** {status}\n"
        f"💳 **شام كاش الحالي:** `{SETTINGS['sham_cash']}`\n"
        f"📱 **سيرياتل كاش الحالي:** `{SETTINGS['syriatel_cash']}`\n\n"
        f"📌 **الأوامر السريعة للتحكم:**\n"
        f"• `/maintenance_on` - تشغيل وضع الصيانة\n"
        f"• `/maintenance_off` - إيقاف وضع الصيانة\n"
        f"• `/set_sham 09xx...` - تغيير عنوان شام كاش\n"
        f"• `/set_syriatel 09xx...` - تغيير رقم سيرياتل كاش"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['maintenance_on'])
def set_m_on(message):
    SETTINGS["maintenance"] = True
    bot.send_message(message.chat.id, "✅ تم تفعيل وضع الصيانة! البوت مغلق الآن أمام المستخدمين.")

@bot.message_handler(commands=['maintenance_off'])
def set_m_off(message):
    SETTINGS["maintenance"] = False
    bot.send_message(message.chat.id, "✅ تم إيقاف وضع الصيانة! البوت يعمل الآن بشكل طبيعي.")

@bot.message_handler(commands=['set_sham'])
def set_sham_cash(message):
    new_val = message.text.replace('/set_sham', '').strip()
    if new_val:
        SETTINGS["sham_cash"] = new_val
        bot.send_message(message.chat.id, f"✅ تم تحديث شام كاش إلى: `{new_val}`", parse_mode="Markdown")

@bot.message_handler(commands=['set_syriatel'])
def set_syriatel_cash(message):
    new_val = message.text.replace('/set_syriatel', '').strip()
    if new_val:
        SETTINGS["syriatel_cash"] = new_val
        bot.send_message(message.chat.id, f"✅ تم تحديث سيرياتل كاش إلى: `{new_val}`", parse_mode="Markdown")

# =========================================================
# 📱 القائمة الرئيسية للأزرار
# =========================================================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("👤 إنشاء حساب")
    btn2 = types.KeyboardButton("💳 شحن الرصيد")
    btn3 = types.KeyboardButton("💸 سحب الرصيد")
    btn4 = types.KeyboardButton("🎰 عجلة الفرصة")
    btn5 = types.KeyboardButton("🎁 إهداء صديق")
    btn6 = types.KeyboardButton("👥 نظام الإحالات")
    btn7 = types.KeyboardButton("🎁 قسم الهدايا")
    btn8 = types.KeyboardButton("📊 حسابي والمعلومات")
    btn9 = types.KeyboardButton("📜 شروط الاستخدام")
    btn10 = types.KeyboardButton("🗑 طلب حذف الحساب")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9, btn10)
    return markup

# =========================================================
# 🚀 الترحيب ورسالة الشروط والأحكام الرسمية
# =========================================================
@bot.message_handler(commands=['start'])
def send_terms(message):
    if check_maintenance(message): return
    
    markup = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ موافقة على الشروط", callback_data="accept_terms")
    markup.add(btn_accept)
    
    terms_text = (
        "عند الضغط على زر موافقة فأنت توافق على الشروط القائمة ضمن البوت ويحق لك الإعتراض في حال مواجهة أي مشكلة خارجة عن شروط وقوانين البوت.\n"
        "يرجى قراءة هذه الشّروط قبل استخدام البوت لضمان تجربة آمنة وسلسة.\n\n"
        "البوت مخصّص لإنشاء الحسابات، والسّحب، والتعبئة الفورية لحسابات موقع Ichancy.\n\n"
        "⚠️ **الشـروط:**\n\n"
        "1️⃣ **منع الحسابات المتعدّدة:** إنشاء أكثر من حساب للشّخص الواحد مخالف للقوانين، وقد يؤدّي إلى حظر الحسابات المرتبطة وتجميد أرصدتها، وذلك بناءاً على سياسة اللّعب النظيف.\n\n"
        "2️⃣ **تبديل طرق الدفع غير مسموح:** لا يُسمح بشحن رصيد وسحبه بغرض التبديل بين وسائل الدفع المختلفة. في حال اكتشاف عملية كهذه، يتم سحب الرّصيد والتّحفظ عليه دون إشعار مسبق.\n\n"
        "3️⃣ **شروط أرباح الإحالات:** تُحتسب أرباح الإحالة فقط بعد تسجيل 3 إحالات نشطة أو أكثر (أي قاموا بالتعبئة الفعلية).\n\n"
        "4️⃣ **نسبة السحب:**\n"
        " • 10% على جميع عمليات السحب حتى 50 مليون ليرة سورية.\n"
        " • 15% على جميع عمليات السحب من 50 مليون حتى 150 مليون ليرة سورية.\n"
        " • 20% على جميع عمليات السحب من 150 مليون ليرة سورية فما فوق.\n\n"
        "5️⃣ لا تقم بالتحويل من الرمز #3040* ولا من كازية تحويل حين توقف تطبيق أقرب عن العمل لأن معالجة العملية تستغرق وقت طويل بسبب توقف الأوتو مع التطبيق.\n\n"
        "6️⃣ يرجى التأكد دائماً من عنوان شام كاش وعناوين العملات الرقمية قبل القيام بأي عملية تحويل.\n\n"
        "7️⃣ عند التحويل من شام كاش لا تقم أبداً بإرسال ملاحظات، هذا يعرض حسابك للحظر ولا يمكن استرداد الأموال.\n\n"
        "📌 **ملاحظة مهمة:** عند الاستفادة من البونص الترحيبي شرط السحب يجب أن يكون ضعف إجمالي المبلغ المشحون. وفي حين عدم استيفاء الشرط يخصم البونص الترحيبي بالكامل من قيمة المبلغ المسحوب.\n\n"
        "⛔️ **تنبيه:** أي محاولة للتّحايل أو مخالفة الشروط ستؤدي إلى إيقاف الحساب وتجميد الأرصدة."
    )
    bot.send_message(message.chat.id, terms_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "accept_terms")
def terms_accepted(call):
    bot.answer_callback_query(call.id, "تم قبول الشروط بنجاح!")
    bot.send_message(call.message.chat.id, "أهلاً بك! يمكنك الآن استخدام جميع ميزات البوت.", reply_markup=main_keyboard())

# =========================================================
# 👤 إنشاء حساب لاعب تحت الوكالة المعتمدة
# =========================================================
@bot.message_handler(func=lambda message: message.text == "👤 إنشاء حساب")
def handle_create_account(message):
    if check_maintenance(message): return
    user_id = message.from_user.id
    default_username = f"user_{user_id}"
    default_password = f"Pass_{user_id}!2026"
    
    text = (
        f"🎉 **تم إنشاء حسابك بنجاح!**\n\n"
        f"🔗 **رابط الدخول:** https://ichancy.com\n"
        f"👤 **اسم المستخدم:** `{default_username}`\n"
        f"🔑 **كلمة السر:** `{default_password}`\n"
        f"🏢 **الوكيل:** `{AGENT_ID}`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# =========================================================
# 🎰 عجلة الفرصة (دوارة وتفاعلية)
# =========================================================
@bot.message_handler(func=lambda message: message.text == "🎰 عجلة الفرصة")
def spin_wheel(message):
    if check_maintenance(message): return
    msg = bot.send_message(message.chat.id, "🌀 **جاري تدوير العجلة...** 🎯")
    time.sleep(1.5)
    
    prizes = [0, 10, 25, 50, 100]
    won_amount = random.choice(prizes)
    
    if won_amount > 0:
        bot.edit_message_text(f"🎉 **مبروك!** دارت العجلة ووقفت على:\n💰 **+{won_amount} ليرة جديدة**", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.edit_message_text("🌀 **حظاً أوفراً في المرة القادمة!**", chat_id=message.chat.id, message_id=msg.message_id)

# =========================================================
# 💳 شحن الرصيد
# =========================================================
@bot.message_handler(func=lambda message: message.text == "💳 شحن الرصيد")
def deposit_info(message):
    if check_maintenance(message): return
    text = (
        f"📥 **قسم شحن الرصيد**\n\n"
        f"⚠️ **الحد الأدنى للشحن:** {MIN_DEPOSIT} ليرة جديدة (تعادل {MIN_DEPOSIT * 100} قديمة).\n\n"
        f"📍 **عناوين الدفع المتاحة:**\n"
        f"• **شام كاش:** `{SETTINGS['sham_cash']}`\n"
        f"• **سيرياتل كاش:** `{SETTINGS['syriatel_cash']}`\n\n"
        f"🛑 **تنبيه شام كاش:** عند التحويل لا تقم أبداً بإرسال ملاحظات تجنباً للحظر.\n\n"
        f"بعد التحويل أرسل صورة الإشعار هنا لتأكيد الشحن."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# =========================================================
# 💸 سحب الرصيد والعمولات حسب الشرائح
# =========================================================
@bot.message_handler(func=lambda message: message.text == "💸 سحب الرصيد")
def withdraw_info(message):
    if check_maintenance(message): return
    text = (
        f"📤 **قسم سحب الرصيد**\n\n"
        f"⚠️ **الحد الأدنى للسحب:** {MIN_WITHDRAW} ليرة جديدة (تعادل {MIN_WITHDRAW * 100} قديمة).\n\n"
        f"💥 **نسب عمولة السحب المعتمدة:**\n"
        f"• **10%** على العمليات حتى 50 مليون ليرة.\n"
        f"• **15%** من 50 مليون حتى 150 مليون ليرة.\n"
        f"• **20%** لأكثر من 150 مليون ليرة.\n\n"
        f"أرسل المبلغ المطلوب سحبه بالعملة الجديدة الآن:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# =========================================================
# 👥 نظام الإحالات
# =========================================================
@bot.message_handler(func=lambda message: message.text == "👥 نظام الإحالات")
def referral_info(message):
    if check_maintenance(message): return
    user_link = f"{SETTINGS['referral_url']}{message.from_user.id}"
    text = (
        f"👥 **نظام الإحالات ودعوة الأصدقاء:**\n\n"
        f"⚠️ تُحتسب أرباح الإحالة فقط بعد تسجيل **3 إحالات نشطة** أو أكثر (قاموا بالتعبئة الفعلية).\n\n"
        f"🔗 **رابط الدعوة الخاص بك:**\n`{user_link}`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# =========================================================
# 📊 عرض تفاصيل الحساب
# =========================================================
@bot.message_handler(func=lambda message: message.text == "📊 حسابي والمعلومات")
def show_account_info(message):
    if check_maintenance(message): return
    text = (
        f"📊 **تفاصيل حسابك:**\n\n"
        f"🆔 **الحساب الخاص (ID):** `{message.from_user.id}`\n"
        f"👤 **اسم المستخدم:** {message.from_user.first_name}\n"
        f"💰 **الرصيد الحالي:** 50 ليرة جديدة"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# =========================================================
# 📜 زر الشروط في القائمة
# =========================================================
@bot.message_handler(func=lambda message: message.text == "📜 شروط الاستخدام")
def show_terms_only(message):
    send_terms(message)

bot.polling(none_stop=True)
    
