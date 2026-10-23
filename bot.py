import os
import time
import random
import requests
import telebot
from flask import Flask, request

# =========================================================
# ⚙️ الإعدادات والبيانات الخاصة بك والربط مع iChancy
# =========================================================
API_TOKEN = '8734379872:AAFpX_ZqN0_mdJhZW2gj1yiNYJDIAVUqp18' 
AGENT_ID = "2826132-odai1@agents.nps"
ICHANCY_API_URL = "https://agents.ichancy.com/api/create_player"

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
ADMIN_IDS = set()            # لتخزين أيدي الأدمن لتلقي الطلبات
REGISTERED_USERNAMES = set()
TEMP_USER_DATA = {}
TEMP_DEPOSIT_DATA = {}
PENDING_DEPOSITS = {}        # لتخزين طلبات الشحن المعلقة
ADMIN_STATES = {}            # لحالة الأدمن (مثل إرسال سبب الرفض)

def check_maintenance(message):
    if SETTINGS["maintenance"] and message.chat.id not in ADMIN_IDS:
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
    ADMIN_IDS.add(message.chat.id)
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

# =========================================================
# معالجة قبول أو رفض طلبات الشحن من الأدمن
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("dep_acc_") or call.data.startswith("dep_rej_"))
def handle_deposit_review(call):
    data_parts = call.data.split("_")
    action = data_parts[1] # acc or rej
    req_id = data_parts[2]
    
    if req_id not in PENDING_DEPOSITS:
        bot.answer_callback_query(call.id, "⚠️ هذا الطلب غير موجود أو تم معالجته مسبقاً.")
        return
        
    dep_info = PENDING_DEPOSITS[req_id]
    user_id = dep_info["user_id"]
    amount = float(dep_info["amount"])
    
    # تطبيق البونص إذا كان مفعّلاً
    final_amount = amount
    if SETTINGS["deposit_bonus_active"]:
        final_amount += amount * (SETTINGS["deposit_bonus_percentage"] / 100)
        
    if action == "acc":
        # تحديث رصيد المستخدم محلياً
        USER_BALANCES[user_id] = USER_BALANCES.get(user_id, 0) + final_amount
        
        bot.answer_callback_query(call.id, "✅ تمت الموافقة وإضافة الرصيد بنجاح!")
        bot.edit_message_text(
            call.message.text + f"\n\n🟢 **الحالة:** تم قبول الطلب وإضافة {final_amount} ليرة.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        
        # إشعار الزبون
        bot.send_message(
            user_id,
            f"🎉 **مبروك! تم قبول عملية الشحن الخاصة بك وإضافة الرصيد بنجاح.**\n\n"
            f"💰 المبلغ المضاف: `{final_amount}` ليرة جديدة",
            parse_mode="Markdown"
        )
        del PENDING_DEPOSITS[req_id]
        
    elif action == "rej":
        bot.answer_callback_query(call.id, "❌ يرجى إرسال سبب الرفض أو الخطأ للزبون:")
        ADMIN_STATES[call.message.chat.id] = {"target_user": user_id, "req_id": req_id, "msg_id": call.message.message_id}
        msg = bot.send_message(call.message.chat.id, "✍️ أرسل الآن سبب فشل العملية (مثال: رقم العملية خاطئ، أو القيمة غير مطابقة):")
        bot.register_next_step_handler(msg, process_admin_rejection_reason)

def process_admin_rejection_reason(message):
    admin_id = message.chat.id
    if admin_id not in ADMIN_STATES:
        return
        
    reason = message.text.strip()
    state = ADMIN_STATES[admin_id]
    user_id = state["target_user"]
    req_id = state["req_id"]
    
    # إشعار الزبون بالسبب
    bot.send_message(
        user_id,
        f"❌ **عذراً، فشلت عملية الشحن الخاصة بك!**\n\n"
        f"⚠️ **السبب:** {reason}\n\n"
        f"يرجى التأكد من البيانات وإعادة المحاولة أو التواصل مع الدعم الفني.",
        parse_mode="Markdown"
    )
    
    bot.send_message(admin_id, "✅ تم إرسال سبب الرفض إلى الزبون بنجاح.")
    
    if req_id in PENDING_DEPOSITS:
        del PENDING_DEPOSITS[req_id]
    del ADMIN_STATES[admin_id]

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

# =========================================================
# 👤 إنشاء حساب تفاعلي
# =========================================================
@bot.message_handler(func=lambda message: message.text == "👤 إنشاء حساب")
def ask_username(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    msg = bot.send_message(message.chat.id, "👤 أرسل **اسم المستخدم (Username)** الذي ترغب به:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_custom_username)

def process_custom_username(message):
    if message.text in ["👤 إنشاء حساب", "💳 شحن الرصيد", "💸 سحب الرصيد", "🎰 عجلة الفرصة", "📊 حسابي والمعلومات", "📜 شروط الاستخدام", "🎧 خدمة الدعم"]:
        bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=main_keyboard())
        return
    
    username = message.text.strip()
    if len(username) < 3:
        msg = bot.send_message(message.chat.id, "❌ اسم المستخدم قصير جداً (3 أحرف على الأقل). أعد المحاولة:")
        bot.register_next_step_handler(msg, process_custom_username)
        return

    if username in REGISTERED_USERNAMES:
        msg = bot.send_message(message.chat.id, "⚠️ **اسم المستخدم هذا مستخدم مسبقاً!**\nالرجاء إرسال اسم مستخدم آخر:")
        bot.register_next_step_handler(msg, process_custom_username)
        return

    TEMP_USER_DATA[message.chat.id] = {"username": username}

    msg = bot.send_message(message.chat.id, "🔑 ممتاز. الآن أرسل **كلمة السر (Password)** التي ترغب بها لحسابك:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_custom_password)

def process_custom_password(message):
    if message.text in ["👤 إنشاء حساب", "💳 شحن الرصيد", "💸 سحب الرصيد", "🎰 عجلة الفرصة", "📊 حسابي والمعلومات", "📜 شروط الاستخدام", "🎧 خدمة الدعم"]:
        bot.send_message(message.chat.id, "تم الإلغاء.", reply_markup=main_keyboard())
        return

    password = message.text.strip()
    if len(password) < 4:
        msg = bot.send_message(message.chat.id, "❌ كلمة السر قصيرة جداً (4 خانات على الأقل). أعد المحاولة:")
        bot.register_next_step_handler(msg, process_custom_password)
        return

    user_id = message.chat.id
    username = TEMP_USER_DATA.get(user_id, {}).get("username")

    REGISTERED_USERNAMES.add(username)

    try:
        payload = {
            "agent_id": AGENT_ID,
            "username": username,
            "password": password,
            "telegram_id": user_id
        }
        requests.post(ICHANCY_API_URL, json=payload, timeout=10)
    except Exception:
        pass

    text = (
        f"🎉 **تم إنشاء حسابك وربطه بوكالتنا بنجاح!**\n\n"
        f"🔗 **رابط الدخول:** https://ichancy.com\n"
        f"👤 **اسم المستخدم:** `{username}`\n"
        f"🔑 **كلمة السر:** `{password}`"
    )
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_keyboard())

    if user_id in TEMP_USER_DATA:
        del TEMP_USER_DATA[user_id]

# =========================================================
# 🎰 عجلة الفرصة التفاعلية (Web App)
# =========================================================
@bot.message_handler(func=lambda message: message.text == "🎰 عجلة الفرصة")
def spin_wheel_webapp(message):
    USER_IDS.add(message.chat.id)
    if check_maintenance(message): return
    
    render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
    wheel_url = f"{render_url}/wheel"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎡 اضغط لفتح العجلة وتدويرها", web_app=telebot.types.WebAppInfo(url=wheel_url)))
    
    bot.send_message(
        message.chat.id, 
        "🎰 **عجلة الفرصة الكبرى**\n\nاضغط على الزر أدناه لفتح العجلة وتدويرها أمام عينك لتربح الجوائز!", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@app.route('/wheel')
def wheel_page():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>عجلة الفرصة</title>
        <style>
            body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 20px; }
            h2 { color: #facc15; }
            .wheel-container { position: relative; width: 300px; height: 300px; margin: 30px auto; }
            canvas { width: 100%; height: 100%; border-radius: 50%; border: 6px solid #facc15; transition: transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99); }
            .pin { position: absolute; top: -15px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 12px solid transparent; border-right: 12px solid transparent; border-top: 24px solid #ef4444; z-index: 10; }
            button { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; padding: 12px 35px; font-size: 18px; font-weight: bold; border-radius: 30px; cursor: pointer; margin-top: 20px; }
            #result { margin-top: 20px; font-size: 20px; font-weight: bold; color: #4ade80; }
        </style>
    </head>
    <body>
        <h2>⭐ عجلة الفرصة الكبرى ⭐</h2>
        <div class="wheel-container">
            <div class="pin"></div>
            <canvas id="wheelCanvas" width="300" height="300"></canvas>
        </div>
        <button id="spinBtn" onclick="spinWheel()">دَوْر الآن 🎯</button>
        <div id="result"></div>
        <script>
            const canvas = document.getElementById('wheelCanvas');
            const ctx = canvas.getContext('2d');
            const sectors = [
                {label: "5,000", color: "#3b82f6"}, {label: "10,000", color: "#1d4ed8"},
                {label: "25,000", color: "#4f46e5"}, {label: "50,000", color: "#2563eb"},
                {label: "100,000", color: "#312e81"}, {label: "حظ أوفر", color: "#dc2626"},
                {label: "لفة مجانية", color: "#9333ea"}, {label: "1,000,000", color: "#1e40af"}
            ];
            const arc = Math.PI / (sectors.length / 2);
            let angle = 0, isSpinning = false;
            function drawWheel() {
                const center = canvas.width / 2;
                sectors.forEach((sector, i) => {
                    const sa = i * arc, ea = (i + 1) * arc;
                    ctx.beginPath(); ctx.moveTo(center, center); ctx.arc(center, center, center, sa, ea);
                    ctx.fillStyle = sector.color; ctx.fill(); ctx.save();
                    ctx.translate(center, center); ctx.rotate(sa + arc / 2);
                    ctx.textAlign = "right"; ctx.fillStyle = "#fff"; ctx.font = "bold 14px Tahoma";
                    ctx.fillText(sector.label, center - 25, 10); ctx.restore();
                });
            }
            drawWheel();
            function spinWheel() {
                if (isSpinning) return;
                isSpinning = true; document.getElementById('spinBtn').disabled = true;
                angle += Math.floor(1000 + Math.random() * 2000);
                canvas.style.transform = `rotate(${angle}deg)`;
                setTimeout(() => {
                    isSpinning = false;
                    const prize = sectors[Math.floor(sectors.length - ((angle % 360) / (360 / sectors.length))) % sectors.length].label;
                    document.getElementById('result').innerText = `🎉 مبروك! ربحت: ${prize} ليرة`;
                }, 4000);
            }
        </script>
    </body>
    </html>
    """

# =========================================================
# 💳 نظام شحن الرصيد التفاعلي (مراجعة الأدمن)
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

@bot.callback_query_handler(func=lambda 
