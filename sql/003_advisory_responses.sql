CREATE TABLE IF NOT EXISTS advisory_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advisory_id INTEGER NOT NULL,
    worker_phone TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advisory_id) REFERENCES ministry_advisories (id)
);
