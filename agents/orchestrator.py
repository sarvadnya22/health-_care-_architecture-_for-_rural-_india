"""
Agent Orchestrator
Coordinates execution of multiple AI agents
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict

# Import all agents
from agents.triage_agent import triage_agent
from agents.asha_task_agent import asha_task_agent
from agents.followup_agent import followup_agent
from agents.vital_trend_analyzer import analyze_vital_trends
from agents.task_prioritization_agent import generate_daily_task_list
from agents.doctor_case_prep_agent import prepare_case_summary

class AgentOrchestrator:
    """Coordinates multi-agent execution"""
    
    def __init__(self):
        self.execution_log = []
    
    def execute_triage_workflow(self, patient_id: int, triage_data: dict) -> dict:
        """
        Execute complete triage workflow with multiple agents
        
        Workflow:
        1. Triage Agent (diagnosis + risk assessment)
        2. Vital Trend Analyzer (check history)
        3. ASHA Task Agent (generate tasks)
        4. Follow-up Agent (schedule follow-up)
        
        Args:
            patient_id: Patient ID
            triage_data: Triage form data from ASHA
            
        Returns:
            Complete workflow results
        """
        start_time = datetime.now()
        results = {
            "patient_id": patient_id,
            "workflow": "triage",
            "agents_executed": [],
            "final_decision": None
        }
        
        # Step 1: Run Triage Agent
        print("🤖 Running Triage Agent...")
        triage_input = {
            "patient_id": patient_id,
            "age": triage_data.get("age"),
            "chief_complaint": triage_data.get("chief_complaint"),
            "symptoms": triage_data.get("symptoms", []),
            "notes": triage_data.get("notes", "")
        }
        
        triage_output = triage_agent(triage_input)
        results["agents_executed"].append({
            "agent": "triage_agent",
            "output": triage_output
        })
        results["triage_assessment"] = triage_output
        
        # Step 2: Run Vital Trend Analyzer
        print("🤖 Running Vital Trend Analyzer...")
        trend_output = analyze_vital_trends(patient_id)
        results["agents_executed"].append({
            "agent": "vital_trend_analyzer",
            "output": trend_output
        })
        results["vital_trends"] = trend_output
        
        # Step 3: Run ASHA Task Agent
        print("🤖 Running ASHA Task Agent...")
        task_input = {
            "decision": triage_output.get("decision", "ASHA Follow-up")
        }
        task_output = asha_task_agent(task_input)
        results["agents_executed"].append({
            "agent": "asha_task_agent",
            "output": task_output
        })
        results["asha_task"] = task_output
        
        # Step 4: Determine follow-up schedule based on risk
        print("🤖 Scheduling Follow-up...")
        risk_level = triage_output.get("risk", "Moderate")
        
        if risk_level == "Critical" or triage_output.get("decision") == "Emergency":
            followup_days = 0  # Immediate hospital referral
        elif risk_level == "High":
            followup_days = 1  # 24 hours
        elif risk_level == "Moderate":
            followup_days = 2  # 48 hours
        else:
            followup_days = 5  # 5 days
        
        results["follow_up_schedule"] = {
            "days": followup_days,
            "priority": task_output.get("task_priority", "MEDIUM")
        }
        
        # Final decision
        results["final_decision"] = {
            "risk": risk_level,
            "action": triage_output.get("decision"),
            "asha_task": task_output.get("asha_task"),
            "follow_up_days": followup_days
        }
        
        # SAVE FOLLOW-UP TO DB (NEW)
        try:
             conn = sqlite3.connect('health.db') # Import sqlite3 inside logic if needed, or pass connection
             from datetime import timedelta
             follow_up_date = (start_time + timedelta(days=followup_days)).strftime('%Y-%m-%d')
             
             # Assuming we have a recent triage_report entry or we update workflow
             # Ideally this should be called by app.py after creating the report, but we can do it here if we have IDs
             # For now, just logging that logic is ready
             results['calculated_follow_up_date'] = follow_up_date
             conn.close()
        except Exception as e:
            print(f"Error calculating date: {e}")

        # Step 5: Autonomous Outbreak Detection (Agentic Feature)
        print("🤖 Running Autonomous Outbreak Monitor...")
        outbreak_alert = self.detect_outbreak_patterns(triage_data.get('village', 'Unknown'), triage_output.get('decision'))
        if outbreak_alert:
            results["agent_alert"] = outbreak_alert
            print(f"🚨 AGENT ACTION: {outbreak_alert['message']}")

        # Log execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        results["execution_time_seconds"] = execution_time
        
        print(f"✅ Triage workflow completed in {execution_time:.2f}s")
        return results

    def detect_outbreak_patterns(self, village: str, current_decision: str) -> dict:
        """
        Autonomous Agent: Monitors for outbreaks and takes action.
        Returns alert dict if action taken, else None.
        """
        if not village or village == 'Unknown': return None
        
        try:
            conn = sqlite3.connect('health.db')
            cursor = conn.cursor()
            
            # 1. Look for recent high-risk cases in the same village (last 7 days)
            # We count cases with 'High' or 'Emergency' decisions, OR similar symptoms (simplified here to decision/risk)
            query = """
                SELECT count(*) FROM triage_reports 
                WHERE symptoms LIKE ? 
                AND timestamp >= date('now', '-7 days')
                AND patient_id IN (SELECT id FROM patients WHERE village = ?)
            """
            # For this demo, we'll simpler logic: Just count recent reports in this village
            # A real agent would do sophisticated clustering on symptoms.
            cursor.execute("SELECT count(*) FROM triage_reports WHERE timestamp >= date('now', '-7 days') AND patient_id IN (SELECT id FROM patients WHERE village = ?)", (village,))
            recent_count = cursor.fetchone()[0]
            
            # Threshold: If this is the 3rd case (or more), trigger alert
            # We add +1 for the current case being processed
            if recent_count + 1 >= 3:
                # Check if advisory already exists recently to avoid spamming
                cursor.execute("SELECT count(*) FROM ministry_advisories WHERE village = ? AND sent_at >= date('now', '-1 days')", (village,))
                advisory_exists = cursor.fetchone()[0]
                
                if not advisory_exists:
                    # AUTONOMOUS ACTION: Create Advisory
                    message_body = f"DETECTED OUTBREAK: {recent_count + 1} recent triage reports in {village}. Immediate survey required."
                    cursor.execute("INSERT INTO ministry_advisories (district, village, message) VALUES (?, ?, ?)", 
                                   ('Dhule', village, message_body)) # Defaulting to Dhule for demo, ideally fetch district from patient
                    conn.commit()
                    conn.close()
                    return {
                        "type": "OUTBREAK_DETECTED",
                        "message": f"Potential outbreak detected in {village}. Ministry notified automatically."
                    }
            
            conn.close()
        except Exception as e:
            print(f"Agent Error: {e}")
            return None
            
        return None
    
    def execute_daily_analysis(self, asha_worker_phone: str) -> dict:
        """
        Execute daily morning routine for ASHA worker
        
        Workflow:
        1. Vital Trend Analyzer (all patients)
        2. Task Prioritization Agent
        
        Args:
            asha_worker_phone: ASHA worker's phone number
            
        Returns:
            Daily task list with priorities
        """
        start_time = datetime.now()
        print(f"🌅 Running daily analysis for {asha_worker_phone}...")
        
        # Step 1: Generate prioritized task list
        task_list = generate_daily_task_list(asha_worker_phone)
        
        # Step 2: Run vital trend analyzer for high-priority patients
        for patient_item in task_list.get("patients", [])[:5]:  # Top 5 only
            patient_id = patient_item["patient"]["id"]
            analyze_vital_trends(patient_id)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        task_list["execution_time_seconds"] = execution_time
        
        print(f"✅ Daily analysis completed in {execution_time:.2f}s")
        return task_list
    
    def execute_doctor_prep(self, patient_id: int, use_llm: bool = True) -> str:
        """
        Execute doctor case preparation
        
        Args:
            patient_id: Patient ID
            use_llm: Whether to use LLM for formatting
            
        Returns:
            Formatted case summary
        """
        print(f"🩺 Preparing case summary for patient {patient_id}...")
        summary = prepare_case_summary(patient_id, use_llm=use_llm)
        print("✅ Case summary ready")
        return summary
    
    def get_execution_summary(self) -> dict:
        """Get summary of all agent executions"""
        return {
            "total_workflows": len(self.execution_log),
            "recent_executions": self.execution_log[-10:]
        }

# Global orchestrator instance
orchestrator = AgentOrchestrator()

if __name__ == "__main__":
    # Test the orchestrator
    print("Testing Agent Orchestrator...")
    
    # Test triage workflow
    test_triage_data = {
        "age": 65,
        "chief_complaint": "Fever and cough",
        "symptoms": ["fever", "cough", "headache"],
        "notes": "Patient complains of chest pain"
    }
    
    results = orchestrator.execute_triage_workflow(1, test_triage_data)
    print(json.dumps(results, indent=2))
