# app.py - Media Web 6 AI Backend (FIXED Session Error)
# ============================================================
# MEDIA WEB 6 AI - Backend
# Flask + Grok AI, Voice (gTTS), Tasks, Settings & Memory
# ============================================================

import os
import sys
import json
import time
import uuid
import threading
import secrets
import logging
import random
import re
from datetime import datetime

# ============================================================
# FORCE LOAD .env FILE
# ============================================================
from dotenv import load_dotenv

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

# Load .env file with override
load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# GROK AI BRAIN (xAI)
# ============================================================

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-1")

print("=" * 60)
print("🔑 GROK API KEY STATUS:")
print(f"   API Key present: {'Yes' if GROK_API_KEY else 'No'}")
print(f"   API Key length: {len(GROK_API_KEY) if GROK_API_KEY else 0}")
print(f"   Model: {GROK_MODEL}")
print("=" * 60)

_grok_client = None
if GROK_API_KEY:
    try:
        import httpx
        from openai import OpenAI
        
        http_client = httpx.Client(
            timeout=60.0,
            follow_redirects=True,
        )
        
        _grok_client = OpenAI(
            api_key=GROK_API_KEY,
            base_url="https://api.x.ai/v1",
            http_client=http_client,
        )
        
        logger.info("✅ Grok AI brain enabled successfully")
        print("✅ Grok AI client initialized successfully!")
        
        try:
            test_response = _grok_client.chat.completions.create(
                model=GROK_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            print("✅ Grok API test successful!")
        except Exception as test_e:
            print(f"⚠️ Grok API test failed (but client is initialized): {test_e}")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Grok client: {e}")
        print(f"❌ Failed to initialize Grok client: {e}")
        _grok_client = None
else:
    logger.warning("⚠️ No GROK_API_KEY set — falling back to canned responses.")
    print("❌ No GROK_API_KEY found in .env file")


def grok_reply(message: str, history: list, user_name: str, assistant_name: str = "Media Web 6 AI"):
    """Ask Grok for a reply. Returns None if the LLM is unavailable/fails."""
    if not _grok_client:
        print("⚠️ Grok client not available, using fallback")
        return None

    system_prompt = (
        f"You are {assistant_name}, a friendly, professional AI assistant for Media Web 6 Services. "
        "Media Web 6 Services is a premier digital solutions company offering web development, "
        "mobile apps, UI/UX design, digital marketing, SEO, and e-commerce solutions. "
        "Keep replies concise, professional, and helpful (2-4 sentences). "
        "Be warm and conversational. "
        + (f"The user's name is {user_name}; address them by name occasionally. " if user_name else "")
        + "If asked about services, mention web development, mobile apps, digital marketing, "
        "UI/UX design, SEO, and e-commerce. Provide pricing as per requirements. "
        "Company contact: Phone: +91 999 427 2027, Email: info@mediaweb6.com, Website: www.mediaweb6.com"
    )

    api_messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-6:]:
        api_messages.append({"role": "user", "content": turn["user"]})
        api_messages.append({"role": "assistant", "content": turn["assistant"]})
    api_messages.append({"role": "user", "content": message})

    try:
        print(f"🤖 Sending request to Grok API...")
        response = _grok_client.chat.completions.create(
            model=GROK_MODEL,
            messages=api_messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        print(f"✅ Grok response received: {reply[:50]}...")
        return reply or None
    except Exception as e:
        logger.error(f"❌ Grok API error: {e}")
        print(f"❌ Grok API error: {e}")
        return None


# ============================================================
# JSON FILE STORAGE
# ============================================================

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
_store_lock = threading.Lock()


def _path(name: str) -> str:
    return os.path.join(DATA_DIR, name)


def _read_json(name: str, default):
    try:
        path = _path(name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else default
        return default
    except Exception as e:
        logger.warning(f"Could not read {name}: {e}")
        return default


def _write_json(name: str, data):
    try:
        with open(_path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Could not write {name}: {e}")


DEFAULT_SETTINGS = {
    "assistant_name": "Media Web 6 AI",
    "voice_language": "en",
    "voice_enabled": True,
    "theme": "light",
}


# ============================================================
# MEDIA WEB 6 AI VOICE BOT
# ============================================================

class MediaWeb6AIBot:
    def __init__(self, name="Media Web 6 AI", speak_language="en"):
        self.name = name
        self.speak_language = speak_language
        self.user_name = None
        self.conversation_history = []
        self.greeting_played = False

        self.audio_dir = "audio_files"
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        self.responses = {
            "greeting": [
                "Welcome to Media Web 6 Services! How can I help you today?",
                "Hello! I'm your AI assistant at Media Web 6. What can I do for you?",
                "Hi there! Ready to assist you with our digital solutions.",
            ],
            "farewell": [
                "Thank you for visiting Media Web 6! Have a great day!",
                "Goodbye! Feel free to reach out anytime.",
            ],
            "thanks": [
                "You're welcome! Always happy to help!",
                "My pleasure! Let me know if you need anything else.",
            ],
            "default": [
                "How can I assist you with our services today?",
                "I'd love to help! What would you like to know?",
                "That's great! Tell me more about what you're looking for.",
            ],
            "help": [
                f"I'm {self.name}, the AI assistant for Media Web 6 Services. "
                "I can help with web development, mobile apps, digital marketing, "
                "UI/UX design, SEO, and e-commerce solutions.",
                "Ask me about our services, pricing, portfolio, or anything else!",
            ],
        }

    def generate_audio(self, text, lang=None):
        """Generate audio from text using gTTS"""
        lang = lang or self.speak_language
        if not text:
            return None
        try:
            filename = f"speech_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.audio_dir, filename)

            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filepath)

            logger.info(f"🎵 Audio saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

    def get_auto_greeting(self):
        """Generate a welcome greeting"""
        if self.user_name:
            greetings = [
                f"Welcome back, {self.user_name}! I'm {self.name} from Media Web 6 Services. How can I help you today?",
                f"Hi {self.user_name}! Great to see you again. What can we do for you at Media Web 6?",
                f"Hello {self.user_name}! Media Web 6 AI is ready to assist you.",
            ]
            return random.choice(greetings)
        greetings = [
            f"Welcome to Media Web 6 Services! I'm {self.name}. How can I help you today?",
            f"Hello! I'm {self.name}, your AI assistant at Media Web 6. What can I do for you?",
            f"Hi there! I'm the Media Web 6 AI assistant. Ready to help with your digital needs!",
        ]
        return random.choice(greetings)

    def _quick_intent(self, message: str, msg_lower: str):
        """Handle quick intents for common commands"""
        # Name capture
        name_match = re.search(r"(?:my name is|call me|i am|i'm)\s+([A-Za-z][A-Za-z\s]{1,20})", message, re.IGNORECASE)
        if name_match and not self.user_name:
            self.user_name = name_match.group(1).strip().title()
            return f"Nice to meet you, {self.user_name}! How can Media Web 6 assist you today?"

        # Services
        if any(word in msg_lower for word in ["services", "offer", "provide", "do you do"]):
            return "Media Web 6 Services offers:\n• Web Development\n• Mobile App Development\n• UI/UX Design\n• Digital Marketing\n• SEO Services\n• E-commerce Solutions\n\nWhich service interests you?"

        # Web Development
        if any(word in msg_lower for word in ["web", "website", "site", "development"]):
            return "Our web development services include custom websites, e-commerce platforms, CMS development (WordPress, Shopify), and responsive design. Would you like to see our portfolio?"

        # Mobile Apps
        if any(word in msg_lower for word in ["app", "mobile", "android", "ios"]):
            return "We specialize in mobile app development for iOS and Android using React Native and Flutter. We handle UI/UX design, development, and app store optimization."

        # Digital Marketing
        if any(word in msg_lower for word in ["marketing", "seo", "social", "ads", "ppc"]):
            return "Our digital marketing services include SEO, social media marketing, Google Ads, content marketing, and email marketing. We can help grow your online presence!"

        # Pricing
        if any(word in msg_lower for word in ["price", "cost", "pricing", "quote", "budget"]):
            return "We offer customized pricing based on your project requirements. Contact us at +91 999 427 2027 for a free consultation and detailed quote."

        # Portfolio
        if any(word in msg_lower for word in ["portfolio", "work", "projects", "examples"]):
            return "We've delivered 200+ successful projects across various industries including corporate websites, e-commerce platforms, mobile apps, and custom solutions. Would you like to see specific examples?"

        # Contact
        if any(word in msg_lower for word in ["contact", "phone", "email", "reach"]):
            return "You can reach Media Web 6 Services at:\n• Phone: +91 999 427 2027\n• WhatsApp: +91 999 427 2027\n• Email: info@mediaweb6.com\n• Website: www.mediaweb6.com"

        return None

    def generate_response(self, message):
        """Generate a response using Grok AI or fallback"""
        if not message:
            return None

        msg_lower = message.lower().strip()

        # Check quick intents first
        quick = self._quick_intent(message, msg_lower)
        if quick:
            return quick

        # Try Grok AI
        grok_text = grok_reply(message, self.conversation_history, self.user_name, self.name)
        if grok_text:
            return grok_text

        # Fallback responses
        if any(word in msg_lower for word in ["hello", "hi", "hey", "how are you"]):
            if self.user_name:
                return f"Hello {self.user_name}! How can Media Web 6 assist you today?"
            return random.choice(self.responses["greeting"])

        if any(word in msg_lower for word in ["help", "what can you do"]):
            return random.choice(self.responses["help"])

        if any(word in msg_lower for word in ["thanks", "thank you"]):
            return random.choice(self.responses["thanks"])

        if any(word in msg_lower for word in ["bye", "goodbye", "see you"]):
            return random.choice(self.responses["farewell"])

        if "time" in msg_lower:
            return f"The current time is {datetime.now().strftime('%I:%M %p')}"

        if self.user_name:
            return f"{self.user_name}, {random.choice(self.responses['default'])}"
        return random.choice(self.responses["default"])


# ============================================================
# FLASK APPLICATION - FIXED SESSION
# ============================================================

from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from flask_session import Session
from gtts import gTTS

app = Flask(__name__, static_folder='static', static_url_path='')

# Generate a secure secret key if not provided
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# ========== FIXED SESSION CONFIGURATION ==========
# Use simple session without complex cookie handling
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = False  # Disabled to avoid cookie issues
app.config['SESSION_KEY_PREFIX'] = 'mediaweb6_'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
app.config['SESSION_COOKIE_NAME'] = 'mediaweb6_session'  # Custom cookie name
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Create session directory
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize session
Session(app)

# ========== CORS CONFIGURATION ==========
CORS(app,
     supports_credentials=True,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000', 
              'http://localhost:3000', 'http://localhost:5173', 
              'http://localhost:3001', 'http://localhost:3002', 
              'http://192.168.1.17:5000', '*'],
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
     expose_headers=['Content-Type', 'Content-Disposition'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Global state
user_bots = {}
user_locks = {}

SETTINGS = _read_json("settings.json", DEFAULT_SETTINGS.copy()) or DEFAULT_SETTINGS.copy()
TASKS = _read_json("tasks.json", {})


def get_user_bot(user_id):
    if user_id not in user_bots:
        user_bots[user_id] = MediaWeb6AIBot(
            name=SETTINGS.get("assistant_name", "Media Web 6 AI"),
            speak_language=SETTINGS.get("voice_language", "en"),
        )
        user_locks[user_id] = threading.Lock()
        logger.info(f"🆕 New bot created for user: {user_id[:8]}")
    return user_bots[user_id]


def get_or_create_user_id():
    user_id = request.args.get('user_id')
    if not user_id and request.is_json:
        user_id = request.get_json(silent=True).get('user_id') if request.get_json(silent=True) else None
    if not user_id:
        user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
        session.permanent = True
        logger.info(f"🆕 New user session created: {user_id[:8]}")
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


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_users': len(user_bots),
        'grok_enabled': _grok_client is not None,
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/greeting', methods=['GET'])
def get_greeting():
    try:
        user_id = get_or_create_user_id()
        bot = get_user_bot(user_id)

        greeting = bot.get_auto_greeting()
        audio_file = bot.generate_audio(greeting, bot.speak_language)
        audio_url = f"/api/audio/{audio_file}" if audio_file else None

        return jsonify({
            'success': True,
            'user_id': user_id,
            'greeting': greeting,
            'audio_url': audio_url,
            'language': bot.speak_language,
            'user_name': bot.user_name,
        })
    except Exception as e:
        logger.error(f"❌ Greeting error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_id = data.get('user_id') or session.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
            session['user_id'] = user_id
            session.permanent = True

        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': 'Empty message'}), 400

        bot = get_user_bot(user_id)

        with user_locks[user_id]:
            response = bot.generate_response(message)
            audio_file = bot.generate_audio(response, bot.speak_language)
            audio_url = f"/api/audio/{audio_file}" if audio_file else None

            bot.conversation_history.append({
                'user': message,
                'assistant': response,
                'timestamp': datetime.now().isoformat(),
            })

            return jsonify({
                'success': True,
                'user_id': user_id,
                'response': response,
                'audio_url': audio_url,
                'language': bot.speak_language,
                'user_name': bot.user_name,
                'history_count': len(bot.conversation_history),
            })
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    try:
        if not filename.endswith('.mp3'):
            return jsonify({'error': 'Invalid file'}), 400

        filepath = None
        for user_id, bot in user_bots.items():
            audio_path = os.path.join(bot.audio_dir, filename)
            if os.path.exists(audio_path):
                filepath = audio_path
                break

        if not filepath:
            audio_path = os.path.join("audio_files", filename)
            if os.path.exists(audio_path):
                filepath = audio_path

        if filepath and os.path.exists(filepath):
            response = send_file(filepath, mimetype='audio/mpeg', as_attachment=False, download_name=filename)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"❌ Audio serve error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        if user_id and user_id in user_bots:
            bot = user_bots[user_id]
            return jsonify({
                'status': 'ready',
                'language': bot.speak_language,
                'name': bot.name,
                'user_name': bot.user_name,
                'history_count': len(bot.conversation_history),
                'active_users': len(user_bots),
                'grok_enabled': _grok_client is not None,
            })
        return jsonify({
            'status': 'ready',
            'language': SETTINGS.get('voice_language', 'en'),
            'name': SETTINGS.get('assistant_name', 'Media Web 6 AI'),
            'user_name': None,
            'history_count': 0,
            'active_users': len(user_bots),
            'grok_enabled': _grok_client is not None,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/user-info', methods=['GET'])
def user_info():
    try:
        user_id = get_or_create_user_id()
        is_active = user_id in user_bots
        user_name = None
        history_count = 0
        if is_active:
            bot = user_bots[user_id]
            user_name = bot.user_name
            history_count = len(bot.conversation_history)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_active': is_active,
            'user_name': user_name,
            'history_count': history_count,
            'active_users': len(user_bots),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    return jsonify({'success': True, 'tasks': list(TASKS.values())})


@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'title is required'}), 400

    task_id = uuid.uuid4().hex[:8]
    task = {
        'id': task_id,
        'title': title,
        'time': data.get('time', ''),
        'priority': data.get('priority', 'medium'),
        'completed': False,
        'created_at': datetime.now().isoformat(),
    }
    with _store_lock:
        TASKS[task_id] = task
        _write_json("tasks.json", TASKS)
    return jsonify({'success': True, 'task': task})


@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    if task_id not in TASKS:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    data = request.get_json(silent=True) or {}
    with _store_lock:
        TASKS[task_id].update({k: v for k, v in data.items() if k in ('title', 'time', 'priority', 'completed')})
        _write_json("tasks.json", TASKS)
    return jsonify({'success': True, 'task': TASKS[task_id]})


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    with _store_lock:
        existed = TASKS.pop(task_id, None) is not None
        _write_json("tasks.json", TASKS)
    return jsonify({'success': existed})


@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({'success': True, 'settings': SETTINGS})


@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json(silent=True) or {}
    with _store_lock:
        for key in ('assistant_name', 'voice_language', 'voice_enabled', 'theme'):
            if key in data:
                SETTINGS[key] = data[key]
        _write_json("settings.json", SETTINGS)
    return jsonify({'success': True, 'settings': SETTINGS})


@app.route('/api/memory', methods=['GET'])
def get_memory():
    user_id = request.args.get('user_id') or session.get('user_id')
    bot = user_bots.get(user_id)
    return jsonify({
        'success': True,
        'user_name': bot.user_name if bot else None,
        'conversation_history': bot.conversation_history if bot else [],
        'grok_enabled': _grok_client is not None,
    })


@app.route('/api/memory', methods=['DELETE'])
def clear_memory():
    user_id = request.args.get('user_id') or session.get('user_id')
    bot = user_bots.get(user_id)
    if bot:
        bot.conversation_history = []
        bot.user_name = None
    return jsonify({'success': True})


# ============================================================
# CLEANUP
# ============================================================

def cleanup_audio_files():
    try:
        for user_id, bot in user_bots.items():
            if hasattr(bot, 'audio_dir') and os.path.exists(bot.audio_dir):
                for file in os.listdir(bot.audio_dir):
                    if file.endswith('.mp3'):
                        filepath = os.path.join(bot.audio_dir, file)
                        try:
                            mtime = os.path.getmtime(filepath)
                            if time.time() - mtime > 300:
                                os.remove(filepath)
                                logger.info(f"🧹 Cleaned audio: {file}")
                        except Exception:
                            pass
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")


def cleanup_sessions():
    while True:
        time.sleep(300)
        cleanup_audio_files()


cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    if not os.path.exists('static'):
        os.makedirs('static')
        with open('static/index.html', 'w') as f:
            f.write('''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Media Web 6 AI</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        color: #fff;
                    }
                    .container {
                        text-align: center;
                        padding: 40px;
                        background: rgba(255,255,255,0.1);
                        backdrop-filter: blur(10px);
                        border-radius: 20px;
                        border: 1px solid rgba(255,255,255,0.2);
                        max-width: 500px;
                        width: 90%;
                    }
                    .logo { font-size: 80px; margin-bottom: 20px; }
                    h1 {
                        font-size: 36px;
                        margin-bottom: 10px;
                        background: linear-gradient(to right, #fff, #e0e0ff);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    p { font-size: 18px; opacity: 0.9; margin-bottom: 20px; line-height: 1.6; }
                    .status {
                        display: inline-block;
                        padding: 8px 20px;
                        background: rgba(0,255,0,0.2);
                        border-radius: 20px;
                        font-size: 14px;
                        border: 1px solid rgba(0,255,0,0.3);
                    }
                    .dot {
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        background: #00ff00;
                        border-radius: 50%;
                        margin-right: 8px;
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.3; }
                    }
                    .footer { margin-top: 30px; font-size: 14px; opacity: 0.7; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">🤖</div>
                    <h1>Media Web 6 AI</h1>
                    <p>Your AI assistant for digital solutions</p>
                    <div class="status">
                        <span class="dot"></span>
                        Backend is running
                    </div>
                    <div class="footer">© 2026 Media Web 6 Services</div>
                </div>
            </body>
            </html>
            ''')

    if not os.path.exists('audio_files'):
        os.makedirs('audio_files')

    print("=" * 60)
    print("🤖  MEDIA WEB 6 AI - Backend")
    print("=" * 60)
    print(f"📍 Server: http://localhost:{port}")
    print(f"🧠 AI Brain: {'Grok AI (ACTIVE)' if _grok_client else 'DISABLED - Check GROK_API_KEY'}")
    print(f"🔊 Voice: English")
    print("=" * 60)
    print("\n📋 API Endpoints:")
    print(f"  • Health:  http://localhost:{port}/api/health")
    print(f"  • Greeting: http://localhost:{port}/api/greeting")
    print(f"  • Chat:    http://localhost:{port}/api/chat (POST)")
    print("=" * 60)
    print("\n🚀 Server starting...")

    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)