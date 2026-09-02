# app.py - Media Web 6 AI Backend (HYBRID MODE WITH MULTI-LANGUAGE)
# ============================================================
# MEDIA WEB 6 AI - Backend
# Hybrid: Grok API + Intelligent Fallback
# Multi-language voice support
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
    
    # Services with detailed pricing
    "services": {
        "web_development": {
            "name": "Web Development",
            "description": "Custom website development, e-commerce platforms, CMS solutions, and web applications",
            "technologies": ["React", "Next.js", "Node.js", "PHP", "WordPress", "Magento", "Shopify", "HTML5", "CSS3", "JavaScript"],
            "types": ["Corporate Websites", "E-commerce Stores", "Web Portals", "PWA Applications", "Landing Pages"],
            "pricing": "₹25,000+",
            "pricing_detail": "Starting from ₹25,000 for basic websites. E-commerce and complex projects start from ₹50,000."
        },
        "seo_optimization": {
            "name": "SEO Optimization",
            "description": "Search engine optimization to improve organic rankings and visibility",
            "services": ["On-Page SEO", "Off-Page SEO", "Technical SEO", "Local SEO", "E-commerce SEO", "Content Strategy"],
            "pricing": "₹10,000+/month",
            "pricing_detail": "SEO packages start from ₹10,000 per month. Comprehensive packages include monthly reports and strategy updates."
        },
        "graphic_design": {
            "name": "Graphic Design",
            "description": "Creative visual design solutions for branding and marketing",
            "services": ["Logo Design", "Brand Identity", "Social Media Graphics", "Print Materials", "Packaging Design", "UI Design"],
            "pricing": "₹5,000+",
            "pricing_detail": "Logo design starts from ₹5,000. Complete branding packages start from ₹15,000."
        },
        "mobile_application": {
            "name": "Mobile Application",
            "description": "Native and cross-platform mobile applications for iOS and Android",
            "technologies": ["React Native", "Flutter", "Swift", "Kotlin", "Java"],
            "types": ["Business Apps", "E-commerce Apps", "Social Apps", "Healthcare Apps", "Educational Apps"],
            "pricing": "₹50,000+",
            "pricing_detail": "Mobile app development starts from ₹50,000. Complex apps with backend integration start from ₹1,00,000."
        },
        "digital_marketing": {
            "name": "Digital Marketing",
            "description": "Comprehensive digital marketing strategies to boost online presence and conversions",
            "services": ["SEO", "Social Media Marketing", "Content Marketing", "Google Ads", "Email Marketing", "Analytics", "SMM"],
            "pricing": "₹15,000+/month",
            "pricing_detail": "Digital marketing packages start from ₹15,000 per month. Includes SEO, social media, and content marketing."
        },
        "desktop_application": {
            "name": "Desktop Application",
            "description": "Custom desktop applications for Windows, Mac, and Linux",
            "technologies": ["Electron", "Java", "Python", "C#", ".NET"],
            "types": ["Business Software", "Enterprise Applications", "Utility Tools", "Management Systems"],
            "pricing": "₹30,000+",
            "pricing_detail": "Desktop application development starts from ₹30,000. Enterprise solutions start from ₹75,000."
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
    
    # Pricing Summary
    "pricing_summary": {
        "web_development": "Starting from ₹25,000",
        "mobile_apps": "Starting from ₹50,000",
        "digital_marketing": "Starting from ₹15,000/month",
        "seo": "Starting from ₹10,000/month",
        "graphic_design": "Starting from ₹5,000",
        "desktop_applications": "Starting from ₹30,000"
    },
    
    # FAQs with more detailed answers
    "faqs": [
        {"question": "what services do you offer", 
         "answer": "We offer 6 core services: Web Development, SEO Optimization, Graphic Design, Mobile Application Development, Digital Marketing, and Desktop Application Development. Each service is tailored to your specific needs."},
        {"question": "how much does a website cost", 
         "answer": "Our web development starts from ₹25,000 for a basic website. E-commerce and complex websites start from ₹50,000. The final cost depends on features, design complexity, and functionality requirements."},
        {"question": "what is the cost of a mobile app", 
         "answer": "Mobile app development starts from ₹50,000 for basic apps. Complex apps with backend integration, payment gateways, and advanced features start from ₹1,00,000. We use React Native and Flutter for cross-platform development."},
        {"question": "do you offer mobile app development", 
         "answer": "Yes, we develop native and cross-platform mobile apps for iOS and Android using React Native and Flutter. We build business apps, e-commerce apps, social apps, healthcare apps, and educational apps."},
        {"question": "what is your mission", 
         "answer": "Our mission is to craft high-quality digital solutions that businesses can trust and rely on. We simplify complex challenges through intelligent, modern technology and ensure every solution reflects precision, performance, and long-term value."},
        {"question": "what is your vision", 
         "answer": "To become a globally trusted partner for digital innovation and set industry standards through quality, reliability, and user-focused design. We aim to empower brands to evolve with confidence in a digital-first world."},
        {"question": "do you provide seo services", 
         "answer": "Yes, we offer comprehensive SEO services including on-page SEO, off-page SEO, technical SEO, local SEO, e-commerce SEO, and content strategy. SEO packages start from ₹10,000 per month."},
        {"question": "where are you located", 
         "answer": "We are located in Coimbatore, Tamil Nadu. We serve clients globally with our remote-first approach."},
        {"question": "what are your working hours", 
         "answer": "We are available Monday to Friday, 9AM to 7PM. You can reach us anytime via email at mediawebsix@gmail.com."},
        {"question": "how can i contact you", 
         "answer": "You can call us at +91 99942 72027 or 0422 429 2027, email us at mediawebsix@gmail.com, WhatsApp us at +91 99942 72027, or visit our website www.mediaweb6.com"},
        {"question": "what types of projects have you worked on", 
         "answer": "We've worked on E-Commerce, Advertising, Printing & Branding, Event Management, Digital Signage, News & Media, Directory Platforms, Export & Manufacturing, and NGO & Non-Profit projects."},
        {"question": "what technologies do you use", 
         "answer": "We use modern technologies including React, Next.js, Node.js, PHP, WordPress, React Native, Flutter, Electron, Java, Python, and C#."},
        {"question": "what is your tagline", 
         "answer": "Our tagline is 'Transforming Business Through Digital Innovation'."},
        {"question": "what graphic design services do you offer", 
         "answer": "We offer Logo Design, Brand Identity, Social Media Graphics, Print Materials, Packaging Design, and UI Design. Logo design starts from ₹5,000."},
        {"question": "what digital marketing services do you offer", 
         "answer": "We offer SEO, Social Media Marketing (SMM), Content Marketing, Google Ads, Email Marketing, and Analytics. Packages start from ₹15,000 per month."},
        {"question": "do you develop desktop applications", 
         "answer": "Yes, we develop custom desktop applications for Windows, Mac, and Linux using Electron, Java, Python, C#, and .NET. Starting from ₹30,000."},
        {"question": "what is media web 6", 
         "answer": "Media Web 6 Services is a digital solutions company founded in 2018. We blend creativity, innovation, and technology to craft digital solutions that elevate brands and unlock new growth opportunities."},
        {"question": "how much does seo cost", 
         "answer": "SEO packages start from ₹10,000 per month. This includes on-page optimization, content strategy, and monthly performance reports."},
        {"question": "what is the price of digital marketing", 
         "answer": "Digital marketing packages start from ₹15,000 per month. This includes SEO, social media management, content marketing, and analytics reporting."},
        {"question": "how much for graphic design", 
         "answer": "Logo design starts from ₹5,000. Complete branding packages including logo, business cards, and social media graphics start from ₹15,000."},
        {"question": "what is the cost of desktop application", 
         "answer": "Desktop application development starts from ₹30,000. Enterprise-grade solutions with complex features start from ₹75,000."}
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
            r"mobile app|app development|ios app|android app|mobile application": self.get_mobile_app_info,
            r"seo|search engine|ranking|seo services": self.get_seo_info,
            r"graphic design|design|logo|branding|graphics": self.get_graphic_design_info,
            r"digital marketing|marketing|social media|ads|smm": self.get_digital_marketing_info,
            r"desktop app|desktop application|windows app": self.get_desktop_app_info,
            
            # Pricing queries with more specific patterns
            r"cost of (web|website|web development)|how much (web|website)|web price|website cost": self.get_web_pricing,
            r"cost of (mobile|app|mobile app)|mobile app price|app cost|how much (mobile|app)": self.get_mobile_pricing,
            r"cost of (seo|search engine)|seo price|seo cost|how much seo": self.get_seo_pricing,
            r"cost of (graphic|design|logo)|design price|logo cost|how much (graphic|design)": self.get_design_pricing,
            r"cost of (digital marketing|marketing|social media)|marketing price|how much marketing": self.get_marketing_pricing,
            r"cost of (desktop|desktop app)|desktop price|how much desktop": self.get_desktop_pricing,
            
            # General queries
            r"services|offer|provide|do you do|what do you": self.get_all_services,
            r"mission|purpose|goal": self.get_mission,
            r"vision|future|aspire": self.get_vision,
            r"contact|phone|email|reach|call": self.get_contact,
            r"location|address|where": self.get_location,
            r"hours|timing|working|time": self.get_working_hours,
            r"achievements|projects|success": self.get_achievements,
            r"portfolio|past work|clients": self.get_portfolio,
            r"pricing|cost|price|charge|rates": self.get_all_pricing,
            r"technologies|tech stack|tools|technology": self.get_technologies,
            r"tagline|slogan": self.get_tagline,
            r"values|principle|belief": self.get_values,
        }
    
    def get_response(self, message):
        """Get intelligent response based on message"""
        message_lower = message.lower().strip()
        
        # Check FAQ first with exact matching
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
    # PRICING HANDLER METHODS (Specific)
    # ============================================================
    
    def get_web_pricing(self):
        service = self.knowledge["services"]["web_development"]
        return f"""🌐 **Web Development Pricing**

{service['pricing_detail']}

**What's included:**
• Custom design and development
• Responsive/mobile-friendly layout
• CMS integration (WordPress, etc.)
• Basic SEO optimization
• 1 month free support

Contact us at +91 99942 72027 for a detailed quote!"""
    
    def get_mobile_pricing(self):
        service = self.knowledge["services"]["mobile_application"]
        return f"""📱 **Mobile App Development Pricing**

{service['pricing_detail']}

**What's included:**
• Native or cross-platform development
• UI/UX design
• API integration
• App store deployment
• 1 month free support

**Technology:** React Native, Flutter, Swift, Kotlin

Contact us at +91 99942 72027 for a detailed quote!"""
    
    def get_seo_pricing(self):
        service = self.knowledge["services"]["seo_optimization"]
        return f"""🔍 **SEO Services Pricing**

{service['pricing_detail']}

**What's included:**
• On-page and off-page SEO
• Technical SEO audit
• Content strategy
• Monthly performance reports
• Keyword research and tracking

Contact us at +91 99942 72027 for a customized SEO plan!"""
    
    def get_design_pricing(self):
        service = self.knowledge["services"]["graphic_design"]
        return f"""🎨 **Graphic Design Pricing**

{service['pricing_detail']}

**What's included:**
• Logo design and brand identity
• Social media graphics
• Print materials
• Packaging design
• UI/UX design

Contact us at +91 99942 72027 for a customized design quote!"""
    
    def get_marketing_pricing(self):
        service = self.knowledge["services"]["digital_marketing"]
        return f"""📊 **Digital Marketing Pricing**

{service['pricing_detail']}

**What's included:**
• SEO and content marketing
• Social media management
• Google Ads management
• Email marketing
• Analytics and reporting

Contact us at +91 99942 72027 for a customized marketing plan!"""
    
    def get_desktop_pricing(self):
        service = self.knowledge["services"]["desktop_application"]
        return f"""💻 **Desktop Application Pricing**

{service['pricing_detail']}

**What's included:**
• Custom application development
• UI/UX design
• Database integration
• Deployment and installation
• 1 month free support

**Technology:** Electron, Java, Python, C#, .NET

Contact us at +91 99942 72027 for a detailed quote!"""
    
    def get_all_pricing(self):
        pricing = []
        for key, service in self.knowledge["services"].items():
            if "pricing" in service:
                pricing.append(f"• {service['name']}: {service['pricing']}")
        
        return f"""💰 **Complete Pricing Guide**

{chr(10).join(pricing)}

📞 For detailed quotes and custom requirements, contact us at +91 99942 72027 or email mediawebsix@gmail.com

💡 All prices are starting estimates. Final cost depends on project complexity and requirements."""
    
    # ============================================================
    # GENERAL HANDLER METHODS
    # ============================================================
    
    def get_all_services(self):
        services = []
        for key, service in self.knowledge["services"].items():
            name = service["name"]
            desc = service["description"]
            services.append(f"• **{name}**: {desc}")
        return "Media Web 6 offers 6 core services:\n\n" + "\n".join(services) + "\n\nFor pricing details, ask me about specific services or contact us at +91 99942 72027!"
    
    def get_web_development_info(self):
        service = self.knowledge["services"]["web_development"]
        return f"""🌐 **Web Development Services**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**Project Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

We build custom websites that are fast, secure, and scalable. Contact us at +91 99942 72027 to discuss your project!"""
    
    def get_mobile_app_info(self):
        service = self.knowledge["services"]["mobile_application"]
        return f"""📱 **Mobile Application Development**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**App Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

We build native and cross-platform apps that deliver exceptional user experiences. Reach out at +91 99942 72027!"""
    
    def get_seo_info(self):
        service = self.knowledge["services"]["seo_optimization"]
        return f"""🔍 **SEO Optimization Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

Improve your online visibility and rankings with our expert SEO strategies. Contact us at +91 99942 72027!"""
    
    def get_graphic_design_info(self):
        service = self.knowledge["services"]["graphic_design"]
        return f"""🎨 **Graphic Design Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

We create visually stunning designs that elevate your brand identity. Get in touch at +91 99942 72027!"""
    
    def get_digital_marketing_info(self):
        service = self.knowledge["services"]["digital_marketing"]
        return f"""📊 **Digital Marketing Services**

{service['description']}

**Services:** {', '.join(service['services'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

Boost your online presence and drive conversions with our comprehensive digital marketing strategies. Call us at +91 99942 72027!"""
    
    def get_desktop_app_info(self):
        service = self.knowledge["services"]["desktop_application"]
        return f"""💻 **Desktop Application Development**

{service['description']}

**Technologies:** {', '.join(service['technologies'])}
**App Types:** {', '.join(service['types'])}
**Pricing:** {service['pricing']}
**Details:** {service['pricing_detail']}

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
• How much does a website cost?
• What is the cost of a mobile app?
• SEO services pricing
• Graphic design pricing
• Digital marketing packages
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

SERVICES AND PRICING:
1. Web Development - Starting ₹25,000 (Basic) to ₹50,000+ (E-commerce)
2. Mobile Applications - Starting ₹50,000 (Basic) to ₹1,00,000+ (Complex)
3. SEO Optimization - Starting ₹10,000/month
4. Graphic Design - Starting ₹5,000 (Logo) to ₹15,000+ (Branding)
5. Digital Marketing - Starting ₹15,000/month
6. Desktop Applications - Starting ₹30,000 (Basic) to ₹75,000+ (Enterprise)

TECHNOLOGIES: React, Next.js, Node.js, PHP, WordPress, React Native, Flutter, Electron, Java, Python

CONTACT:
Email: mediawebsix@gmail.com
Phone: +91 99942 72027, 0422 429 2027
Location: Coimbatore, Tamil Nadu
Hours: Mon-Fri, 9AM-7PM
Website: www.mediaweb6.com

ACHIEVEMENTS: 25+ Projects | 100% Quality | Fast Delivery
"""
    
    return f"""You are {assistant_name}, the official AI assistant for Media Web 6 Services.

{knowledge_base}

Guidelines:
- Be warm, conversational, and professional
- Provide thorough, detailed answers with specific pricing
- Always include contact information when appropriate
- For pricing, give estimates and encourage direct contact for custom quotes
- Share mission/vision when asked about company values
- Be specific about service costs and what's included

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
# VOICE BOT WITH MULTI-LANGUAGE SUPPORT
# ============================================================

class MediaWeb6AIBot:
    def __init__(self, name="Media Web 6 AI", speak_language="en"):
        self.name = name
        self.speak_language = speak_language
        self.user_name = None
        self.user_language = "en"  # Default language
        self.conversation_history = []
        self.audio_dir = "audio_files"
        os.makedirs(self.audio_dir, exist_ok=True)
        self.response_engine = MediaWeb6ResponseEngine()
        self.use_api = API_WORKING and bool(GROK_API_KEY)
        
        # Supported languages for voice
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'fr': 'French',
            'de': 'German',
            'es': 'Spanish',
            'ja': 'Japanese',
            'zh': 'Chinese',
            'ar': 'Arabic'
        }
        
        print(f"🤖 Bot initialized - API Mode: {'ON' if self.use_api else 'OFF (Fallback)'}")
        print(f"🗣️ Default Voice Language: {self.supported_languages.get(speak_language, 'English')}")
        
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

    def detect_language(self, text):
        """Detect language from text for voice output"""
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # Tamil detection
        tamil_chars = ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ']
        if any(char in text for char in tamil_chars):
            return 'ta'
        
        # Hindi detection
        hindi_chars = ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ', 'क', 'ख', 'ग', 'घ', 'च']
        if any(char in text for char in hindi_chars):
            return 'hi'
        
        # Telugu detection
        telugu_chars = ['అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ', 'ఋ', 'ఎ', 'ఏ', 'ఐ', 'ఒ', 'ఓ', 'ఔ']
        if any(char in text for char in telugu_chars):
            return 'te'
        
        # Malayalam detection
        malayalam_chars = ['അ', 'ആ', 'ഇ', 'ഈ', 'ഉ', 'ഊ', 'ഋ', 'എ', 'ഏ', 'ഐ', 'ഒ', 'ഓ', 'ഔ']
        if any(char in text for char in malayalam_chars):
            return 'ml'
        
        # Kannada detection
        kannada_chars = ['ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ', 'ಋ', 'ಎ', 'ಏ', 'ಐ', 'ಒ', 'ಓ', 'ಔ']
        if any(char in text for char in kannada_chars):
            return 'kn'
        
        # Check for language keywords
        if 'नमस्ते' in text or 'धन्यवाद' in text:
            return 'hi'
        if 'வணக்கம்' in text or 'நன்றி' in text:
            return 'ta'
        
        # Default to user's preferred language or English
        return self.user_language

    def generate_audio(self, text, lang=None):
        """Generate audio with language detection"""
        if not text:
            return None
        
        # If no language specified, detect from text
        if lang is None:
            lang = self.detect_language(text)
        
        # If language not supported, fallback to English
        if lang not in self.supported_languages:
            lang = 'en'
        
        try:
            filename = f"speech_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            print(f"🎤 Generating audio in: {self.supported_languages.get(lang, 'English')}")
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filepath)
            return filename
        except Exception as e:
            print(f"Audio error: {e}")
            # Try English fallback
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(filepath)
                return filename
            except:
                return None

    def get_auto_greeting(self):
        greetings = [
            f"Welcome to Media Web 6 Services! I'm {self.name}. Transforming Business Through Digital Innovation. How can I help you today?",
            f"Hello! I'm {self.name}, your AI assistant. We blend creativity, innovation, and technology to craft digital solutions. What brings you here?"
        ]
        if self.user_name:
            greetings.append(f"Welcome back, {self.user_name}! How can I assist you with your digital needs today?")
        return random.choice(greetings)

    def set_user_language(self, language_code):
        """Set user's preferred language for voice output"""
        if language_code in self.supported_languages:
            self.user_language = language_code
            print(f"🗣️ User language set to: {self.supported_languages[language_code]}")
            return True
        return False

    def generate_response(self, message):
        """Generate response - Try API first, fallback to intelligent engine"""
        if not message:
            return None
        
        # Detect language from user message
        detected_lang = self.detect_language(message)
        if detected_lang in self.supported_languages:
            self.user_language = detected_lang
        
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
        'services': len(MEDIA_WEB_6_KNOWLEDGE['services']),
        'languages_supported': list(MEDIA_WEB_6_KNOWLEDGE['response_engine'].supported_languages.keys()) if hasattr(MEDIA_WEB_6_KNOWLEDGE, 'response_engine') else ['en']
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
            'language': bot.user_language
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
            
            # Get preferred language from request or detect
            preferred_lang = data.get('language', bot.user_language)
            if preferred_lang in bot.supported_languages:
                bot.user_language = preferred_lang
            
            # Generate audio in detected language
            audio_file = bot.generate_audio(response, bot.user_language)
            
            if len(bot.conversation_history) > 50:
                bot.conversation_history = bot.conversation_history[-50:]
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'response': response,
                'audio_url': f"/api/audio/{audio_file}" if audio_file else None,
                'user_name': bot.user_name,
                'history_count': len(bot.conversation_history),
                'mode': 'api' if bot.use_api else 'fallback',
                'language': bot.user_language,
                'language_name': bot.supported_languages.get(bot.user_language, 'English')
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
            'language': bot.user_language if bot else 'en',
            'languages': bot.supported_languages if bot else ['en']
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
    print("🤖  MEDIA WEB 6 AI - HYBRID MODE WITH MULTI-LANGUAGE")
    print("=" * 60)
    print(f"📍 Server: http://0.0.0.0:{port}")
    print(f"🧠 API Mode: {'✅ Active' if API_WORKING else '❌ Fallback Mode'}")
    print(f"📚 Knowledge Base: {'✅ Loaded'}")
    print(f"🎤 Voice: {'✅ Enabled'} (Multi-language support)")
    print(f"🗣️ Languages: English, Hindi, Tamil, Telugu, Malayalam, Kannada, French, German, Spanish, Japanese, Chinese, Arabic")
    print(f"🏢 Company: {MEDIA_WEB_6_KNOWLEDGE['company']['name']}")
    print(f"📞 Contact: {MEDIA_WEB_6_KNOWLEDGE['contact']['phone_primary']}")
    print(f"📧 Email: {MEDIA_WEB_6_KNOWLEDGE['contact']['email']}")
    print("=" * 60)
    if not API_WORKING:
        print("⚠️  Grok API not available - Using INTELLIGENT FALLBACK mode")
        print("✅  All responses are pre-trained with your company data")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)