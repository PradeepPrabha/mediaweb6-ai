# app.py - Media Web 6 AI Backend (FULLY UPDATED WITH ALL COMPANY DATA)
# ============================================================
# MEDIA WEB 6 AI - Backend
# Flask + Grok AI (via requests), Voice (gTTS)
# Fully trained with Media Web 6 Services complete data
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
# GROK AI - DIRECT API CALLS
# ============================================================

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-1")

print("=" * 60)
print("🔑 GROK API STATUS:")
print(f"   API Key: {'✅ Present' if GROK_API_KEY else '❌ Missing'}")
print(f"   Length: {len(GROK_API_KEY) if GROK_API_KEY else 0}")
print(f"   Model: {GROK_MODEL}")
print("=" * 60)

def call_grok_api(messages, max_tokens=600, temperature=0.7):
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
            print(f"   Response: {response.text[:200]}")
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

# ============================================================
# MEDIA WEB 6 - COMPLETE KNOWLEDGE BASE
# ============================================================

MEDIA_WEB_6_KNOWLEDGE = {
    # Company Information
    "company": {
        "name": "Media Web 6 Services",
        "full_name": "Media Web 6 Services",
        "tagline": "Transforming Business Through Digital Innovation",
        "description": "We blend creativity, innovation, and technology to craft digital solutions that elevate brands and unlock new growth opportunities.",
        "founded": "2018",
        "mission": """To craft high-quality digital solutions that business can trust and rely on.
To simplify complex challenges through intelligent, modern technology.
To ensure every solution reflects precision, performance, and long-term value.
To serve clients with transparency, accountability, and professionalism.
To deliver results that create measurable impact and continuous growth.""",
        "vision": """To become a globally trusted partner for digital innovation.
To set industry standards through quality, reliability, and user-focused design.
To empower brands to evolve with confidence in a digital-first world.
To lead with innovation and build technology that stands the test of time.
To shape a future where companies grow stronger through smart digital solutions.""",
        "values": "Innovation, Quality, Customer Success, Integrity, Transparency, Professionalism"
    },
    
    # Contact Information
    "contact": {
        "email": "mediawebsix@gmail.com",
        "phone_primary": "+91 99942 72027",
        "phone_secondary": "0422 429 2027",
        "whatsapp": "+91 99942 72027",
        "website": "www.mediaweb6.com",
        "address": "Coimbatore, Tamil Nadu",
        "working_hours": "Mon - Fri, 9AM - 7PM"
    },
    
    # Services
    "services": {
        "web_development": {
            "name": "Web Development",
            "description": "Custom website development, e-commerce platforms, CMS solutions, and web applications",
            "technologies": ["React", "Next.js", "Node.js", "PHP", "WordPress", "Magento", "Shopify", "HTML5", "CSS3", "JavaScript"],
            "types": ["Corporate Websites", "E-commerce Stores", "Web Portals", "PWA Applications", "Landing Pages"]
        },
        "seo_optimization": {
            "name": "SEO Optimization",
            "description": "Search engine optimization to improve organic rankings and visibility",
            "services": ["On-Page SEO", "Off-Page SEO", "Technical SEO", "Local SEO", "E-commerce SEO", "Content Strategy"]
        },
        "graphic_design": {
            "name": "Graphic Design",
            "description": "Creative visual design solutions for branding and marketing",
            "services": ["Logo Design", "Brand Identity", "Social Media Graphics", "Print Materials", "Packaging Design", "UI Design"]
        },
        "mobile_application": {
            "name": "Mobile Application",
            "description": "Native and cross-platform mobile applications for iOS and Android",
            "technologies": ["React Native", "Flutter", "Swift", "Kotlin", "Java"],
            "types": ["Business Apps", "E-commerce Apps", "Social Apps", "Healthcare Apps", "Educational Apps"]
        },
        "digital_marketing": {
            "name": "Digital Marketing",
            "description": "Comprehensive digital marketing strategies to boost online presence and conversions",
            "services": ["SEO", "Social Media Marketing", "Content Marketing", "Google Ads", "Email Marketing", "Analytics", "SMM"]
        },
        "desktop_application": {
            "name": "Desktop Application",
            "description": "Custom desktop applications for Windows, Mac, and Linux",
            "technologies": ["Electron", "Java", "Python", "C#", ".NET"],
            "types": ["Business Software", "Enterprise Applications", "Utility Tools", "Management Systems"]
        }
    },
    
    # Portfolio Categories
    "portfolio": {
        "e_commerce": "E-Commerce Solutions - Online stores, shopping platforms, payment integrations",
        "advertising": "Advertising - Digital ad campaigns, promotional content, banner designs",
        "printing_branding": "Printing & Branding - Print materials, brand identity, packaging",
        "event_management": "Event Management - Event websites, registration systems, virtual events",
        "digital_signage": "Digital Signage & Advertising - Digital displays, kiosks, interactive screens",
        "news_media": "News & Media - News portals, media platforms, content management",
        "directory_platform": "Directory Platform - Business directories, listing platforms, review systems",
        "export_manufacturing": "Export & Manufacturing - Supply chain solutions, inventory management, export platforms",
        "ngo_nonprofit": "NGO & Non-Profit - Donation platforms, awareness sites, community portals"
    },
    
    # Achievements
    "achievements": {
        "projects": "25+ Projects Successfully delivered solutions",
        "quality": "100% Quality Focused on performance & reliability",
        "delivery": "Fast Delivery Quick turnaround with top quality"
    },
    
    # Pricing
    "pricing": {
        "web_development": "Starting from ₹25,000",
        "mobile_apps": "Starting from ₹50,000",
        "digital_marketing": "Starting from ₹15,000/month",
        "seo": "Starting from ₹10,000/month",
        "graphic_design": "Starting from ₹5,000",
        "desktop_applications": "Starting from ₹30,000"
    },
    
    # FAQs
    "faqs": [
        {"question": "What services do you offer?", 
         "answer": "We offer Web Development, SEO Optimization, Graphic Design, Mobile Application Development, Digital Marketing, and Desktop Application Development."},
        {"question": "How much does a website cost?", 
         "answer": "Our web development starts from ₹25,000, depending on complexity and features."},
        {"question": "Do you offer mobile app development?", 
         "answer": "Yes, we develop native and cross-platform mobile apps for iOS and Android using React Native and Flutter."},
        {"question": "What is your mission?", 
         "answer": "Our mission is to craft high-quality digital solutions that businesses can trust and rely on. We simplify complex challenges through intelligent, modern technology."},
        {"question": "What is your vision?", 
         "answer": "To become a globally trusted partner for digital innovation and set industry standards through quality, reliability, and user-focused design."},
        {"question": "Do you provide SEO services?", 
         "answer": "Yes, we offer comprehensive SEO services including on-page, off-page, technical SEO, local SEO, and e-commerce SEO."},
        {"question": "Where are you located?", 
         "answer": "We are located in Coimbatore, Tamil Nadu. We serve clients globally."},
        {"question": "What are your working hours?", 
         "answer": "We are available Monday to Friday, 9AM to 7PM."},
        {"question": "How can I contact you?", 
         "answer": "You can call us at +91 99942 72027 or 0422 429 2027, email us at mediawebsix@gmail.com, or visit our website www.mediaweb6.com"},
        {"question": "What types of projects have you worked on?", 
         "answer": "We've worked on E-Commerce, Advertising, Printing & Branding, Event Management, Digital Signage, News & Media, Directory Platforms, Export & Manufacturing, and NGO & Non-Profit projects."},
        {"question": "What technologies do you use?", 
         "answer": "We use modern technologies including React, Next.js, Node.js, PHP, WordPress, React Native, Flutter, and more."}
    ]
}

