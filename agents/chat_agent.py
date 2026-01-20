"""
Patient Chat Agent - Hybrid AI-powered chatbot for patient health assistance
Uses Gemini/OpenRouter for natural language understanding with structured follow-ups
"""

import os
import json
import requests
import re
import sqlite3
from typing import Optional

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# =====================================================
# HOME REMEDIES DATABASE (Bilingual)
# =====================================================
HOME_REMEDIES = {
    "fever": {
        "en": [
            "🌡️ Rest in a cool, comfortable room",
            "💧 Drink plenty of fluids (water, ORS, coconut water)",
            "🧊 Apply wet cloth on forehead (lukewarm water)",
            "🍵 Drink ginger tea with honey",
            "⚠️ If fever exceeds 103°F (39.4°C) or lasts more than 3 days, consult a doctor"
        ],
        "hi": [
            "🌡️ ठंडे, आरामदायक कमरे में आराम करें",
            "💧 खूब पानी पिएं (पानी, ORS, नारियल पानी)",
            "🧊 माथे पर गीला कपड़ा रखें (गुनगुने पानी से)",
            "🍵 शहद के साथ अदरक की चाय पिएं",
            "⚠️ अगर बुखार 103°F से ज्यादा हो या 3 दिन से ज्यादा रहे, तो डॉक्टर से मिलें"
        ]
    },
    "headache": {
        "en": [
            "😌 Rest in a dark, quiet room",
            "💧 Drink water - dehydration often causes headaches",
            "🧊 Apply cold compress on forehead",
            "💆 Gentle head and neck massage",
            "🌿 Peppermint or eucalyptus oil on temples"
        ],
        "hi": [
            "😌 अंधेरे, शांत कमरे में आराम करें",
            "💧 पानी पिएं - डिहाइड्रेशन से सिरदर्द होता है",
            "🧊 माथे पर ठंडा कपड़ा रखें",
            "💆 हल्की सिर और गर्दन की मालिश करें",
            "🌿 कनपटी पर पुदीना या नीलगिरी का तेल लगाएं"
        ]
    },
    "cold": {
        "en": [
            "🍵 Drink warm liquids (ginger tea, turmeric milk)",
            "💨 Steam inhalation 2-3 times a day",
            "🍯 Honey and warm water for throat relief",
            "🧂 Gargle with warm salt water",
            "😴 Get plenty of rest"
        ],
        "hi": [
            "🍵 गर्म पेय पिएं (अदरक चाय, हल्दी दूध)",
            "💨 दिन में 2-3 बार भाप लें",
            "🍯 गले के लिए शहद और गर्म पानी",
            "🧂 गर्म नमक के पानी से गरारे करें",
            "😴 पूरा आराम करें"
        ]
    },
    "cough": {
        "en": [
            "🍯 Honey with warm water or tea",
            "🍵 Tulsi (basil) and ginger tea",
            "💨 Steam inhalation with eucalyptus",
            "🧂 Gargle with warm salt water",
            "🌿 Licorice (mulethi) to chew"
        ],
        "hi": [
            "🍯 शहद गर्म पानी या चाय के साथ",
            "🍵 तुलसी और अदरक की चाय",
            "💨 नीलगिरी के साथ भाप लें",
            "🧂 गर्म नमक के पानी से गरारे",
            "🌿 मुलेठी चबाएं"
        ]
    },
    "stomach_pain": {
        "en": [
            "🌿 Drink ajwain (carom seeds) water",
            "🍵 Ginger tea or jeera water",
            "🔥 Apply warm compress on stomach",
            "🚫 Avoid spicy and oily food",
            "😌 Rest and avoid heavy meals"
        ],
        "hi": [
            "🌿 अजवाइन का पानी पिएं",
            "🍵 अदरक की चाय या जीरा पानी",
            "🔥 पेट पर गर्म सेंक करें",
            "🚫 मसालेदार और तला खाना न खाएं",
            "😌 आराम करें और भारी खाना न खाएं"
        ]
    },
    "body_pain": {
        "en": [
            "🔥 Apply warm compress on painful area",
            "💆 Gentle massage with mustard oil",
            "😴 Get adequate rest",
            "🧘 Light stretching exercises",
            "🍵 Turmeric milk before bed"
        ],
        "hi": [
            "🔥 दर्द वाली जगह पर गर्म सेंक करें",
            "💆 सरसों के तेल से हल्की मालिश",
            "😴 पर्याप्त आराम करें",
            "🧘 हल्की स्ट्रेचिंग करें",
            "🍵 सोने से पहले हल्दी वाला दूध"
        ]
    },
    "general": {
        "en": [
            "💧 Stay hydrated - drink 8-10 glasses of water",
            "😴 Get 7-8 hours of sleep",
            "🥗 Eat nutritious, home-cooked meals",
            "🚶 Light physical activity if feeling well",
            "⚠️ If symptoms persist for more than 3 days, consult a doctor"
        ],
        "hi": [
            "💧 हाइड्रेटेड रहें - 8-10 गिलास पानी पिएं",
            "😴 7-8 घंटे की नींद लें",
            "🥗 पौष्टिक, घर का बना खाना खाएं",
            "🚶 अगर ठीक महसूस करें तो हल्की फिजिकल एक्टिविटी",
            "⚠️ अगर लक्षण 3 दिन से ज्यादा रहें, डॉक्टर से मिलें"
        ]
    }
}

