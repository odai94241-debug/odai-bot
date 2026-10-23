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

# --- خادم ويب مصغر لضمان استقرار Render ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot is active and running!'


def run_web():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# --- بيانات التوكن والأدمن ---
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
user_accounts = {}


# --- القوائم والأزرار ---
def main_menu():
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add('👤 إنشاء حساب', '💳 شحن الرصيد')
  markup.add('🌟 عجلة الفرصة')
  return markup


def back_menu():
  markup = ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add('🔙 رجوع للقائمة الرئيسية')
  return markup


# --- أمر البداية /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
  user_id = message.from_user.id
  user_states[user_id] = None

  if settings['maintenance'] and user_id != ADMIN_ID:
    bot.reply_to(
        message, '🛠️ البوت متوقف حالياً للصيانة، يرجى العودة لاحقاً.'
    )
    return

  bot.send_message(
      message.chat.id,
      'أهلاً بك في البوت الرسمي! استخدم الأزرار بالأسفل للتنقل بين الخدمات:',
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
      '🛠️ وضع الصيانة: مفعل'
      if settings['maintenance']
      else '🛠️ وضع الصيانة: معطل'
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

  text = '🎛️ **لوحة التحكم السريعة للأدمن:**'

  if is_new:
    bot.send_message(
        chat_id, text, reply_markup=keyboard, parse_mode='Markdown'
    )
  else:
    bot.edit_message_text(
        text, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown'
    )


@bot.callback_query_handler(
    func=lambda call: call.data
    in ['toggle_maint', 'toggle_syr', 'toggle_sham', 'toggle_dollar']
)
def admin_callbacks(call):
  if call.from_user.id != ADMIN_ID:
    bot.answer_callback_query(call.id, 'غير مسموح لك!', show_alert=True)
    return

  if call.data == 'toggle_maint':
    settings['maintenance'] = not settings['maintenance']
  elif call.data == 'toggle_syr':
    settings['syr_cash'] = not settings['syr_cash']
  elif call.data == 'toggle_sham':
    settings['sham_cash'] = not settings['sham_cash']
  elif call.data == 'toggle_dollar':
    settings['sham_dollar'] = not settings['sham_dollar']

  send_admin_menu(call.message.chat.id, call.message.message_id, is_new=False)
  bot.answer_callback_query(call.id, '✅ تم تحديث الحالة بنجاح!')


# ==========================================
# 2. منح لفة مجانية
# ==========================================
def add_free_spin_on_deposit(user_id):
  today = datetime.now().strftime('%Y-%m-%d')
  if user_id not in user_spins:
    user_spins[user_id] = {'date': today, 'spins_left': 1}
  else:
    if user_spins[user_id]['date'] == today:
      user_spins[user_id]['spins_left'] += 1
    else:
      user_spins[user_id] = {'date': today, 'spins_left': 1}


# ==========================================
# 3. 🌟 عجلة الفرصة (مع ضبط الاحتمالات)
# ==========================================
@bot.message_handler(
    func=lambda m: m.text
    in ['🌟 عجلة الفرصة', 'عجلة الفرصة', 'عجلة الحظ', '/spin']
)
def wheel_intro(message):
  chat_id = message.chat.id
  user_id = message.from_user.id
  today = datetime.now().strftime('%Y-%m-%d')

  spins_data = user_spins.get(user_id, {'date': today, 'spins_left': 0})
  if spins_data['date'] != today:
    spins_data = {'date': today, 'spins_left': 0}
    user_spins[user_id] = spins_data

  spins_left = spins_data['spins_left']

  text = (
      '🌟 **★ عجلة الفرصة ★** 🌟\n\n'
      '🎁 **الجوائز الكبرى المتاحة بالعجلة:**\n'
      '• 🎁 1,000,000 نقطة/ليرة\n'
      '• 🎁 100,000 نقطة/ليرة\n'
      '• 🎁 50,000 نقطة/ليرة\n'
      '• 🎁 25,000 نقطة/ليرة\n'
      '• 🎁 10,000 نقطة/ليرة\n'
      '• 🎁 5,000 نقطة/ليرة\n'
      '• 🎟️ لفة مجانية إضافية\n\n'
      f'🎟️ **اللفات المتاحة لديك اليوم:** `{spins_left}` لفة.'
  )

  markup = InlineKeyboardMarkup()
  if spins_left > 0:
    markup.add(
        InlineKeyboardButton('🎰 دَوْر العجلة الآن', callback_data='spin_free')
    )
  else:
    markup.add(
        InlineKeyboardButton(
            '❌ لقد استخدمت لفتك لهذا اليوم (اشحن لتفعيلها)',
            callback_data='no_spins',
        )
    )

  bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')


@bot.callback_query_handler(
    func=lambda call: call.data in ['spin_free', 'no_spins']
)
def process_spin(call):
  user_id = call.from_user.id
  today = datetime.now().strftime('%Y-%m-%d')

  if call.data == 'no_spins':
    bot.answer_callback_query(
        call.id,
        '⚠️ لقد استخدمت لفتك لهذا اليوم! اشحن رصيدك للحصول على فرصة جديدة.',
        show_alert=True,
    )
    return

  spins_data = user_spins.get(user_id, {'date': today, 'spins_left': 0})

  if spins_data['spins_left'] <= 0:
    bot.answer_callback_query(
        call.id, '⚠️ لقد استخدمت لفتك لهذا اليوم!', show_alert=True
    )
    return

  spins_data['spins_left'] -= 1

  # مصفوفة الجوائز مضبوطة: التركيز الثقيل على حظ أوفر، لفة مجانية، و5,000 فقط
  prizes = [
      ('❌ حظ أوفر، خيرها في غيرها!', 65),  # 65% حظ أوفر
      ('🎟️ مبروك! ربحت لفة مجانية إضافية!', 25),  # 25% لفة مجانية
      ('🎁 مبروك! ربحت 5,000 ليرة/نقطة!', 10),  # 10% ربح 5000
      ('🎁 مبروك! ربحت 10,000 ليرة/نقطة!', 0),  # شكليات فقط (0%)
      ('🎁 مبروك! ربحت 25,000 ليرة/نقطة!', 0),  # شكليات فقط (0%)
      ('🎁 🎉 بالجائزة الكبرى! ربحت 1,000,000!', 0),  # شكليات فقط (0%)
  ]

  prize_list, weights = zip(*prizes)
  result = random.choices(prize_list, weights=weights, k=1)[0]

  if '5,000' in result:
    user_balances[user_id] = user_balances.get(user_id, 0) + 5000
  elif 'لفة مجانية' in result:
    spins_data['spins_left'] += 1

  remaining = spins_data['spins_left']
  result_text = f'🌟 **نتيجة دورة عجلة الفرصة:**\n\n{result}\n\n🎟️ **اللفات المتاحة المتبقية:** `{remaining}`'

  markup = InlineKeyboardMarkup()
  if remaining > 0:
    markup.add(
        InlineKeyboardButton('🔄 دَوْر العجلة مرة أخرى', callback_data='spin_free')
    )
  else:
    markup.add(
        InlineKeyboardButton(
            '⏳ لقد استخدمت لفتك لهذا اليوم', callback_data='no_spins'
        )
    )

  bot.edit_message_text(
      result_text,
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
      parse_mode='Markdown',
  )
  bot.answer_callback_query(call.id, 'تمت العملية ودوران العجلة!')


# ==========================================
# 4. معالجة الرسائل والرجوع والإنشاء
# ==========================================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
  user_id = message.from_user.id
  text = message.text

  if text in ['🔙 رجوع للقائمة الرئيسية', 'رجوع']:
    user_states[user_id] = None
    bot.send_message(
        message.chat.id,
        '🔙 تم الرجوع للقائمة الرئيسية:',
        reply_markup=main_menu(),
    )
    return

  if settings['maintenance'] and user_id != ADMIN_ID:
    bot.reply_to(
        message, '🛠️ البوت متوقف حالياً للصيانة، يرجى العودة لاحقاً.'
    )
    return

  username = (
      message.from_user.username
      if message.from_user.username
      else message.from_user.first_name
  )
  state = user_states.get(user_id)

  if text == '👤 إنشاء حساب':
    if user_id in user_accounts:
      acc = user_accounts[user_id]
      info_msg = f"👤 **حسابك المسجل سابقاً:**\n\n📌 الاسم: `{acc['name']}`\n🏛️ البلدية: `{acc['city']}`\n🔑 كلمة السر: `{acc['pass']}`"
      bot.send_message(
          message.chat.id,
          info_msg,
          reply_markup=main_menu(),
          parse_mode='Markdown',
      )
    else:
      user_states[user_id] = 'reg_name'
      user_accounts[user_id] = {}
      bot.send_message(
          message.chat.id,
          '👤 **خطوة 1/3:** يرجى إدخال **اسمك الكامل** الآن:',
          reply_markup=back_menu(),
      )

  elif state == 'reg_name':
    user_accounts[user_id]['name'] = text
    user_states[user_id] = 'reg_city'
    bot.send_message(
        message.chat.id,
        '🏛️ **خطوة 2/3:** ممتاز! يرجى إدخال **اسم البلدية / المنطقة** الآن:',
        reply_markup=back_menu(),
    )

  elif state == 'reg_city':
    user_accounts[user_id]['city'] = text
    user_states[user_id] = 'reg_pass'
    bot.send_message(
        message.chat.id,
        '🔑 **خطوة 3/3:** يرجى كتابة **كلمة السر** التي تفضلها لحسابك:',
        reply_markup=back_menu(),
    )

  elif state == 'reg_pass':
    user_accounts[user_id]['pass'] = text
    user_states[user_id] = None
    acc = user_accounts[user_id]

    success_text = f"🎉 **تم إنشاء حسابك بنجاح!**\n\n📌 **الاسم:** `{acc['name']}`\n🏛️ **البلدية:** `{acc['city']}`\n🔑 **كلمة السر:** `{acc['pass']}`\n\nيمكنك الان شحن رصيدك والدخول لعجلة الفرصة!"
    bot.send_message(
        message.chat.id,
        success_text,
        reply_markup=main_menu(),
        parse_mode='Markdown',
    )

  elif text == '💳 شحن الرصيد':
    markup = InlineKeyboardMarkup()
    if settings['syr_cash']:
      markup.add(
          InlineKeyboardButton(
              '🟢 شحن عبر سيريتل كاش', callback_data='pay_syr'
          )
      )
    if settings['sham_cash']:
      markup.add(
          InlineKeyboardButton('🟢 شحن عبر شام كاش', callback_data='pay_sham')
      )
    if settings['sham_dollar']:
      markup.add(
          InlineKeyboardButton(
              '🟢 شحن عبر شام كاش دولار ($)', callback_data='pay_dollar'
          )
      )

    if not markup.keyboard:
      bot.reply_to(
          message,
          '⚠️ جميع وسائل الدفع متوقفة مؤقتاً للصيانة.',
          reply_markup=main_menu(),
      )
      return

    bot.send_message(
        message.chat.id,
        '💳 **اختر وسيلة الدفع المناسبة لشحن رصيدك:**',
        reply_markup=markup,
        parse_mode='Markdown',
    )

  elif state in ['waiting_syr', 'waiting_sham', 'waiting_dollar']:
    method_name = (
        'سيريتل كاش'
        if state == 'waiting_syr'
        else ('شام كاش' if state == 'waiting_sham' else 'شام كاش دولار ($)')
    )
    user_states[user_id] = None

    bot.send_message(
        message.chat.id,
        '⏳ **تم إرسال طلب الشحن بنجاح!**\nتم تحويل التفاصيل للأدمن للمراجعة، وسيتم منحك لفة مجانية فور القبول.',
        reply_markup=main_menu(),
        parse_mode='Markdown',
    )

    admin_notification = f'🔔 **طلب شحن جديد!**\n\n👤 المستخدم: @{username} (ID: `{user_id}`)\n💳 الوسيلة: {method_name}\n📝 التفاصيل:\n{text}'

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton(
            '✅ موافق (قبول الشحن)', callback_data=f'approve_dep_{user_id}'
        )
    )

    bot.send_message(
        ADMIN_ID,
        admin_notification,
        reply_markup=admin_markup,
        parse_mode='Markdown',
    )

  else:
    bot.send_message(
        message.chat.id,
        'أهلاً بك! استخدم الأزرار بالأسفل للتنقل:',
        reply_markup=main_menu(),
    )


