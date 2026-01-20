"""
Background Task Scheduler for Rural HealthGuard
Uses APScheduler to run daily agent tasks
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sqlite3
from datetime import datetime

# Import agents
from agents.vital_trend_analyzer import analyze_all_patients
from agents.orchestrator import orchestrator

scheduler = BackgroundScheduler()

def get_db_connection():
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def daily_vital_analysis():
    """Run vital trend analysis for all patients"""
    print(f"[{datetime.now()}] 🤖 Running scheduled vital analysis...")
    try:
        summary = analyze_all_patients()
        print(f"[{datetime.now()}] ✅ Vital analysis complete: {summary['total_alerts_created']} alerts created")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Vital analysis failed: {e}")

def daily_asha_tasks():
    """Generate daily task lists for all ASHA workers"""
    print(f"[{datetime.now()}] 🤖 Running scheduled ASHA task generation...")
    try:
        conn = get_db_connection()
        # Get all unique ASHA worker phones
        asha_workers = conn.execute("SELECT DISTINCT asha_worker_phone FROM patients WHERE asha_worker_phone IS NOT NULL").fetchall()
        conn.close()
        
        for worker in asha_workers:
            phone = worker['asha_worker_phone']
            if phone:
                try:
                    result = orchestrator.execute_daily_analysis(phone)
                    print(f"[{datetime.now()}] ✅ Tasks generated for {phone}: {result.get('total_patients', 0)} patients")
                except Exception as e:
                    print(f"[{datetime.now()}] ❌ Task generation failed for {phone}: {e}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ ASHA task generation failed: {e}")

def outbreak_check():
    """Check for potential outbreaks across villages"""
    print(f"[{datetime.now()}] 🤖 Running scheduled outbreak scan...")
    try:
        conn = get_db_connection()
        # Check for villages with multiple high-risk cases in last 7 days
        query = """
            SELECT p.village, COUNT(*) as case_count
            FROM triage_reports tr
            JOIN patients p ON tr.patient_id = p.id
            WHERE tr.created_at >= date('now', '-7 days')
            AND (tr.ai_prediction LIKE '%High%' OR tr.ai_prediction LIKE '%Critical%')
            GROUP BY p.village
            HAVING case_count >= 3
        """
        hotspots = conn.execute(query).fetchall()
        
        for spot in hotspots:
            print(f"[{datetime.now()}] 🚨 Potential outbreak in {spot['village']}: {spot['case_count']} cases")
            # Could auto-create ministry advisories here
        
        conn.close()
        print(f"[{datetime.now()}] ✅ Outbreak scan complete: {len(hotspots)} hotspots detected")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Outbreak scan failed: {e}")

def init_scheduler():
    """Initialize and start the background scheduler"""
    global scheduler
    
    # Daily vital analysis at 6:00 AM
    scheduler.add_job(
        daily_vital_analysis,
        CronTrigger(hour=6, minute=0),
        id='daily_vital_analysis',
        name='Daily Vital Trend Analysis',
        replace_existing=True
    )
    
    # Daily ASHA task generation at 5:30 AM (before vital analysis)
    scheduler.add_job(
        daily_asha_tasks,
        CronTrigger(hour=5, minute=30),
        id='daily_asha_tasks',
        name='Daily ASHA Task Generation',
        replace_existing=True
    )
    
    # Outbreak check every 6 hours
    scheduler.add_job(
        outbreak_check,
        CronTrigger(hour='*/6'),
        id='outbreak_check',
        name='Outbreak Detection Scan',
        replace_existing=True
    )
    
    scheduler.start()
    print("🕐 Background scheduler initialized with 3 jobs:")
    print("   - Daily Vital Analysis (6:00 AM)")
    print("   - Daily ASHA Tasks (5:30 AM)")
    print("   - Outbreak Check (Every 6 hours)")

def shutdown_scheduler():
    """Gracefully shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Background scheduler stopped")

# For testing manually
if __name__ == "__main__":
    print("Testing scheduler jobs manually...")
    daily_vital_analysis()
    daily_asha_tasks()
    outbreak_check()
