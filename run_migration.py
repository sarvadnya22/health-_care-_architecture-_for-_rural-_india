import sqlite3

# Connect to database
conn = sqlite3.connect('health.db')
cursor = conn.cursor()

# Read and execute migration
with open('migrations/002_agent_system.sql', 'r') as f:
    migration_sql = f.read()
    cursor.executescript(migration_sql)

conn.commit()
conn.close()

print("✅ Database migration completed successfully!")
print("✅ Created tables: agent_logs, patient_alerts, follow_up_schedule")
print("✅ Added indexes for performance")
print("✅ Inserted sample data")
