import sqlite3
import random

# ---------------------------
# 1) Connect to database
# ---------------------------
conn = sqlite3.connect("database.db")
c = conn.cursor()

# ---------------------------
# 2) Create tables
# ---------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS researchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    field TEXT,
    institution TEXT,
    email TEXT,
    bio TEXT,
    citation_count INTEGER DEFAULT 0,
    publication_count INTEGER DEFAULT 0,
    photo TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS research_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    researcher_id INTEGER,
    platform TEXT,
    url TEXT,
    FOREIGN KEY(researcher_id) REFERENCES researchers(id) ON DELETE CASCADE
)
""")

conn.commit()

# ---------------------------
# 3) Prepare sample data
# ---------------------------

first_names = ["Sok", "Vannak", "Chenda", "Rithy", "Srey", "Pich", "Kosal", "Dara", "Sopheap", "Chan"]
last_names = ["Kou", "Chhay", "Sok", "Roth", "Ly", "Ngin", "Heng", "Meas", "Chea", "Phan"]

fields = ["AI", "Cybersecurity", "Networking", "Software Engineering",
          "Data Science", "Robotics", "IoT", "Cloud Computing", "HCI", "Bioinformatics"]

institutions = ["Royal University of Phnom Penh", "Institute of Technology of Cambodia",
                "University of Cambodia", "Cambodian Mekong University", "National Polytechnic Institute"]

platforms = ["Google Scholar", "ORCID", "LinkedIn", "ResearchGate"]

# ---------------------------
# 4) Generate 1000 researchers
# ---------------------------

for i in range(1000):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    field = ', '.join(random.sample(fields, k=random.randint(1,3)))
    institution = random.choice(institutions)
    email = f"user{i+1}@example.com"
    bio = f"{name} is a researcher in {field} at {institution}."
    citation_count = random.randint(0, 1000)
    publication_count = random.randint(1, 100)
    photo = None  # optional placeholder

    c.execute("""
        INSERT INTO researchers (name, field, institution, email, bio, citation_count, publication_count, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, field, institution, email, bio, citation_count, publication_count, photo))

    researcher_id = c.lastrowid

    # Add 1-3 random research profiles
    num_profiles = random.randint(1, 3)
    chosen_platforms = random.sample(platforms, num_profiles)
    for p in chosen_platforms:
        url = f"https://{p.replace(' ', '').lower()}.com/{name.replace(' ', '').lower()}"
        c.execute("""
            INSERT INTO research_profiles (researcher_id, platform, url)
            VALUES (?, ?, ?)
        """, (researcher_id, p, url))

conn.commit()
conn.close()
print("Database initialized with 1000+ realistic sample researchers!")
