
import os
from dotenv import load_dotenv
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
import json
import random
import string
import pandas as pd
import pickle
import requests
import re
from datetime import datetime

# --- AGENTIC AI IMPORTS ---
from agents.orchestrator import orchestrator

# --- Load Environment Variables ---
load_dotenv()

# --- Main Application Setup ---
app = Flask(__name__,
            template_folder='english/templates',
            static_folder='english')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_dev_key") 

# --- TWILIO CONFIGURATION ---
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER" )
HEALTH_WORKER_PHONE = os.getenv("HEALTH_WORKER_PHONE" ) 

twilio_client = None
if ACCOUNT_SID and AUTH_TOKEN:
    try:
        twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
    except Exception as e:
        print(f"Twilio client initialization failed: {e}")
        twilio_client = None

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute("SELECT * FROM patients LIMIT 1")
    except sqlite3.OperationalError:
        print("Database schema not found. Please run setup_database.py")
    
    # Ensure care_workflows exists
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS care_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                current_state TEXT,
                next_action TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            );
        """)
    except Exception as e:
        print(f"Error creating care_workflows table: {e}")
        
    # Ensure patient_alerts exists (CRITICAL FIX)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patient_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                vital_name TEXT,
                is_acknowledged INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            );
        """)
    except Exception as e:
        print(f"Error creating patient_alerts table: {e}")
    
    # Ensure pharmacy tables exist
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pharmacies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pharmacy_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pharmacy_id INTEGER,
                medication TEXT NOT NULL,
                stock_status TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
            );
        """)
        
        # Seed Pharmacy Data if empty
        if not conn.execute("SELECT * FROM pharmacies").fetchone():
            conn.execute("INSERT INTO pharmacies (name, location) VALUES ('Jeevan Raksha Pharmacy', 'Main Market, Rampur'), ('City Medical Store', 'District Hospital Road')")
            conn.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (1, 'Paracetamol 500mg', 'In Stock'), (1, 'Amoxicillin 250mg', 'Low Stock'), (2, 'Insulin', 'In Stock')")
            
    except Exception as e:
        print(f"Error creating pharmacy tables: {e}")
    
    conn.commit()
    conn.close()

def send_alert(phone_number, message):
    """Send SMS via Twilio"""
    print(f"[SMS] Attempting to send SMS to: {phone_number}", flush=True)
    print(f"[SMS] Twilio Client: {'Initialized' if twilio_client else 'NOT INITIALIZED'}", flush=True)
    print(f"[SMS] From Number: {TWILIO_PHONE_NUMBER}", flush=True)
    
    if not twilio_client:
        print(f"[SMS ERROR] Twilio client not initialized. Check ACCOUNT_SID and AUTH_TOKEN in .env", flush=True)
        print(f"[SMS FALLBACK] Would have sent to {phone_number}: {message[:100]}...", flush=True)
        return False
    
    if not TWILIO_PHONE_NUMBER:
        print(f"[SMS ERROR] TWILIO_PHONE_NUMBER is not set in .env", flush=True)
        return False
        
    try:
        result = twilio_client.messages.create(
            to=phone_number, 
            from_=TWILIO_PHONE_NUMBER, 
            body=message
        )
        print(f"[SMS SUCCESS] Message sent! SID: {result.sid}", flush=True)
        return True
    except Exception as e:
        print(f"[SMS ERROR] Twilio error: {e}", flush=True)
        return False

# --- Test SMS Route ---
@app.route("/test-sms")
def test_sms():
    """Test route to verify SMS functionality"""
    test_phone = request.args.get('phone', '+919834358534')
    print(f"[TEST SMS] Testing SMS to: {test_phone}", flush=True)
    result = send_alert(test_phone, "Test message from HealthGuard - If you receive this, SMS is working!")
    if result:
        return f"SMS sent successfully to {test_phone}! Check the terminal for details."
    else:
        return f"SMS FAILED to {test_phone}. Check terminal for error details."

# --- Website Routes ---
@app.route("/")
def home():
    return render_template("index.html")

# ... (Previous routes omitted for brevity in tool call, focusing on pharmacy implementation below) ...

@app.route("/pharmacy/login", methods=['GET', 'POST'])
def pharmacy_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Demo credentials for pharmacy login
        valid_creds = [
            ("pharmacy@nabha.gov", "pharmacy123"),
            ("pharm@health.com", "pharm123")
        ]
        
        if (email, password) in valid_creds:
            # Get the first pharmacy from database for session
            conn = get_db_connection()
            pharmacy = conn.execute("SELECT * FROM pharmacies LIMIT 1").fetchone()
            conn.close()
            
            session['pharmacy_logged_in'] = True
            session['pharmacy_id'] = pharmacy['id'] if pharmacy else 1
            session['pharmacy_name'] = pharmacy['name'] if pharmacy else 'Demo Pharmacy'
            
            flash(f"Welcome to Pharmacy Portal!", "success")
            return redirect(url_for('pharmacy_dashboard'))
        else:
            flash("Invalid credentials. Try pharmacy@nabha.gov / pharmacy123", "danger")
            
    return render_template("pharmacy_login.html")

@app.route("/pharmacy/dashboard", methods=['GET', 'POST'])
def pharmacy_dashboard():
    if not session.get('pharmacy_logged_in'):
        return redirect(url_for('pharmacy_login'))
        
    pharmacy_id = session.get('pharmacy_id')
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Handle Stock Updates
        for key, value in request.form.items():
            if key.startswith('stock_status_'):
                item_id = key.split('_')[-1]
                # Ensure this item belongs to the logged-in pharmacy
                conn.execute("UPDATE pharmacy_inventory SET stock_status = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ? AND pharmacy_id = ?", (value, item_id, pharmacy_id))
        conn.commit()
        flash("Stock statuses updated successfully.", "success")
        
    # Fetch ONLY this pharmacy's data
    pharmacy = conn.execute("SELECT * FROM pharmacies WHERE id = ?", (pharmacy_id,)).fetchone()
    
    # Keep the template structure working by passing a list containing just this pharmacy
    pharmacies = [pharmacy] if pharmacy else []
    
    inventory_data = {}
    if pharmacy:
        items = conn.execute("SELECT id, medication, stock_status FROM pharmacy_inventory WHERE pharmacy_id = ?", (pharmacy_id,)).fetchall()
        # Template expects medication_name but column is medication. 
        # Using a list comprehension to adapt if needed, but SQL alias is cleaner if I could change the query.
        # Actually proper fix: the previous code used `medication_name` in SELECT but `medication` in INSERT. 
        # `recreate_pharmacy_db` uses `medication`. Let's alias it for safety with the template.
        inventory_data[pharmacy['id']] = []
        for item in items:
            inventory_data[pharmacy['id']].append({
                'id': item['id'],
                'medication_name': item['medication'], # Alias for template compatibility
                'stock_status': item['stock_status']
            })
        
    conn.close()
    return render_template("pharmacy_dashboard.html", pharmacies=pharmacies, inventory_data=inventory_data)

@app.route("/pharmacy/add_medicine", methods=['POST'])
def add_new_medicine():
    if not session.get('pharmacy_logged_in'):
        return redirect(url_for('pharmacy_login'))
    
    pharmacy_id = session.get('pharmacy_id') # Use session, ignore form ID for security
    medication = request.form.get('medication_name')
    stock_status = request.form.get('stock_status')
    
    if pharmacy_id and medication:
        conn = get_db_connection()
        conn.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (?, ?, ?)", 
                     (pharmacy_id, medication, stock_status))
        conn.commit()
        conn.close()
        flash(f"Added {medication} to inventory.", "success")
        
    return redirect(url_for('pharmacy_dashboard'))

@app.route("/pharmacy/prescriptions")
def pharmacy_prescriptions():
    if not session.get('pharmacy_logged_in'):
        return redirect(url_for('pharmacy_login'))
    
    pharmacy_district = session.get('pharmacy_district')
    # Default to Dhule if None (e.g. old session), but better to re-login.
    if not pharmacy_district: 
         pharmacy_district = 'Dhule'
    
    conn = get_db_connection()
    
    # Get Pending Prescriptions - FILTERED BY DISTRICT
    # "Serve patients in your district"
    # Note: Using is_active=1 for pending (status column doesn't exist in schema)
    pending = conn.execute("""
        SELECT pr.*, p.name as patient_name, p.phone_number as patient_phone, p.district, p.village
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE pr.is_active = 1
        AND (p.district = ? OR p.district IS NULL) -- Handle legacy data with NULL district
        ORDER BY pr.timestamp DESC
    """, (pharmacy_district,)).fetchall()
    
    # Get History (Dispensed prescriptions - is_active = 0)
    history = conn.execute("""
        SELECT pr.*, p.name as patient_name 
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE pr.is_active = 0
        ORDER BY pr.timestamp DESC LIMIT 20
    """).fetchall()
    
    conn.close()
    return render_template("pharmacy_prescriptions.html", 
                         pending_prescriptions=pending, 
                         dispensed_history=history,
                         pharmacy_district=pharmacy_district)

@app.route("/pharmacy/dispense/<int:prescription_id>", methods=['POST'])
def dispense_medicine(prescription_id):
    if not session.get('pharmacy_logged_in'):
        return redirect(url_for('pharmacy_login'))
        
    pharmacy_id = session.get('pharmacy_id')
    
    conn = get_db_connection()
    # Update with dispensed_by
    try:
        conn.execute("UPDATE prescriptions SET status = 'Dispensed', dispensed_at = CURRENT_TIMESTAMP, dispensed_by = ? WHERE id = ?", (pharmacy_id, prescription_id))
        conn.commit()
        flash("Medication dispensed successfully.", "success")
    except Exception as e:
        print(f"Dispense Check Error: {e}")
        flash(f"Error dispensing: {e}", "danger")
        
    conn.close()
    return redirect(url_for('pharmacy_prescriptions'))

@app.route("/asha_training")
def asha_training():
    if not session.get('worker_logged_in'): 
        return redirect(url_for('worker_login'))
    return render_template("asha_training.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone_number'].strip()
        asha_phone = request.form['asha_worker_phone'].strip()
        password = request.form['password']
        age = request.form.get('age')
        gender = request.form.get('gender')
        village = request.form.get('village')
        district = request.form.get('district', 'Dhule') # Default to Dhule if not provided
        
        if phone.startswith('0'): phone = phone[1:]
        if not phone.startswith('+91'): phone = f"+91{phone}"
        if asha_phone.startswith('0'): asha_phone = asha_phone[1:]
        if not asha_phone.startswith('+91'): asha_phone = f"+91{asha_phone}" 
        
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO patients (name, phone_number, password_hash, asha_worker_phone, age, gender, village, district) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (name, phone, hashed_password, asha_phone, age, gender, village, district))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("This Patient Phone Number is already registered.", "danger")
            conn.close()
            return redirect(url_for('signup'))
        finally:
            conn.close()
            
        flash("Patient registration successful! Please log in.", "success")
        return redirect(url_for('login'))
        
    return render_template("signup.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone_number'].strip()
        password = request.form['password']
        
        if phone.startswith('0'): phone = phone[1:]
        if not phone.startswith('+91'): phone = f"+91{phone}"
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM patients WHERE phone_number = ?', (phone,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'], session['user_name'] = user['id'], user['name']
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid phone number or password.", "danger")
            return redirect(url_for('login'))
            
    return render_template("login.html")

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    
    # 1. Readings
    readings = conn.execute("SELECT *, strftime('%Y-%m-%d %-I:%M %p', timestamp) as formatted_time FROM readings WHERE patient_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
    
    # 2. Charts Logic
    chart_labels = []
    systolic_data = []
    diastolic_data = []

    try:
         # Get last 7 days of BP readings for chart
         chart_readings = conn.execute("""
            SELECT timestamp, value1, value2 
            FROM readings 
            WHERE patient_id = ? AND reading_type = 'BP' 
            ORDER BY timestamp ASC 
            LIMIT 20
         """, (user_id,)).fetchall()
         
         for r in chart_readings:
             # Simplify time label
             dt_obj = datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S')
             label = dt_obj.strftime('%b %d')
             chart_labels.append(label)
             systolic_data.append(r['value1'])
             diastolic_data.append(r['value2'])

    except Exception as e:
        print(f"Chart Error: {e}")

    # 3. Prescriptions (For Unification)
    # Fixed: Query prescriptions directly as it stores medication name, no ID join needed.
    prescriptions = conn.execute("""
        SELECT *
        FROM prescriptions 
        WHERE patient_id = ? 
        ORDER BY timestamp DESC
    """, (user_id,)).fetchall()

    conn.close()
    
    # 4. Generate Standard Video Call Room ID
    room_id = f"RuralHealthGuard-{user_id}-{datetime.now().strftime('%Y%m%d')}"

    return render_template("user_dashboard.html", 
                         user_name=session['user_name'], 
                         readings=readings,
                         prescriptions=prescriptions,
                         room_id=room_id,
                         chart_labels=chart_labels,
                         systolic_data=systolic_data,
                         diastolic_data=diastolic_data)

# --- PATIENT CHAT (Health Assistant) ---
@app.route('/patient/chat')
def patient_chat():
    """Patient health assistant chatbot page"""
    if 'user_id' not in session:
        flash("Please login to access Health Assistant", "warning")
        return redirect(url_for('login'))
    
    return render_template("patient_chat.html", patient_id=session['user_id'])

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from agents.chat_agent import process_chat_message
        
        data = request.get_json()
        patient_id = data.get('patient_id', session['user_id'])
        message = data.get('message', '')
        language = data.get('language', 'en')
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        result = process_chat_message(patient_id, message, history, language)
        
        return jsonify({
            'response': result['response'],
            'intent': result.get('intent'),
            'risk_level': result.get('risk_level')
        })
    except Exception as e:
        print(f"[CHAT API] Error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route("/worker_login", methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        phone = request.form['phone_number'].strip()
        password = request.form['password']
        
        # Auto-format phone
        if phone.startswith('0'): phone = phone[1:]
        if not phone.startswith('+91'): phone = f"+91{phone}"
        
        conn = get_db_connection()
        worker = conn.execute("SELECT * FROM asha_workers WHERE phone_number = ?", (phone,)).fetchone()
        conn.close()
        
        # Demo Auth: Check if worker exists AND password is default
        if worker and password == "asha123":
            session['worker_logged_in'] = True
            session['worker_phone'] = phone 
            flash(f"Login successful! Welcome {worker['name']}.", "success")
            return redirect(url_for('monitoring_dashboard'))
        else:
            flash("Invalid ASHA worker credentials. Use password 'asha123'.", "danger")
            return redirect(url_for('worker_login'))
            
    return render_template("worker_login.html")

# --- SOS ALERT ROUTE (FIXED) ---
@app.route("/patient/<int:patient_id>/send_sos")
def send_sos(patient_id):
    if not session.get('worker_logged_in'):
        return redirect(url_for('worker_login'))
    
    conn = get_db_connection()
    # Update workflow to emergency
    conn.execute("""
        INSERT INTO care_workflows (patient_id, current_state, next_action, status)
        VALUES (?, 'EMERGENCY', 'Immediate Ambulance Dispatch', 'LOCKED')
    """, (patient_id,))
    
    # Get patient details for SMS
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    # Alert Logic (Simulated or Real)
    if patient:
        msg = f"EMERGENCY SOS: Patient {patient['name']} (ID: {patient_id}) requires immediate ambulance at {patient['village']}."
        print(f"🚨 SENT TO DISPATCH: {msg}")
        
        # Also create a high severity alert
        conn.execute("""
            INSERT INTO patient_alerts (patient_id, alert_type, severity, message, vital_name)
            VALUES (?, 'SOS_TRIGGERED', 'CRITICAL', 'Manual SOS triggered by ASHA', 'SOS')
        """, (patient_id,))
    
    conn.commit()
    conn.close()
    
    flash("SOS Alert Sent! Emergency workflow activated.", "danger")
    return redirect(url_for('monitoring_dashboard'))

@app.route("/dashboard")
def monitoring_dashboard():
    if not session.get('worker_logged_in'): 
        return redirect(url_for('worker_login'))

    worker_phone = session.get('worker_phone')
    
    # 🔥 Execute Daily Analysis (Agent Orchestrator) 🔥
    try:
        daily_analysis = orchestrator.execute_daily_analysis(worker_phone)
        prioritized_patients = daily_analysis.get('patients', [])
    except Exception as e:
        print(f"Agent Orchestrator Error: {e}")
        prioritized_patients = []

    conn = get_db_connection()
    
    # Ensure tables exist (just in case init_db wasn't called)
    try:
        # Get alerts for this worker's patients
        alerts = conn.execute("""
            SELECT a.*, p.name 
            FROM patient_alerts a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE p.asha_worker_phone = ? AND a.is_acknowledged = 0
            ORDER BY a.severity DESC
        """, (worker_phone,)).fetchall()
    except Exception:
        alerts = []
    
    # Get standard patient list
    patients_from_db = conn.execute(
        "SELECT * FROM patients WHERE asha_worker_phone = ? ORDER BY id DESC",
        (worker_phone,)
    ).fetchall()
    print(f"DEBUG: Worker Phone in Session: '{worker_phone}'")
    print(f"DEBUG: Patients found in DB for this phone: {len(patients_from_db)}")

    patients_data = []

    for patient_row in patients_from_db:
        patient_dict = dict(patient_row)
        
        # Determine priority status from agent output
        priority = "LOW"
        urgency_score = 0
        reason = ""
        
        for p in prioritized_patients:
            if p['patient']['id'] == patient_dict['id']:
                priority = p['priority_level']
                urgency_score = p['urgency_score']
                break
        
        # FALLBACK: If agent didn't set priority, check for HIGH severity alerts
        if priority == "LOW":
            patient_alerts_count = conn.execute("""
                SELECT COUNT(*) FROM patient_alerts 
                WHERE patient_id = ? AND severity = 'HIGH' AND is_acknowledged = 0
            """, (patient_dict['id'],)).fetchone()[0]
            
            if patient_alerts_count > 0:
                priority = "HIGH"
                urgency_score = 90  # High urgency for patients with alerts
        
        patient_dict['priority'] = priority
        patient_dict['urgency_score'] = urgency_score

        # Get workflow info
        try:
             workflow = conn.execute("""
                SELECT current_state, next_action, status, created_at
                FROM care_workflows
                WHERE patient_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (patient_dict['id'],)).fetchone()
             patient_dict["workflow"] = dict(workflow) if workflow else None
        except Exception:
            patient_dict["workflow"] = None

        readings_rows = conn.execute(
            "SELECT *, strftime('%Y-%m-%d %I:%M %p', timestamp) as formatted_time "
            "FROM readings WHERE patient_id = ? ORDER BY timestamp DESC LIMIT 5",
            (patient_dict['id'],)
        ).fetchall()

        reports_rows = conn.execute(
            "SELECT *, strftime('%Y-%m-%d %I:%M %p', timestamp) as formatted_time "
            "FROM triage_reports WHERE patient_id = ? ORDER BY timestamp DESC LIMIT 3",
            (patient_dict['id'],)
        ).fetchall()

        # Get latest triage date for sorting
        if reports_rows:
            patient_dict['latest_triage_date'] = reports_rows[0]['timestamp']
        else:
            patient_dict['latest_triage_date'] = ""

        # Get prescriptions
        try:
            prescriptions_rows = conn.execute("""
                SELECT pr.*, ph.name as pharmacy_name 
                FROM prescriptions pr
                LEFT JOIN pharmacies ph ON pr.dispensed_by = ph.id
                WHERE pr.patient_id = ? AND pr.is_active = 1
            """, (patient_dict['id'],)).fetchall()
        except:
             prescriptions_rows = []
             
        # Get Chart Data
        bp_readings_rows = conn.execute(
            "SELECT *, strftime('%d-%b', timestamp) as chart_time "
            "FROM readings WHERE patient_id = ? AND reading_type = 'BP' "
            "ORDER BY timestamp ASC LIMIT 7",
            (patient_dict['id'],)
        ).fetchall()
        
        chart_data = {
            'labels': [row['chart_time'] for row in bp_readings_rows],
            'systolic': [row['value1'] for row in bp_readings_rows],
            'diastolic': [row['value2'] for row in bp_readings_rows]
        }

        patients_data.append({
            'info': patient_dict,
            'readings': [dict(r) for r in readings_rows],
            'reports': [dict(r) for r in reports_rows],
            'prescriptions': [dict(r) for r in prescriptions_rows],
            'chart_data': chart_data,
            'alerts': [dict(a) for a in alerts if a['patient_id'] == patient_dict['id']]
        })
        
    # Sort patients by urgency then recent triage
    patients_data.sort(key=lambda x: (x['info']['urgency_score'], x['info'].get('latest_triage_date', '')), reverse=True)

    # Get Ministry Advisories
    active_advisories = []
    sent_updates = []
    
    try:
        all_advisories = conn.execute("""
            SELECT DISTINCT ma.*
            FROM ministry_advisories ma
            JOIN patients p ON ma.village = p.village
            WHERE p.asha_worker_phone = ?
            ORDER BY ma.sent_at DESC
        """, (worker_phone,)).fetchall()
        
        # Get existing responses by this worker
        responses = conn.execute("""
            SELECT advisory_id, status, message, responded_at 
            FROM advisory_responses 
            WHERE worker_phone = ?
        """, (worker_phone,)).fetchall()
        
        responded_ids = {r['advisory_id']: r for r in responses}
        
        for adv in all_advisories:
            adv_dict = dict(adv)
            if adv['id'] in responded_ids:
                response_info = responded_ids[adv['id']]
                adv_dict['response_status'] = response_info['status']
                adv_dict['response_message'] = response_info['message']
                adv_dict['responded_at'] = response_info['responded_at']
                sent_updates.append(adv_dict)
            else:
                active_advisories.append(adv_dict)
                
    except Exception:
        active_advisories = []
        sent_updates = []

    conn.close()
    return render_template("monitoring_dashboard.html", 
                           all_patients=patients_data,
                           total_alerts=len(alerts),
                           high_priority_count=sum(1 for p in prioritized_patients if p['priority_level'] == 'HIGH'),
                           active_advisories=active_advisories,
                           sent_updates=sent_updates)

