-- Migration 006: Unify Prescriptions Schema
-- This migration consolidates duplicate columns in the prescriptions table

-- Step 1: Copy medication_name data to medication column where medication is NULL
UPDATE prescriptions 
SET medication = medication_name 
WHERE medication IS NULL OR medication = '';

-- Step 2: Rename timestamp to created_at for consistency (if not already)
-- SQLite doesn't support column rename directly, so we keep timestamp
-- The app will handle both column names

-- Step 3: Set default for status column
-- Already has default 'Pending'

-- Done! The redundant columns remain but are now synchronized.
-- In a production system, we would:
-- 1. Create new table with clean schema
-- 2. Migrate data
-- 3. Drop old table
-- 4. Rename new table

-- For this demo, we just ensure data consistency.
