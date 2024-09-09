import streamlit as st
import sqlite3
import json
import hashlib
import time
import pandas as pd
from datetime import datetime
from community_questions import load_community_questions, add_community_question
import requests
from dotenv import load_dotenv
import os
import datetime

# Constantes
COOLDOWN_TIME = 15




def get_top_users(limit=10):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("""
        SELECT username, SUM(points) as total_points 
        FROM users
        GROUP BY username 
        ORDER BY total_points DESC 
        LIMIT ?
    """, (limit,))
    results = c.fetchall()
    conn.close()
    return results

def display_leaderboard():
    top_users = get_top_users()
    
    st.markdown("""
    <style>
    .leaderboard {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .leaderboard h3 {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 15px;
    }
    .leaderboard table {
        width: 100%;
        border-collapse: collapse;
    }
    .leaderboard th, .leaderboard td {
        text-align: left;
        padding: 8px;
        border-bottom: 1px solid #ddd;
    }
    .leaderboard tr:nth-child(even) {
        background-color: #e6e9ed;
    }
    .leaderboard tr:hover {
        background-color: #d1d5db;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="leaderboard">', unsafe_allow_html=True)
    st.markdown('<h3>Top 10 des utilisateurs : Leaderboard</h3>', unsafe_allow_html=True)
    
    df = pd.DataFrame(top_users, columns=['Utilisateur', 'Points'])
    df.index = df.index + 1  # Start index at 1
    st.table(df)
    
    st.markdown('</div>', unsafe_allow_html=True)








def display_chat():
    st.subheader("Chat en direct")

    # Styles CSS améliorés
    st.markdown("""
    <style>
    .message {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);

    }
    .message.new {
        animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    .username {
        font-weight: bold;
        color: #2196F3;
        margin-right: 5px;
    }
    .domain {
        font-style: italic;
        color: #4CAF50;
        margin-left: 5px;
    }
    .timestamp {
        font-size: 0.8em;
        color: #888;
        float: right;
    }
.input-container {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}
.input-container > div {
    display: flex;
    flex-grow: 1;
}
.input-container .stTextInput {
    flex-grow: 1;
}
.input-container .stButton {
    margin-left: 10px;
}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='input-container'>", unsafe_allow_html=True)
    message = st.text_input("Votre message:", key="message_input", value="", max_chars=None, type="default")
    send_button = st.button("Envoyer")
    st.markdown("</div>", unsafe_allow_html=True)

    # Affichage du message de cooldown
    cooldown_container = st.empty()

    # Gestion du cooldown
    if 'last_message_time' not in st.session_state:
        st.session_state.last_message_time = 0

    current_time = time.time()
    cooldown = 5  # 5 secondes de cooldown

    if send_button:
        if current_time - st.session_state.last_message_time >= cooldown:
            if message:
                add_message(st.session_state.username, message)
                st.session_state.last_message_time = current_time
                st.session_state.messages = get_messages()
                st.rerun()
        else:
            remaining_time = cooldown - (current_time - st.session_state.last_message_time)
            cooldown_container.warning(f"Veuillez attendre {remaining_time:.1f} secondes avant d'envoyer un nouveau message.")

    # Assurez-vous que les messages sont chargés dès l'ouverture de la page
    if 'messages' not in st.session_state:
        st.session_state.messages = get_messages()

    # Affichage des messages
    for i, (username, msg, timestamp) in enumerate(reversed(st.session_state.messages)):
        time_str = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        domain = get_user_domain(username)
        message_class = 'message new' if i == 0 else 'message'
        st.markdown(f"""
        <div class='{message_class}' id='message-{i}'>
            <span class='username'>{username}</span>
            <span class='domain'>({domain})</span>
            <span class='timestamp'>{time_str}</span>
            <br>{msg}
        </div>
        """, unsafe_allow_html=True)

    # Script JavaScript pour l'animation
    st.markdown(
    """
    <script>
    function animateNewMessage() {
        var messages = document.querySelectorAll('.message');
        if (messages.length > 0) {
            var latestMessage = messages[0];
            latestMessage.classList.add('new');
        }
    }

    // Animer le dernier message au chargement de la page
    document.addEventListener('DOMContentLoaded', animateNewMessage);
    </script>
    """,
    unsafe_allow_html=True
    )
    
    st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', (event) => {
    const inputField = document.querySelector('.input-container .stTextInput input');
    const sendButton = document.querySelector('.input-container .stButton button');
    
    if (inputField && sendButton) {
        inputField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendButton.click();
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)

# Fonction pour récupérer le domaine d'étude de l'utilisateur
def get_user_domain(username):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("SELECT domain FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Non spécifié"
    

# Fonction pour initialiser la base de données du chat (inchangée)
def init_chat_db():
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  message TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Fonction pour ajouter un message au chat
def add_message(username, message):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

# Fonction pour récupérer les messages du chat
def get_messages():
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    return messages[::-1]  # Inverser l'ordre pour afficher les messages les plus récents en bas









def display_account_details(username):
    st.subheader(f"Compte de {username}")
    
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("SELECT points, quizzes_completed, domain, study_level, registration_date FROM users WHERE username=?", (username,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        points, quizzes_completed, domain, study_level, registration_date = user_data
        
        st.write(f"**Nom d'utilisateur:** {username}")
        st.write(f"**Points obtenus aux QCM:** {points}")
        st.write(f"**Nombre de quiz complétés:** {quizzes_completed}")
        st.write(f"**Domaine d'étude:** {domain}")
        st.write(f"**Niveau d'étude:** {study_level}")
        st.write(f"**Date d'inscription:** {registration_date}")
        
        # Vous pouvez ajouter d'autres statistiques ici si nécessaire
    else:
        st.error("Erreur lors de la récupération des données utilisateur.")
        
        
def initialize_question_files():
    domains = ["anatomie", "physiologie", "chimie_biochimie", "mathematiques_arithmetique", "hygiene", "pharmacologie", "psychologie"]
    types = ["official", "community"]
    
    placeholder_question = {
        "domain": "",
        "subdomain": "",
        "subsystem": "",
        "type": "QCM",
        "question": "Ceci est une question placeholder.",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer": "Option 1",
        "explanation": "Ceci est une explication placeholder."
    }

    for domain in domains:
        for qtype in types:
            filename = f"{domain}_{qtype}_questions.json"
            if not os.path.exists(filename):
                with open(filename, 'w') as f:
                    json.dump([placeholder_question], f, indent=2)
            else:
                with open(filename, 'r+') as f:
                    try:
                        data = json.load(f)
                        if not data:  # Si le fichier est vide (liste vide)
                            f.seek(0)
                            json.dump([placeholder_question], f, indent=2)
                            f.truncate()
                    except json.JSONDecodeError:  # Si le fichier est vide ou mal formaté
                        f.seek(0)
                        json.dump([placeholder_question], f, indent=2)
                        f.truncate()

    print("Tous les fichiers de questions ont été initialisés ou vérifiés.")










# Configuration de Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Chargement des variables d'environnement
load_dotenv()
brevo_api_key = os.getenv("BREVO_API_KEY")
brevo_api_url = os.getenv("BREVO_API_URL")

# Fonctions d'authentification et de gestion des utilisateurs
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, domain, study_level):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password, domain, study_level, registration_date) VALUES (?, ?, ?, ?, ?)",
                  (username, hashed_password, domain, study_level, datetime.datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_stats(username):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("SELECT points, quizzes_completed, registration_date FROM users WHERE username=?", (username,))
    stats = c.fetchone()
    conn.close()
    return stats

def update_user_stats(username, points=0, quizzes_completed=0):
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ?, quizzes_completed = quizzes_completed + ? WHERE username=?",
              (points, quizzes_completed, username))
    conn.commit()
    conn.close()

# Fonctions de gestion des quiz
def load_questions(domain, subdomain=None, subsystem=None, question_type="official"):
    file_name = f"{domain.lower().replace('/', '_')}_{question_type}_questions.json"
    try:
        with open(file_name, "r") as file:
            all_questions = json.load(file)
    except FileNotFoundError:
        return []
    
    if domain == "Anatomie":
        if subdomain and subsystem:
            return [q for q in all_questions if q["subdomain"] == subdomain and q["subsystem"] == subsystem]
        elif subdomain:
            return [q for q in all_questions if q["subdomain"] == subdomain]
    else:
        if subdomain:
            return [q for q in all_questions if q["subdomain"] == subdomain]
    
    return all_questions

def add_question_to_json(question, question_type):
    domain = question["domain"].lower().replace("/", "_")
    file_name = f"{domain}_{question_type}_questions.json"
    
    try:
        with open(file_name, "r") as file:
            questions = json.load(file)
    except FileNotFoundError:
        questions = []
    
    questions.append(question)
    
    with open(file_name, "w") as file:
        json.dump(questions, file, indent=2)

# Fonction d'envoi d'email
def send_email(name, email, message):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": brevo_api_key
    }
    data = {
        "sender": {"email": "maxaubert17@gmail.com", "name": "Formulaire de contact"},
        "to": [{"email": "maxaubert17@gmail.com", "name": "Max Aubert"}],
        "cc": [{"email": email, "name": name}],
        "subject": "Message depuis votre formulaire de contact",
        "htmlContent": f"""
        <html>
            <body>
                <h2>Nouveau message depuis le formulaire de contact</h2>
                <p><strong>Nom:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
            </body>
        </html>
        """
    }
    response = requests.post(brevo_api_url, json=data, headers=headers)
    return response.status_code == 201


st.markdown("""
<style>
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7bcf,#2e7bcf);
        color: white;
    }
    .sidebar-nav {
        padding-top: 30px;
    }
    .sidebar-nav ul {
        padding-left: 0;
    }
    .sidebar-nav li {
        list-style-type: none;
        margin-bottom: 20px;
    }
    .nav-link {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        text-decoration: none;
        display: block;
        transition: background-color 0.3s;
    }
    .nav-link:hover {
        background-color: #45a049;
    }
    .nav-subtitle {
        font-size: 12px;
        color: #ddd;
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour créer un bouton radio personnalisé avec sous-titre
def custom_radio(label, options, subtitles):
    st.sidebar.markdown('<div class="sidebar-nav">', unsafe_allow_html=True)
    for i, (option, subtitle) in enumerate(zip(options, subtitles)):
        if st.sidebar.button(option, key=f"nav_{i}"):
            st.session_state.page = option
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.get('page', options[0])


# Interface utilisateur Streamlit
def main():
    st.title(":blue[Learn]")

# Gestion de l'authentification
    if 'username' not in st.session_state:  
     st.session_state.username = None
     
    choice = None

    if st.session_state.username is None:
      st.title("Apprentissage collaboratif")
      st.subheader(":blue[Connexion]")
      username = st.text_input("Nom d'utilisateur", key="login_username")
      password = st.text_input("Mot de passe", type="password", key="login_password")
      if st.button(":blue[Se connecter]"):
            if verify_user(username, password):
                st.session_state.username = username
                st.success("Connexion réussie!")
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect")
                
      st.subheader(":green[Inscription]")
      new_username = st.text_input("Nom d'utilisateur", key="signup_username")
      new_password = st.text_input("Mot de passe", type="password", key="signup_password")
      domain = st.selectbox("Domaine d'étude", ["Médecine", "Paramédical", "Autre"])
      study_level = st.text_input("Niveau d'étude (ex: Première année)")
      if st.button(":green[S'inscrire]"):
            if create_user(new_username, new_password, domain, study_level):
                st.success("Compte créé avec succès! Vous pouvez maintenant vous connecter.")
            else:
                st.error("Ce nom d'utilisateur existe déjà")

    else:
       menu = ["**:blue[Accueil]**", "**:blue[Quiz]**", "**:blue[Créer une question]**", "**:blue[Chat]**", "**:blue[Mon compte]**", "**:red[Déconnexion]**"]
       menu_subtitles = [
        "Page d'accueil et leaderboard",
        "Commencer à apprendre",
        "Ajouter une nouvelle question",
        "Discuter avec d'autres utilisateurs",
        "Accédez vos informations personnelles",
        "Se déconnecter de l'application"
    ]
    
       choice = custom_radio("Menu", menu, menu_subtitles)


    if choice == "**:blue[Accueil]**":
        st.success(f"Bienvenue, **{st.session_state.username}**!")
        st.write(f"Bienvenue sur cette plateforme d'apprentissage collaboratif ! Le principe est de pouvoir réviser à plusieurs, créer des questions et des quiz communautaires, et s'entraider dans le domaine de la santé !")
        st.write("*Le développement est toujours actif, n'hésitez pas à contacter le développeur en cas de retour ou problème !*")
        st.write(f"Vous pouvez naviguer sur le site grâce à la side bar, sur téléphone, elle est **:red[accessible en ouvrant la flèche en haut à gauche]** : ")
        st.image("arrow.png")
        st.write("Ensuite, **:red[naviguez sur les différents menus disponibles]** ! (cliquez comme sur l'image en dessous !)")
        st.image("menu_1.png", width=250)
    
        display_leaderboard()
    
    elif choice == "**:blue[Chat]**":
     display_chat()
     
    elif choice == "**:blue[Quiz]**":
        st.subheader("Quiz")
        domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]
        selected_domain = st.selectbox("Qu'est-ce que vous souhaitez réviser ?", domains)

        subdomains = {
            "Anatomie": ["Système osseux", "Système circulatoire", "Système nerveux", "Système urinaire", "Système respiratoire"],
            "Physiologie": ["Physiologie fondamentale", "Physiologie appliquée", "Physiopathologie"],
            "Chimie/Biochimie": ["Chimie organique", "Biochimie structurale", "Métabolisme"],
            "Mathématiques et arithmétique": ["Algèbre", "Géométrie", "Statistiques"],
            "Hygiène": ["Hygiène personnelle", "Hygiène alimentaire", "Hygiène environnementale"],
            "Pharmacologie": ["Pharmacocinétique", "Pharmacodynamique", "Classes de médicaments"],
            "Psychologie": ["Psychologie cognitive", "Psychologie sociale", "Psychopathologie"]
        }

        selected_subdomain = st.selectbox("Choisissez un sous-domaine", subdomains[selected_domain])

        if selected_domain == "Anatomie":
            subsystems = {
                "Système osseux": ["Crâne", "Colonne vertébrale", "Membres supérieurs", "Membres inférieurs"],
                "Système circulatoire": ["Cœur", "Artères", "Veines"],
                "Système nerveux": ["Cerveau", "Moelle épinière", "Nerfs périphériques"],
                "Système urinaire": ["Reins", "Vessie", "Urètres"],
                "Système respiratoire": ["Poumons", "Trachée", "Bronches"]
            }
            selected_subsystem = st.selectbox("Choisissez un sous-système", subsystems[selected_subdomain])
        else:
            selected_subsystem = None


        question_type = st.radio("Sélectionnez la source des questions",[":green[Questions vérifiées]", ":blue[Questions de la communauté]"],captions=["Questions créées par le développeur, vérifiées et sûres","Questions faites par les membres de la communauté, potentiellemment troll ou inexactes"],)
        if question_type == ":green[Questions vérifiées]":
            questions = load_questions(selected_domain, selected_subdomain, selected_subsystem, "official")
        else:
            questions = load_questions(selected_domain, selected_subdomain, selected_subsystem, "community")

        if not questions:
            st.warning("Aucune question disponible pour cette sélection.")
        else:
            # Affichage et gestion des questions
            score = 0
            total_questions = len(questions)
            user_answers = []

            for i, question in enumerate(questions):
                st.subheader(f"Question {i+1}")
                st.write(question["question"])

                if question["type"] == "QCM":
                    user_answer = st.radio(f"Choisissez la bonne réponse pour la question {i+1}:", question["options"])
                elif question["type"] == "Vrai/Faux":
                    user_answer = st.radio(f"Choisissez la bonne réponse pour la question {i+1}:", ["Vrai", "Faux"])
                else:  # Réponse courte
                    user_answer = st.text_input(f"Votre réponse pour la question {i+1}:")

                user_answers.append(user_answer)

                st.write("---")  # Séparateur entre les questions

            if st.button("Terminer le quiz"):
                for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
                    if user_answer.lower() == question["correct_answer"].lower():
                        score += 1
                        st.success(f"Question {i+1}: Correct!")
                    else:
                        st.error(f"Question {i+1}: Incorrect. La bonne réponse était: {question['correct_answer']}")
                    st.write(f"Explication: {question['explanation']}")
                    st.write("---")

                st.success(f"Quiz terminé! Votre score: {score}/{total_questions}")
                update_user_stats(st.session_state.username, points=score, quizzes_completed=1)

    elif choice == "**:blue[Créer une question]**":
        st.subheader("Créer une nouvelle question")
        domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]
        domain = st.selectbox("Domaine", domains)
        
        subdomains = {
            "Anatomie": ["Système osseux", "Système circulatoire", "Système nerveux", "Système urinaire", "Système respiratoire"],
            "Physiologie": ["Système cardiovasculaire", "Système respiratoire", "Système digestif"],
            "Chimie/Biochimie": ["Chimie organique", "Biochimie structurale", "Métabolisme"],
            "Mathématiques et arithmétique": ["Algèbre", "Géométrie", "Statistiques"],
            "Hygiène": ["Hygiène personnelle", "Hygiène alimentaire", "Hygiène environnementale"],
            "Pharmacologie": ["Pharmacocinétique", "Pharmacodynamique", "Classes de médicaments"],
            "Psychologie": ["Psychologie cognitive", "Psychologie sociale", "Psychopathologie"]
        }
        
        subdomain = st.selectbox("Sous-domaine", subdomains[domain])
        
        if domain == "Anatomie":
            subsystems = {
                "Système osseux": ["Crâne", "Colonne vertébrale", "Membres supérieurs", "Membres inférieurs"],
                "Système circulatoire": ["Cœur", "Artères", "Veines"],
                "Système nerveux": ["Cerveau", "Moelle épinière", "Nerfs périphériques"],
                "Système urinaire": ["Reins", "Vessie", "Urètres"],
                "Système respiratoire": ["Poumons", "Trachée", "Bronches"]
            }
            subsystem = st.selectbox("Sous-système", subsystems[subdomain])
        else:
            subsystem = None
        
        question_type = st.selectbox("Type de question", ["QCM", "Vrai/Faux", "Réponse courte"])
        question_text = st.text_area("Question")
        
        if question_type == "QCM":
            options = []
            for i in range(4):
                option = st.text_input(f"Option {i+1}")
                options.append(option)
            correct_answer = st.selectbox("Réponse correcte", options)
        elif question_type == "Vrai/Faux":
            options = ["Vrai", "Faux"]
            correct_answer = st.selectbox("Réponse correcte", options)
        else:
            correct_answer = st.text_input("Réponse correcte")
        
        explanation = st.text_area("Explication")
        
        if st.button("Soumettre la question"):
            new_question = {
                "domain": domain,
                "subdomain": subdomain,
                "subsystem": subsystem,
                "type": question_type,
                "question": question_text,
                "options": options if question_type == "QCM" else None,
                "correct_answer": correct_answer,
                "explanation": explanation
            }
            
            add_question_to_json(new_question, "community")
            st.success("Question ajoutée avec succès !")
            
    elif choice == "Contact":
            st.subheader("Contactez-nous")
            
  
    elif choice == "**:blue[Mon compte]**":
     if st.session_state.username:
            display_account_details(st.session_state.username)
     else:
            st.warning("Vous devez être connecté pour accéder à cette page.")
    

    if choice == "**:red[Déconnexion]**":
        st.session_state.username = None
        st.success("Vous avez été déconnecté.")
        st.rerun()


if __name__ == "__main__":
    main()
    
   