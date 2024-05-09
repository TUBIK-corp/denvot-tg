import telebot
from telebot import types
from functions import youtube_remix, tts_lip, video_file_remix
from threading import Thread
from queue import Queue
import requests
import tempfile
from tts_with_rvc_with_lipsync import Text2RVCLipSync
import json

with open('secrets.json', 'r') as f:
    secrets = json.load(f)

tg_api = secrets["tg_api"]
bot = telebot.TeleBot(tg_api)

request_queue = Queue()


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Кружок", callback_data="kruzhok")
    btn2 = types.InlineKeyboardButton("AI Cover", callback_data="ai_cover")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Привет я бот, по имени ДенВот! Я умею делать озвучку прямо в телеграмме! Выбор:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "kruzhok":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Наберите текст для кружка!")
        bot.register_next_step_handler(call.message, start_tts_lip)
    elif call.data == "ai_cover":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("Видео", callback_data="video")
        btn2 = types.InlineKeyboardButton("Аудио", callback_data="audio")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите способ создания кавера!", reply_markup=markup)
    elif call.data == "video":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("YouTube", callback_data="youtube")
        btn2 = types.InlineKeyboardButton("Файл", callback_data="file")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите способ озвучки видео:", reply_markup=markup)
    elif call.data == "youtube":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Скиньте ссылку на видео для озвучки!")
        bot.register_next_step_handler(call.message, get_youtube_link)
    elif call.data == "file":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пришлите видеофайл для озвучки!")
        bot.register_next_step_handler(call.message, get_video_file)

def get_video_file(message):
    video_file = message.video
    if (video_file.file_size/1024/1024) > 20:
        bot.send_message(message.chat.id, "Файл занимает слишком много: " + str(round(video_file.file_size/1024/1024, 2)) + " \nMB. Попробуйте сжать его через сервис: https://www.freeconvert.com/video-compressor")
        return
    file_id = video_file.file_id
    file_info = bot.get_file(file_id)
    bot.send_message(message.chat.id, "Введите pitch (целое число):")
    bot.register_next_step_handler(message, start_video_file_remix, file_info.file_path)

def start_video_file_remix(message, file_info):
    pitch = int(message.text)
    url = f"https://api.telegram.org/file/bot{tg_api}/{file_info}"
    response = requests.get(url)
    temp_video_path = tempfile.mktemp(suffix=".mp4")
    with open(temp_video_path, 'wb') as temp_file:
            temp_file.write(response.content)

    request_queue.put((message, 'video-file-remix', temp_video_path, pitch))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

def get_youtube_link(message):
    video_link = message.text
    bot.send_message(message.chat.id, "Введите pitch (целое число):")
    bot.register_next_step_handler(message, start_youtube_remix, video_link)

def start_youtube_remix(message, video_link):
    pitch = int(message.text)
    request_queue.put((message, 'youtube-remix', video_link, pitch))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

def start_tts_lip(message):
    text = message.text
    request_queue.put((message, 'tts-lip', text, 0))
    bot.reply_to(message, "Отправил текст в очередь на озвучку 😉")

def execute_requests():
    while True:
        message, command_type, content, pitch = request_queue.get()
        if command_type == 'youtube-remix':
            try:
                video_location = youtube_remix(content, pitch=pitch)
                bot.reply_to(message, "Ваш файл готов 😊")
                with open(video_location, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        elif command_type == 'video-file-remix':
            try:
                video_location = video_file_remix(content, pitch)
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
