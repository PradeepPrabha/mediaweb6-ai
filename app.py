# app.py - Media Web 6 AI Backend (HYBRID MODE)
# ============================================================
# MEDIA WEB 6 AI - Backend
# Hybrid: Grok API + Intelligent Fallback
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
# GROK API SETUP
# ============================================================

GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
# Try different model names - API will try them in order
GROK_MODELS = ["grok-1", "grok-beta", "grok-2", "grok-2-1212"]
GROK_MODEL = os.getenv("GROK_MODEL", "grok-1")

print("=" * 60)
print("🔑 GROK API STATUS:")
print(f"   API Key: {'✅ Present' if GROK_API_KEY else '❌ Missing'}")
print(f"   Length: {len(GROK_API_KEY) if GROK_API_KEY else 0}")
print(f"   Requested Model: {GROK_MODEL}")
print("=" * 60)

def call_grok_api(messages, max_tokens=600, temperature=0.7):
    """Direct Grok API call with automatic model fallback"""
    if not GROK_API_KEY:
        return None
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try each model in order
    models_to_try = [GROK_MODEL] + [m for m in GROK_MODELS if m != GROK_MODEL]
    
    for model in models_to_try:
        try:
            print(f"🤖 Trying Grok API with model: {model}")
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                print(f"✅ Grok response with {model}: {reply[:50]}...")
                return reply
            elif response.status_code == 400 and "Model not found" in response.text:
                print(f"⚠️ Model {model} not found, trying next...")
                continue
            else:
                print(f"⚠️ Grok API Error: {response.status_code} with {model}")
                continue
        except Exception as e:
            print(f"⚠️ Grok API Exception with {model}: {e}")
            continue
    
    print("❌ All Grok models failed")
    return None

# Test the API
API_WORKING = False
if GROK_API_KEY:
    test_result = call_grok_api([{"role": "user", "content": "Hello"}], max_tokens=5)
    if test_result:
        API_WORKING = True
        print(f"✅ Grok API is working!")
    else:
        print("⚠️ Grok API test failed - using intelligent fallback mode")
