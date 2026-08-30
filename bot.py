import os, io, json, base64, asyncio, requests, threading
from flask import Flask, request, jsonify, render_template, send_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# SOZLAMALAR (Render Environment Variables dan olinadi)
TOKEN = os.environ.get("BOT_TOKEN", "8863844713:AAE5ldHvA9V2AduZH7V3qiJZrV4fKGchT2I")
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_3b151807bc0c25aa79731fa312361d7b14f0a47b7c5f2b68") 
WEB_URL = os.environ.get("WEB_APP_URL", "https://sizning-render-manzilingiz.onrender.com")

app = Flask(__name__, template_folder='.', static_folder='.')


@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/generate-voice', methods=['POST'])
def gen_voice():
    try:
        d = request.json; txt = d.get('text','').strip(); vid = d.get('voice', 'EXAVITQu4vr4xnSDxMaL')
        if not txt: return jsonify({'error':'Matn yo\'q'}), 400
        
        h = {"Accept":"audio/mpeg","Content-Type":"application/json","xi-api-key":ELEVEN_KEY}
        p = {"text":fix_text(txt), "model_id":"eleven_multilingual_v2", "voice_settings":{"stability":0.3,"similarity_boost":0.8}}
        
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}", json=p, headers=h, timeout=30)
        if r.status_code != 200:
            p["model_id"] = "eleven_flash_v2_5"
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}", json=p, headers=h, timeout=30)
            
        if r.status_code == 200:
            return send_file(io.BytesIO(r.content), mimetype='audio/mpeg', as_attachment=True, download_name='v.mp3')
        return jsonify({'error':'API xato'}), 500
    except Exception as e: return jsonify({'error':str(e)}), 500

# BOT LOGIKASI
async def start_cmd(u, c):
    kb = [[InlineKeyboardButton("🎙️ Ilovani ochish", web_app={"url": WEB_URL})]]
    await u.message.reply_text("Salom! Ovoz yaratish uchun tugmani bosing.", reply_markup=InlineKeyboardMarkup(kb))

async def handle_data(u, c):
    try:
        data_str = u.effective_message.web_app_data.data
        if not data_str: return
        d = json.loads(data_str)
        if d.get('action') == 'send_audio' and d.get('audio'):
            ab = base64.b64decode(d['audio'])
            await c.bot.send_audio(u.effective_chat.id, io.BytesIO(ab), caption="🎙️ Tayyor ovoz:", title="Voice Bot")
    except Exception as e: print(f"Bot xato: {e}")

# Webhook marshruti
@app.route('/webhook', methods=['POST'])
def wh():
    try:
        upd = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(upd))
        return 'OK'
    except Exception as e:
        print(f"Webhook xato: {e}")
        return 'ERROR', 500

# GLOBAL APPLICATION
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start_cmd))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_data))

# RENDER UCHUN MAXSUS ISHGA TUSHIRISH
def run_bot_async():
    """Botni alohida thread da ishga tushirish"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def setup():
        # Webhook ni o'rnatish
        await application.bot.set_webhook(f"{WEB_URL}/webhook")
        print("✅ Webhook o'rnatildi!")
        
    loop.run_until_complete(setup())
    # Botni doimiy kutish rejimida ushlab turish
    loop.run_forever()

if __name__ == '__main__':
    # 1. Botni fon rejimida ishga tushirish
    bot_thread = threading.Thread(target=run_bot_async, daemon=True)
    bot_thread.start()
    
    # 2. Flask serverini ishga tushirish (Render PORT muhit o'zgaruvchisidan oladi)
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server {port} portda ishga tushdi...")
    app.run(host='0.0.0.0', port=port)