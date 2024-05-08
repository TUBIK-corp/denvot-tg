import telebot
from functions import youtube_remix, tts_lip
from threading import Thread
from queue import Queue
import config
from tts_with_rvc_with_lipsync import Text2RVCLipSync


bot = telebot.TeleBot(config.tg_api)

request_queue = Queue()

@bot.message_handler(commands=['youtube-remix'])
def start_youtube_remix(message):
    video_link = message.text.split(' ', 1)[1]
    request_queue.put((message, 'youtube-remix', video_link))
    bot.reply_to(message, "Отправил видео в очередь на озвучку 😉")

@bot.message_handler(commands=['tts-lip'])
def start_tts_lip(message):
    text = message.text.split(' ', 1)[1]
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
    Thread(target=execute_requests, daemon=True).start()
    bot.polling()

if __name__ == '__main__':
    main()
