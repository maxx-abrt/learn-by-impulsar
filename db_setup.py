import sqlite3

def init_db():
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    

    
    # Création de la table des scores
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    # Création de la table des réponses des utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    # Création de la table des sessions des utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
              
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        user_answers TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
''')
    


    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        domain TEXT NOT NULL,
        study_level TEXT NOT NULL,
        points INTEGER DEFAULT 0,
        community_points INTEGER DEFAULT 0,
        quizzes_completed INTEGER DEFAULT 0,
        registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
    
    # Ajoutez cette ligne au script db_setup.py dans la définition de la table users
    c.execute('''
    ALTER TABLE users ADD COLUMN community_points INTEGER DEFAULT 0;
    ''')



    
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