# =====================================================
# HEALTH TIPS (Bilingual)
# =====================================================
HEALTH_TIPS = {
    "en": [
        "💧 Drink at least 8 glasses of water daily",
        "🥗 Include green vegetables in every meal",
        "🚶 Walk for at least 30 minutes daily",
        "😴 Sleep 7-8 hours every night",
        "🧘 Practice deep breathing for 5 minutes daily",
        "🍎 Eat seasonal fruits for natural vitamins",
        "🧂 Reduce salt and sugar intake",
        "🚭 Avoid tobacco and limit alcohol",
        "🧴 Wash hands frequently with soap",
        "💉 Keep vaccinations up to date"
    ],
    "hi": [
        "💧 रोज़ कम से कम 8 गिलास पानी पिएं",
        "🥗 हर भोजन में हरी सब्जियां शामिल करें",
        "🚶 रोज़ कम से कम 30 मिनट टहलें",
        "😴 हर रात 7-8 घंटे सोएं",
        "🧘 रोज़ 5 मिनट गहरी सांस लें",
        "🍎 प्राकृतिक विटामिन के लिए मौसमी फल खाएं",
        "🧂 नमक और चीनी कम खाएं",
        "🚭 तंबाकू से बचें और शराब सीमित करें",
        "🧴 साबुन से बार-बार हाथ धोएं",
        "💉 टीकाकरण समय पर करवाएं"
    ]
}


def get_db_connection():
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def call_llm(messages: list, temperature: float = 0.7) -> str:
    """Call OpenRouter/Gemini API for chat responses"""
    if not OPENROUTER_API_KEY:
        return "I apologize, but the AI service is currently unavailable. Please try again later."
    
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"[CHAT AGENT] API Error: {response.status_code} - {response.text}")
            return "I'm having trouble processing your request. Please try again."
    except Exception as e:
        print(f"[CHAT AGENT] Exception: {e}")
        return "I'm having trouble connecting. Please try again."


