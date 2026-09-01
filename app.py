# app.py - Media Web 6 AI Backend (CLEAN - No httpx, No OpenAI)
# ============================================================
# MEDIA WEB 6 AI - Backend
# Flask + Grok AI (via requests), Voice (gTTS)
# ============================================================

import os
import json
import time
import uuid
import threading
import secrets
import logging
import random
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from flask_session import Session
from gtts import gTTS
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# GROK AI - DIRECT API CALLS (No external AI libraries)
# ============================================================

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-1")

print("=" * 60)
print("🔑 GROK API STATUS:")
print(f"   API Key: {'✅ Present' if GROK_API_KEY else '❌ Missing'}")
print(f"   Length: {len(GROK_API_KEY) if GROK_API_KEY else 0}")
print(f"   Model: {GROK_MODEL}")
print("=" * 60)

def call_grok_api(messages, max_tokens=300, temperature=0.7):
    """Direct Grok API call using requests - NO httpx"""
    if not GROK_API_KEY:
        return None
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROK_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        print(f"🤖 Calling Grok API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Grok response: {reply[:50]}...")
            return reply
        else:
            print(f"⚠️ Grok API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Grok API Exception: {e}")
        return None

# Test the API
if GROK_API_KEY:
    test_result = call_grok_api([{"role": "user", "content": "Hello"}], max_tokens=5)
    if test_result:
        print("✅ Grok API is working!")
    else:
        print("⚠️ Grok API test failed - check your API key")
else:
    print("❌ No GROK_API_KEY found - using fallback responses")

