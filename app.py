import streamlit as st
import sqlite3
import json
import hashlib
import time
import pandas as pd  # Assurez-vous que pandas est importé
import datetime
from community_questions import load_community_questions, add_community_question


COOLDOWN_TIME = 15







def show_login_page():
    st.header("Connexion")

    # Formulaire de connexion
    username = st.text_input("Nom d'utilisateur (connexion)")
    password = st.text_input("Mot de passe (connexion)", type="password")
    login_button = st.button(":green[Se connecter]")

    st.header("Inscription")
    # Formulaire d'inscription
    register_username = st.text_input("Nom d'utilisateur (inscription)")
    register_password = st.text_input("Mot de passe (inscription)", type="password")
    register_button = st.button(":blue[S'inscrire]")

    if login_button:
        if authenticate_user(username, password):
            st.success("Connexion réussie !")
            st.session_state.logged_in = True  # Mettre à jour l'état
            st.session_state.username = username  # Stocker l'utilisateur connecté
            st.rerun()  # Recharger la page pour afficher la page principale
        else:
            st.error("Identifiants incorrects.")

    if register_button:
        if register_user(register_username, register_password):
            st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")
        else:
            st.error("Erreur lors de l'inscription.")



def load_community_questions():
    with open('community_questions.json', 'r') as f:
        return json.load(f)


def update_last_submission_time(username):
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = int(time.time())
    c.execute('INSERT INTO user_submissions (username, timestamp) VALUES (?, ?)', (username, timestamp))
    conn.commit()
    conn.close()

def get_last_submission_time(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT MAX(timestamp) FROM user_submissions WHERE username=?', (username,))
    last_submission_time = c.fetchone()[0]
    conn.close()
    return last_submission_time

COOLDOWN_TIME = 5

def update_cooldown():
    if "last_submission_time" not in st.session_state:
        st.session_state.last_submission_time = time.time()
    
    current_time = time.time()
    time_since_last_submission = current_time - st.session_state.last_submission_time
    
    st.session_state.can_submit = time_since_last_submission >= COOLDOWN_TIME
    
    time_remaining = COOLDOWN_TIME - time_since_last_submission
    st.session_state.time_remaining = max(0, int(time_remaining))

def display_cooldown():
    update_cooldown()
    
    if not st.session_state.can_submit:
        # Espace vide pour le compte à rebours dynamique
        countdown_placeholder = st.empty()
        
        while not st.session_state.can_submit:
            # Met à jour le compte à rebours
            update_cooldown()
            
            if st.session_state.can_submit:
                countdown_placeholder.write("*Vous pouvez soumettre un nouveau quizz !*")
            else:
                countdown_placeholder.write(f"### Cooldown en cours\nVous pouvez soumettre à nouveau dans {st.session_state.time_remaining} secondes.")
            
            # Met à jour toutes les 1 seconde
            time.sleep(1)
    else:
        st.write("Vous pouvez soumettre un nouveau quizz !")  
# Définir le cooldown en secondes



def submit_quiz():
    """Gère la soumission du quiz et met à jour le temps de la dernière soumission."""
    st.session_state.last_submission_time = time.time()
    st.session_state.can_submit = False
    st.session_state.time_remaining = COOLDOWN_TIME
    st.success("Quiz soumis avec succès!")

# Charger les données des questions depuis le fichier JSON
with open('questions_data.json', 'r') as f:
    questions_data = json.load(f)

    # Fonction pour obtenir les détails du profil public
def get_public_profile(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT SUM(score) FROM scores WHERE username=?', (username,))
    total_points = c.fetchone()[0] or 0
    c.execute('SELECT COUNT(DISTINCT question_id) FROM user_answers WHERE username=?', (username,))
    quizzes_completed = c.fetchone()[0] or 0
    conn.close()
    return total_points, quizzes_completed


# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('quiz_app.db')
    return conn

# Fonction pour vérifier les identifiants
def authenticate_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashlib.sha256(password.encode()).hexdigest()))
    user = c.fetchone()
    conn.close()
    return user is not None

# Fonction pour enregistrer un nouvel utilisateur
def register_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashlib.sha256(password.encode()).hexdigest()))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def save_score(username, score):
     if username != "invité":  # Ne pas enregistrer le score pour les invités
         conn = get_db_connection()
         c = conn.cursor()
         c.execute('INSERT INTO scores (username, score) VALUES (?, ?)', (username, score))
         conn.commit()
         conn.close()


