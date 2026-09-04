BEGIN;

ALTER TABLE "user"
    ALTER COLUMN password DROP NOT NULL;

CREATE TABLE IF NOT EXISTS user_auth_identity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    provider VARCHAR(32) NOT NULL,
    provider_subject VARCHAR(255) NOT NULL,
    provider_email VARCHAR(128),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_auth_identity_user_id_user
        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT uq_user_auth_identity_provider_subject
        UNIQUE (provider, provider_subject),
    CONSTRAINT uq_user_auth_identity_user_provider
        UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS ix_user_auth_identity_user_id
    ON user_auth_identity (user_id);

COMMIT;
