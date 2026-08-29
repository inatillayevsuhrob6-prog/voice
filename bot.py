import os
import io
import json
import base64
import threading
import requests
from flask import Flask, request, jsonify, render_template, send_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ============================================
# SOZLAMALAR
# ============================================

TELEGRAM_BOT_TOKEN = "8863844713:AAE5ldHvA9V2AduZH7V3qiJZrV4fKGchT2I"
ELEVENLABS_API_KEY = "sk_0bdcd2aa15990def6eaa38e8785caab0edd94d3d526c6ac7" # O'zingizniki qo'ying!
FLASK_PORT = 5000
WEB_APP_URL = "https://your-domain.com" 

app = Flask(__name__, template_folder='.', static_folder='.')

def fix_uzbek_pronunciation(text):
    replacements = { "axmoq": "ahmoq", "Sevinch": "Sevinch" }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-voice', methods=['POST'])
def generate_voice():
    try:
        data = request.json
        text = data.get('text', '').strip()
        voice_id = data.get('voice', 'EXAVITQu4vr4xnSDxMaL') 
        
        if not text:
            return jsonify({'error': 'Matn kiritilmagan'}), 400
        
        optimized_text = fix_uzbek_pronunciation(text)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        payload = {
            "text": optimized_text,
            "model_id": "eleven_multilingual_v2", 
            "voice_settings": { "stability": 0.3, "similarity_boost": 0.8 }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print("Multilingual xatosi, Flash modelga o'tilmoqda...")
            payload["model_id"] = "eleven_flash_v2_5"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = response.json().get('detail', 'Noma\'lum xatolik')
                return jsonify({'error': f'ElevenLabs xatosi: {error_msg}'}), 500
            
        return send_file(
            io.BytesIO(response.content),
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='voice.mp3'
        )
    
    except Exception as e:
        print(f"Xatolik: {e}")
        return jsonify({'error': str(e)}), 500

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎙️ Ilovani ochish", web_app={"url": WEB_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Assalomu alaykum! Voice Generator Bot.", reply_markup=reply_markup)

# ============================================
# YANGI QISM: TELEGRAMGA AUDIO YUBORISH
# ============================================

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Web App dan kelgan ma'lumotni qabul qilish"""
    try:
        data_str = update.effective_message.web_app_data.data
        if not data_str:
            return
            
        data = json.loads(data_str)
        
        # Faqat 'send_audio' harakatini bajarish
        if data.get('action') == 'send_audio':
            audio_base64 = data.get('audio')
            filename = data.get('filename', 'voice.mp3')
            
            if audio_base64:
                # Base64 ni bytes ga aylantirish
                audio_bytes = base64.b64decode(audio_base64)
                
                # Foydalanuvchiga audio yuborish
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=io.BytesIO(audio_bytes),
                    caption="🎙️ Siz yaratgan ovoz:",
                    title="Voice Generator",
                    performer="Voice Bot"
                )
                
                # Tasdiqlash xabari
                await update.effective_message.reply_text("✅ Ovoz muvaffaqiyatli yuborildi!")
            else:
                await update.effective_message.reply_text("❌ Xatolik: Audio ma'lumoti topilmadi.")
                
    except Exception as e:
        print(f"Web App data xatosi: {e}")
        await update.effective_message.reply_text(f"❌ Yuborishda xatolik: {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"✅ Flask server http://0.0.0.0:{FLASK_PORT} da ishga tushdi")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    # Web App dan kelgan ma'lumotni eshitish uchun handler
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()