else:
    print("❌ No GROK_API_KEY found - using intelligent fallback mode")

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
            "types": ["Corporate Websites", "E-commerce Stores", "Web Portals", "PWA Applications", "Landing Pages"],
            "pricing": "₹25,000+"
        },
        "seo_optimization": {
            "name": "SEO Optimization",
            "description": "Search engine optimization to improve organic rankings and visibility",
            "services": ["On-Page SEO", "Off-Page SEO", "Technical SEO", "Local SEO", "E-commerce SEO", "Content Strategy"],
            "pricing": "₹10,000+/month"
        },
        "graphic_design": {
            "name": "Graphic Design",
            "description": "Creative visual design solutions for branding and marketing",
            "services": ["Logo Design", "Brand Identity", "Social Media Graphics", "Print Materials", "Packaging Design", "UI Design"],
            "pricing": "₹5,000+"
        },
        "mobile_application": {
            "name": "Mobile Application",
            "description": "Native and cross-platform mobile applications for iOS and Android",
            "technologies": ["React Native", "Flutter", "Swift", "Kotlin", "Java"],
            "types": ["Business Apps", "E-commerce Apps", "Social Apps", "Healthcare Apps", "Educational Apps"],
            "pricing": "₹50,000+"
        },
        "digital_marketing": {
            "name": "Digital Marketing",
            "description": "Comprehensive digital marketing strategies to boost online presence and conversions",
            "services": ["SEO", "Social Media Marketing", "Content Marketing", "Google Ads", "Email Marketing", "Analytics", "SMM"],
            "pricing": "₹15,000+/month"
        },
        "desktop_application": {
            "name": "Desktop Application",
            "description": "Custom desktop applications for Windows, Mac, and Linux",
            "technologies": ["Electron", "Java", "Python", "C#", ".NET"],
            "types": ["Business Software", "Enterprise Applications", "Utility Tools", "Management Systems"],
            "pricing": "₹30,000+"
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
        {"question": "what services do you offer", 
         "answer": "We offer Web Development, SEO Optimization, Graphic Design, Mobile Application Development, Digital Marketing, and Desktop Application Development."},
        {"question": "how much does a website cost", 
         "answer": "Our web development starts from ₹25,000, depending on complexity and features."},
        {"question": "do you offer mobile app development", 
         "answer": "Yes, we develop native and cross-platform mobile apps for iOS and Android using React Native and Flutter."},
        {"question": "what is your mission", 
         "answer": "Our mission is to craft high-quality digital solutions that businesses can trust and rely on. We simplify complex challenges through intelligent, modern technology."},
        {"question": "what is your vision", 
         "answer": "To become a globally trusted partner for digital innovation and set industry standards through quality, reliability, and user-focused design."},
        {"question": "do you provide seo services", 
         "answer": "Yes, we offer comprehensive SEO services including on-page, off-page, technical SEO, local SEO, and e-commerce SEO."},
        {"question": "where are you located", 
         "answer": "We are located in Coimbatore, Tamil Nadu. We serve clients globally."},
        {"question": "what are your working hours", 
         "answer": "We are available Monday to Friday, 9AM to 7PM."},
        {"question": "how can i contact you", 
         "answer": "You can call us at +91 99942 72027 or 0422 429 2027, email us at mediawebsix@gmail.com, or visit our website www.mediaweb6.com"},
        {"question": "what types of projects have you worked on", 
         "answer": "We've worked on E-Commerce, Advertising, Printing & Branding, Event Management, Digital Signage, News & Media, Directory Platforms, Export & Manufacturing, and NGO & Non-Profit projects."},
        {"question": "what technologies do you use", 
         "answer": "We use modern technologies including React, Next.js, Node.js, PHP, WordPress, React Native, Flutter, and more."},
        {"question": "what is your tagline", 
         "answer": "Our tagline is 'Transforming Business Through Digital Innovation'."},
        {"question": "what graphic design services do you offer", 
         "answer": "We offer Logo Design, Brand Identity, Social Media Graphics, Print Materials, Packaging Design, and UI Design."},
        {"question": "what digital marketing services do you offer", 
         "answer": "We offer SEO, Social Media Marketing, Content Marketing, Google Ads, Email Marketing, Analytics, and SMM."},
        {"question": "do you develop desktop applications", 
         "answer": "Yes, we develop custom desktop applications for Windows, Mac, and Linux using Electron, Java, Python, C#, and .NET."},
        {"question": "what is media web 6", 
         "answer": "Media Web 6 Services is a digital solutions company founded in 2018. We blend creativity, innovation, and technology to craft digital solutions that elevate brands and unlock new growth opportunities."}
    ]
}

# ============================================================
# INTELLIGENT RESPONSE ENGINE (FALLBACK)
# ============================================================

