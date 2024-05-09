from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip, afx
from tts_with_rvc_with_lipsync import Text2RVCLipSync
import json
import tempfile
import os
from pytube import YouTube
from audio import AudioSeparator
from pytube.exceptions import RegexMatchError

# Загрузка ключа API и создание экземпляра Text2RVCLipSync
with open('secrets.json', 'r') as f:
    secrets = json.load(f)

api_key = secrets["lip_api_key"]
rvc_path = "src/rvclib"
model_path = "models/denvot.pth"

file_path = 'images/big_pups.png'
rvc_pitch = 6

text2lip = Text2RVCLipSync(lip_api_key=api_key, rvc_path=rvc_path, model_path=model_path, lip_crop=True)

separator = AudioSeparator(model_name="UVR-MDX-NET-Inst_HQ_3")

def video_file_remix(video_path, pitch=rvc_pitch):
    return voice_video(video_path, pitch=pitch)


def youtube_remix(video_url, pitch=rvc_pitch):
    global separator
    video_path = tempfile.mktemp(suffix=".mp4")
    folder, file_name = os.path.split(video_path)


    yt = YouTube(video_url)

    try:
        streams = yt.streams.filter(progressive=True)

        medium_streams = streams.filter(resolution='720p')

        if not medium_streams:
            print("No medium quality stream available. Downloading the highest resolution.")
            video = yt.streams.get_highest_resolution()
        else:
            video = medium_streams.first()
    except RegexMatchError:
        print("RegexMatchError occurred. Trying alternative stream.")
        video = yt.streams.first()
        
    video.download(output_path=folder, filename=file_name)
    print("Downloaded video: ", video_path)
    return voice_video(video_path, pitch=pitch)


def voice_video(video_path, pitch, video_chunks=False, vocal_volume=3):
    video_clip = VideoFileClip(video_path)
    audio = video_clip.audio
    audio_path = tempfile.mktemp(suffix=".mp3")
    audio.write_audiofile(audio_path, fps=44100)

    primary_stem_path, secondary_stem_path = separator(audio_path)

    vocal_audio = primary_stem_path
    instrumental_audio = secondary_stem_path

    

    if video_chunks is True:
        audio = AudioFileClip(vocal_audio)

        chunk_duration = 30
        audio_chunks = []
        total_duration = audio.duration
        start_time = 0

        while start_time < total_duration:
            end_time = min(start_time + chunk_duration, total_duration)
            chunk = audio.subclip(start_time, end_time)
            chunk_path = tempfile.mktemp(suffix=".mp3")
            chunk.write_audiofile(chunk_path, fps=44100)
            audio_chunks.append(chunk_path)
            start_time += chunk_duration

        processed_sound_paths = []


        for chunk_path in audio_chunks:
            sound_path = text2lip.rvc.speech(pitch=pitch, input_path=chunk_path, output_directory=tempfile.gettempdir())
            processed_sound_paths.append(sound_path)
            os.remove(chunk_path)

        final_sound = concatenate_audioclips([AudioFileClip(sound_path) for sound_path in processed_sound_paths])

        final_path = tempfile.mktemp(suffix=".wav")
        final_sound.write_audiofile(final_path, fps=44100)

        audio = AudioFileClip(final_path).volumex(vocal_volume)
    else:
        audio = AudioFileClip(text2lip.rvc.speech(pitch=pitch, input_path=vocal_audio, output_directory=tempfile.gettempdir())).volumex(vocal_volume)

    instrumental_audio_clip = AudioFileClip(instrumental_audio)

    merged_audio = CompositeAudioClip([audio, instrumental_audio_clip])

    final_clip = video_clip.set_audio(merged_audio)

    output_video_path = tempfile.mktemp(suffix=".mp4")
    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=30)

    return output_video_path

def tts_lip(text):
    return text2lip(text=text, file_path=file_path, rvc_pitch=rvc_pitch)