def extract_symptoms_from_message(message: str) -> dict:
    """Use AI to extract symptoms and intent from user message"""
    system_prompt = """You are a medical symptom extractor. Analyze the user's message and extract:
1. symptoms: List of symptoms mentioned (in English, normalized)
2. duration: How long symptoms have been present (if mentioned)
3. severity: mild/moderate/severe (if indicated)
4. intent: "symptom_report", "view_prescriptions", "health_tips", or "general_query"

Respond ONLY in JSON format:
{"symptoms": ["fever", "headache"], "duration": "2 days", "severity": "mild", "intent": "symptom_report"}

Common symptom mappings:
- बुखार/bukhar/fever -> fever
- सिरदर्द/sar dard/headache -> headache
- खांसी/khansi/cough -> cough
- सर्दी/जुकाम/cold -> cold
- पेट दर्द/stomach pain -> stomach_pain
- बदन दर्द/body pain -> body_pain"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    try:
        response = call_llm(messages, temperature=0.1)
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[CHAT AGENT] Symptom extraction error: {e}")
    
    return {"symptoms": [], "duration": None, "severity": None, "intent": "general_query"}


def get_home_remedies(symptoms: list, language: str = "en") -> str:
    """Get home remedies for given symptoms"""
    lang = "hi" if language.lower() in ["hi", "hindi", "हिंदी"] else "en"
    
    remedies_text = ""
    matched_symptoms = []
    
    for symptom in symptoms:
        symptom_lower = symptom.lower().replace(" ", "_")
        if symptom_lower in HOME_REMEDIES:
            matched_symptoms.append(symptom)
            remedies = HOME_REMEDIES[symptom_lower][lang]
            
            if lang == "hi":
                remedies_text += f"\n\n**{symptom.title()} के लिए घरेलू उपचार:**\n"
            else:
                remedies_text += f"\n\n**Home remedies for {symptom.title()}:**\n"
            
            for remedy in remedies:
                remedies_text += f"• {remedy}\n"
    
    # Add general remedies if no specific match
    if not matched_symptoms:
        remedies = HOME_REMEDIES["general"][lang]
        if lang == "hi":
            remedies_text = "\n**सामान्य स्वास्थ्य सुझाव:**\n"
        else:
            remedies_text = "\n**General health tips:**\n"
        for remedy in remedies:
            remedies_text += f"• {remedy}\n"
    
    return remedies_text


def get_random_health_tips(language: str = "en", count: int = 3) -> str:
    """Get random health tips"""
    import random
    lang = "hi" if language.lower() in ["hi", "hindi", "हिंदी"] else "en"
    
    tips = random.sample(HEALTH_TIPS[lang], min(count, len(HEALTH_TIPS[lang])))
    
    if lang == "hi":
        text = "💡 **आज के स्वास्थ्य सुझाव:**\n\n"
    else:
        text = "💡 **Today's Health Tips:**\n\n"
    
    for tip in tips:
        text += f"• {tip}\n"
    
    return text


def get_patient_prescriptions(patient_id: int, language: str = "en") -> str:
    """Fetch patient's prescriptions"""
    conn = get_db_connection()
    try:
        prescriptions = conn.execute("""
            SELECT p.*, d.name as doctor_name
            FROM prescriptions p
            LEFT JOIN doctors d ON p.doctor_id = d.id
            WHERE p.patient_id = ?
            ORDER BY p.created_at DESC
            LIMIT 5
        """, (patient_id,)).fetchall()
        
        if not prescriptions:
            if language.lower() in ["hi", "hindi"]:
                return "📋 आपके लिए कोई प्रिस्क्रिप्शन नहीं मिला।"
            return "📋 No prescriptions found for you."
        
        if language.lower() in ["hi", "hindi"]:
            text = "📋 **आपकी दवाइयां:**\n\n"
        else:
            text = "📋 **Your Prescriptions:**\n\n"
        
        for rx in prescriptions:
            text += f"💊 **{rx['medication']}** - {rx['dosage']}\n"
            if rx['notes']:
                text += f"   📝 {rx['notes']}\n"
            text += f"   👨‍⚕️ Dr. {rx['doctor_name'] or 'Unknown'}\n\n"
        
        return text
    finally:
        conn.close()


