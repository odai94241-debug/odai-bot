import telebot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import random
import math
from flask import Flask
import threading

# إعداد خادم الويب المصغر ليبقى البوت مستيقظاً على الاستضافة المجانية
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

TOKEN = "8734379872:AAH9eYSzblCoQec4nLYxwnCgbMcgz2kacY8"
ADMIN_ID = 7753870725
CASHIER = "Odai1@Agents.nps"
SYR = "22178762"
SHAM = "0644a94631c29107483da39ac41cb10b"
CHANNEL = "@YourChannelName"  # ضع قناتك هنا للنشر التلقائي

bot = telebot.TeleBot(TOKEN)
states = {}
user_balances = {}
users_list = set()

@bot.message_handler(commands=['start'])
def start(m):
  
