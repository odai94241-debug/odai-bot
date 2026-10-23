from datetime import datetime
import os
import random
from threading import Thread
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

# --- خادم ويب مصغر لإرضاء موقع Render ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot is active and running!'


def run_web():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# --- التوكن الجديد الخاص بك ومعرف الأدمن ---
TOKEN = '8734379872:AAGowWGMdx5WKBY1_YcItMHAfs1d5UKEL28'
ADMIN_ID = 7753870725

bot = telebot.TeleBot(TOKEN)

settings = {
    'maintenance': False,
    'syr_cash': True,
    'sham_cash': True,
    'sham_dollar': True,
}

user_balances = {ADMIN_ID: 5000}
user_spins = {}
user_states = {}


# --- القائمة الرئيسية (الأزرار السفلية) ---
def main_menu():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add('👤 إنشاء حساب', '💳 شحن الرصيد')
  markup.add('🎡 عجلة الحظ')
  return markup


# --- أمر البداية /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
  if settings['maintenance'] and message.from_user.id != ADMIN_ID:
    bot.reply_to(
        message, '🛠️ البوت متوقف حالياً للصيانة، يرجى العودة لاحقاً.'
    )
    return

  bot.send_message(
      message.chat.id,
      'أهلاً بك في البوت الرسمي! استخدم الأزرار بالأسفل للتنقل بين إنشاء'
      ' الحساب، شحن الرصيد، وعجلة الحظ:',
      reply_markup=main_menu(),
  )


# ==========================================
# 1. لوحة تحكم الأدمن (/admin)
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(message, 'عذراً، هذا الأمر مخصص للأدمن فقط.')
    return
  send_admin_menu(message.chat.id, is_new=True)


def send_admin_menu(chat_id, message_id=None, is_new=False):
  keyboard = InlineKeyboardMarkup()

  maint_text = (
      '🛠️ وضع الصيانة: مفعل (مغلق)'
      if settings['maintenance']
      else '🛠️ وضع الصيانة: معطل (يعمل)'
  )
  syr_text = (
      '🟢 سيريتل كاش: شغال' if settings['syr_cash'] else '🔴 سيريتل كاش: متوقف'
  )
  sham_text = '🟢 شام كاش: شغال' if settings['sham_cash'] else '🔴 شام كاش: متوقف'
  dollar_text = (
      '🟢 شام كاش دولار: شغال'
      if settings['sham_dollar']
      else '🔴 شام كاش دولار: متوقف'
  )

  keyboard.add(InlineKeyboardButton(maint_text, callback_data='toggle_maint'))
  keyboard.add(InlineKeyboardButton(syr_text, callback_data='toggle_syr'))
  keyboard.add(InlineKeyboardButton(sham_text, callback_data='toggle_sham'))
  keyboard.add(InlineKeyboardButton(dollar_text, callback_data='toggle_dollar'))

  text = (
      '🎛️ **لوحة التحكم السريعة للأدمن:**\nاضغط على الزر لتغيير حالة الخدمة فوراً'
      ' بـ "كبسة زر":'
  )

  if is_new:
    bot.send_message(
        chat_id, text, reply_markup=keyboard, parse_mode='Markdown'
    )
  else:
    bot.edit_message_text(
        text, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown'
    )


@bot.callback_query_handler(
    func=lambda call: call.data in [
        'toggle_maint',
        'toggle_syr',
        'toggle_sham',
        'toggle_dollar',
    ]
)
def admin_callbacks(call):
  if call.from_user.id != ADMIN_ID:
    bot.answer_callback_query(call.id, 'غير مسموح لك
    
