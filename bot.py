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

  text = '🎛️ **لوحة التحكم السريعة للأدمن:**\nاضغط على الزر لتغيير حالة الخدمة فوراً بـ "كبسة زر":'

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
# 2. منح لفة مجانية عند قبول الشحن
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
# 3. عجلة الحظ اليومية
# ==========================================
@bot.message_handler(func=lambda m: m.text in ['🎡 عجلة الحظ', '/spin'])
def wheel_intro(message):
  chat_id = message.chat.id
  user_id = message.from_user.id
  today = datetime.now().strftime('%Y-%m-%d')

  spins_data = user_spins.get(user_id, {'date': today, 'spins_left': 0})
  if spins_data['date'] != today:
    spins_data = {'date': today, 'spins_left': 0}
    user_spins[user_id] = spins_data

  spins_left = spins_data['spins_left']

  text = f'🎡 **عجلة الحظ اليومية:**\n\n🔹 عند شحن رصيدك ويوافق عليه الأدمن تحصل على لفة مجانية لليوم بدون أي خصم.\n🎁 الجوائز المتاحة: (حظ أوفر ❌، لفة مجانية 🎟️، أو 50 ليرة سورية 💵 كحد أقصى).\n\n🎟️ **اللفات المتاحة لديك اليوم:** `{spins_left}` لفة.'

  markup = InlineKeyboardMarkup()
  if spins_left > 0:
    markup.add(
        InlineKeyboardButton(
            '🎰 تدوير العجلة مجاناً الآن', callback_data='spin_free'
        )
    )
  else:
    markup.add(
        InlineKeyboardButton(
            '❌ لا توجد لفات مجانية (اشحن رصيدك لتحصيلها)',
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
        '⚠️ ليس لديك لفات مجانية اليوم! اشحن رصيدك للحصول على لفتك.',
        show_alert=True,
    )
    return

  spins_data = user_spins.get(user_id, {'date': today, 'spins_left': 0})

  if spins_data['spins_left'] <= 0:
    bot.answer_callback_query(
        call.id, '⚠️ لقد نفذت لفاتك المجانية اليوم!', show_alert=True
    )
    return

  spins_data['spins_left'] -= 1

  prizes = [
      ('❌ حظ أوفر، خيرها في غيرها!', 55),
      ('🎟️ مبروك! ربحت لفة مجانية إضافية!', 25),
      ('💵 مبروك! ربحت 50 ليرة سورية!', 20),
  ]

  prize_list, weights = zip(*prizes)
  result = random.choices(prize_list, weights=weights, k=1)[0]

  reward_note = ''
  if '50' in result:
    user_balances[user_id] = user_balances.get(user_id, 0) + 50
    reward_note = '\n💰 تمت إضافة 50 ليرة إلى رصيدك!'
  elif 'لفة مجانية' in result:
    spins_data['spins_left'] += 1
    reward_note = '\n🎟️ تمت إضافة اللفة المجانية لرصيدك!'

  remaining = spins_data['spins_left']
  result_text = f'🎡 **نتيجة عجلة الحظ:**\n\n{result}{reward_note}\n\n🎟️ **اللفات المتاحة اليوم:** `{remaining}`'

  markup = InlineKeyboardMarkup()
  if remaining > 0:
    markup.add(
        InlineKeyboardButton('🔄 لفة مجانية أخرى', callback_data='spin_free')
    )
  else:
    markup.add(
        InlineKeyboardButton(
            '⏳ انتهت لفاتك المجانية اليومية', callback_data='no_spins'
        )
    )

  bot.edit_message_text(
      result_text,
      call.message.chat.id,
      call.message.message_id,
      reply_markup=markup,
      parse_mode='Markdown',
  )
  bot.answer_callback_query(call.id, 'تمت العملية بنجاح!')


# ==========================================
# 4. معالجة الأزرار (إنشاء حساب وشحن الرصيد)
# ==========================================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
  if settings['maintenance'] and message.from_user.id != ADMIN_ID:
    bot.reply_to(
        message, '🛠️ البوت متوقف حالياً للصيانة، يرجى العودة لاحقاً.'
    )
    return

  text = message.text
  user_id = message.from_user.id
  username = (
      message.from_user.username
      if message.from_user.username
      else message.from_user.first_name
  )

  if text == '👤 إنشاء حساب':
    user_states[user_id] = 'creating_account'
    bot.reply_to(
        message,
        '👤 **قسم إنشاء الحساب:**\nأهلاً بك! لقد تم تجهيز حسابك بنجاح في النظام. يمكنك الآن شحن رصيدك أو الاستفادة من عجلة الحظ.',
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
          '⚠️ عذراً، جميع وسائل الدفع متوقفة مؤقتاً للصيانة من قبل الأدمن.',
      )
      return

    bot.reply_to(
        message,
        '💳 **اختر وسيلة الدفع المناسبة لشحن رصيدك:**',
        reply_markup=markup,
        parse_mode='Markdown',
    )

  elif user_states.get(user_id) in ['waiting_syr', 'waiting_sham', 'waiting_dollar']:
    method = user_states[user_id]
    method_name = (
        'سيريتل كاش'
        if method == 'waiting_syr'
        else ('شام كاش' if method == 'waiting_sham' else 'شام كاش دولار ($)')
    )

    user_states[user_id] = None

    bot.reply_to(
        message,
        '⏳ **تم إرسال طلب الشحن بنجاح!**\nتم تحويل تفاصيل التحويل إلى الأدمن للمراجعة، وسيتم إضافة الرصيد ومنحك لفة مجانية فور الموافقة.',
        reply_markup=main_menu(),
        parse_mode='Markdown',
    )

    admin_notification = f'🔔 **طلب شحن جديد بانتظار الموافقة!**\n\n👤 المستخدم: @{username} (ID: `{user_id}`)\n💳 الوسيلة: {method_name}\n📝 التفاصيل:\n{text}'

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton(
            '✅ موافق (قبول الشحن)',
            callback_data=f'approve_dep_{user_id}',
        )
    )

    bot.send_message(
        ADMIN_ID,
        admin_notification,
        reply_markup=admin_markup,
        parse_mode='Markdown',
    )

  else:
    bot.reply_to(
        message,
        'أهلاً بك! استخدم الأزرار بالأسفل (إنشاء حساب، شحن الرصيد، عجلة الحظ).',
        reply_markup=main_menu(),
    )