class MediaWeb6ResponseEngine:
    """Intelligent response engine - Used as fallback when API fails"""
    
    def __init__(self):
        self.knowledge = MEDIA_WEB_6_KNOWLEDGE
        self._build_response_patterns()
    
    def _build_response_patterns(self):
        """Build intelligent response patterns"""
        self.patterns = {
            # Service queries
            r"web development|website|web design|web dev": self.get_web_development_info,
            r"mobile app|app development|ios app|android app": self.get_mobile_app_info,
            r"seo|search engine|ranking": self.get_seo_info,
            r"graphic design|design|logo|branding": self.get_graphic_design_info,
            r"digital marketing|marketing|social media|ads": self.get_digital_marketing_info,
            r"desktop app|desktop application|windows app": self.get_desktop_app_info,
            r"services|offer|provide|do you do": self.get_all_services,
            r"mission|purpose|goal": self.get_mission,
            r"vision|future|aspire": self.get_vision,
            r"contact|phone|email|reach": self.get_contact,
            r"location|address|where": self.get_location,
            r"hours|timing|working": self.get_working_hours,
            r"achievements|projects|success": self.get_achievements,
            r"portfolio|past work|projects": self.get_portfolio,
            r"pricing|cost|price|charge": self.get_pricing,
            r"technologies|tech stack|tools": self.get_technologies,
            r"tagline|slogan": self.get_tagline,
            r"values|principle|belief": self.get_values,
        }
    
    def get_response(self, message):
        """Get intelligent response based on message"""
        message_lower = message.lower().strip()
        
        # Check FAQ first
        for faq in self.knowledge["faqs"]:
            if faq["question"] in message_lower:
                return faq["answer"]
        
        # Check patterns
        for pattern, handler in self.patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return handler()
        
        # Check if it's a greeting
        if re.search(r"hello|hi|hey|greetings", message_lower, re.IGNORECASE):
            return random.choice([
                "Hello! Welcome to Media Web 6 Services. How can I help you today?",
                "Hi there! I'm your AI assistant. What would you like to know about our services?",
                "Welcome! Feel free to ask me about our web development, mobile apps, digital marketing, or any other services."
            ])
        
        # Check if it's a thank you
        if re.search(r"thank|thanks|appreciate", message_lower, re.IGNORECASE):
            return "You're welcome! I'm glad I could help. Is there anything else you'd like to know about Media Web 6 Services?"
        
        # Check if it's a goodbye
        if re.search(r"bye|goodbye|see you|farewell", message_lower, re.IGNORECASE):
            return f"Thank you for connecting with Media Web 6! You can always reach us at +91 99942 72027 or email mediawebsix@gmail.com. Have a great day!"
        
        # Default response
        return self.get_default_response()
    
    # ============================================================
    # HANDLER METHODS
    # ============================================================
    
    def get_all_services(self):
        services = []
        for key, service in self.knowledge["services"].items():
            name = service["name"]
            desc = service["description"]
            services.append(f"• **{name}**: {desc}")
        return "Media Web 6 offers 6 core services:\n\n" + "\n".join(services) + "\n\nContact us at +91 99942 72027 for more details!"
    
    def get_web_development_info(self):
        service = self.knowledge["services"]["web_development"]
        return f"""🌐 **Web Development Services**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**Project Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}

We build custom websites that are fast, secure, and scalable. Contact us at +91 99942 72027 to discuss your project!"""
    
    def get_mobile_app_info(self):
        service = self.knowledge["services"]["mobile_application"]
        return f"""📱 **Mobile Application Development**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**App Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}

We build native and cross-platform apps that deliver exceptional user experiences. Reach out at +91 99942 72027!"""
    
    def get_seo_info(self):
        service = self.knowledge["services"]["seo_optimization"]
        return f"""🔍 **SEO Optimization Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}

Improve your online visibility and rankings with our expert SEO strategies. Contact us at +91 99942 72027!"""
    
    def get_graphic_design_info(self):
        service = self.knowledge["services"]["graphic_design"]
        return f"""🎨 **Graphic Design Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}

We create visually stunning designs that elevate your brand identity. Get in touch at +91 99942 72027!"""
    
    def get_digital_marketing_info(self):
        service = self.knowledge["services"]["digital_marketing"]
        return f"""📊 **Digital Marketing Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}

Boost your online presence and drive conversions with our comprehensive digital marketing strategies. Call us at +91 99942 72027!"""
    
    def get_desktop_app_info(self):
        service = self.knowledge["services"]["desktop_application"]
        return f"""💻 **Desktop Application Development**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**App Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}

We build powerful desktop applications for Windows, Mac, and Linux. Contact us at +91 99942 72027!"""
    
    def get_mission(self):
        return f"""🎯 **Our Mission**

{self.knowledge['company']['mission']}

We're committed to delivering digital solutions that create measurable impact and drive business growth."""
    
    def get_vision(self):
        return f"""👁️ **Our Vision**

{self.knowledge['company']['vision']}

We aim to be your trusted partner for digital innovation and transformation."""
    
    def get_contact(self):
        contact = self.knowledge["contact"]
        return f"""📞 **Contact Media Web 6**

📧 Email: {contact['email']}
📱 Phone: {contact['phone_primary']}
📞 Alternate: {contact['phone_secondary']}
💬 WhatsApp: {contact['whatsapp']}
🌐 Website: {contact['website']}
📍 Location: {contact['address']}
🕐 Hours: {contact['working_hours']}

We're here to help! Reach out anytime."""
    
    def get_location(self):
        return f"""📍 **Location**

{self.knowledge['contact']['address']}

We serve clients globally from our base in Coimbatore, Tamil Nadu. Contact us at +91 99942 72027!"""
    
    def get_working_hours(self):
        return f"""🕐 **Working Hours**

{self.knowledge['contact']['working_hours']}

We're available to assist you during these hours. Call us at +91 99942 72027 or email mediawebsix@gmail.com!"""
    
    def get_achievements(self):
        ach = self.knowledge["achievements"]
        return f"""🏆 **Our Achievements**

• {ach['projects']}
• {ach['quality']}
• {ach['delivery']}

We take pride in delivering excellence in every project. Let's work together!"""
    
    def get_portfolio(self):
        portfolio = self.knowledge["portfolio"]
        categories = []
        for key, value in portfolio.items():
            categories.append(f"• {value}")
        return f"""📂 **Our Portfolio Categories**

{chr(10).join(categories)}

We've successfully delivered projects across all these categories. Contact us to see our work!"""
    
    def get_pricing(self):
        pricing = []
        for key, service in self.knowledge["services"].items():
            if "pricing" in service:
                pricing.append(f"• {service['name']}: {service['pricing']}")
        return f"""💰 **Pricing Information**

{chr(10).join(pricing)}

These are starting prices. Contact us at +91 99942 72027 for a customized quote!"""
    
    def get_technologies(self):
        techs = set()
        for key, service in self.knowledge["services"].items():
            if "technologies" in service:
                techs.update(service["technologies"])
        return f"""🛠️ **Technologies We Use**

{', '.join(sorted(techs))}

We use modern, cutting-edge technologies to build robust digital solutions."""
    
    def get_tagline(self):
        return f"""✨ **Our Tagline**

{self.knowledge['company']['tagline']}

We transform businesses through digital innovation!"""
    
    def get_values(self):
        return f"""💎 **Our Values**

{self.knowledge['company']['values']}

These core values guide everything we do at Media Web 6 Services."""
    
    def get_default_response(self):
        return f"""I'm here to help you with all things Media Web 6!

Here are some things you can ask me:
• What services do you offer?
• Tell me about web development
• Mobile app development pricing
• SEO services
• Graphic design
• Digital marketing
• Your mission and vision
• Contact information
• Portfolio and achievements
• Technologies you use

Or call us directly at +91 99942 72027 for immediate assistance!"""