# ============================================================
# ENHANCED SYSTEM PROMPT - FULLY TRAINED
# ============================================================

def get_system_prompt(assistant_name="Media Web 6 AI", user_name=None):
    """Get the enhanced system prompt with complete company knowledge"""
    
    knowledge_base = f"""
============================================================
🏢 COMPANY INFORMATION
============================================================
Company Name: {MEDIA_WEB_6_KNOWLEDGE['company']['name']}
Tagline: {MEDIA_WEB_6_KNOWLEDGE['company']['tagline']}
Description: {MEDIA_WEB_6_KNOWLEDGE['company']['description']}
Founded: {MEDIA_WEB_6_KNOWLEDGE['company']['founded']}

🎯 MISSION:
{MEDIA_WEB_6_KNOWLEDGE['company']['mission']}

👁️ VISION:
{MEDIA_WEB_6_KNOWLEDGE['company']['vision']}

Values: {MEDIA_WEB_6_KNOWLEDGE['company']['values']}

============================================================
📞 CONTACT INFORMATION
============================================================
Email: {MEDIA_WEB_6_KNOWLEDGE['contact']['email']}
Phone: {MEDIA_WEB_6_KNOWLEDGE['contact']['phone_primary']}
Alternate Phone: {MEDIA_WEB_6_KNOWLEDGE['contact']['phone_secondary']}
WhatsApp: {MEDIA_WEB_6_KNOWLEDGE['contact']['whatsapp']}
Website: {MEDIA_WEB_6_KNOWLEDGE['contact']['website']}
Location: {MEDIA_WEB_6_KNOWLEDGE['contact']['address']}
Working Hours: {MEDIA_WEB_6_KNOWLEDGE['contact']['working_hours']}

============================================================
💼 SERVICES OFFERED
============================================================

1. 🌐 WEB DEVELOPMENT
   {MEDIA_WEB_6_KNOWLEDGE['services']['web_development']['description']}
   Technologies: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['web_development']['technologies'])}
   Types: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['web_development']['types'])}

2. 🔍 SEO OPTIMIZATION
   {MEDIA_WEB_6_KNOWLEDGE['services']['seo_optimization']['description']}
   Services: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['seo_optimization']['services'])}

3. 🎨 GRAPHIC DESIGN
   {MEDIA_WEB_6_KNOWLEDGE['services']['graphic_design']['description']}
   Services: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['graphic_design']['services'])}

4. 📱 MOBILE APPLICATION
   {MEDIA_WEB_6_KNOWLEDGE['services']['mobile_application']['description']}
   Technologies: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['mobile_application']['technologies'])}
   Types: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['mobile_application']['types'])}

5. 📊 DIGITAL MARKETING
   {MEDIA_WEB_6_KNOWLEDGE['services']['digital_marketing']['description']}
   Services: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['digital_marketing']['services'])}

6. 💻 DESKTOP APPLICATION
   {MEDIA_WEB_6_KNOWLEDGE['services']['desktop_application']['description']}
   Technologies: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['desktop_application']['technologies'])}
   Types: {', '.join(MEDIA_WEB_6_KNOWLEDGE['services']['desktop_application']['types'])}

============================================================
📂 PORTFOLIO CATEGORIES
============================================================
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['e_commerce']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['advertising']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['printing_branding']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['event_management']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['digital_signage']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['news_media']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['directory_platform']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['export_manufacturing']}
{MEDIA_WEB_6_KNOWLEDGE['portfolio']['ngo_nonprofit']}

============================================================
🏆 ACHIEVEMENTS
============================================================
- {MEDIA_WEB_6_KNOWLEDGE['achievements']['projects']}
- {MEDIA_WEB_6_KNOWLEDGE['achievements']['quality']}
- {MEDIA_WEB_6_KNOWLEDGE['achievements']['delivery']}

============================================================
💰 PRICING (Approximate)
============================================================
- Web Development: {MEDIA_WEB_6_KNOWLEDGE['pricing']['web_development']}
- Mobile Apps: {MEDIA_WEB_6_KNOWLEDGE['pricing']['mobile_apps']}
- Digital Marketing: {MEDIA_WEB_6_KNOWLEDGE['pricing']['digital_marketing']}
- SEO: {MEDIA_WEB_6_KNOWLEDGE['pricing']['seo']}
- Graphic Design: {MEDIA_WEB_6_KNOWLEDGE['pricing']['graphic_design']}
- Desktop Applications: {MEDIA_WEB_6_KNOWLEDGE['pricing']['desktop_applications']}
"""
    
    return f"""You are {assistant_name}, the official AI assistant for Media Web 6 Services. You are knowledgeable, friendly, and professional.

IMPORTANT: You are representing Media Web 6 Services. All information provided below is accurate and official.

{knowledge_base}

============================================================
📋 RESPONSE GUIDELINES
============================================================
1. Use the knowledge above to provide accurate, detailed responses about Media Web 6 Services
2. Be warm, conversational, and professional in your tone
3. Provide thorough answers - don't limit yourself to 2-3 sentences
4. If asked about pricing, give the estimated ranges provided
5. For specific project costs, encourage users to contact the company directly
6. Always include contact information when appropriate
7. For questions about services, provide comprehensive details about what we offer
8. Share our mission and vision when asked about company values
9. Mention our portfolio categories when asked about past work
10. Highlight our achievements (25+ projects, 100% quality, fast delivery)
11. For questions you don't know, politely offer to connect users with a human representative

{chr(10) + "User's Name: " + user_name + chr(10) if user_name else ""}
Current Date: {datetime.now().strftime('%B %d, %Y')}

Remember: You are the voice of Media Web 6 Services. Be helpful, accurate, and professional at all times.
"""

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
# GROK REPLY - UPDATED
# ============================================================

