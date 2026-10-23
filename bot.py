from datetime import datetime
import random
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# توكن البوت ومعرف الأدمن الخاص بك (مضبوط بالكامل)
TOKEN = '8734379872:AAH9eYSzblCoQec4nLYxwnCgbMcgz2kacY8'
ADMIN_ID = 7753870725

bot = telebot.TeleBot(TOKEN)

# إعدادات البوت ولوحة التحكم (وضع الصيانة ووسائل الدفع: سيريتل، شام كاش، وشام كاش دولار)
settings = {
    'maintenance': False,  # False يعني يعمل، True يعني صيانة
    'syr_cash': True,  # سيريتل كاش
    'sham_cash': True,  # شام كاش (بالعملة الجديدة)
    'sham_dollar': True,  # شام كاش دولار ($)
}

# أرصدة المستخدمين واللفات المجانية
user_balances = {ADMIN_ID: 5000}  # رصيد تجريبي للأدمن
user_spins = {}  # لتخزين اللفات المجانية اليومية


# ==========================================
# 1. لوحة تحكم الأدمن (عبر أمر /admin في تليجرام)
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
# 2. دالة منح لفة مجانية عند إتمام الشحن
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
# 3. عجلة الحظ (بالعملة الجديدة - بدون خصم رصيد)
# ==========================================
@bot.message_handler(func=lambda m: m.text in ['🎡 عجلة الحظ', '/spin', 'عجلة الحظ'])
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
      '🎡 **عجلة الحظ اليومية (بالعملة الجديدة):**\n\n🔹 **النظام:** عند شحن رصيدك'
      ' تحصل على لفة مجانية لليوم فقط بدون أي خصم من رصيدك.\n🎁 **الجوائز المتاحة'
      ' فقط:** (حظ أوفر ❌، لفة مجانية 🎟️، أو 50 ليرة سورية 💵 كحد'
      f' أقصى).\n\n🎟️ **اللفات المتاحة لديك اليوم:** `{spins_left}` لفة.'
  )

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

  # الاحتمالات وضبط الجوائز بالعملة الجديدة (أقصى ربح 50 ليرة)
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
    reward_note = '\n💰 تمت إضافة 50 ليرة إلى رصيدك الأساسي!'
  elif 'لفة مجانية' in result:
    spins_data['spins_left'] += 1
    reward_note = '\n🎟️ تمت إضافة اللفة المجانية لرصيدك!'

  remaining = spins_data['spins_left']
  result_text = (
      f'🎡 **نتيجة عجلة الحظ:**\n\n{result}{reward_note}\n\n🎟️ **اللفات'
      f' المتبقية لديك اليوم:** `{remaining}`'
  )

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
# 4. استقبال الرسائل، الصيانة، ووسائل الدفع
# ==========================================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
  if settings['maintenance'] and message.from_user.id != ADMIN_ID:
    bot.reply_to(
        message,
        '🛠️ البوت متوقف حالياً للصيانة وتحديث النظام، يرجى العودة لاحقاً.',
    )
    return

  text = message.text

  if text == 'شحن عبر سيريتل كاش':
    if not settings['syr_cash']:
      bot.reply_to(
          message,
          '⚠️ عذراً، الشحن عبر سيريتل كاش متوقف مؤقتاً بسبب أعمال الصيانة.',
      )
      return
    bot.reply_to(
        message,
        '💳 أرسل تفاصيل ورقم تحويل سيريتل كاش (بالقيمة الجديدة بعد حذف'
        ' الصفرين)...',
    )

  elif text == 'شحن عبر شام كاش':
    if not settings['sham_cash']:
      bot.reply_to(
          message, '⚠️ عذراً، الشحن عبر شام كاش متوقف مؤقتاً حالياً للصيانة.'
      )
      return
    bot.reply_to(
        message,
        '💳 أرسل تفاصيل ورقم تحويل شام كاش (بالقيمة الجديدة بعد حذف الصفرين)...',
    )

  elif text == 'شحن عبر شام كاش دولار':
    if not settings['sham_dollar']:
      bot.reply_to(
          message,
          '⚠️ عذراً، الشحن عبر شام كاش دولار متوقف مؤقتاً حالياً للصيانة.',
      )
      return
    bot.reply_to(
        message, '💳 أرسل تفاصيل ورقم تحويل شام كاش دولار ($)...'
    )

  else:
    bot.reply_to(
        message,
        'أهلاً بك في البوت! استخدم الأزرار أو القائمة الرئيسية أو اكتب "عجلة'
        ' الحظ".',
    )


# تشغيل البوت باستمرار
bot.polling(none_stop=True)
    