# ============================================================
# ENHANCED SYSTEM PROMPT (For Grok API)
# ============================================================

def get_system_prompt(assistant_name="Media Web 6 AI", user_name=None):
    """Get the enhanced system prompt with complete company knowledge"""
    
    knowledge_base = f"""
COMPANY: Media Web 6 Services
Tagline: Transforming Business Through Digital Innovation
Founded: 2018
Mission: To craft high-quality digital solutions that businesses can trust and rely on.
Vision: To become a globally trusted partner for digital innovation.

SERVICES:
1. Web Development - Custom websites, e-commerce, CMS. Technologies: React, Next.js, Node.js, PHP, WordPress
2. SEO Optimization - On-page, off-page, technical, local SEO
3. Graphic Design - Logo design, branding, social media graphics, print materials
4. Mobile Applications - iOS/Android apps using React Native, Flutter
5. Digital Marketing - SEO, social media, content marketing, Google Ads
6. Desktop Applications - Windows, Mac, Linux using Electron, Java, Python

CONTACT:
Email: mediawebsix@gmail.com
Phone: +91 99942 72027, 0422 429 2027
Location: Coimbatore, Tamil Nadu
Hours: Mon-Fri, 9AM-7PM
Website: www.mediaweb6.com

ACHIEVEMENTS: 25+ Projects | 100% Quality | Fast Delivery

PRICING: Web(₹25k+), Mobile(₹50k+), Marketing(₹15k/month), SEO(₹10k/month), Design(₹5k+), Desktop(₹30k+)
"""
    
    return f"""You are {assistant_name}, the official AI assistant for Media Web 6 Services.

{knowledge_base}

Guidelines:
- Be warm, conversational, and professional
- Provide thorough, detailed answers
- Always include contact information when appropriate
- For pricing, give estimates and encourage direct contact
- Share mission/vision when asked about company values

{chr(10) + "User: " + user_name if user_name else ""}
Date: {datetime.now().strftime('%B %d, %Y')}
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
# GROK REPLY
# ============================================================

def grok_reply(message, history, user_name, assistant_name="Media Web 6 AI"):
    """Get reply from Grok API or return None if fails"""
    if not GROK_API_KEY:
        return None
    
    system_prompt = get_system_prompt(assistant_name, user_name)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for turn in history[-10:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    
    messages.append({"role": "user", "content": message})
    
    return call_grok_api(messages, max_tokens=700, temperature=0.7)

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
        self.response_engine = MediaWeb6ResponseEngine()
        self.use_api = API_WORKING and bool(GROK_API_KEY)
        
        print(f"🤖 Bot initialized - API Mode: {'ON' if self.use_api else 'OFF (Fallback)'}")
        
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

    def generate_response(self, message):
        """Generate response - Try API first, fallback to intelligent engine"""
        if not message:
            return None
        msg_lower = message.lower().strip()
        
        # First try: Grok API (if available)
        if self.use_api:
            grok_response = grok_reply(message, self.conversation_history, self.user_name, self.name)
            if grok_response:
                self.conversation_history.append({
                    'user': message,
                    'assistant': grok_response,
                    'timestamp': datetime.now().isoformat(),
                })
                return grok_response
        
        # Second try: Intelligent Fallback Engine
        fallback_response = self.response_engine.get_response(message)
        
        # Store in conversation history
        self.conversation_history.append({
            'user': message,
            'assistant': fallback_response,
            'timestamp': datetime.now().isoformat(),
        })
        
        return fallback_response

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
        'mode': 'hybrid',
        'api_working': API_WORKING,
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
            
            if len(bot.conversation_history) > 50:
                bot.conversation_history = bot.conversation_history[-50:]
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'response': response,
                'audio_url': f"/api/audio/{audio_file}" if audio_file else None,
                'user_name': bot.user_name,
                'history_count': len(bot.conversation_history),
                'mode': 'api' if bot.use_api else 'fallback'
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
            'mode': 'hybrid',
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
    print("🤖  MEDIA WEB 6 AI - HYBRID MODE")
    print("=" * 60)
    print(f"📍 Server: http://0.0.0.0:{port}")
    print(f"🧠 API Mode: {'✅ Active' if API_WORKING else '❌ Fallback Mode'}")
    print(f"📚 Knowledge Base: {'✅ Loaded'}")
    print(f"🎤 Voice: {'✅ Enabled'}")
    print(f"🏢 Company: {MEDIA_WEB_6_KNOWLEDGE['company']['name']}")
    print(f"📞 Contact: {MEDIA_WEB_6_KNOWLEDGE['contact']['phone_primary']}")
    print(f"📧 Email: {MEDIA_WEB_6_KNOWLEDGE['contact']['email']}")
    print("=" * 60)
    if not API_WORKING:
        print("⚠️  Grok API not available - Using INTELLIGENT FALLBACK mode")
        print("✅  All responses are pre-trained with your company data")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)