def grok_reply(message, history, user_name, assistant_name="Media Web 6 AI"):
    """Get reply from Grok or fallback"""
    if not GROK_API_KEY:
        return None
    
    system_prompt = (
        f"You are {assistant_name}, a friendly, professional AI assistant for Media Web 6 Services. "
        "Media Web 6 Services offers web development, mobile apps, UI/UX design, "
        "digital marketing, SEO, and e-commerce solutions. "
        "Keep replies concise (2-4 sentences). Be warm and conversational. "
        + (f"The user's name is {user_name}. " if user_name else "")
        + "Company: +91 999 427 2027, info@mediaweb6.com, www.mediaweb6.com"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-6:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": message})
    
    return call_grok_api(messages)


# ============================================================
# JSON STORAGE
# ============================================================

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
_store_lock = threading.Lock()

def _read_json(name, default):
    try:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default
    except:
        return default

def _write_json(name, data):
    try:
        with open(os.path.join(DATA_DIR, name), 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Write error: {e}")

DEFAULT_SETTINGS = {
    "assistant_name": "Media Web 6 AI",
    "voice_language": "en",
    "voice_enabled": True,
    "theme": "light",
}


# ============================================================
# VOICE BOT
# ============================================================

class MediaWeb6AIBot:
    def __init__(self, name="Media Web 6 AI", speak_language="en"):
        self.name = name
        self.speak_language = speak_language
        self.user_name = None
        self.conversation_history = []
        self.audio_dir = "audio_files"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.responses = {
            "greeting": [
                "Welcome to Media Web 6 Services! How can I help you today?",
                "Hello! I'm your AI assistant at Media Web 6.",
                "Hi there! Ready to assist you with our digital solutions.",
            ],
            "farewell": ["Thank you! Have a great day!", "Goodbye! Feel free to reach out anytime."],
            "thanks": ["You're welcome! Always happy to help!", "My pleasure!"],
            "default": ["How can I assist you today?", "I'd love to help! What would you like to know?"],
            "help": [
                f"I'm {self.name}, the AI assistant for Media Web 6 Services. "
                "I can help with web development, mobile apps, digital marketing, "
                "UI/UX design, SEO, and e-commerce solutions."
            ],
        }

    def generate_audio(self, text, lang=None):
        lang = lang or self.speak_language
        if not text:
            return None
        try:
            filename = f"speech_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filepath)
            return filename
        except Exception as e:
            print(f"Audio error: {e}")
            return None

    def get_auto_greeting(self):
        if self.user_name:
            return random.choice([
                f"Welcome back, {self.user_name}! How can I help you today?",
                f"Hi {self.user_name}! Great to see you again!",
            ])
        return random.choice(self.responses["greeting"])

    def _quick_intent(self, message, msg_lower):
        if any(w in msg_lower for w in ["services", "offer", "provide"]):
            return "Media Web 6 offers: Web Development, Mobile Apps, UI/UX Design, Digital Marketing, SEO, and E-commerce."
        if any(w in msg_lower for w in ["web", "website"]):
            return "We build custom websites, e-commerce platforms, and CMS solutions."
        if any(w in msg_lower for w in ["app", "mobile"]):
            return "We develop iOS and Android apps using React Native and Flutter."
        if any(w in msg_lower for w in ["marketing", "seo"]):
            return "We offer SEO, social media marketing, Google Ads, and content marketing."
        if any(w in msg_lower for w in ["price", "cost", "pricing"]):
            return "We offer customized pricing. Contact us at +91 999 427 2027 for a quote."
        if any(w in msg_lower for w in ["contact", "phone", "email"]):
            return "Contact us: +91 999 427 2027, info@mediaweb6.com, www.mediaweb6.com"
        return None

    def generate_response(self, message):
        if not message:
            return None
        msg_lower = message.lower().strip()
        
        quick = self._quick_intent(message, msg_lower)
        if quick:
            return quick
        
        grok_response = grok_reply(message, self.conversation_history, self.user_name, self.name)
        if grok_response:
            return grok_response
        
        if any(w in msg_lower for w in ["hello", "hi", "hey"]):
            return f"Hello! How can Media Web 6 assist you today?"
        if any(w in msg_lower for w in ["help"]):
            return random.choice(self.responses["help"])
        if any(w in msg_lower for w in ["thanks", "thank"]):
            return random.choice(self.responses["thanks"])
        if any(w in msg_lower for w in ["bye", "goodbye"]):
            return random.choice(self.responses["farewell"])
        if "time" in msg_lower:
            return f"The current time is {datetime.now().strftime('%I:%M %p')}"
        
        return random.choice(self.responses["default"])


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = False
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
Session(app)

# CORS
ALLOWED_ORIGINS = [
    'http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174',
    'http://127.0.0.1:3000', 'http://127.0.0.1:5173',
    'https://mediaweb6-ai.onrender.com',
    'https://mediaweb6.com', 'http://mediaweb6.com',
    'https://www.mediaweb6.com', 'http://www.mediaweb6.com',
]

CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS,
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

def cors_preflight():
    response = jsonify({'success': True})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# State
user_bots = {}
user_locks = {}
SETTINGS = _read_json("settings.json", DEFAULT_SETTINGS)
TASKS = _read_json("tasks.json", {})

def get_user_bot(user_id):
    if user_id not in user_bots:
        user_bots[user_id] = MediaWeb6AIBot(
            name=SETTINGS.get("assistant_name", "Media Web 6 AI"),
            speak_language=SETTINGS.get("voice_language", "en"),
        )
        user_locks[user_id] = threading.Lock()
    return user_bots[user_id]

def get_or_create_user_id():
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    return user_id


# ============================================================
# ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def root():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return cors_preflight()
    return jsonify({
        'status': 'healthy',
        'active_users': len(user_bots),
        'grok_enabled': bool(GROK_API_KEY),
        'timestamp': datetime.now().isoformat(),
    })

@app.route('/api/greeting', methods=['GET', 'OPTIONS'])
def get_greeting():
    if request.method == 'OPTIONS':
        return cors_preflight()
    try:
        user_id = get_or_create_user_id()
        bot = get_user_bot(user_id)
        greeting = bot.get_auto_greeting()
        audio_file = bot.generate_audio(greeting)
        return jsonify({
            'success': True,
            'user_id': user_id,
            'greeting': greeting,
            'audio_url': f"/api/audio/{audio_file}" if audio_file else None,
            'user_name': bot.user_name,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return cors_preflight()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
        
        user_id = data.get('user_id') or get_or_create_user_id()
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Empty message'}), 400
        
        bot = get_user_bot(user_id)
        with user_locks[user_id]:
            response = bot.generate_response(message)
            audio_file = bot.generate_audio(response)
            bot.conversation_history.append({
                'user': message,
                'assistant': response,
                'timestamp': datetime.now().isoformat(),
            })
            return jsonify({
                'success': True,
                'user_id': user_id,
                'response': response,
                'audio_url': f"/api/audio/{audio_file}" if audio_file else None,
                'user_name': bot.user_name,
                'history_count': len(bot.conversation_history),
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET', 'OPTIONS'])
def serve_audio(filename):
    if request.method == 'OPTIONS':
        return cors_preflight()
    try:
        filepath = os.path.join('audio_files', filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg')
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-info', methods=['GET', 'OPTIONS'])
def user_info():
    if request.method == 'OPTIONS':
        return cors_preflight()
    try:
        user_id = get_or_create_user_id()
        bot = user_bots.get(user_id)
        return jsonify({
            'success': True,
            'user_id': user_id,
            'user_name': bot.user_name if bot else None,
            'active_users': len(user_bots),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("=" * 60)
    print("🤖  MEDIA WEB 6 AI")
    print("=" * 60)
    print(f"📍 Server: http://0.0.0.0:{port}")
    print(f"🧠 Grok: {'✅ Active' if GROK_API_KEY else '❌ Disabled'}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)