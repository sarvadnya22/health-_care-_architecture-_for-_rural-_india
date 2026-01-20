import sqlite3
from agents.followup_agent import followup_agent

def run_followup_workflows():
    conn = sqlite3.connect("health.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    workflows = cursor.execute("""
        SELECT * FROM care_workflows
        WHERE status = 'active'
    """).fetchall()

    for wf in workflows:
        result = followup_agent(dict(wf))

        cursor.execute("""
            UPDATE care_workflows
            SET current_state = ?, next_action = ?
            WHERE id = ?
        """, (
            result["new_state"],
            result["next_action"],
            wf["id"]
        ))

    conn.commit()
    conn.close()