# Fonction pour obtenir le leaderboard
def get_leaderboard():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT username, SUM(score) as total_score
        FROM scores
        GROUP BY username
        ORDER BY total_score DESC
    ''')
    leaderboard = c.fetchall()
    conn.close()
    return leaderboard


# Fonction pour obtenir les détails du compte
def get_account_details(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT SUM(score) FROM scores WHERE username=?', (username,))
    total_points = c.fetchone()[0] or 0
    c.execute('SELECT COUNT(DISTINCT question_id) FROM user_answers WHERE username=?', (username,))
    quizzes_completed = c.fetchone()[0] or 0
    c.execute('SELECT MAX(timestamp) FROM user_sessions WHERE username=?', (username,))
    last_session_time = c.fetchone()[0]
    conn.close()
    
    # Calcul du temps total passé
    if last_session_time:
        time_spent = (time.time() - last_session_time) / 3600  # en heures
    else:
        time_spent = 0
    
    return total_points, quizzes_completed, time_spent



# Fonction pour afficher les questions et vérifier les réponses
def display_questions(questions, username):
    user_answers = {}
    correct_answers = {}
    
    # Collecte des réponses utilisateur
    for idx, q in enumerate(questions):
        q_type = q.get("type")
        question = q.get("question")
        if q_type == "mcq":
            options = q.get("options")
            user_answers[idx] = st.radio(question, options, key=idx)
            correct_answers[idx] = q.get("answer")
        elif q_type == "true_false":
            user_answers[idx] = st.radio(question, ["Vrai", "Faux"], key=idx)
            correct_answers[idx] = q.get("answer")
        elif q_type == "fill_in":
            user_answers[idx] = st.text_input(question, key=idx)
            correct_answers[idx] = q.get("answer")
    

    # Vérifier les réponses et afficher les résultats
    ##if st.button("Vérifier les réponses"):
        score = 0
        total_questions = len(questions)
        correct_count = 0
        incorrect_count = 0
        
        st.write("### Résultats")
        for idx, q in enumerate(questions):
            q_type = q.get("type")
            question = q.get("question")
            correct_answer = correct_answers.get(idx)
            user_answer = user_answers.get(idx)
            
            if q_type == "mcq":
                is_correct = user_answer == correct_answer
            elif q_type == "true_false":
                is_correct = user_answer == correct_answer
            elif q_type == "fill_in":
                if not user_answer.strip():
                    user_answer = "Aucune"
                is_correct = user_answer.strip().lower() == correct_answer.lower()
            
            if is_correct:
                score += 1
                correct_count += 1
                st.markdown(f"**Question {idx + 1}:** {question} - <span style='color:green;'>Votre réponse est correcte.</span>", unsafe_allow_html=True)
            else:
                incorrect_count += 1
                st.markdown(f"**Question {idx + 1}:** {question} - <span style='color:red;'>Votre réponse : `{user_answer}` - Réponse correcte : `{correct_answer}`</span>", unsafe_allow_html=True)
        
        # Enregistrement du score
        save_score(username, score)
        
        # Affichage du score avec une barre de progression
        st.write("### Votre Score")
        score_percentage = (score / total_questions) * 100
        st.write(f"**Score:** {score}/{total_questions}")
        st.write(f"**Pourcentage de bonnes réponses:** {score_percentage:.2f}%")
        st.progress(score_percentage / 100)

        # Affichage du nombre de réponses correctes et incorrectes
        st.write(f"**Réponses correctes:** {correct_count}")
        st.write(f"**Réponses incorrectes:** {incorrect_count}")

def display_public_profile(username):
    total_points, quizzes_completed, _ = get_account_details(username)
    leaderboard = get_leaderboard()
    rank = next((i + 1 for i, (user, _) in enumerate(leaderboard) if user == username), "N/A")
    
    st.header(f"Profil public de {username}")
    st.write(f"**Points totaux :** {total_points}")
    st.write(f"**Nombre de quiz complétés :** {quizzes_completed}")
    st.write(f"**Position dans le leaderboard :** {rank}")


def main():
    st.title("Apprentissage collaboratif")
    
    
    # Initialisation de st.session_state.username
    if "username" not in st.session_state:
        st.session_state.username = None

    # Récupérer les cookies
    cookie_username = None
    if st.session_state.username:
        cookie_username = st.session_state.username
    else:
        cookies = st.experimental_get_query_params()
        cookie_username = cookies.get("username", [None])[0]
    
    if cookie_username:
        if authenticate_user(cookie_username, "dummy_password"):
            st.session_state.username = cookie_username
            st.experimental_rerun()
        else:
            cookie_username = None
            
    
    if 'logged_in' not in st.session_state:
     st.session_state.logged_in = False
     st.write(f":red-background[Veuillez remplir le formulaire ci-dessous pour vous **connecter** ou alors vous **inscrire** !]")
    if st.session_state.logged_in:
     username = get_account_details(st.session_state.username)
     st.success(f"Bienvenue, vous êtes connecté en tant que **{st.session_state.username}**")
    # Afficher la page principale (Quiz, etc.)
      # Assurez-vous d'avoir une fonction pour la page principale
    else:
     
     show_login_page()  # Affichez le formulaire de connexion ou d'inscription

    # Afficher le leaderboard avant connexion
    if not st.session_state.username:
        st.write("### Leaderboard")
        leaderboard = get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
        leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
        leaderboard_df = leaderboard_df.head(10)
        st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
        
        # Barre latérale avec options de connexion et d'inscription
        
        

    # Partie principale (contenu du quiz et des questions) au centre de la page
    if st.session_state.username:
        with st.sidebar:
            menu_option = st.selectbox(
                "Menu",
                ["Quiz", "Voir mon compte", "Contribuer aux questions", "Déconnexion"]
            )
        
        if menu_option == "Déconnexion":
            st.session_state.username = None
            st.success("Vous êtes déconnecté. ***:red[Veuillez recharger cette page une fois la déconnexion faite ! (avec f5 ou en swipant en haut)]***")
            st.write("Redirection en cours...")
        
        elif menu_option == "Quiz":
            st.write("### Sélectionnez un système")
            system_choice = st.selectbox("Choisissez un système", ["Système osseux", "Système circulatoire", "Système respiratoire", "Système nerveux"])
            
            if system_choice:
                st.write("### Sélectionnez un sous-système")
                sub_system_choice = st.selectbox("Choisissez un sous-système", list(questions_data[system_choice].keys()))
            
            if sub_system_choice:
             question_source = st.radio("Sélectionnez la source des questions",[":green[Questions vérifiées]", ":blue[Questions de la communauté]"],captions=["Questions créées par le développeur, vérifiées et sûres","Questions faites par les membres de la communauté, potentiellemment troll ou inexactes"],)

            if question_source == ":green[Questions vérifiées]":
                    questions = questions_data[system_choice][sub_system_choice]
            else:
                    community_questions = load_community_questions()
                    questions = community_questions.get(system_choice, {}).get(sub_system_choice, [])

                # Vérification s'il y a des questions disponibles
            if questions:
                    st.write(f"##### Questions chargées depuis la base de données  : :blue[{sub_system_choice}] - :blue[{system_choice}] :")
                    
                    # Boucle sur les questions de la communauté pour les afficher

                    display_cooldown()
                    
                    if st.session_state.can_submit:
                        display_questions(questions, st.session_state.username)
                        if st.button("Soumettre le quiz"):
                            submit_quiz()
                            
                    else:
                        st.write("Vous devez attendre avant de pouvoir soumettre à nouveau.")
            else:
                    st.info("Aucune question disponible pour cette sélection.")






        elif menu_option == "Contribuer aux questions":
            st.header("Contribuer aux questions")
            contribute_questions()

        elif menu_option == "Voir mon compte":
            total_points, quizzes_completed, time_spent = get_account_details(st.session_state.username)
            st.header("Détails de mon compte")
            st.write(f"**Nom d'utilisateur :** {st.session_state.username}")
            st.write(f"**Points totaux :** {total_points}")
            st.write(f"**Nombre de quiz complétés :** {quizzes_completed}")
            st.write(f"**Temps total passé sur le site :** {time_spent:.2f} heures")

            st.write("### Voir un profil public")
            public_username = st.text_input("Entrez le nom d'utilisateur pour voir le profil public")
            
            if st.button("Afficher le profil"):
                if public_username:
                    public_total_points, public_quizzes_completed = get_public_profile(public_username)
                    st.write(f"**Nom d'utilisateur :** {public_username}")
                    st.write(f"**Points totaux :** {public_total_points}")
                    st.write(f"**Nombre de quiz complétés :** {public_quizzes_completed}")

            with st.expander("Voir la leaderboard complète"):
                leaderboard = get_leaderboard()
                leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
                leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
                st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))

st.write("Développé avec ❤️ par [maxx.abrt](https://www.instagram.com/maxx.abrt/) en python 🐍")

def contribute_questions():
    question_type = st.selectbox("Type de question", ["mcq", "vrai_ou_faux", "fill_in"])
    system = st.selectbox("Système", list(questions_data.keys()))
    subsystem = st.selectbox("Sous-système", list(questions_data[system].keys()))
    
    question = st.text_input("Question")
    
    if question_type == "mcq":
        options = []
        for i in range(4):
            option = st.text_input(f"Option {i+1}")
            options.append(option)
        correct_answers = st.multiselect("Réponse(s) correcte(s)", options)
        
        question_data = {
            "question": question,
            "options": options,
            "answer": correct_answers
        }
    
    elif question_type == "vrai_ou_faux":
        answer = st.radio("Réponse correcte", ["Vrai", "Faux"])
        
        question_data = {
            "question": question,
            "answer": answer
        }
    
    else:  # Quiz
        answer = st.text_input("fill_in")
        
        question_data = {
            "question": question,
            "answer": answer
        }
    
    if st.button("Valider ma question"):
        add_community_question(system, subsystem, question_type.lower().replace(" ", "_"), question_data)
        st.success("Votre question a été ajoutée avec succès!")

def save_user_answers(username, question_id, answer, is_correct):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO user_answers (username, question_id, answer, is_correct) VALUES (?, ?, ?, ?)', 
          (username, question_id, answer, is_correct))
    conn.commit()
    conn.close()




def display_questions(questions, username):
    user_answers = {}
    correct_answers = {}
    

    for idx, q in enumerate(questions):
        q_type = q.get("type")
        question = q.get("question")
        if q_type == "mcq":
            options = q.get("options")
            user_answers[idx] = st.radio(question, options, key=idx)
            correct_answers[idx] = q.get("answer")
        elif q_type == "vrai_ou_faux" or q_type == "true_false":
            user_answers[idx] = st.radio(question, ["Vrai", "Faux"], key=idx)
            correct_answers[idx] = q.get("answer")
        elif q_type == "fill_in":
            user_answers[idx] = st.text_input(question, key=idx)
            correct_answers[idx] = q.get("answer")
    
    # Vérification des réponses et affichage des résultats

    # Vérification des réponses et affichage des résultats
    if st.button("Voir la correction"):
        score = 0
        total_questions = len(questions)
        st.write("### Résultats")
        
        for idx, q in enumerate(questions):
            question = q.get("question")
            correct_answer = correct_answers.get(idx)
            user_answer = user_answers.get(idx)
            
            # Validation de la réponse en fonction du type de question
            if q.get("type") == "mcq":
                is_correct = user_answer == correct_answer
            elif q.get("type") == "vrai_ou_faux" or q.get("type") == "true_false":
                is_correct = user_answer == correct_answer
            elif q.get("type") == "fill_in":
                is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            
            # Affichage des résultats
            if is_correct:
                score += 1
                st.markdown(f"**Question {idx + 1}:** {question} - <span style='color:green;'>Correct</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**Question {idx + 1}:** {question} - <span style='color:red;'>Incorrect, Réponse correcte : `{correct_answer}`</span>", unsafe_allow_html=True)

            
                    # Enregistrement du score
        save_score(username, score)
        
        st.write("### Votre Score")
        score_percentage = (score / total_questions) * 100
        st.write(f"**Score:** {score}/{total_questions}")
        st.write(f"**Pourcentage de bonnes réponses:** {score_percentage:.2f}%")
        st.progress(score_percentage / 100)


        st.write("### Leaderboard")
        leaderboard = get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
        leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
        leaderboard_df = leaderboard_df.head(10)
        st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
            

if __name__ == "__main__":
    main()
