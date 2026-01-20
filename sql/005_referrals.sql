CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    referred_by_asha TEXT NOT NULL,
    doctor_id INTEGER,
    reason TEXT NOT NULL,
    priority TEXT DEFAULT 'Routine', -- Routine, Urgent, Emergency
    status TEXT DEFAULT 'Pending', -- Pending, Accepted, Completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients (id),
    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
);

ALTER TABLE triage_reports ADD COLUMN follow_up_date DATE;
