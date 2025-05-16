import os
import requests
import telebot
import tempfile
from deep_translator import GoogleTranslator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENSUBTITLES_API_KEY = os.getenv("OPENSUBTITLES_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def search_subtitle(query):
    headers = {
        "Api-Key": OPENSUBTITLES_API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"https://api.opensubtitles.com/api/v1/subtitles?query={query}&languages=en",
        headers=headers,
    )
    data = response.json()
    if data.get("data"):
        file_id = data["data"][0]["attributes"]["files"][0]["file_id"]
        return file_id
    return None

def download_subtitle(file_id):
    headers = {"Api-Key": OPENSUBTITLES_API_KEY}
    response = requests.get(
        f"https://api.opensubtitles.com/api/v1/download", headers=headers, json={"file_id": file_id}
    )
    link = response.json()["link"]
    subtitle_data = requests.get(link).text
    return subtitle_data

def translate_subtitle(srt_text, target_lang="es"):
    translated = []
    for line in srt_text.splitlines():
        if line.strip().isdigit() or "-->" in line or line.strip() == "":
            translated.append(line)
        else:
            translated.append(GoogleTranslator(source='auto', target=target_lang).translate(line))
    return "\n".join(translated)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Envía el nombre de una película o serie para obtener los subtítulos traducidos.")

@bot.message_handler(func=lambda msg: True)
def handle_query(message):
    query = message.text
    bot.send_message(message.chat.id, f"Buscando subtítulos para: {query}")
    file_id = search_subtitle(query)
    if not file_id:
        bot.send_message(message.chat.id, "No se encontraron subtítulos.")
        return
    srt_text = download_subtitle(file_id)
    bot.send_message(message.chat.id, "Traduciendo subtítulo...")
    translated = translate_subtitle(srt_text)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp:
        temp.write(translated.encode("utf-8"))
        temp_path = temp.name

    with open(temp_path, "rb") as f:
        bot.send_document(message.chat.id, f)

    os.remove(temp_path)

bot.polling()