def assess_risk_level(symptoms: list, duration: str, severity: str) -> str:
    """Simple risk assessment based on symptoms"""
    high_risk_symptoms = ["chest pain", "difficulty breathing", "unconscious", "severe bleeding", "stroke"]
    moderate_symptoms = ["high fever", "persistent vomiting", "severe headache"]
    
    symptom_text = " ".join(symptoms).lower()
    
    # Check for high-risk
    for hs in high_risk_symptoms:
        if hs in symptom_text:
            return "HIGH"
    
    # Check severity
    if severity and severity.lower() == "severe":
        return "MODERATE"
    
    # Check for moderate risk
    for ms in moderate_symptoms:
        if ms in symptom_text:
            return "MODERATE"
    
    # Check duration
    if duration:
        duration_lower = duration.lower()
        if any(x in duration_lower for x in ["week", "weeks", "month", "months"]):
            return "MODERATE"
    
    return "LOW"


def process_chat_message(patient_id: int, message: str, conversation_history: list, language: str = "en") -> dict:
    """
    Main function to process patient chat messages
    
    Returns:
        {
            "response": str,  # Bot response
            "intent": str,    # Detected intent
            "risk_level": str # LOW/MODERATE/HIGH (for symptom reports)
        }
    """
    lang = "hi" if language.lower() in ["hi", "hindi", "हिंदी"] else "en"
    
    # Extract symptoms and intent
    extracted = extract_symptoms_from_message(message)
    intent = extracted.get("intent", "general_query")
    
    # Handle different intents
    if intent == "view_prescriptions":
        response = get_patient_prescriptions(patient_id, lang)
        return {"response": response, "intent": intent, "risk_level": None}
    
    elif intent == "health_tips":
        response = get_random_health_tips(lang)
        return {"response": response, "intent": intent, "risk_level": None}
    
    elif intent == "symptom_report" and extracted.get("symptoms"):
        symptoms = extracted["symptoms"]
        duration = extracted.get("duration")
        severity = extracted.get("severity")
        
        # Assess risk level
        risk_level = assess_risk_level(symptoms, duration, severity)
        
        if risk_level == "HIGH":
            # --- FETCH HOSPITALS ---
            hospitals = []
            conn = get_db_connection()
            try:
                # Get Patient District
                patient = conn.execute("SELECT district FROM patients WHERE id = ?", (patient_id,)).fetchone()
                district = patient['district'] if patient else 'Dhule'
                
                # Get Hospitals
                hospitals = conn.execute("SELECT name, location, contact_number FROM hospitals WHERE district = ? LIMIT 3", (district,)).fetchall()
            except Exception as e:
                print(f"[CHAT AGENT] Hospital Fetch Error: {e}")
                district = "your district"
            finally:
                conn.close()

            # --- BUILD RICH HTML RESPONSE ---
            import urllib.parse
            
            # Common Elements
            ambulance_num = "108"
            near_me_link = "https://www.google.com/maps/search/government+hospitals+near+me"
            
            if lang == "hi":
                header_title = "तत्काल चिकित्सा सहायता आवश्यक!"
                header_sub = "गंभीर लक्षण पाए गए"
                body_text = "कृपया तुरंत नजदीकी अस्पताल जाएं या एम्बुलेंस बुलाएं। अपने ASHA कार्यकर्ता से संपर्क करें।"
                btn_ambulance = "एम्बुलेंस बुलाएं (108)"
                btn_near_me = "मेरे पास के अस्पताल खोजें"
                hospital_header = "नजदीकी सरकारी अस्पताल"
            else:
                header_title = "IMMEDIATE ATTENTION NEEDED"
                header_sub = "Serious symptoms detected"
                body_text = "Please visit the nearest hospital or call emergency immediately. Contact your ASHA worker."
                btn_ambulance = "CALL AMBULANCE (108)"
                btn_near_me = "Find Hospitals Near Me"
                hospital_header = "Nearby Government Hospitals"

            # Build Hospital Cards HTML
            hospitals_html = ""
            if hospitals:
                for h in hospitals:
                    query = urllib.parse.quote(f"{h['name']} {h['location']}")
                    map_link = f"https://www.google.com/maps/search/?api=1&query={query}"
                    
                    hospitals_html += f"""
                    <div class="card mb-2 border-0 shadow-sm" style="background: rgba(255,255,255,0.9);">
                        <div class="card-body p-2 d-flex justify-content-between align-items-center">
                             <div style="flex:1">
                                <strong class="text-dark small">{h['name']}</strong><br>
                                <small class="text-muted" style="font-size:0.75rem"><i class="fa-solid fa-map-pin me-1"></i>{h['location']}</small>
                                <div class="mt-1"><small class="text-success"><i class="fa-solid fa-phone me-1"></i>{h['contact_number']}</small></div>
                             </div>
                             <a href="{map_link}" target="_blank" class="btn btn-sm btn-outline-primary ms-2">
                                <i class="fa-solid fa-location-arrow"></i>
                             </a>
                        </div>
                    </div>"""
            else:
                fallback_text = f"District Hospital ({district})"
                hospitals_html = f"""<div class="text-muted small text-center p-2">No specific data. Go to {fallback_text}</div>"""

            # Construct Final HTML Card
            response = f"""
            <div class="alert alert-danger border-2 border-danger shadow-sm mb-0">
                <div class="d-flex align-items-center mb-3">
                    <div class="bg-danger text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width:50px; height:50px; min-width:50px;">
                        <i class="fa-solid fa-truck-medical fa-lg"></i>
                    </div>
                    <div>
                       <h6 class="alert-heading fw-bold mb-0 text-danger text-uppercase">{header_title}</h6>
                       <small class="text-dark fw-bold">{header_sub}</small>
                    </div>
                </div>
                
                <p class="mb-3 small text-dark border-bottom border-danger pb-2">{body_text}</p>
                
                <div class="d-grid gap-2 mb-3">
                    <a href="tel:{ambulance_num}" class="btn btn-danger fw-bold py-2 shadow-sm pulse-animation">
                        <i class="fa-solid fa-phone-volume me-2"></i> {btn_ambulance}
                    </a>
                    <a href="{near_me_link}" target="_blank" class="btn btn-outline-danger fw-bold py-2 shadow-sm">
                        <i class="fa-solid fa-location-crosshairs me-2"></i> {btn_near_me}
                    </a>
                </div>

                <h6 class="fw-bold small text-dark mb-2"><i class="fa-solid fa-hospital me-1"></i> {hospital_header}</h6>
                {hospitals_html}
            </div>"""
        
        elif risk_level == "MODERATE":
            remedies = get_home_remedies(symptoms, lang)
            if lang == "hi":
                response = f"""⚠️ **डॉक्टर से परामर्श की सलाह**

आपके लक्षणों को डॉक्टर को दिखाना चाहिए। कृपया जल्द से जल्द डॉक्टर से मिलें।

इस बीच, आप ये घरेलू उपचार आज़मा सकते हैं:
{remedies}

अगर लक्षण बिगड़ें, तुरंत अस्पताल जाएं।"""
            else:
                response = f"""⚠️ **Doctor Consultation Recommended**

Your symptoms should be evaluated by a doctor. Please schedule a visit soon.

Meanwhile, you can try these home remedies:
{remedies}

If symptoms worsen, visit the hospital immediately."""
        
        else:  # LOW risk
            remedies = get_home_remedies(symptoms, lang)
            if lang == "hi":
                response = f"""✅ **घरेलू उपचार से राहत मिल सकती है**

आपके लक्षण हल्के लगते हैं। ये घरेलू उपचार आज़माएं:
{remedies}

अगर 2-3 दिन में सुधार न हो, तो डॉक्टर से मिलें।"""
            else:
                response = f"""✅ **Home Remedies May Help**

Your symptoms appear to be mild. Try these home remedies:
{remedies}

If no improvement in 2-3 days, please consult a doctor."""
        
        return {"response": response, "intent": intent, "risk_level": risk_level}

    elif intent == "find_hospitals":
        # --- FIND HOSPITALS INTENT (BLUE CARD) ---
        hospitals = []
        conn = get_db_connection()
        try:
             # Get Patient District
            patient = conn.execute("SELECT district FROM patients WHERE id = ?", (patient_id,)).fetchone()
            district = patient['district'] if patient else 'Dhule'
            # Get Hospitals
            hospitals = conn.execute("SELECT name, location, contact_number FROM hospitals WHERE district = ? LIMIT 3", (district,)).fetchall()
        finally:
            conn.close()
        
        # Build HTML
        import urllib.parse
        near_me_link = "https://www.google.com/maps/search/government+hospitals+near+me"

        if lang == "hi":
             title = "सरकारी अस्पताल सूची"
             btn_near_me = "मेरे पास के अस्पताल खोजें"
        else:
             title = "Government Hospitals List"
             btn_near_me = "Find Hospitals Near Me"

        hospitals_html = ""
        if hospitals:
            for h in hospitals:
                query = urllib.parse.quote(f"{h['name']} {h['location']}")
                map_link = f"https://www.google.com/maps/search/?api=1&query={query}"
                hospitals_html += f"""
                <div class="card mb-2 border-0 shadow-sm">
                    <div class="card-body p-2 d-flex justify-content-between align-items-center">
                            <div style="flex:1">
                            <strong class="text-dark small">{h['name']}</strong><br>
                            <small class="text-muted" style="font-size:0.75rem"><i class="fa-solid fa-map-pin me-1"></i>{h['location']}</small>
                            <div class="mt-1"><small class="text-success"><i class="fa-solid fa-phone me-1"></i>{h['contact_number']}</small></div>
                            </div>
                            <a href="{map_link}" target="_blank" class="btn btn-sm btn-outline-primary ms-2">
                            <i class="fa-solid fa-location-arrow"></i>
                            </a>
                    </div>
                </div>"""
        else:
             hospitals_html = f"""<div class="text-muted text-center p-3">No hospitals found in {district}.</div>"""

        response = f"""
        <div class="alert alert-info border-2 border-info shadow-sm mb-0" style="background-color: #f0f9ff; border-color: #0ea5e9;">
            <div class="d-flex align-items-center mb-3">
                <div class="bg-info text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width:40px; height:40px; min-width:40px;">
                    <i class="fa-solid fa-hospital fa-lg"></i>
                </div>
                <h6 class="alert-heading fw-bold mb-0 text-dark">{title} ({district})</h6>
            </div>
            
            <a href="{near_me_link}" target="_blank" class="btn btn-info text-white w-100 mb-3 fw-bold py-2 shadow-sm">
                <i class="fa-solid fa-location-crosshairs me-2"></i> {btn_near_me}
            </a>

            {hospitals_html}
        </div>"""
        
        return {"response": response, "intent": intent, "risk_level": None}
    
    else:
        # General conversation - use AI
        system_prompt = f"""You are a friendly health assistant for rural patients in India. 
Respond helpfully in {'Hindi' if lang == 'hi' else 'English'}.
Keep responses short and simple.
If asked about symptoms, suggest they describe their symptoms in detail.
Never diagnose or prescribe medications.
Remind them to consult a doctor for serious concerns."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-5:])  # Last 5 messages for context
        messages.append({"role": "user", "content": message})
        
        response = call_llm(messages)
        return {"response": response, "intent": "general_query", "risk_level": None}


def get_greeting(language: str = "en") -> str:
    """Get initial greeting message"""
    if language.lower() in ["hi", "hindi", "हिंदी"]:
        return """🩺 **नमस्ते! मैं आपका स्वास्थ्य सहायक हूं।**

मैं आपकी इन चीज़ों में मदद कर सकता हूं:
• 🤒 अपने लक्षण बताएं और सलाह पाएं
• 💊 अपनी प्रिस्क्रिप्शन देखें
• 💡 स्वास्थ्य सुझाव लें

आप क्या जानना चाहते हैं?"""
    else:
        return """🩺 **Hello! I'm your Health Assistant.**

I can help you with:
• 🤒 Report symptoms and get advice
• 💊 View your prescriptions
• 💡 Get health tips

How can I help you today?"""
