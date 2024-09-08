import streamlit as st
import sqlite3
import json
import hashlib
import time
import pandas as pd  # Assurez-vous que pandas est importé

import datetime





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
    if st.button("Vérifier les réponses"):
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
    st.title("Quiz Anatomie")
    st.subheader("Cliquez sur la flèche ➤ en haut à gauche pour ouvrir la barre de contrôle et vous créer un compte, vous connecter ou découvrir en tant qu'invité !")
    
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

    # Afficher la leaderboard avant connexion
    if not st.session_state.username:
        st.write("### Leaderboard")
        leaderboard = get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
        leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
        leaderboard_df = leaderboard_df.head(10)
        st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
        
        # Barre latérale avec options de connexion et d'inscription
        with st.sidebar:
            st.header("Connexion / Inscription")
            choice = st.radio("Choisissez une action", ["Connexion", "Inscription"])
            
            if choice == "Inscription":
                st.subheader("Inscription")
                username = st.text_input("Nom d'utilisateur")
                password = st.text_input("Mot de passe", type="password")
                remember_me = st.checkbox("Se rappeler de moi")
                
                if st.button("S'inscrire"):
                    if register_user(username, password):
                        st.success("Inscription réussie! Vous serez redirigé vers la page de quiz.")
                        st.session_state.username = username
                        st.experimental_rerun()
                    else:
                        st.error("Nom d'utilisateur déjà pris.")
            
            elif choice == "Connexion":
                st.subheader("Connexion")
                username = st.text_input("Nom d'utilisateur", key="login")
                password = st.text_input("Mot de passe", type="password", key="password")
                remember_me = st.checkbox("Se rappeler de moi")
                
                if st.button("Se connecter"):
                    if authenticate_user(username, password):
                        st.success("Connexion réussie! Vous serez redirigé vers la page de quiz.")
                        st.session_state.username = username
                        st.write("Redirection en cours...")
                    else:
                        st.error("Identifiants incorrects.")
        
            if not st.session_state.username:
                # Connexion en tant qu'invité
                if st.button("Se connecter en tant qu'invité"):
                    st.session_state.username = "invité"
                    st.success("Vous êtes connecté en tant qu'invité.")
                    st.write("Redirection en cours...")
    
    # Partie principale (contenu du quiz et des questions) au centre de la page
    if st.session_state.username:
        with st.sidebar:
            menu_option = st.selectbox(
                "Menu",
                ["Quiz", "Voir mon compte", "Déconnexion"]
            )
        
        if menu_option == "Déconnexion":
            st.session_state.username = None
            st.success("Vous êtes déconnecté. Vous serez redirigé vers la page de connexion.")
            st.write("Redirection en cours...")
        
        if menu_option == "Quiz":
            st.write("### Leaderboard")
            leaderboard = get_leaderboard()
            leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
            leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
            leaderboard_df = leaderboard_df.head(10)
            st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
            
            st.write("### Sélectionnez un système")
            system_choice = st.selectbox("Choisissez un système", ["Système osseux", "Système circulatoire", "Système respiratoire", "Système nerveux"])
            
            if system_choice:
                st.write("### Sélectionnez un sous-système")
                sub_system_choice = st.selectbox("Choisissez un sous-système", list(questions_data[system_choice].keys()))
                
                if sub_system_choice:
                    st.header(f"Questions pour {sub_system_choice} du {system_choice}")
                    questions = questions_data[system_choice][sub_system_choice]
                    display_questions(questions, st.session_state.username)
        
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

if __name__ == "__main__":
    main()
