-- Database initialization script for Spotijudge
-- This runs automatically when PostgreSQL container starts up

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the database user if running as superuser
-- (This might not be needed if using docker-compose with predefined user)
-- CREATE USER spotijudge_user WITH PASSWORD 'spotijudge_password';
-- GRANT ALL PRIVILEGES ON DATABASE spotijudge TO spotijudge_user;

-- Set timezone
SET timezone = 'UTC';

-- Additional configurations
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Reload configuration
SELECT pg_reload_conf();