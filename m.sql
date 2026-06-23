-- Tabel reputasi domain
CREATE TABLE domain_reputation (
    id              SERIAL PRIMARY KEY,
    domain          VARCHAR(255) UNIQUE NOT NULL,
    risk_score      FLOAT DEFAULT 0.0,
    threat_type     VARCHAR(50),
    first_seen      TIMESTAMP DEFAULT NOW(),
    last_scanned    TIMESTAMP DEFAULT NOW(),
    scan_count      INTEGER DEFAULT 1,
    confirmed_bad   BOOLEAN DEFAULT FALSE,
    source          VARCHAR(50) DEFAULT 'ml_detected'
);
 
-- Cache fitur network domain
CREATE TABLE domain_features_cache (
    domain          VARCHAR(255) PRIMARY KEY,
    features_json   JSONB,
    cached_at       TIMESTAMP DEFAULT NOW(),
    expires_at      TIMESTAMP
);
 
-- Database hash file berbahaya
CREATE TABLE file_signatures (
    sha256_hash     CHAR(64) PRIMARY KEY,
    file_type       VARCHAR(20),
    threat_name     VARCHAR(100),
    detected_at     TIMESTAMP DEFAULT NOW(),
    source          VARCHAR(50)
);
 
-- History scan
CREATE TABLE scan_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_type       VARCHAR(20) NOT NULL,
    input_value     TEXT NOT NULL,
    risk_score      FLOAT,
    threat_label    VARCHAR(50),
    features_json   JSONB,
    shap_values     JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);
 
-- Feedback untuk continuous learning
CREATE TABLE scan_feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID REFERENCES scan_history(id),
    ml_prediction   FLOAT,
    user_correction VARCHAR(20),
    created_at      TIMESTAMP DEFAULT NOW()
);
 
-- Versi model
CREATE TABLE model_versions (
    id              SERIAL PRIMARY KEY,
    model_type      VARCHAR(50),
    version         VARCHAR(20),
    accuracy        FLOAT,
    f1_score        FLOAT,
    trained_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT FALSE
);