@app.route("/worker/refer_patient", methods=['POST'])
def refer_patient():
    print("DEBUG: refer_patient route hit") # DEBUG LOG
    if not session.get('worker_logged_in'):
        print("DEBUG: User not logged in") # DEBUG LOG
        return jsonify({'error': 'Unauthorized'}), 401
    
    worker_phone = session.get('worker_phone')
    data = request.json
    print(f"DEBUG: Data received: {data}") # DEBUG LOG
    
    patient_id = data.get('patient_id')
    reason = data.get('reason')
    priority = data.get('priority', 'Routine')
    doctor_id = data.get('doctor_id') # Optional, if they know which doctor
    
    if not all([patient_id, reason]):
        print("DEBUG: Missing fields") # DEBUG LOG
        return jsonify({'error': 'Missing required fields'}), 400
        
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO referrals (patient_id, referred_by_asha, doctor_id, reason, priority, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
        """, (patient_id, worker_phone, doctor_id, reason, priority))
        conn.commit()
        print("DEBUG: Insert successful") # DEBUG LOG
    except Exception as e:
        conn.rollback()
        print(f"DEBUG: Error inserting referral: {e}") # DEBUG LOG
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({'success': True, 'message': 'Referral sent to Doctor successfully!'})

@app.route("/doctor/mark_attended/<int:referral_id>", methods=['POST'])
def mark_referral_attended(referral_id):
    """Mark a referral as attended and remove from active list"""
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        # Update the referral status to 'Attended'
        conn.execute("""
            UPDATE referrals SET status = 'Attended' WHERE id = ?
        """, (referral_id,))
        conn.commit()
        print(f"[DOCTOR] Marked referral {referral_id} as attended", flush=True)
        return jsonify({'success': True, 'message': 'Patient marked as attended!'})
    except Exception as e:
        conn.rollback()
        print(f"[DOCTOR] Error marking referral as attended: {e}", flush=True)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route("/doctor/mark_patient_attended/<int:patient_id>", methods=['POST'])
def mark_patient_attended(patient_id):
    """Mark high-risk patient alerts and triage reports as acknowledged"""
    if not session.get('doctor_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        # 1. Acknowledge all HIGH severity alerts for this patient
        conn.execute("""
            UPDATE patient_alerts 
            SET is_acknowledged = 1,
                acknowledged_at = datetime('now'),
                acknowledged_by = 'Doctor'
            WHERE patient_id = ? AND severity = 'HIGH'
        """, (patient_id,))
        
        # 2. Mark high-risk triage reports as doctor_reviewed
        # First check if column exists, if not add it
        try:
            conn.execute("ALTER TABLE triage_reports ADD COLUMN doctor_reviewed INTEGER DEFAULT 0")
        except:
            pass  # Column already exists
        
        conn.execute("""
            UPDATE triage_reports 
            SET doctor_reviewed = 1
            WHERE patient_id = ? 
            AND (ai_prediction LIKE '%High%' OR ai_prediction LIKE '%Critical%' OR ai_prediction LIKE '%Emergency%')
        """, (patient_id,))
        
        conn.commit()
        print(f"[DOCTOR] Marked patient {patient_id} as attended (alerts + triage)", flush=True)
        return jsonify({'success': True, 'message': 'Patient marked as attended!'})
    except Exception as e:
        conn.rollback()
        print(f"[DOCTOR] Error marking patient as attended: {e}", flush=True)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route("/patient/<int:patient_id>/add_report", methods=['GET', 'POST'])
def add_triage_report(patient_id):
    if not session.get('worker_logged_in'):
        return redirect(url_for('worker_login'))

    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    if request.method == 'POST':
        chief_complaint = request.form.get('chief_complaint', '').strip()
        notes = request.form.get('notes', '').strip()
        symptoms = request.form.getlist('symptoms')
        
        # --- 🔥 AGENT ORCHESTRATOR WORKFLOW 🔥 ---
        triage_data = {
            "age": patient["age"],
            "chief_complaint": chief_complaint,
            "symptoms": symptoms,
            "notes": notes
        }
        
        try:
            workflow_result = orchestrator.execute_triage_workflow(patient_id, triage_data)
            
            # Extract results
            decision_data = workflow_result.get("final_decision", {})
            risk = decision_data.get("risk", "Moderate")
            decision = decision_data.get("action", "ASHA Follow-up")
            asha_task = decision_data.get("asha_task", "Monitor patient")
            
            # Get rich AI output
            triage_output = workflow_result.get("triage_assessment", {})
            reasoning = triage_output.get("reasoning", "")
            diagnosis = triage_output.get("primary_diagnosis", "Unknown")
            red_flags = ", ".join(triage_output.get("detected_red_flags", []))
            home_remedies = triage_output.get("home_remedies", [])
            asha_instructions = triage_output.get("asha_instructions", [asha_task])
            
            # Format Home Remedies HTML
            remedies_html = ""
            if home_remedies and risk in ["Low", "Moderate"]:
                remedies_html = f"""
                <div class="mt-3 p-3 bg-light rounded border-start border-4 border-success">
                    <h6 class="text-success fw-bold"><i class="fa-solid fa-house-medical"></i> Home Remedies</h6>
                    <ul class="mb-0 ps-3">
                        {''.join([f'<li>{r}</li>' for r in home_remedies])}
                    </ul>
                </div>
                """
            
            # Format ASHA Instructions HTML
            instructions_html = ""
            if isinstance(asha_instructions, list):
                instructions_html = "<ul>" + "".join([f"<li>{i}</li>" for i in asha_instructions]) + "</ul>"
            else:
                instructions_html = f"<p>{asha_instructions}</p>"

            # Save Triage Report as Rich HTML
            ai_output_html = f"""
            <div class="triage-report-content">
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="mb-2">
                            <h6 class="fw-bold text-muted text-uppercase small">Diagnosis</h6>
                            <p class="fw-bold mb-0 text-primary">{diagnosis}</p>
                        </div>
                        <div class="mb-2">
                             <h6 class="fw-bold text-muted text-uppercase small">Decision</h6>
                             <p class="mb-0">{decision}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-2">
                            <h6 class="fw-bold text-muted text-uppercase small">Risk Level</h6>
                            <span class="badge {'bg-danger' if risk in ['High', 'Critical'] else 'bg-warning' if risk == 'Moderate' else 'bg-success'}">{risk}</span>
                        </div>
                        <div class="mb-2">
                            <h6 class="fw-bold text-muted text-uppercase small">Red Flags</h6>
                            <p class="mb-0 {'text-danger fw-bold' if red_flags else 'text-muted'}">{red_flags if red_flags else 'None Detected'}</p>
                        </div>
                    </div>
                </div>

                <div class="mt-3">
                    <h6 class="fw-bold text-muted text-uppercase small">Reasoning</h6>
                    <p class="text-muted small">{reasoning}</p>
                </div>
                
                <div class="mt-3">
                    <h6 class="fw-bold text-muted text-uppercase small">ASHA Task List</h6>
                    <div class="small">{instructions_html}</div>
                </div>

                {remedies_html}
            </div>
            """
            
            conn.execute(
                "INSERT INTO triage_reports (patient_id, chief_complaint, symptoms, notes, ai_prediction) VALUES (?, ?, ?, ?, ?)",
                (patient_id, chief_complaint, ", ".join(symptoms), notes, ai_output_html)
            )
            
            # Save Alert if High Risk
            if risk in ["High", "Critical"]:
                conn.execute(
                    "INSERT INTO patient_alerts (patient_id, alert_type, severity, message, vital_name) VALUES (?, ?, ?, ?, ?)",
                    (patient_id, "TRIAGE_RISK", "HIGH" if risk == "Critical" else "MODERATE", f"High risk triage: {diagnosis}", "TRIAGE")
                )
            
            # --- AGENTIC AI FEEDBACK ---
            # Check if the autonomous agent took action
            if workflow_result.get("agent_alert"):
                alert = workflow_result["agent_alert"]
                flash(f"🤖 {alert['message']}", "warning") # Special flash for agent action
            
            conn.commit()
            flash(f"Triage complete. Risk: {risk}. Action: {decision}", "success")
            
        except Exception as e:
            print(f"Orchestrator Failed: {e}")
            flash("AI analysis failed, saved as manual report.", "warning")
            # Save basic report
            conn.execute(
                "INSERT INTO triage_reports (patient_id, chief_complaint, symptoms, notes, ai_prediction) VALUES (?, ?, ?, ?, ?)",
                (patient_id, chief_complaint, ", ".join(symptoms), notes, "Manual Review Needed")
            )
            conn.commit()

        conn.close()
        return redirect(url_for('monitoring_dashboard'))
        
    conn.close()
    return render_template('add_triage_report.html', patient=patient)

# --- DOCTOR PORTAL ---
@app.route("/doctor/login", methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Accept both sets of demo credentials
        valid_creds = [
            ("doc@health.com", "doc123"),
            ("doctor@hospital.gov", "doctor123")
        ]
        
        if (email, password) in valid_creds:
            session['doctor_logged_in'] = True
            flash("Welcome Doctor!", "success")
            return redirect(url_for('doctor_dashboard'))
        else:
            flash("Invalid credentials. Try doctor@hospital.gov / doctor123", "danger")
            
    return render_template("doctor_login.html")

@app.route("/doctor/dashboard")
def doctor_dashboard():
    if not session.get('doctor_logged_in'):
        return redirect(url_for('doctor_login'))
        
    conn = get_db_connection()
    try:
        # Get high risk patients from TWO sources:
        # 1. Patients with HIGH severity alerts
        # 2. Patients with High/Critical risk triage reports (AUTO-DETECTED by AI)
        high_risk_patients = conn.execute("""
            SELECT DISTINCT p.*, 
                   COALESCE(tr.ai_prediction, '') as latest_triage,
                   tr.chief_complaint as latest_complaint,
                   tr.timestamp as triage_time,
                   'ALERT' as source
            FROM patients p 
            JOIN patient_alerts a ON p.id = a.patient_id 
            LEFT JOIN triage_reports tr ON p.id = tr.patient_id
            WHERE a.severity = 'HIGH' AND a.is_acknowledged = 0
            
            UNION
            
            SELECT DISTINCT p.*, 
                   tr.ai_prediction as latest_triage,
                   tr.chief_complaint as latest_complaint,
                   tr.timestamp as triage_time,
                   'TRIAGE' as source
            FROM patients p 
            JOIN triage_reports tr ON p.id = tr.patient_id 
            WHERE (tr.ai_prediction LIKE '%High%' OR tr.ai_prediction LIKE '%Critical%' OR tr.ai_prediction LIKE '%Emergency%')
            AND tr.timestamp >= datetime('now', '-7 days')
            AND COALESCE(tr.doctor_reviewed, 0) = 0
            ORDER BY triage_time DESC
        """).fetchall()
        print(f"[DOCTOR DASHBOARD] Found {len(high_risk_patients)} high risk patients", flush=True)
    except Exception as e:
        print(f"[DOCTOR DASHBOARD] Error fetching high risk patients: {e}", flush=True)
        high_risk_patients = []
        
    # Get NEW Referrals
    referrals = conn.execute("""
        SELECT r.*, p.name as patient_name, p.age, p.gender, p.phone_number
        FROM referrals r
        JOIN patients p ON r.patient_id = p.id
        WHERE (r.doctor_id IS NULL) AND r.status = 'Pending'
        ORDER BY r.created_at DESC
    """).fetchall()
    
    conn.close()
    
    # Generate AI Case Summaries for each referral
    case_summaries = {}
    try:
        from agents.doctor_case_prep_agent import prepare_case_summary
        for referral in referrals:
            patient_id = referral['patient_id']
            try:
                # Use non-LLM version for speed (LLM can be slow)
                summary = prepare_case_summary(patient_id, use_llm=False)
                case_summaries[patient_id] = summary
            except Exception as e:
                case_summaries[patient_id] = f"<p><em>Case summary unavailable: {e}</em></p>"
    except Exception as e:
        print(f"Case prep agent import failed: {e}")
    
    return render_template("doctor_dashboard.html", high_risk_patients=high_risk_patients, referrals=referrals, case_summaries=case_summaries)

@app.route("/doctor/patient/<int:patient_id>")
def doctor_patient_record(patient_id):
    if not session.get('doctor_logged_in'):
        return redirect(url_for('doctor_login'))
        
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    # Fetch Reports
    reports = conn.execute("SELECT *, strftime('%Y-%m-%d %H:%M', timestamp) as formatted_time FROM triage_reports WHERE patient_id = ? ORDER BY timestamp DESC", (patient_id,)).fetchall()
    
    # Fetch Prescriptions (Joined with pharmacy)
    prescriptions = conn.execute("""
        SELECT pr.*, ph.name as pharmacy_name 
        FROM prescriptions pr
        LEFT JOIN pharmacies ph ON pr.dispensed_by = ph.id
        WHERE pr.patient_id = ?
        ORDER BY pr.timestamp DESC
    """, (patient_id,)).fetchall()
    
    # Fetch Vitals
    readings = conn.execute("SELECT *, strftime('%Y-%m-%d %H:%M', timestamp) as formatted_time FROM readings WHERE patient_id = ? ORDER BY timestamp DESC LIMIT 20", (patient_id,)).fetchall()
    
    # Chart Data
    bp_rows = conn.execute("SELECT *, strftime('%d-%b', timestamp) as chart_time FROM readings WHERE patient_id = ? AND reading_type = 'BP' ORDER BY timestamp ASC", (patient_id,)).fetchall()
    chart_data = {
        'labels': [r['chart_time'] for r in bp_rows],
        'systolic': [r['value1'] for r in bp_rows],
        'diastolic': [r['value2'] for r in bp_rows]
    }
    
    conn.close()
    return render_template("doctor_patient_record.html", patient=patient, reports=reports, prescriptions=prescriptions, readings=readings, chart_data=chart_data)


# --- DUMMY ROUTES FOR MISSING FEATURES ---
# --- VIDEO CALL ROUTES (JITSI INTEGRATION) ---
@app.route('/patient/<int:patient_id>/start_call')
def start_video_call(patient_id):
    print(f"[VIDEO CALL] Route called for patient_id: {patient_id}", flush=True)
    print(f"[VIDEO CALL] Session: worker_logged_in={session.get('worker_logged_in')}, doctor_logged_in={session.get('doctor_logged_in')}", flush=True)
    
    # Check if either worker or doctor is logged in
    is_worker = session.get('worker_logged_in')
    is_doctor = session.get('doctor_logged_in')
    
    if not (is_worker or is_doctor):
        print("[VIDEO CALL] User not logged in, redirecting to appropriate login", flush=True)
        flash("Please login to start a video call.", "warning")
        return redirect(url_for('worker_login'))  # Redirect to worker login

    conn = get_db_connection()
    patient = conn.execute("SELECT name, id, phone_number FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    
    print(f"[VIDEO CALL] Patient found: {patient['name'] if patient else 'None'}, Phone: {patient['phone_number'] if patient else 'None'}", flush=True)

    if not patient:
        flash("Patient not found", "error")
        return redirect(url_for('monitoring_dashboard'))

    # Generate a unique secure room name
    room_id = f"RuralHealthGuard-{patient['id']}-{datetime.now().strftime('%Y%m%d%H%M')}"
    video_call_url = f"https://meet.jit.si/{room_id}"
    
    # Send SMS to patient with video call link
    # Note: Message format designed to avoid carrier spam filtering
    if patient['phone_number']:
        sms_message = (
            f"HealthGuard Telemedicine\n\n"
            f"Dear {patient['name']},\n"
            f"Your video consultation is ready.\n\n"
            f"Room: {room_id}\n\n"
            f"To join: Open meet.jit.si and enter the room name above, "
            f"or visit:\n{video_call_url}\n\n"
            f"- Rural HealthGuard Team"
        )
        print(f"[VIDEO CALL] Sending SMS to: {patient['phone_number']}", flush=True)
        send_alert(patient['phone_number'], sms_message)
        flash(f"SMS sent to patient {patient['name']} with video call link.", "info")
    
    return redirect(url_for('video_call_route', room_id=room_id))

@app.route('/video_call')
def video_call_route():
    room_id = request.args.get('room_id')
    if not room_id:
        flash("Invalid Call ID", "error")
        return redirect(url_for('monitoring_dashboard'))

    display_name = "User"
    if session.get('worker_logged_in'):
        display_name = f"ASHA Worker ({session.get('worker_phone')})"
    elif session.get('doctor_logged_in'):
        display_name = f"Dr. {session.get('doctor_name')}"
    elif session.get('user_id'):
        display_name = f"Patient"

    return render_template('video_call.html', room_id=room_id, display_name=display_name)

@app.route('/patient/<int:patient_id>/end_call')
def end_video_call(patient_id):
    # Logic to log call duration could go here
    return redirect(url_for('monitoring_dashboard'))

@app.route('/patient/<int:patient_id>/add_prescription', methods=['GET', 'POST'])
def add_prescription(patient_id):
    if not session.get('doctor_logged_in'):
        return redirect(url_for('doctor_login'))

    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    # Get all distinct medications for the dropdown
    all_medications_rows = conn.execute("SELECT DISTINCT medication FROM pharmacy_inventory ORDER BY medication").fetchall()
    all_medications = [row['medication'] for row in all_medications_rows]
    
    selected_medication = request.args.get('medication_name') or request.form.get('medication_name')
    pharmacy_stock = []
    
    if selected_medication:
        stock_rows = conn.execute("""
            SELECT pi.*, p.name as pharmacy_name, p.location 
            FROM pharmacy_inventory pi
            JOIN pharmacies p ON pi.pharmacy_id = p.id
            WHERE pi.medication = ?
        """, (selected_medication,)).fetchall()
        
        for row in stock_rows:
            pharmacy_stock.append({
                'pharmacy': {'id': row['pharmacy_id'], 'name': row['pharmacy_name'], 'location': row['location']},
                'status': row['stock_status']
            })
            
    if request.method == 'POST':
        medication_name = request.form.get('medication_name')
        dosage = request.form.get('dosage')
        notes = request.form.get('notes')
        pharmacy_id = request.form.get('pharmacy_id')
        
        if medication_name and dosage and pharmacy_id:
            conn.execute("""
                INSERT INTO prescriptions (patient_id, medication_name, dosage, notes, dispensing_pharmacy_id, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (patient_id, medication_name, dosage, notes, pharmacy_id))
            conn.commit()
            
            # Get pharmacy details for SMS
            pharmacy = conn.execute("SELECT name, location FROM pharmacies WHERE id = ?", (pharmacy_id,)).fetchone()
            pharmacy_name = pharmacy['name'] if pharmacy else "your assigned pharmacy"
            pharmacy_location = pharmacy['location'] if pharmacy else ""
            
            # Send SMS to patient about prescription with pharmacy info
            if patient['phone_number']:
                sms_message = (
                    f"💊 HealthGuard Prescription\n\n"
                    f"Dear {patient['name']},\n"
                    f"Your doctor has prescribed:\n\n"
                    f"• Medicine: {medication_name}\n"
                    f"• Dosage: {dosage}\n"
                    f"• Notes: {notes if notes else 'None'}\n\n"
                    f"📍 Where to collect:\n"
                    f"{pharmacy_name}"
                    f"{' - ' + pharmacy_location if pharmacy_location else ''}\n\n"
                    f"- Rural HealthGuard Team"
                )
                send_alert(patient['phone_number'], sms_message)
                flash("Prescription sent to pharmacy and SMS sent to patient.", "success")
            else:
                flash("Prescription sent to pharmacy successfully.", "success")
            conn.close()
            return redirect(url_for('doctor_dashboard'))
        else:
            flash("Please fill all required fields.", "danger")

    conn.close()
    return render_template('add_prescription.html', 
                           patient=patient, 
                           all_medications=all_medications, 
                           selected_medication=selected_medication,
                           pharmacy_stock=pharmacy_stock)
    
@app.route('/prescription/<int:prescription_id>/send_reminder')
def send_reminder(prescription_id):
    """Send prescription reminder SMS to patient"""
    if not session.get('worker_logged_in') and not session.get('doctor_logged_in'):
        flash("Please login to send reminders.", "warning")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        # Get prescription and patient details
        prescription = conn.execute("""
            SELECT p.*, pt.name as patient_name, pt.phone_number 
            FROM prescriptions p
            JOIN patients pt ON p.patient_id = pt.id
            WHERE p.id = ?
        """, (prescription_id,)).fetchone()
        
        if not prescription:
            flash("Prescription not found.", "error")
            return redirect(url_for('monitoring_dashboard'))
        
        if prescription['phone_number']:
            # Build reminder message
            sms_message = (
                f"HealthGuard Prescription Reminder\n\n"
                f"Dear {prescription['patient_name']},\n"
                f"This is a reminder for your medication:\n\n"
                f"Medicine: {prescription['medication_name']}\n"
                f"Dosage: {prescription['dosage']}\n"
            )
            if prescription['notes']:
                sms_message += f"Notes: {prescription['notes']}\n"
            sms_message += f"\n- Rural HealthGuard Team"
            
            print(f"[REMINDER] Sending reminder for prescription {prescription_id} to {prescription['phone_number']}", flush=True)
            result = send_alert(prescription['phone_number'], sms_message)
            
            if result:
                flash(f"Reminder sent to {prescription['patient_name']}!", "success")
            else:
                flash("Failed to send SMS. Check Twilio configuration.", "warning")
        else:
            flash("Patient has no phone number registered.", "warning")
    finally:
        conn.close()
    
    return redirect(url_for('monitoring_dashboard'))

@app.route("/run-followups")
def run_followups():
    flash("Follow-up agent executed.", "success")
    return redirect(url_for("monitoring_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('home'))

 

@app.route("/health_dept/login", methods=['GET', 'POST'])
def health_dept_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == "minister@health.gov" and password == "admin123":
            session['health_dept_logged_in'] = True
            flash("Welcome to National Health Portal", "success")
            return redirect(url_for('health_dept_overview'))
        else:
            flash("Invalid credentials", "danger")
            
    return render_template("health_dept_login.html")

@app.route("/health_dept/overview")
def health_dept_overview():
    if not session.get('health_dept_logged_in'):
        return redirect(url_for('health_dept_login'))
    
    # Fetch districts with actual patient data
    conn = get_db_connection()
    districts_data = conn.execute("""
        SELECT district, 
               COUNT(*) as patient_count,
               COUNT(DISTINCT asha_worker_phone) as asha_count,
               COUNT(DISTINCT village) as village_count
        FROM patients 
        WHERE district IS NOT NULL AND district != ''
        GROUP BY district
        ORDER BY patient_count DESC
    """).fetchall()
    
    # Get high-risk counts per district
    high_risk_counts = {}
    for d in districts_data:
        district = d['district']
        count = conn.execute("""
            SELECT COUNT(*) FROM triage_reports tr
            JOIN patients p ON tr.patient_id = p.id
            WHERE p.district = ? 
            AND (tr.ai_prediction LIKE '%High%' OR tr.ai_prediction LIKE '%Critical%')
        """, (district,)).fetchone()[0]
        high_risk_counts[district] = count
    
    conn.close()
    
    return render_template("health_ministry_overview.html", 
                         districts=districts_data,
                         high_risk_counts=high_risk_counts)

@app.route("/health_dept/send_advisory", methods=['POST'])
def send_advisory():
    if not session.get('health_dept_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    district = data.get('district')
    village = data.get('village')
    message = data.get('message') # Frontend sends 'message', DB stores as 'content'
    title = data.get('title', 'Health Advisory')
    urgency = data.get('urgency', 'Routine')
    
    if not all([district, village, message]):
        return jsonify({'error': 'Missing data'}), 400
        
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO ministry_advisories (district, village, content, title, urgency) 
            VALUES (?, ?, ?, ?, ?)
        """, (district, village, message, title, urgency))
        conn.commit()
        success = True
        msg = 'Advisory sent successfully'
    except Exception as e:
        print(f"Error sending advisory: {e}")
        success = False
        msg = f"Error: {str(e)}"
    finally:
        conn.close()
    
    if success:
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'error': msg}), 500

@app.route("/health_dept/dashboard/<district>")
def health_dept_district_dashboard(district):
    if not session.get('health_dept_logged_in'):
        return redirect(url_for('health_dept_login'))
        
    conn = get_db_connection()
    
    # Calculate Stats - SCOPED TO SELECTED DISTRICT
    total_patients = conn.execute("SELECT COUNT(*) FROM patients WHERE district = ?", (district,)).fetchone()[0]
    
    # High risk count - from triage reports for patients in this district
    high_risk_count = conn.execute("""
        SELECT COUNT(*) FROM triage_reports tr
        JOIN patients p ON tr.patient_id = p.id
        WHERE p.district = ? AND (tr.ai_prediction LIKE '%High%' OR tr.ai_prediction LIKE '%Critical%')
    """, (district,)).fetchone()[0]
    
    # Total triage reports for this district (LEFT JOIN to include orphaned reports)
    # For orphaned reports (no patient match), we still count them if district param is 'Dhule' (default)
    total_reports = conn.execute("""
        SELECT COUNT(*) FROM triage_reports tr
        LEFT JOIN patients p ON tr.patient_id = p.id
        WHERE p.district = ? OR (p.id IS NULL AND ? = 'Dhule')
    """, (district, district)).fetchone()[0]
    
    # Active ASHA workers in this district
    active_workers = conn.execute("SELECT COUNT(DISTINCT asha_worker_phone) FROM patients WHERE district = ?", (district,)).fetchone()[0]
    
    # --- DYNAMIC HOTSPOT ALGORITHM ---
    # Logic: Find villages with > 1 HIGH priority triage report or alert
    # For demo purposes, we treat any HIGH risk report as a signal.
    
    hotspot_query = """
        SELECT p.village, COUNT(*) as case_count
        FROM triage_reports tr
        JOIN patients p ON tr.patient_id = p.id
        WHERE tr.ai_prediction LIKE '%High%' OR tr.ai_prediction LIKE '%Emergency%'
        GROUP BY p.village
        HAVING case_count > 0
        ORDER BY case_count DESC
    """
    try:
        hotspot_rows = conn.execute(hotspot_query).fetchall()
        hotspots = []
        for row in hotspot_rows:
            hotspots.append({
                'village': row['village'] or 'Unknown Village',
                'condition': 'Viral Outbreak Risk', # Generic label for now, could be refined by parsing symptoms
                'trend': 'RISING',
                'cases': row['case_count']
            })
    except Exception as e:
        print(f"Hotspot Error: {e}")
        hotspots = []
        
    # --- DYNAMIC SYMPTOM STATS ---
    # Parse all reports to count keywords
    symptom_rows = conn.execute("SELECT symptoms FROM triage_reports").fetchall()
    
    symptom_counts = {'Fever': 0, 'Cough': 0, 'Headache': 0, 'Other': 0}
    
    for row in symptom_rows:
        text = (row['symptoms'] or "").lower()
        matched = False
        if 'fever' in text or 'temperature' in text:
            symptom_counts['Fever'] += 1
            matched = True
        if 'cough' in text or 'cold' in text or 'throat' in text:
            symptom_counts['Cough'] += 1
            matched = True
        if 'headache' in text or 'pain' in text:
            symptom_counts['Headache'] += 1
            matched = True
        if not matched:
            symptom_counts['Other'] += 1
            
    # Serialize for Chart.js
    symptom_data = [
        symptom_counts['Fever'],
        symptom_counts['Cough'],
        symptom_counts['Headache'],
        symptom_counts['Other']
    ]

    stats = {
        'total_patients': total_patients,
        'high_risk_count': high_risk_count,
        'active_workers': active_workers,
        'total_reports': total_reports,
        'district': district
    }
        
    # Get ASHA Responses
    try:
        responses = conn.execute("""
            SELECT ar.*, ma.village, ma.content as advisory_message, ma.title as advisory_title
            FROM advisory_responses ar
            JOIN ministry_advisories ma ON ar.advisory_id = ma.id
            WHERE ma.district = ?
            ORDER BY ar.responded_at DESC
        """, (district,)).fetchall()
        print(f"[HEALTH DEPT] Found {len(responses)} ASHA responses for district {district}", flush=True)
    except Exception as e:
        print(f"[HEALTH DEPT] Error fetching responses: {e}", flush=True)
        responses = []
    
    conn.close()
    return render_template("health_dept_dashboard.html", stats=stats, hotspots=hotspots, updates=responses, symptom_data=symptom_data)

@app.route("/worker/respond_advisory", methods=['POST'])
def respond_advisory():
    if not session.get('worker_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    worker_phone = session.get('worker_phone')
    data = request.json
    advisory_id = data.get('advisory_id')
    status = data.get('status')
    message = data.get('message')
    
    if not all([advisory_id, status]):
        return jsonify({'error': 'Missing data'}), 400
        
    conn = get_db_connection()
    conn.execute("INSERT INTO advisory_responses (advisory_id, worker_phone, status, message) VALUES (?, ?, ?, ?)", 
                 (advisory_id, worker_phone, status, message))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Response submitted successfully'})

# --- API Routes for Agents ---
@app.route("/api/agent/case_summary/<int:patient_id>")
def api_case_summary(patient_id):
    summary = orchestrator.execute_doctor_prep(patient_id, use_llm=True)
    return jsonify({"summary": summary})

# --- Main Execution ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)