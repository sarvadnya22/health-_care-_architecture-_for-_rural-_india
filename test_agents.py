"""
Multi-Agent AI System - Testing Guide
Step-by-step instructions to test all agents
"""

# ============================================
# STEP 1: Setup Test Data
# ============================================

import sqlite3
from datetime import datetime, timedelta

def setup_test_data():
    """Create realistic test data for agent testing"""
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    # Add multiple BP readings to trigger trend detection
    print("Adding test vital readings...")
    
    # Patient 1 (Ramesh Patil) - Rising BP trend
    base_date = datetime.now()
    cursor.execute("""
        INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (1, 'BP', 130, 85, (base_date - timedelta(days=5)).isoformat()))
    
    cursor.execute("""
        INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (1, 'BP', 145, 90, (base_date - timedelta(days=3)).isoformat()))
    
    cursor.execute("""
        INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (1, 'BP', 160, 95, base_date.isoformat()))
    
    # Add sugar readings
    cursor.execute("""
        INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (1, 'SUGAR', 120, None, (base_date - timedelta(days=2)).isoformat()))
    
    conn.commit()
    conn.close()
    print("✅ Test data created!")

# Run this first
if __name__ == "__main__":
    setup_test_data()


# ============================================
# STEP 2: Test Individual Agents
# ============================================

# Test 2.1: Vital Trend Analyzer
# --------------------------------
def test_vital_trend_analyzer():
    """Test vital trend detection"""
    from agents.vital_trend_analyzer import analyze_vital_trends, analyze_all_patients
    
    print("\n" + "="*50)
    print("TEST: Vital Trend Analyzer")
    print("="*50)
    
    # Test for specific patient
    print("\n1. Analyzing patient 1...")
    result = analyze_vital_trends(1)
    print(f"   Vitals analyzed: {len(result['analyzed_vitals'])}")
    print(f"   Alerts created: {len(result['alerts_created'])}")
    
    if result['alerts_created']:
        for alert in result['alerts_created']:
            print(f"   🚨 Alert: {alert['vital_type']} - {alert['severity']}")
    
    # Test for all patients
    print("\n2. Analyzing all patients...")
    summary = analyze_all_patients()
    print(f"   Total patients: {summary['total_patients_analyzed']}")
    print(f"   Total alerts: {summary['total_alerts_created']}")
    print(f"   High severity: {summary['high_severity_alerts']}")
    
    return result

# Test 2.2: ASHA Task Prioritization
# -----------------------------------
def test_task_prioritization():
    """Test ASHA task prioritization"""
    from agents.task_prioritization_agent import generate_daily_task_list
    
    print("\n" + "="*50)
    print("TEST: ASHA Task Prioritization")
    print("="*50)
    
    asha_phone = "+919123456789"
    task_list = generate_daily_task_list(asha_phone)
    
    print(f"\nTotal patients: {task_list['total_patients']}")
    print(f"🔴 High priority: {task_list['high_priority']}")
    print(f"🟡 Moderate priority: {task_list['moderate_priority']}")
    print(f"🟢 Low priority: {task_list['low_priority']}")
    
    print("\nTop 3 patients:")
    for i, patient_item in enumerate(task_list['patients'][:3], 1):
        patient = patient_item['patient']
        print(f"{i}. {patient['name']} - Score: {patient_item['urgency_score']}/100")
        print(f"   Priority: {patient_item['priority_level']}")
    
    return task_list

# Test 2.3: Doctor Case Preparation
# ----------------------------------
def test_doctor_case_prep():
    """Test doctor case summary generation"""
    from agents.doctor_case_prep_agent import prepare_case_summary
    
    print("\n" + "="*50)
    print("TEST: Doctor Case Preparation")
    print("="*50)
    
    # Test without LLM (faster)
    print("\nGenerating case summary (without LLM)...")
    summary = prepare_case_summary(1, use_llm=False)
    print(summary)
    
    return summary

# Test 2.4: Enhanced Triage Agent
# --------------------------------
def test_triage_agent():
    """Test enhanced triage agent"""
    from agents.triage_agent import triage_agent
    
    print("\n" + "="*50)
    print("TEST: Enhanced Triage Agent")
    print("="*50)
    
    # Test case 1: Normal symptoms
    print("\n1. Testing normal case...")
    input_data = {
        "patient_id": 1,
        "age": 65,
        "chief_complaint": "Fever and cough",
        "symptoms": ["fever", "cough", "headache"],
        "notes": "Patient has mild symptoms"
    }
    
    result = triage_agent(input_data)
    print(f"   Risk: {result['risk']}")
    print(f"   Decision: {result['decision']}")
    print(f"   Primary Diagnosis: {result.get('primary_diagnosis', 'N/A')}")
    
    if result.get('differential_diagnosis'):
        print("   Differential Diagnosis:")
        for dx in result['differential_diagnosis']:
            print(f"     - {dx['disease']} ({dx['confidence']*100:.1f}%)")
    
    # Test case 2: Red flag symptoms
    print("\n2. Testing emergency case (red flags)...")
    input_data_emergency = {
        "patient_id": 1,
        "age": 65,
        "chief_complaint": "Severe chest pain",
        "symptoms": ["chest pain", "difficulty breathing", "sweating"],
        "notes": "Pain radiating to left arm"
    }
    
    result_emergency = triage_agent(input_data_emergency)
    print(f"   Risk: {result_emergency['risk']}")
    print(f"   Decision: {result_emergency['decision']}")
    print(f"   Red Flags: {result_emergency.get('detected_red_flags', [])}")
    
    return result, result_emergency

# Test 2.5: Agent Orchestrator
# -----------------------------
def test_orchestrator():
    """Test complete workflow orchestration"""
    from agents.orchestrator import orchestrator
    
    print("\n" + "="*50)
    print("TEST: Agent Orchestrator (Complete Workflow)")
    print("="*50)
    
    # Test triage workflow
    print("\n1. Testing triage workflow...")
    triage_data = {
        "age": 65,
        "chief_complaint": "Fever and cough",
        "symptoms": ["fever", "cough", "headache"],
        "notes": "Patient complains of chest discomfort"
    }
    
    workflow_result = orchestrator.execute_triage_workflow(1, triage_data)
    
    print(f"\n   Agents executed: {len(workflow_result['agents_executed'])}")
    for agent_exec in workflow_result['agents_executed']:
        print(f"   ✅ {agent_exec['agent']}")
    
    print(f"\n   Final Decision:")
    print(f"   - Risk: {workflow_result['final_decision']['risk']}")
    print(f"   - Action: {workflow_result['final_decision']['action']}")
    print(f"   - Follow-up: {workflow_result['final_decision']['follow_up_days']} days")
    
    # Test daily analysis
    print("\n2. Testing daily analysis...")
    daily_analysis = orchestrator.execute_daily_analysis("+919123456789")
    print(f"   Patients analyzed: {daily_analysis['total_patients']}")
    print(f"   High priority: {daily_analysis['high_priority']}")
    
    return workflow_result


# ============================================
# STEP 3: Run All Tests
# ============================================

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("MULTI-AGENT AI SYSTEM - COMPLETE TEST SUITE")
    print("="*60)
    
    # Setup
    print("\n📋 Setting up test data...")
    setup_test_data()
    
    # Individual agent tests
    print("\n🧪 Running individual agent tests...")
    
    test_vital_trend_analyzer()
    test_task_prioritization()
    test_doctor_case_prep()
    test_triage_agent()
    
    # Orchestrator test
    print("\n🎭 Running orchestrator test...")
    test_orchestrator()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
