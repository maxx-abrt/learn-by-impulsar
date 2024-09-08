
import streamlit as st
import pandas as pd
from streamlit_javascript import st_javascript
from app import authenticate_user, register_user, save_score, get_leaderboard, get_account_details

import datetime

def set_cookie(key, value, expire_days=2):
    expires = datetime.datetime.utcnow() + datetime.timedelta(days=expire_days)
    st_javascript(f"document.cookie = '{key}={value}; expires={expires.strftime('%a, %d %b %Y %H:%M:%S GMT')}; path=/';")

def get_cookie(key):
    cookies = st_javascript("return document.cookie;")
    cookie_dict = dict(x.split('=') for x in cookies.split('; ') if '=' in x)
    return cookie_dict.get(key, None)


def show_login_signup():
    st.header("Connexion / Inscription")
    choice = st.radio("Choisissez une action", ["Connexion", "Inscription"])
    
    if st.button("Se connecter en tant qu'invité"):
      st.session_state.username = "invité"
      st.success("Vous êtes connecté en tant qu'invité.")
      st.experimental_rerun()

    if choice == "Inscription":
        st.subheader("Inscription")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        remember_me = st.checkbox("Se rappeler de moi")
        
        if st.button("S'inscrire"):
            if register_user(username, password):
                st.success("Inscription réussie! Vous serez redirigé vers la page de quiz.")
                st.session_state.username = username
                if remember_me:
                    st_javascript(f"document.cookie = 'username={username}; path=/';")
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
                if remember_me:
                    st_javascript(f"document.cookie = 'username={username}; path=/';")
                st.experimental_rerun()
            else:
                st.error("Identifiants incorrects.")

def show_quiz(questions_data, username, get_leaderboard, save_score):
    # Affichage du leaderboard
    st.write("### Leaderboard")
    leaderboard = get_leaderboard()
    leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
    leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
    leaderboard_df = leaderboard_df.head(10)
    st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
    
    # Menu de sélection du système
    system_choice = st.selectbox("Choisissez un système", ["Système osseux", "Système circulatoire", "Système respiratoire", "Système nerveux"])
    
    if system_choice:
        # Menu de sélection du sous-système
        sub_system_choice = st.selectbox("Choisissez un sous-système", list(questions_data[system_choice].keys()))
        
        if sub_system_choice:
            # Affichage des questions
            st.header(f"Questions pour {sub_system_choice} du {system_choice}")
            questions = questions_data[system_choice][sub_system_choice]
            display_questions(questions, username, save_score)

def display_questions(questions, username, save_score):
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

def show_account_details(username, get_account_details, get_leaderboard):
    # Affichage des détails du compte
    total_points, quizzes_completed, time_spent = get_account_details(username)
    st.header("Détails de mon compte")
    st.write(f"**Nom d'utilisateur :** {username}")
    st.write(f"**Points totaux :** {total_points}")
    st.write(f"**Nombre de quiz complétés :** {quizzes_completed}")
    st.write(f"**Temps total passé sur le site :** {time_spent:.2f} heures")

    # Affichage de la leaderboard complète
    with st.expander("Voir la leaderboard complète"):
        leaderboard = get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
        leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
        st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))

def show_account_details(username, get_account_details, get_leaderboard):
    # Affichage des détails du compte
    total_points, quizzes_completed, time_spent = get_account_details(username)
    st.header("Détails de mon compte")
    st.write(f"**Nom d'utilisateur :** {username}")
    st.write(f"**Points totaux :** {total_points}")
    st.write(f"**Nombre de quiz complétés :** {quizzes_completed}")
    st.write(f"**Temps total passé sur le site :** {time_spent:.2f} heures")

    # Affichage du profil public
    st.write("### Voir un profil public")
    public_username = st.text_input("Entrez le nom d'utilisateur pour voir le profil public")
    
    if st.button("Afficher le profil"):
        if public_username:
            public_total_points, public_quizzes_completed = get_public_profile(public_username)
            st.write(f"**Nom d'utilisateur :** {public_username}")
            st.write(f"**Points totaux :** {public_total_points}")
            st.write(f"**Nombre de quiz complétés :** {public_quizzes_completed}")

    # Affichage de la leaderboard complète
    with st.expander("Voir la leaderboard complète"):
        leaderboard = get_leaderboard()
        leaderboard_df = pd.DataFrame(leaderboard, columns=['Username', 'Total Points'])
        leaderboard_df = leaderboard_df.rename_axis('Rank').reset_index()
        st.write(leaderboard_df.style.apply(lambda x: ['background-color: gold' if i == 0 else 'background-color: silver' if i == 1 else 'background-color: #cd7f32' if i == 2 else '' for i in x.index], axis=1))
