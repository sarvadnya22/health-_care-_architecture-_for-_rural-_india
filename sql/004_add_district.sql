ALTER TABLE patients ADD COLUMN district TEXT DEFAULT 'Dhule';
UPDATE patients SET district = 'Dhule';