# ==========================================
# 5. استقبال كولباك وسائل الدفع وموافقة الأدمن
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
        '📲 **سيريتل كاش:**\nيرجى إرسال رقم عملية التحويل أو التفاصيل الآن:',
    )

  elif call.data == 'pay_sham':
    user_states[user_id] = 'waiting_sham'
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '📲 **شام كاش:**\nيرجى إرسال رقم عملية التحويل أو التفاصيل الآن:',
    )

  elif call.data == 'pay_dollar':
    user_states[user_id] = 'waiting_dollar'
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        '📲 **شام كاش دولار ($):**\nيرجى إرسال رقم عملية التحويل أو التفاصيل الآن:',
    )

  elif call.data.startswith('approve_dep_'):
    if user_id != ADMIN_ID:
      bot.answer_callback_query(call.id, 'غير مسموح لك!', show_alert=True)
      return

    target_user_id = int(call.data.split('_')[2])

    add_free_spin_on_deposit(target_user_id)

    bot.answer_callback_query(
        call.id, '✅ تمت الموافقة بنجاح وإضافة اللفة المجانية للمستخدم!'
    )
    bot.edit_message_text(
        call.message.text
        + '\n\n✅ **الحالة:** تم قبول الطلب واعتماده من قبل الأدمن.',
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown',
    )

    try:
      bot.send_message(
          target_user_id,
          '🎉 **مبروك!** تم الموافقة على طلب شحن رصيدك من قبل الأدمن بنجاح.\n🎟️ حصلت الآن على **لفة مجانية** في عجلة الحظ اليومية!',
          parse_mode='Markdown',
      )
    except Exception:
      pass


# --- التشغيل المتزامن للخادم والبوت ---
if __name__ == '__main__':
  t = Thread(target=run_web)
  t.start()
  bot.polling(none_stop=True)
      
