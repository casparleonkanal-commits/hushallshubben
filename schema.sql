-- 1. Skapa tabellen för Familjer
CREATE TABLE families (
    id SERIAL PRIMARY KEY,
    family_name VARCHAR(100) NOT NULL
);

-- 2. Skapa tabellen för Användare (och koppla till en familj)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    family_id INT REFERENCES families(id) ON DELETE SET NULL
);

-- 3. Skapa tabellen för Sysslor (och koppla till en familj + användare)
CREATE TABLE chores (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    family_id INT REFERENCES families(id) ON DELETE CASCADE,
    assigned_to INT REFERENCES users(id) ON DELETE SET NULL,
    is_completed BOOLEAN DEFAULT FALSE
);