def grok_reply(message, history, user_name, assistant_name="Media Web 6 AI"):
    """Get reply from Grok with enhanced knowledge base"""
    if not GROK_API_KEY:
        return None
    
    system_prompt = get_system_prompt(assistant_name, user_name)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Use more history for better context (up to 10 turns)
    for turn in history[-10:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    
    messages.append({"role": "user", "content": message})
    
    # Use higher max_tokens for detailed responses
    return call_grok_api(messages, max_tokens=700, temperature=0.7)

# ============================================================
# VOICE BOT - FULLY UPDATED
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
                f"Welcome to Media Web 6 Services! I'm {self.name}. Transforming Business Through Digital Innovation. How can I help you today?",
                f"Hello! I'm {self.name}, your AI assistant. We blend creativity, innovation, and technology to craft digital solutions. What brings you here?",
                f"Hi there! Welcome to Media Web 6. I'm here to help you with our digital solutions. Feel free to ask me anything!"
            ],
            "farewell": [
                f"Thank you for connecting with Media Web 6! You can always reach us at +91 99942 72027 or email mediawebsix@gmail.com. Have a great day!",
                f"Goodbye! We're here Monday to Friday, 9AM to 7PM. Feel free to reach out anytime. Visit us at www.mediaweb6.com",
                f"It was a pleasure talking to you! Don't hesitate to contact us at +91 99942 72027 if you need anything."
            ],
            "thanks": [
                "You're welcome! Always happy to help!",
                "My pleasure! Is there anything else I can assist you with?",
                "Glad I could help! Let me know if you have more questions."
            ],
            "help": [
                f"I'm {self.name}, the AI assistant for Media Web 6 Services. "
                "I can help with Web Development, SEO Optimization, Graphic Design, Mobile Applications, Digital Marketing, and Desktop Applications. "
                "Feel free to ask me about our services, pricing, portfolio, or how we can help transform your business through digital innovation!"
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
        greetings = [
            f"Welcome to Media Web 6 Services! I'm {self.name}. Transforming Business Through Digital Innovation. How can I help you today?",
            f"Hello! I'm {self.name}, your AI assistant. We blend creativity, innovation, and technology to craft digital solutions. What brings you here?"
        ]
        if self.user_name:
            greetings.append(f"Welcome back, {self.user_name}! How can I assist you with your digital needs today?")
        return random.choice(greetings)

    def _is_quick_intent(self, message, msg_lower):
        """Check if this is a simple query that doesn't need AI"""
        if len(msg_lower.split()) <= 4:
            # Contact queries
            if any(w in msg_lower for w in ["contact", "phone", "email", "address", "location"]):
                return f"📞 Contact Media Web 6: Email: mediawebsix@gmail.com | Phone: +91 99942 72027, 0422 429 2027 | Location: Coimbatore, Tamil Nadu | Website: www.mediaweb6.com | Working Hours: Mon-Fri, 9AM-7PM"
            # Services summary
            if any(w in msg_lower for w in ["services", "offer", "provide", "do you do"]):
                return "🌐 Media Web 6 offers 6 core services: Web Development, SEO Optimization, Graphic Design, Mobile Applications, Digital Marketing, and Desktop Applications. We transform businesses through digital innovation!"
            # Mission
            if any(w in msg_lower for w in ["mission", "purpose"]):
                return "🎯 Our Mission: To craft high-quality digital solutions that businesses can trust and rely on. We simplify complex challenges through intelligent, modern technology and ensure every solution reflects precision, performance, and long-term value."
            # Vision
            if any(w in msg_lower for w in ["vision", "future"]):
                return "👁️ Our Vision: To become a globally trusted partner for digital innovation, set industry standards through quality and reliability, and empower brands to evolve with confidence in a digital-first world."
            # Achievements
            if any(w in msg_lower for w in ["achievements", "projects", "success"]):
                return "🏆 Media Web 6 Achievements: 25+ Projects Successfully Delivered | 100% Quality Focus on Performance & Reliability | Fast Delivery with Quick Turnaround"
        return None

    def generate_response(self, message):
        """Generate response - ALWAYS try AI first"""
        if not message:
            return None
        msg_lower = message.lower().strip()
        
        # Check for very simple queries that don't need AI
        quick_response = self._is_quick_intent(message, msg_lower)
        if quick_response:
            return quick_response
        
        # ✅ ALWAYS try Grok AI first for all other messages
        grok_response = grok_reply(message, self.conversation_history, self.user_name, self.name)
        if grok_response:
            return grok_response
        
        # 🆘 FALLBACK - Only if AI fails
        if any(w in msg_lower for w in ["hello", "hi", "hey", "hii", "greetings"]):
            return f"Hello! Welcome to Media Web 6 Services. How can I help transform your business through digital innovation today?"
        if any(w in msg_lower for w in ["help", "support", "assist"]):
            return random.choice(self.responses["help"])
        if any(w in msg_lower for w in ["thanks", "thank", "thank you", "appreciate"]):
            return random.choice(self.responses["thanks"])
        if any(w in msg_lower for w in ["bye", "goodbye", "good bye", "see you"]):
            return random.choice(self.responses["farewell"])
        if "time" in msg_lower:
            return f"The current time is {datetime.now().strftime('%I:%M %p')}. We're available Monday to Friday, 9AM to 7PM."
        
        # Last resort - offer to connect with human
        return f"I'm here to help! Could you please rephrase your question? Or you can contact us directly at +91 99942 72027 or email mediawebsix@gmail.com for immediate assistance."

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

# CORS - Updated with all domains
ALLOWED_ORIGINS = [
    'http://localhost:3000', 
    'http://localhost:5173', 
    'http://localhost:5174',
    'http://127.0.0.1:3000', 
    'http://127.0.0.1:5173',
    'https://mediaweb6-ai.onrender.com',
    'https://mediaweb6.com',
    'http://mediaweb6.com',
    'https://www.mediaweb6.com',
    'http://www.mediaweb6.com',
    'https://mediaweb6.vercel.app',
    'https://mediaweb6.netlify.app',
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
        'company': MEDIA_WEB_6_KNOWLEDGE['company']['name'],
        'services': len(MEDIA_WEB_6_KNOWLEDGE['services'])
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
            
            # Keep history manageable
            if len(bot.conversation_history) > 50:
                bot.conversation_history = bot.conversation_history[-50:]
            
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
            'grok_enabled': bool(GROK_API_KEY),
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
    
    if not os.path.exists('audio_files'):
        os.makedirs('audio_files')
    
    print("=" * 60)
    print("🤖  MEDIA WEB 6 AI - FULLY TRAINED")
    print("=" * 60)
    print(f"📍 Server: http://0.0.0.0:{port}")
    print(f"🧠 Grok: {'✅ Active' if GROK_API_KEY else '❌ Disabled'}")
    print(f"📚 Knowledge Base: {'✅ Loaded'}")
    print(f"🎤 Voice: {'✅ Enabled'}")
    print(f"🏢 Company: {MEDIA_WEB_6_KNOWLEDGE['company']['name']}")
    print(f"📞 Contact: {MEDIA_WEB_6_KNOWLEDGE['contact']['phone_primary']}")
    print(f"📧 Email: {MEDIA_WEB_6_KNOWLEDGE['contact']['email']}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)