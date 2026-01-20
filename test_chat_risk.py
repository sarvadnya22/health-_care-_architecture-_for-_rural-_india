import sqlite3
import json
from agents.chat_agent import process_chat_message

def test_hospital_recommendation():
    print("🧪 Testing Chat Agent Hospital Recommendation...")
    
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    try:
        # 1. Setup Test Patient in 'Dhule'
        import random
        phone = f"+91{random.randint(1000000000, 9999999999)}"
        cursor.execute("INSERT INTO patients (name, phone_number, district, password_hash) VALUES ('Test Hopsital Patient', ?, 'Dhule', 'hash')", (phone,))
        patient_id = cursor.lastrowid
        conn.commit()
        
        # 2. Simulate High Risk Message
        message = "I have severe chest pain and cannot breathe."
        history = []
        
        # MOCK the extraction since we might not have LLM access in test env
        from unittest.mock import patch
        with patch('agents.chat_agent.extract_symptoms_from_message') as mock_extract:
            mock_extract.return_value = {
                "symptoms": ["chest pain", "difficulty breathing"],
                "duration": "1 hour",
                "severity": "severe",
                "intent": "symptom_report"
            }
            
            print(f"\n[User]: {message}")
            result = process_chat_message(patient_id, message, history, language="en")
        
        response = result.get('response', '')
        risk = result.get('risk_level')
        
        print(f"\n[Bot Risk]: {risk}")
        print(f"\n[Bot Response]:\n{response}")
        
        # 3. Assertions
        if risk != "HIGH":
            print("\n❌ FAIL: Risk level should be HIGH")
        elif 'class="alert alert-danger' in response and 'href="tel:108"' in response and 'government+hospitals+near+me' in response:
            print("\n✅ PASS: Found Rich HTML Card, Ambulance Button, and Near Me Link")
        else:
            print("\n❌ FAIL: Rich HTML elements NOT found")
            print("Response Snippet:", response[:200], "...")

        # 4. Test Find Hospitals Intent (New)
        print("\n--- Testing Find Hospitals Intent ---")
        message_info = "Where is the nearest government hospital?"
        
        # Mock Intent
        with patch('agents.chat_agent.extract_symptoms_from_message') as mock_extract:
             mock_extract.return_value = {
                "symptoms": [],
                "intent": "find_hospitals"
            }
             result_info = process_chat_message(patient_id, message_info, history, language="en")
        
        resp_info = result_info.get('response', '')
        if 'class="alert alert-info' in resp_info and 'government+hospitals+near+me' in resp_info:
             print("✅ PASS: Found Info Card and Near Me Link")
        else:
             print("❌ FAIL: Info Card not found")
             print(resp_info[:200])
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_hospital_recommendation()
