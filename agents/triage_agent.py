import os
import json
import requests
import re
import sqlite3
import pickle
import pandas as pd

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Load ML model for differential diagnosis
try:
    with open('final_disease_model.pkl', 'rb') as f:
        disease_model = pickle.load(f)
    with open('final_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    remedy_df = pd.read_csv('final_remedy_dataset.csv')
    ML_MODEL_LOADED = True
except:
    ML_MODEL_LOADED = False
    print("Warning: ML model not loaded for differential diagnosis")

def get_db_connection():
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def check_critical_vitals(patient_id: int) -> dict:
    """Checks the patient's latest BP and SUGAR readings."""
    conn = get_db_connection()
    try:
        latest_bp = conn.execute(
            "SELECT value1, value2 FROM readings WHERE patient_id = ? AND reading_type = 'BP' ORDER BY timestamp DESC LIMIT 1",
            (patient_id,)
        ).fetchone()
        latest_sugar = conn.execute(
            "SELECT value1 FROM readings WHERE patient_id = ? AND reading_type = 'SUGAR' ORDER BY timestamp DESC LIMIT 1",
            (patient_id,)
        ).fetchone()
        
        bp_status = f"{latest_bp['value1']}/{latest_bp['value2']}" if latest_bp else "N/A"
        sugar_status = f"{latest_sugar['value1']} mg/dL" if latest_sugar else "N/A"
        
        return {
            "latest_bp": bp_status,
            "latest_sugar": sugar_status,
            "risk_check": "High" if (latest_bp and latest_bp['value1'] >= 160) or (latest_sugar and latest_sugar['value1'] >= 250) else "Normal"
        }
    finally:
        conn.close()

def get_differential_diagnosis(symptoms_text: str, top_n: int = 3) -> list:
    """
    Get differential diagnosis using local ML model
    
    Returns:
        List of (disease, confidence) tuples
    """
    if not ML_MODEL_LOADED:
        return []
    
    try:
        # Vectorize symptoms
        input_vector = vectorizer.transform([symptoms_text])
        
        # Get prediction probabilities
        probabilities = disease_model.predict_proba(input_vector)[0]
        classes = disease_model.classes_
        
        # Get top N predictions
        top_indices = probabilities.argsort()[-top_n:][::-1]
        
        differential = []
        for idx in top_indices:
            differential.append({
                "disease": classes[idx],
                "confidence": float(probabilities[idx])
            })
        
        return differential
    except Exception as e:
        print(f"Differential diagnosis error: {e}")
        return []

def detect_red_flags(symptoms: list, notes: str) -> list:
    """Detect emergency keywords in symptoms and notes"""
    red_flag_keywords = [
        "chest pain", "difficulty breathing", "severe headache", "unconscious",
        "bleeding", "stroke", "seizure", "severe abdominal pain", "vomiting blood"
    ]
    
    text = " ".join(symptoms).lower() + " " + notes.lower()
    detected_flags = []
    
    for keyword in red_flag_keywords:
        if keyword in text:
            detected_flags.append(keyword)
    
    return detected_flags

def extract_json(text):
    """Safely extract JSON object from LLM output"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            return None
    return None

def triage_agent(input_data: dict) -> dict:
    """
    Enhanced Triage Agent with differential diagnosis
    
    Args:
        input_data: Patient data with symptoms, vitals, etc.
        
    Returns:
        Comprehensive triage assessment
    """
    # Check vitals
    vitals = check_critical_vitals(input_data["patient_id"])
    
    # Get differential diagnosis
    symptoms_text = input_data.get("chief_complaint", "") + " " + " ".join(input_data.get("symptoms", []))
    differential = get_differential_diagnosis(symptoms_text, top_n=3)
    
    # Detect red flags
    red_flags = detect_red_flags(input_data.get("symptoms", []), input_data.get("notes", ""))
    
    # Build enhanced prompt
    # Build enhanced prompt
    differential_text = "\n".join([f"- {d['disease']} ({d['confidence']*100:.1f}%)" for d in differential]) if differential else "Not available"
    
    # Get home remedies if available (for Low/Moderate risk suggestions)
    from agents.chat_agent import get_home_remedies
    suggested_remedies = get_home_remedies(input_data.get("symptoms", []), "en")

    prompt = f"""
You are a clinical triage AI for rural India. Your decisions must be safe but BALANCED. Do not be overly alarmist for common, mild symptoms.

Patient details:
Age: {input_data.get("age")}
Chief complaint: {input_data.get("chief_complaint")}
Symptoms: {", ".join(input_data.get("symptoms", []))}
Notes: {input_data.get("notes")}

CRITICAL VITALS:
- Latest BP: {vitals['latest_bp']}
- Latest Sugar: {vitals['latest_sugar']}
- Vitals Risk: {vitals['risk_check']}

DIFFERENTIAL DIAGNOSIS (ML Model):
{differential_text}

RED FLAGS DETECTED: {", ".join(red_flags) if red_flags else "None"}

AVAILABLE HOME REMEDIES (Reference):
{suggested_remedies}

TASK:
1. Assess risk: Low / Moderate / High / Critical
   - LOW: Mild symptoms (cold, cough, mild headache) with NORMAL vitals and NO red flags.
   - MODERATE: Persistent symptoms, moderate pain, or slightly abnormal vitals.
   - HIGH: Red flags present, or Vitals are Critical (BP >= 160/100 or Sugar >= 250).
   - CRITICAL: Life-threatening (chest pain, unconsciousness, severe bleeding).

2. Decide next action: Home Care / ASHA Follow-up / Doctor Consultation / Emergency
3. Provide medical reasoning.
4. List ASHA instructions.
5. List Home Remedies (if Risk is LOW or MODERATE).

RULES:
- If RED FLAGS detected, risk must be at least High.
- If Vitals Risk is High, final risk must be at least High.
- For LOW risk, suggest "Home Care" or "ASHA Follow-up".
- Respond ONLY in valid JSON.

FORMAT:
{{
  "risk": "Low/Moderate/High/Critical",
  "decision": "Next Action",
  "reasoning": "Explanation",
  "primary_diagnosis": "Likely condition",
  "asha_instructions": ["Step 1", "Step 2"],
  "home_remedies": ["Remedy 1", "Remedy 2"],
  "red_flags_to_watch": ["Flag 1"]
}}
"""
    
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"]
        parsed = extract_json(content)
        
        if parsed:
            # Add differential diagnosis to output
            parsed["differential_diagnosis"] = differential
            parsed["detected_red_flags"] = red_flags
            return parsed
        else:
            raise ValueError("JSON parse failed")
    
    except Exception as e:
        print("Triage agent fallback:", e)
        return {
            "risk": "High" if red_flags or vitals['risk_check'] == "High" else "Moderate",
            "decision": "Emergency" if red_flags else "ASHA Follow-up",
            "reasoning": f"AI triage fallback. Red flags: {red_flags}. Vitals: {vitals['risk_check']}",
            "primary_diagnosis": differential[0]["disease"] if differential else "Unknown",
            "differential_diagnosis": differential,
            "detected_red_flags": red_flags,
            "asha_instructions": ["Monitor patient closely", "Check vitals daily", "Report any worsening"],
            "red_flags_to_watch": ["Severe symptoms", "High fever", "Difficulty breathing"]
        }
