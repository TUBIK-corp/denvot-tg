import telebot
from telebot import types
from functions import youtube_remix, tts_lip, video_file_remix, audio_file_remix
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

use_chunks = False

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Кружок", callback_data="kruzhok")
    btn2 = types.InlineKeyboardButton("AI Cover", callback_data="ai_cover")
    btn3 = types.InlineKeyboardButton("Наложение голоса", callback_data="voiceover")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привет я бот, по имени ДенВот! Я умею делать озвучку прямо в телеграмме! Выбор:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "kruzhok":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Наберите текст для кружка!")
        bot.register_next_step_handler(call.message, start_tts_lip)
    elif call.data == "ai_cover":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("Видео", callback_data="video_cover")
        btn2 = types.InlineKeyboardButton("Аудио", callback_data="audio_cover")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите способ создания кавера!", reply_markup=markup)
    elif call.data == "voiceover":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("Видео", callback_data="video_voiceover")
        btn2 = types.InlineKeyboardButton("Аудио", callback_data="audio_voiceover")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите, что нужно переозвучить!", reply_markup=markup)
    elif call.data == "video_cover":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("YouTube", callback_data="youtube_cover")
        btn2 = types.InlineKeyboardButton("Файл", callback_data="file_cover")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите способ озвучки видео:", reply_markup=markup)
    elif call.data == "video_voiceover":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("YouTube", callback_data="youtube_voiceover")
        btn2 = types.InlineKeyboardButton("Файл", callback_data="file_voiceover")
        markup.add(btn1, btn2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите способ переозвучки видео:", reply_markup=markup)
    elif call.data == "youtube_cover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Скиньте ссылку на видео для озвучки!")
        bot.register_next_step_handler(call.message, get_youtube_link, True, use_chunks)
    elif call.data == "file_cover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пришлите видеофайл для озвучки!")
        bot.register_next_step_handler(call.message, get_video_file, True, use_chunks)
    elif call.data == "youtube_voiceover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Скиньте ссылку на видео для озвучки!")
        bot.register_next_step_handler(call.message, get_youtube_link, False, use_chunks)
    elif call.data == "file_voiceover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пришлите видеофайл для озвучки!")
        bot.register_next_step_handler(call.message, get_video_file, False, use_chunks)
    elif call.data == "audio_cover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пришлите аудиофайл для озвучки!")
        bot.register_next_step_handler(call.message, get_audio_file, True, use_chunks)
    elif call.data == "audio_voiceover":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пришлите аудиофайл для озвучки!")
        bot.register_next_step_handler(call.message, get_audio_file, False, use_chunks)

def get_audio_file(message, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start()
        return
    audio_file = message.audio
    if (audio_file.file_size/1024/1024) > 20:
        bot.send_message(message.chat.id, "Файл занимает слишком много: " + str(round(audio_file.file_size/1024/1024, 2)) + " \nMB. Попробуйте сжать его через сервис: https://cdkm.com/ru/compress-audio")
        return
    file_id = audio_file.file_id
    file_info = bot.get_file(file_id)
    bot.send_message(message.chat.id, "Введите pitch (целое число):")
    bot.register_next_step_handler(message, start_audio_file, file_info.file_path, use_separator, video_chunks)

def get_video_file(message, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start()
        return
    video_file = message.video
    if (video_file.file_size/1024/1024) > 20:
        bot.send_message(message.chat.id, "Файл занимает слишком много: " + str(round(video_file.file_size/1024/1024, 2)) + " \nMB. Попробуйте сжать его через сервис: https://www.freeconvert.com/video-compressor")
        return
    file_id = video_file.file_id
    file_info = bot.get_file(file_id)
    bot.send_message(message.chat.id, "Введите pitch (целое число):")
    bot.register_next_step_handler(message, start_video_file, file_info.file_path, use_separator, video_chunks)


def start_audio_file(message, file_info, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start(message)
        return
    pitch = int(message.text)
    url = f"https://api.telegram.org/file/bot{tg_api}/{file_info}"
    response = requests.get(url)
    temp_video_path = tempfile.mktemp(suffix=".wav")
    with open(temp_video_path, 'wb') as temp_file:
            temp_file.write(response.content)

    request_queue.put((message, 'audio-file-remix', temp_video_path, pitch, use_separator, video_chunks))
    bot.reply_to(message, "Отправил аудио в очередь на озвучку 😉")

def start_video_file(message, file_info, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start(message)
        return
    pitch = int(message.text)
    url = f"https://api.telegram.org/file/bot{tg_api}/{file_info}"
    response = requests.get(url)
    temp_video_path = tempfile.mktemp(suffix=".mp4")
    with open(temp_video_path, 'wb') as temp_file:
            temp_file.write(response.content)

    request_queue.put((message, 'video-file-remix', temp_video_path, pitch, use_separator, video_chunks))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

def get_youtube_link(message, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start(message)
        return
    video_link = message.text
    bot.send_message(message.chat.id, "Введите pitch (целое число):")
    bot.register_next_step_handler(message, start_youtube_remix, video_link, use_separator, video_chunks)

def start_youtube_remix(message, video_link, use_separator=True, video_chunks=False):
    if message.text == "/start":
        start(message)
        return
    pitch = int(message.text)
    request_queue.put((message, 'youtube-remix', video_link, pitch, use_separator, video_chunks))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

def start_tts_lip(message):
    if message.text == "/start":
        start(message)
        return
    text = message.text
    request_queue.put((message, 'tts-lip', text, 6, False))
    bot.reply_to(message, "Отправил текст в очередь на озвучку 😉")

def execute_requests():
    while True:
        message, command_type, content, pitch, use_separator, chunks = request_queue.get()
        if command_type == 'youtube-remix':
            try:
                video_location = youtube_remix(content, pitch=pitch, use_separator=use_separator, video_chunks=chunks)
                with open(video_location, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        elif command_type == 'video-file-remix':
            try:
                video_location = video_file_remix(content, pitch=pitch, use_separator=use_separator, video_chunks=chunks)
                with open(video_location, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        elif command_type == 'audio-file-remix':
            try:
                audio_location = audio_file_remix(content, pitch=pitch, use_separator=use_separator, audio_chunks=chunks)
                with open(audio_location, 'rb') as audio_file:
                    bot.send_audio(message.chat.id, audio_file)
            except Exception as e:
                bot.reply_to(message, f"Ошибка: {e}")
        elif command_type == 'tts-lip':
            try:
                video_location = tts_lip(content)
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
