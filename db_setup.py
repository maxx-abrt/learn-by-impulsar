import sqlite3

def init_db():
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    # Création de la table des utilisateurs
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
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

    
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
