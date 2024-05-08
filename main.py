import telebot
from telebot import types
from functions import youtube_remix, tts_lip
from threading import Thread
from queue import Queue
import config
from tts_with_rvc_with_lipsync import Text2RVCLipSync
import json

with open('secrets.json', 'r') as f:
    secrets = json.load(f)

bot = telebot.TeleBot(secrets["tg_api"])

request_queue = Queue()

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Кружок")
    item2 = types.KeyboardButton("AI Cover")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Привет! Я бот, который делает озвучку прямо в Telegram!", reply_markup=markup)

# Обработчик выбора "Кружок"
@bot.message_handler(func=lambda message: message.text == "Кружок")
def handle_circle(message):
    bot.send_message(message.chat.id, "Введите текст для кружка!")
    bot.register_next_step_handler(message, start_tts_lip)

# Обработчик выбора "AI Cover"
@bot.message_handler(func=lambda message: message.text == "AI Cover")
def handle_ai_cover(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Аудио")
    item2 = types.KeyboardButton("Видео")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Выберите способ создания кавера!", reply_markup=markup)

# Обработчик выбора "Аудио"
@bot.message_handler(func=lambda message: message.text == "Аудио")
def handle_audio(message):
    bot.send_message(message.chat.id, "Отправьте аудио для озвучки!")
    bot.register_next_step_handler(message, start_tts_lip)

# Обработчик выбора "Видео"
@bot.message_handler(func=lambda message: message.text == "Видео")
def handle_video(message):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("YouTube", callback_data='youtube')
    item2 = types.InlineKeyboardButton("Файл", callback_data='file')
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Выберите способ озвучки видео:", reply_markup=markup)

# Обработчик нажатий на кнопки inline
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    if call.data == 'youtube':
        bot.send_message(call.message.chat.id, "Введите ссылку на YouTube видео!")
        bot.register_next_step_handler(call.message, start_youtube_remix)
    elif call.data == 'file':
        bot.send_message(call.message.chat.id, "Отправьте видеофайл для обработки!")
        # Добавьте обработчик для обработки файла

def start_youtube_remix(message):
    print(message.text)
    video_link = message.text
    request_queue.put((message, 'youtube-remix', video_link))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

def start_tts_lip(message):
    text = message.text
    request_queue.put((message, 'tts-lip', text))
    bot.reply_to(message, "Отправил текст в очередь на озвучку 😉")

def execute_requests():
    while True:
        message, command_type, content = request_queue.get()
        if command_type == 'youtube-remix':
            try:
                video_location = youtube_remix(content)
                bot.reply_to(message, "Ваш файл готов 😊")
                with open(video_location, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        elif command_type == 'tts-lip':
            try:
                video_location = tts_lip(content)
                bot.reply_to(message, "Ваш файл готов 😊")
                with open(video_location, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        request_queue.task_done()

def main():

    try:
        Thread(target=execute_requests, daemon=True).start()
        print("DenVot-TG launched!")
        bot.infinity_polling()
    except:
        print("ok")
        bot.infinity_polling()

if __name__ == '__main__':
    main()
