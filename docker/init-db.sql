-- Initialize FHIR Analytics Database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index on username and email
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(255) UNIQUE NOT NULL,
    identifier JSONB,
    name JSONB,
    gender VARCHAR(50),
    birth_date DATE,
    address JSONB,
    telecom JSONB,
    marital_status VARCHAR(100),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_patients_fhir_id ON patients(fhir_id);
CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients(gender);
CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON patients(birth_date);

-- Create conditions table
CREATE TABLE IF NOT EXISTS conditions (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id VARCHAR(255),
    code JSONB,
    code_text VARCHAR(500),
    category JSONB,
    clinical_status VARCHAR(100),
    verification_status VARCHAR(100),
    severity VARCHAR(100),
    onset_datetime TIMESTAMP WITH TIME ZONE,
    recorded_date TIMESTAMP WITH TIME ZONE,
    encounter_id VARCHAR(255),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (patient_id) REFERENCES patients(fhir_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conditions_fhir_id ON conditions(fhir_id);
CREATE INDEX IF NOT EXISTS idx_conditions_patient_id ON conditions(patient_id);
CREATE INDEX IF NOT EXISTS idx_conditions_code_text ON conditions(code_text);
CREATE INDEX IF NOT EXISTS idx_conditions_onset_datetime ON conditions(onset_datetime);
CREATE INDEX IF NOT EXISTS idx_conditions_recorded_date ON conditions(recorded_date);

-- Create encounters table
CREATE TABLE IF NOT EXISTS encounters (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id VARCHAR(255),
    status VARCHAR(100),
    encounter_class VARCHAR(100),
    type JSONB,
    service_type VARCHAR(255),
    priority VARCHAR(100),
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    reason_code JSONB,
    diagnosis JSONB,
    location JSONB,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (patient_id) REFERENCES patients(fhir_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_encounters_fhir_id ON encounters(fhir_id);
CREATE INDEX IF NOT EXISTS idx_encounters_patient_id ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_period_start ON encounters(period_start);

-- Create observations table
CREATE TABLE IF NOT EXISTS observations (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id VARCHAR(255),
    encounter_id VARCHAR(255),
    status VARCHAR(100),
    category JSONB,
    code JSONB,
    code_text VARCHAR(500),
    value JSONB,
    value_quantity JSONB,
    effective_datetime TIMESTAMP WITH TIME ZONE,
    issued TIMESTAMP WITH TIME ZONE,
    interpretation JSONB,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (patient_id) REFERENCES patients(fhir_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_observations_fhir_id ON observations(fhir_id);
CREATE INDEX IF NOT EXISTS idx_observations_patient_id ON observations(patient_id);
CREATE INDEX IF NOT EXISTS idx_observations_encounter_id ON observations(encounter_id);
CREATE INDEX IF NOT EXISTS idx_observations_effective_datetime ON observations(effective_datetime);

-- Create ETL jobs table
CREATE TABLE IF NOT EXISTS etl_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    fhir_server_url VARCHAR(500),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_log TEXT,
    config JSONB,
    result JSONB,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etl_jobs_job_id ON etl_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_resource_type ON etl_jobs(resource_type);

-- Create valuesets table
CREATE TABLE IF NOT EXISTS valuesets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) UNIQUE,
    version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    code_system VARCHAR(255),
    codes JSONB,
    compose JSONB,
    expansion JSONB,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_valuesets_name ON valuesets(name);
CREATE INDEX IF NOT EXISTS idx_valuesets_code_system ON valuesets(code_system);
CREATE INDEX IF NOT EXISTS idx_valuesets_status ON valuesets(status);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, full_name, role)
VALUES (
    'admin',
    'admin@fhir-analytics.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB0qJKfgJCm',
    'System Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert engineer user (password: engineer123)
INSERT INTO users (username, email, hashed_password, full_name, role)
VALUES (
    'engineer',
    'engineer@fhir-analytics.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB0qJKfgJCm',
    'System Engineer',
    'engineer'
) ON CONFLICT (username) DO NOTHING;

-- Insert sample valuesets
INSERT INTO valuesets (name, url, code_system, description, codes)
VALUES (
    'ICD-10 Diagnoses',
    'http://hl7.org/fhir/sid/icd-10',
    'ICD-10',
    'International Classification of Diseases, 10th Revision',
    '[
        {"code": "J09", "display": "Influenza due to identified avian influenza virus"},
        {"code": "J10", "display": "Influenza due to other identified influenza virus"},
        {"code": "J11", "display": "Influenza, virus not identified"},
        {"code": "I21", "display": "Acute myocardial infarction"},
        {"code": "C34.1", "display": "Malignant neoplasm of upper lobe, bronchus or lung"},
        {"code": "E10", "display": "Type 1 diabetes mellitus"},
        {"code": "E11", "display": "Type 2 diabetes mellitus"},
        {"code": "I10", "display": "Essential (primary) hypertension"},
        {"code": "J44", "display": "Chronic obstructive pulmonary disease"}
    ]'::jsonb
) ON CONFLICT (url) DO NOTHING;

-- Grant permissions
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fhir_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fhir_user;

