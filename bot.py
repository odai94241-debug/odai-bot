import telebot
from telebot import types
import requests
import time
import random

# =========================================================
# ⚙️ التوكن المعتمد والبيانات الخاصة بك
# =========================================================
API_TOKEN = '8734379872:AAFpX_ZqN0_mdJhZW2gj1yiNYJDIAVUqp18' 

# معرف الوكالة الخاص بك في iChancy (مبت):
AGENT_ID = "2826132-odai1@agents.nps"

# متغيرات النظام (تستطيع التحكم بها من التلغرام بأي وقت عبر أمر /admin)
SETTINGS = {
    "maintenance": False, # وضع الصيانة (True = مفعّل, False = معطّل)
    "sham_cash": "يرجى التواصل مع الإدارة",
    "syriatel_cash": "يرجى التواصل مع الإدارة",
    "referral_url": "https://t.me/odairobertbot?start="
}

# الحدود المالية (بالعملة الجديدة - بعد حذف الصفرين)
MIN_DEPOSIT = 250        # أدنى شحن (250 ليرة جديدة = 25,000 قديمة)
MIN_WITHDRAW = 500       # أدنى سحب (500 ليرة جديدة = 50,000 قديمة)

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
# 👑 لوحة تحكم الإدارة (الصيانة وتغيير العناوين)
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
    btn2 = types.KeyboardButton("💳 شحن الرص
                     