# ==========================================
# 5. الكولباك وموافقة الأدمن
# ==========================================
@bot.callback_query_handler(
    func=lambda call: call.data
    in ['pay_syr', 'pay_sham', 'pay_dollar']
    or call.data.startswith('approve_dep_')
)
def handle_payment_callbacks(call):
  user_id = call.from_user.id

  if call.data == 'pay_syr':
    user_states[user_id] = 'waiting_syr'
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '📲 **سيريتل كاش:**\nيرجى إرسال رقم عملية التحويل الآن:',
        reply_markup=back_menu(),
    )

  elif call.data == 'pay_sham':
    user_states[user_id] = 'waiting_sham'
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '📲 **شام كاش:**\nيرجى إرسال رقم عملية التحويل الآن:',
        reply_markup=back_menu(),
    )

  elif call.data == 'pay_dollar':
    user_states[user_id] = 'waiting_dollar'
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '📲 **شام كاش دولار ($):**\nيرجى إرسال رقم عملية التحويل الآن:',
        reply_markup=back_menu(),
    )

  elif call.data.startswith('approve_dep_'):
    if user_id != ADMIN_ID:
      bot.answer_callback_query(call.id, 'غير مسموح لك!', show_alert=True)
      return

    target_user_id = int(call.data.split('_')[2])
    add_free_spin_on_deposit(target_user_id)

    bot.answer_callback_query(call.id, '✅ تم قبول الشحن وإضافة اللفة المجانية!')
    bot.edit_message_text(
        call.message.text + '\n\n✅ **الحالة:** تم القبول والاعتماد بنجاح.',
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown',
    )

    try:
      bot.send_message(
          target_user_id,
          '🎉 **مبروك!** تم قبول طلب شحنك بنجاح.\n🎟️ تم منحك **لفة مجانية** في عجلة الفرصة!',
          parse_mode='Markdown',
      )
    except Exception:
      pass


# --- التشغيل المتزامن للخادم والبوت ---
if __name__ == '__main__':
  t = Thread(target=run_web)
  t.start()
  bot.polling(none_stop=True)
        
