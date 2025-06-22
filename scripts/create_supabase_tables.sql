-- Script pour créer les tables dans Supabase
-- Exécutez ce script dans l'éditeur SQL de votre dashboard Supabase

-- Table des sources
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
);

-- Table des questions
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des réponses
CREATE TABLE IF NOT EXISTS answers (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des tags
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

-- Table principale des halakhot
CREATE TABLE IF NOT EXISTS halakhot (
    id SERIAL PRIMARY KEY,
    title VARCHAR,
    content TEXT NOT NULL,
    theme VARCHAR,
    source_id INTEGER REFERENCES sources(id) NOT NULL,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE NOT NULL,
    answer_id INTEGER REFERENCES answers(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table de liaison halakha_tags (many-to-many)
CREATE TABLE IF NOT EXISTS halakha_tags (
    halakha_id INTEGER REFERENCES halakhot(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (halakha_id, tag_id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_halakhot_theme ON halakhot(theme);
CREATE INDEX IF NOT EXISTS idx_halakhot_title ON halakhot(title);
CREATE INDEX IF NOT EXISTS idx_halakhot_source_id ON halakhot(source_id);
CREATE INDEX IF NOT EXISTS idx_halakha_tags_halakha_id ON halakha_tags(halakha_id);
CREATE INDEX IF NOT EXISTS idx_halakha_tags_tag_id ON halakha_tags(tag_id);

-- Données d'exemple (optionnel)
INSERT INTO sources (name) VALUES 
    ('Choulhan Aroukh'),
    ('Rambam'),
    ('Talmud')
ON CONFLICT DO NOTHING;

INSERT INTO tags (name) VALUES 
    ('kashrut'),
    ('chabbat'),
    ('prière'),
    ('mariage'),
    ('deuil')
ON CONFLICT DO NOTHING; 