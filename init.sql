-- WorkLog Payment Dashboard - Database Initialization
-- This script creates the schema and seeds initial data for testing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Freelancers table
CREATE TABLE IF NOT EXISTS freelancers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hourly_rate DECIMAL(10, 2) NOT NULL DEFAULT 25.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Worklogs table
CREATE TABLE IF NOT EXISTS worklogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    freelancer_id UUID NOT NULL REFERENCES freelancers(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    description TEXT,
    total_hours DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Time Entries table
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worklog_id UUID NOT NULL REFERENCES worklogs(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    hours DECIMAL(10, 2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Payment Batches table
CREATE TABLE IF NOT EXISTS payment_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create Payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES payment_batches(id) ON DELETE SET NULL,
    worklog_id UUID NOT NULL REFERENCES worklogs(id) ON DELETE CASCADE,
    freelancer_id UUID NOT NULL REFERENCES freelancers(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_worklogs_freelancer ON worklogs(freelancer_id);
CREATE INDEX IF NOT EXISTS idx_worklogs_task ON worklogs(task_id);
CREATE INDEX IF NOT EXISTS idx_worklogs_status ON worklogs(status);
CREATE INDEX IF NOT EXISTS idx_worklogs_created_at ON worklogs(created_at);
CREATE INDEX IF NOT EXISTS idx_time_entries_worklog ON time_entries(worklog_id);
CREATE INDEX IF NOT EXISTS idx_payments_batch ON payments(batch_id);
CREATE INDEX IF NOT EXISTS idx_payments_worklog ON payments(worklog_id);

-- ==================== SEED DATA ====================

-- Insert Freelancers
INSERT INTO freelancers (id, name, email, hourly_rate) VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Alice Johnson', 'alice@example.com', 35.00),
    ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Bob Smith', 'bob@example.com', 40.00),
    ('c3d4e5f6-a7b8-9012-cdef-123456789012', 'Carol Williams', 'carol@example.com', 45.00),
    ('d4e5f6a7-b8c9-0123-defa-234567890123', 'David Brown', 'david@example.com', 30.00),
    ('e5f6a7b8-c9d0-1234-efab-345678901234', 'Eva Martinez', 'eva@example.com', 50.00);

-- Insert Tasks
INSERT INTO tasks (id, title, description, status) VALUES
    ('11111111-1111-1111-1111-111111111111', 'API Development', 'Build REST API endpoints for user management', 'active'),
    ('22222222-2222-2222-2222-222222222222', 'Frontend Dashboard', 'Create admin dashboard with React', 'active'),
    ('33333333-3333-3333-3333-333333333333', 'Database Optimization', 'Optimize database queries and indexes', 'active'),
    ('44444444-4444-4444-4444-444444444444', 'Authentication System', 'Implement OAuth2 authentication', 'active'),
    ('55555555-5555-5555-5555-555555555555', 'Mobile App Integration', 'Integrate mobile app with backend APIs', 'active'),
    ('66666666-6666-6666-6666-666666666666', 'Testing & QA', 'Write unit and integration tests', 'active');

-- Insert Worklogs (various dates for testing date range filtering)
-- Using valid hex UUIDs (0-9, a-f only)
INSERT INTO worklogs (id, freelancer_id, task_id, description, total_hours, total_amount, status, created_at) VALUES
    -- Alice's worklogs
    ('f1111111-1111-1111-1111-111111111111', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '11111111-1111-1111-1111-111111111111', 
     'Implemented user CRUD endpoints', 8.5, 297.50, 'pending', '2026-01-15 10:00:00+00'),
    ('f2222222-2222-2222-2222-222222222222', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '44444444-4444-4444-4444-444444444444', 
     'Set up JWT authentication', 6.0, 210.00, 'pending', '2026-01-20 09:00:00+00'),
    
    -- Bob's worklogs
    ('f3333333-3333-3333-3333-333333333333', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', '22222222-2222-2222-2222-222222222222', 
     'Built dashboard layout and navigation', 12.0, 480.00, 'pending', '2026-01-18 08:00:00+00'),
    ('f4444444-4444-4444-4444-444444444444', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', '22222222-2222-2222-2222-222222222222', 
     'Created data visualization components', 10.5, 420.00, 'pending', '2026-01-25 10:00:00+00'),
    
    -- Carol's worklogs
    ('f5555555-5555-5555-5555-555555555555', 'c3d4e5f6-a7b8-9012-cdef-123456789012', '33333333-3333-3333-3333-333333333333', 
     'Analyzed slow queries and added indexes', 5.0, 225.00, 'pending', '2026-01-22 14:00:00+00'),
    ('f6666666-6666-6666-6666-666666666666', 'c3d4e5f6-a7b8-9012-cdef-123456789012', '33333333-3333-3333-3333-333333333333', 
     'Optimized database connection pooling', 4.0, 180.00, 'paid', '2026-01-10 11:00:00+00'),
    
    -- David's worklogs
    ('f7777777-7777-7777-7777-777777777777', 'd4e5f6a7-b8c9-0123-defa-234567890123', '55555555-5555-5555-5555-555555555555', 
     'Integrated push notifications', 7.5, 225.00, 'pending', '2026-01-28 09:00:00+00'),
    ('f8888888-8888-8888-8888-888888888888', 'd4e5f6a7-b8c9-0123-defa-234567890123', '11111111-1111-1111-1111-111111111111', 
     'Added API rate limiting', 3.5, 105.00, 'pending', '2026-01-30 13:00:00+00'),
    
    -- Eva's worklogs
    ('f9999999-9999-9999-9999-999999999999', 'e5f6a7b8-c9d0-1234-efab-345678901234', '66666666-6666-6666-6666-666666666666', 
     'Wrote comprehensive unit tests', 15.0, 750.00, 'pending', '2026-01-26 08:00:00+00'),
    ('faaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'e5f6a7b8-c9d0-1234-efab-345678901234', '44444444-4444-4444-4444-444444444444', 
     'Security audit and fixes', 8.0, 400.00, 'pending', '2026-02-01 10:00:00+00');

-- Insert Time Entries for each worklog
-- Alice's time entries for worklog 1
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f1111111-1111-1111-1111-111111111111', '2026-01-15 09:00:00+00', '2026-01-15 12:30:00+00', 3.5, 'Created user model and database schema'),
    ('f1111111-1111-1111-1111-111111111111', '2026-01-15 13:30:00+00', '2026-01-15 17:00:00+00', 3.5, 'Implemented GET and POST endpoints'),
    ('f1111111-1111-1111-1111-111111111111', '2026-01-15 17:30:00+00', '2026-01-15 19:00:00+00', 1.5, 'Added input validation and error handling');

-- Alice's time entries for worklog 2
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f2222222-2222-2222-2222-222222222222', '2026-01-20 09:00:00+00', '2026-01-20 12:00:00+00', 3.0, 'Set up JWT token generation'),
    ('f2222222-2222-2222-2222-222222222222', '2026-01-20 13:00:00+00', '2026-01-20 16:00:00+00', 3.0, 'Implemented refresh token logic');

-- Bob's time entries for worklog 3
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f3333333-3333-3333-3333-333333333333', '2026-01-18 08:00:00+00', '2026-01-18 12:00:00+00', 4.0, 'Created responsive sidebar navigation'),
    ('f3333333-3333-3333-3333-333333333333', '2026-01-18 13:00:00+00', '2026-01-18 17:00:00+00', 4.0, 'Built header and user menu components'),
    ('f3333333-3333-3333-3333-333333333333', '2026-01-19 09:00:00+00', '2026-01-19 13:00:00+00', 4.0, 'Implemented routing and page layouts');

-- Bob's time entries for worklog 4
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f4444444-4444-4444-4444-444444444444', '2026-01-25 10:00:00+00', '2026-01-25 14:30:00+00', 4.5, 'Created bar and line chart components'),
    ('f4444444-4444-4444-4444-444444444444', '2026-01-25 15:00:00+00', '2026-01-25 18:00:00+00', 3.0, 'Built data table with sorting'),
    ('f4444444-4444-4444-4444-444444444444', '2026-01-26 09:00:00+00', '2026-01-26 12:00:00+00', 3.0, 'Added export to CSV functionality');

-- Carol's time entries for worklog 5
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f5555555-5555-5555-5555-555555555555', '2026-01-22 14:00:00+00', '2026-01-22 17:00:00+00', 3.0, 'Identified N+1 query issues'),
    ('f5555555-5555-5555-5555-555555555555', '2026-01-22 17:30:00+00', '2026-01-22 19:30:00+00', 2.0, 'Added composite indexes');

-- Carol's time entries for worklog 6 (paid)
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f6666666-6666-6666-6666-666666666666', '2026-01-10 11:00:00+00', '2026-01-10 15:00:00+00', 4.0, 'Configured connection pooling with PgBouncer');

-- David's time entries for worklog 7
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f7777777-7777-7777-7777-777777777777', '2026-01-28 09:00:00+00', '2026-01-28 12:30:00+00', 3.5, 'Set up Firebase Cloud Messaging'),
    ('f7777777-7777-7777-7777-777777777777', '2026-01-28 13:30:00+00', '2026-01-28 17:30:00+00', 4.0, 'Implemented notification handlers');

-- David's time entries for worklog 8
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f8888888-8888-8888-8888-888888888888', '2026-01-30 13:00:00+00', '2026-01-30 16:30:00+00', 3.5, 'Implemented Redis-based rate limiter');

-- Eva's time entries for worklog 9
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('f9999999-9999-9999-9999-999999999999', '2026-01-26 08:00:00+00', '2026-01-26 12:00:00+00', 4.0, 'Wrote tests for authentication module'),
    ('f9999999-9999-9999-9999-999999999999', '2026-01-26 13:00:00+00', '2026-01-26 17:00:00+00', 4.0, 'Wrote tests for user management'),
    ('f9999999-9999-9999-9999-999999999999', '2026-01-27 09:00:00+00', '2026-01-27 13:00:00+00', 4.0, 'Wrote tests for payment processing'),
    ('f9999999-9999-9999-9999-999999999999', '2026-01-27 14:00:00+00', '2026-01-27 17:00:00+00', 3.0, 'Set up CI/CD test pipeline');

-- Eva's time entries for worklog 10
INSERT INTO time_entries (worklog_id, start_time, end_time, hours, description) VALUES
    ('faaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '2026-02-01 10:00:00+00', '2026-02-01 14:00:00+00', 4.0, 'Conducted security vulnerability scan'),
    ('faaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '2026-02-01 15:00:00+00', '2026-02-01 19:00:00+00', 4.0, 'Fixed XSS and CSRF vulnerabilities');

-- Insert a sample completed payment batch
INSERT INTO payment_batches (id, date_from, date_to, total_amount, status, processed_at) VALUES
    ('ab111111-1111-1111-1111-111111111111', '2026-01-01', '2026-01-15', 180.00, 'completed', '2026-01-16 10:00:00+00');

-- Insert payment for the completed batch
INSERT INTO payments (batch_id, worklog_id, freelancer_id, amount, status) VALUES
    ('ab111111-1111-1111-1111-111111111111', 'f6666666-6666-6666-6666-666666666666', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 180.00, 'completed');

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
