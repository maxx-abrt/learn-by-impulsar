import streamlit as st
import sqlite3
import json
import hashlib
import time
import pandas as pd
from datetime import datetime, timedelta
from community_questions import load_community_questions, add_community_question
import requests
from dotenv import load_dotenv
import os
import threading
import cloudinary
import cloudinary.uploader
import uuid
from PIL import Image
from pymongo import MongoClient
import plotly.express as px
import random
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import streamlit.components.v1 as components

load_dotenv()


mongo_uri = os.getenv('MONGODB_URI')


img = Image.open('favicon.png')
igm = Image.open('2.png')

st.logo(igm)
st.set_page_config(
    page_title= "Learn par Impulsar", 
    page_icon =img, 
    layout = "centered", 
    initial_sidebar_state="collapsed" )

def get_db_connection():
    if 'db' not in st.session_state:
        try:
            client = MongoClient(mongo_uri)
            st.session_state.db = client['quiz_app']
            print('Base de données connectée')
        except Exception as e:
            st.error(f"Erreur de connexion : {str(e)}")
    return st.session_state.db

db = get_db_connection()
quiz_interactions_collection = db['quiz_interactions']
users_collection = db['users']
interactions_collection = db['user_interactions']
questions_collection = db['questions']
    
# Assurez-vous que 'db' est défini avant d'utiliser des collections
collection_name = 'users'
try:
    collection = db[collection_name]
except NameError:
    st.error("La base de données n'est pas définie correctement.")
# Create a new collection for storing user interactions

def update_likes_dislikes(question_id, action, username):
                    existing_interaction = interactions_collection.find_one({
                        'username': username,
                        'question_id': question_id
                    })
                    if existing_interaction:
                        st.warning("Vous avez déjà voté pour cette question.")
                    else:
                        if action == 'like':
                            questions_collection.update_one({'_id': question_id}, {'$inc': {'likes': 1}})
                        elif action == 'dislike':
                            questions_collection.update_one({'_id': question_id}, {'$inc': {'dislikes': 1}})
                        
                        interactions_collection.insert_one({
                            'username': username,
                            'question_id': question_id,
                            'action': action
                        })
        
        
        
        
        
        
def get_db_connection():
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = MongoClient(mongo_uri)
    return st.session_state.db_connection
        

##Stats et infos :

def display_user_cards():
    st.title("Découvrir")
    
    username_query = st.text_input("Rechercher un utilisateur par nom:")
    
    if st.button("Rechercher") and username_query:
        user_info = list(users_collection.find(
            {"username": {"$regex": username_query, "$options": "i"}},
            {"username": 1, "points": 1, "quizzes_completed": 1, "community_points": 1, "registration_date": 1, "badges": 1}
        ))
        
        if not user_info:
            st.warning("Utilisateur non trouvé.")
            return
        
    else:
        all_users = list(users_collection.find({}, {"username": 1, "points": 1, "quizzes_completed": 1, "community_points": 1, "registration_date": 1, "badges": 1}))
        user_info = random.sample(all_users, min(20, len(all_users)))
    
    for user in user_info:
        with st.container(border=True):
            st.markdown(f"**Nom d'utilisateur**: **:blue[{user['username']}]**")
            st.markdown(f"**Points aux Quiz**: **:blue[{user['points']}]**")
            st.markdown(f"**Quiz Complétés**: **:blue[{user['quizzes_completed']}]**")
            st.markdown(f"**Points Communautaires**: **:blue[{user['community_points']}]**")
            
            registration_date = user.get('registration_date')
            if registration_date:
                registration_date = registration_date.strftime('%d %b %Y')
                st.markdown(f"**Date d'inscription**: **:blue[{registration_date}]**")

            # Display badges
            badges_display = "".join([badge_info["emoji"] for badge_info in user["badges"].values() if badge_info["level"] > 0])
            if badges_display:
                st.markdown(f"**Badges**: {badges_display}")
            
            
            
            
def report_question(question_id, username, reason):
    user_data = users_collection.find_one({"username": username}, {"user_id": 1})
    if user_data:
        report_data = {
            'username': username,
            'user_id': user_data['user_id'],
            'reason': reason,
            'timestamp': datetime.now()
        }
        result = questions_collection.update_one(
            {'_id': question_id},
            {'$push': {'reports': report_data}}
        )
        return result.modified_count > 0
    return False



                
def display_report_interface(question_id):
    with st.expander("Signaler la question"):
        reason = st.text_input("Raison du signalement (50 caractères max)", max_chars=50)
        if st.button("Envoyer le signalement"):
            username = st.session_state.get('username')
            if not username:
                st.warning("Veuillez vous connecter pour signaler une question.")
                return

            # Retrieve user data
            user_data = users_collection.find_one({"username": username}, {"user_id": 1})
            if not user_data:
                st.error("Erreur lors de la récupération des informations utilisateur.")
                return

            # Check if the user has already reported this question
            question = questions_collection.find_one({"_id": question_id, "reports.user_id": user_data['user_id']})
            if question:
                st.warning("Vous avez déjà signalé cette question.")
                return

            # Proceed to report the question
            if reason:
                report_data = {
                    'username': username,
                    'user_id': user_data['user_id'],
                    'reason': reason,
                    'timestamp': datetime.now()
                }
                result = questions_collection.update_one(
                    {'_id': question_id},
                    {'$push': {'reports': report_data}}
                )
                if result.modified_count > 0:
                    st.success("Signalement envoyé.")
                else:
                    st.error("Erreur lors de l'envoi du signalement.")
            else:
                st.warning("Veuillez fournir une raison pour le signalement.")


def display_advice():
    st.header("Tableau de Bord - Conseils")
    
    user_id = st.session_state.get('username')
    if not user_id:
        st.warning("Veuillez vous connecter pour voir vos conseils.")
        return
    
    user_data = users_collection.find_one({"username": user_id})
    
    if not user_data:
        st.warning("Aucune donnée utilisateur trouvée.")
        return

    # Analyse des données utilisateur pour des conseils personnalisés
    quizzes_completed = user_data.get('quizzes_completed', 0)
    points = user_data.get('points', 0)
    
    # Récupération des interactions de quiz pour analyse détaillée
    quiz_data = pd.DataFrame(list(quiz_interactions_collection.find({"user_id": user_id})))
    
    if not quiz_data.empty:
        # Détection des points faibles
        domain_counts = quiz_data['domains'].apply(lambda x: list(x.keys())).explode().value_counts()
        weak_domains = domain_counts.nsmallest(3).index.tolist()
        
        st.subheader("Conseils personnalisés suivant vos données")
        
        if quizzes_completed < 5:
            st.info("Essayez d'augmenter le nombre de quiz par jour pour améliorer vos résultats ! (nous vous conseillons 5 quiz par jour !)")
        else:
            st.success("Félicitations ! Vous suivez un bon rythme de révision.")
 
        # Calculate average quizzes per week
        days_since_registration = (datetime.now() - user_data['registration_date']).days
        weeks_since_registration = max(days_since_registration / 7, 1)  # Ensure at least one week

        average_quiz_per_week = quizzes_completed / weeks_since_registration

        # Suggestions based on statistics
        st.markdown("### Suggestions Basées sur Vos Statistiques")

        if quizzes_completed < 8:
            st.write("- **Augmentez la fréquence** : Essayez de compléter au moins un quiz par jour.")

        if points < 50:
            st.write("- **Améliorez votre score** : Concentrez-vous sur les domaines où vous avez le moins de points.")

        if domain_counts.max() > 5:
            most_practiced_domain = domain_counts.idxmax()
            st.write(f"- **Diversifiez vos études** : Vous avez beaucoup travaillé sur **:blue[{most_practiced_domain}]**. Essayez d'explorer d'autres domaines pour un apprentissage équilibré.")

        # New suggestions
        if average_quiz_per_week < 10:
            st.write(f"- **Soyez plus régulier** : Essayez de maintenir une moyenne d'au moins 10 quiz par semaine pour garder vos connaissances fraîches. Vous êtes actuellement à : **:blue[{average_quiz_per_week}]** quiz par semaine.")

        community_points = user_data.get('community_points', 0)
        if community_points < 5:
            st.write(f"- **Participez à la communauté** : Contribuez aux questions communautaires pour améliorer vos points et bénéficier des retours des autres utilisateurs. Vous êtes actuellement à : **:blue[{community_points}]** points.")

        quiz_times = pd.to_datetime(quiz_data['timestamp']).dt.hour.value_counts()
        peak_hours = quiz_times.idxmax()
        st.write(f"- **Optimisez votre temps d'étude** : Vous semblez être plus actif autour de **:blue[{peak_hours} h]**. Essayez de planifier vos sessions d'étude à ces heures pour une efficacité maximale.")
   
   
   
   
    # Stratégies de Révision Recommandées
    st.subheader("Stratégies de Révision Recommandées")
    
    strategies = [
        ("Révision Espacée", "Étalez vos sessions d'étude sur plusieurs jours pour améliorer la rétention."),
        ("Test Pratique", "Utilisez des quiz pour tester vos connaissances et identifier les lacunes."),
        ("Interleaving", "Alternez entre différents sujets pour renforcer l'apprentissage."),
        ("Auto-explication", "Expliquez ce que vous avez appris avec vos propres mots."),
        ("Utilisation de Cartes Mémoire", "Créez des cartes mémoire pour mémoriser des concepts clés.")
    ]
    
    for title, description in strategies:
        with st.expander(f"**{title}**"):
            st.write(description)
            if title == "Révision Espacée":
                st.image("spaced_repetition.png", use_column_width=True, caption="Diagramme de révision espacée")







def display_moderation_page():
    # Check if user is logged in by retrieving the username from session state
    username = st.session_state.get('username')
    if not username:
        st.warning("Veuillez vous connecter pour accéder à cette page.")
        return

    # Check if user is a moderator by querying the 'users_collection' in MongoDB
    try:
        user_data = users_collection.find_one({"username": username}, {"is_moderator": 1})
    except Exception as e:
        st.error("Erreur de connexion à la base de données.")
        return

    # If the user is not a moderator or the field doesn't exist, display a warning
    if not (user_data and user_data.get('is_moderator', False)):
        st.warning("Vous n'avez pas les droits d'accès à cette page.")
        return

    # Display the moderation page if the user is a moderator
    st.header("Modération des Signalements")

    # Fetch all questions that have been reported (those with a 'reports' field)
    try:
        reported_questions = questions_collection.find({'reports.0': {'$exists': True}})
    except Exception as e:
        st.error("Erreur lors de la récupération des signalements.")
        return

    # Display each reported question with details
    for question in reported_questions:
        with st.container():
            with st.container(border=True):
                st.write(f"**Question:** **:blue[{question['question']}]**")
                st.write(f"**ID de la Question:** **:blue[{question['_id']}]**")
                st.write(f"**Créée par:** **:blue[{question.get('created_by', 'Inconnu')} (ID: {question.get('creator_id', 'Inconnu')})]**")

                # Display each report related to the question
                for report in question['reports']:
                    st.write(f"**Signalé par:** **:blue[{report['username']} (ID: {report['user_id']})]**")
                    st.write(f"**Motif du signalement:** **:blue[{report['reason']}]**")
                    st.write(f"**Date du signalement:** **:blue[{report['timestamp'].strftime('%d %b %Y %H:%M')}]**")

                # Button to delete the question
                if st.button(":red[Supprimer la question]", key=f"delete_{question['_id']}"):
                    questions_collection.delete_one({'_id': question['_id']})
                    st.success("Question supprimée.")



            
            
            

def collapse_sidebar():
            st.session_state.sidebar_state = 'collapsed'
            st.rerun()





def update_all_user_badges():
    users = users_collection.find()
    
    for user in users:
        assign_badges(user)
        users_collection.update_one({"username": user["username"]}, {"$set": {"badges": user["badges"]}})

badge_thresholds = {
    "completion_badge": {
        "name": "Points de quiz 🏆",
        "levels": [30, 500, 1000, 5000, 10000]
    },
    "community_badge": {
        "name": "Communauté 🤝",
        "levels": [10, 50, 100, 500, 1000]
    },
    "quiz_maker_badge": {
        "name": "Compléteur(euse) de quiz 📚",
        "levels": [5, 20, 50, 100, 200]
    },
    "age_badge": {
        "name": "Ancienneté ⏳",
        "levels": [30, 180, 365] # en jours
    }
}

def assign_badges(user):
    # Ensure 'badges' is a dictionary
    if 'badges' not in user or not isinstance(user['badges'], dict):
        user['badges'] = {
            "completion_badge": {"level": 0, "emoji": ""},
            "community_badge": {"level": 0, "emoji": ""},
            "quiz_maker_badge": {"level": 0, "emoji": ""},
            "age_badge": {"level": 0, "emoji": ""},
            "moderator_badge": {"level": 0, "emoji": ""},
            "medal_badge": {"level": 0, "emoji": ""}
        }
    
    # Define badge criteria
    completion_levels = [30, 500, 1000, 5000, 10000]
    community_levels = [10, 50, 100, 500, 1000]
    quiz_maker_levels = [5, 20, 50, 100, 200]
    age_levels = [30, 180, 365] # Days

    # Calculate user's age on the 
    days_on_platform = (datetime.now() - user['registration_date']).days

    # Assign completion badge
    for i, points in enumerate(completion_levels):
        if user['points'] >= points:
            user['badges']['completion_badge'] = {"level": i+1, "emoji": f"🏆{i+1}"}

    # Assign community badge
    for i, points in enumerate(community_levels):
        if user['community_points'] >= points:
            user['badges']['community_badge'] = {"level": i+1, "emoji": f"🤝{i+1}"}

    # Assign quiz maker badge
    for i, quizzes in enumerate(quiz_maker_levels):
        if user['quizzes_completed'] >= quizzes:
            user['badges']['quiz_maker_badge'] = {"level": i+1, "emoji": f"📚{i+1}"}

    # Assign age badge
    for i, days in enumerate(age_levels):
        if days_on_platform >= days:
            user['badges']['age_badge'] = {"level": i+1, "emoji": f"⏳{i+1}"}




def display_badge_progress(user_data):
    st.subheader("Progression des Badges")

    for badge_type, info in badge_thresholds.items():
        levels = info['levels']
        badge_name = info['name']
        current_level = user_data['badges'].get(badge_type, {}).get('level', 0)
        current_value = None

        if badge_type == "completion_badge":
            current_value = user_data.get('points', 0)
        elif badge_type == "community_badge":
            current_value = user_data.get('community_points', 0)
        elif badge_type == "quiz_maker_badge":
            current_value = user_data.get('quizzes_completed', 0)
        elif badge_type == "age_badge":
            current_value = (datetime.now() - user_data.get('registration_date')).days

        if current_level < len(levels):
            next_threshold = levels[current_level]
            progress = min(current_value / next_threshold, 1.0)
            st.markdown(f"**{badge_name}** - Niveau actuel: {current_level} - Progrès: {current_value}/{next_threshold}")
            st.progress(progress)
        else:
            st.markdown(f"**{badge_name}** - Niveau maximum atteint!")






def display_questions(questions):
    for i, question in enumerate(questions):
        st.subheader(f"Question {i+1}")
        st.write(question["question"])
        
        creator_info = f"Créée par: {question.get('created_by', 'Inconnu')} le {question.get('creation_date').strftime('%d %b') if question.get('creation_date') else 'Date inconnue'}"
        st.caption(creator_info)
        
        # Bouton pour voir le profil
        if st.button(f"Voir le profil de {question.get('created_by', 'Inconnu')}", key=f"profile_{i}"):
            creator_id = question.get('creator_id', 'Inconnu')
            st.info(f"ID Utilisateur: {creator_id}")
        
                # Afficher les likes et dislikes
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍", key=f"like_{i}"):
                update_likes_dislikes(question['_id'], 'like')
            st.write(f"Likes: {question.get('likes', 0)}")
        with col2:
            if st.button("👎", key=f"dislike_{i}"):
                update_likes_dislikes(question['_id'], 'dislike')
            st.write(f"Dislikes: {question.get('dislikes', 0)}")


        if question["type"] == "QCM":
            user_answer = st.radio(f"Choisissez la bonne réponse pour la question {i+1}:", question["options"])
        elif question["type"] == "Vrai/Faux":
            user_answer = st.radio(f"Choisissez la bonne réponse pour la question {i+1}:", ["Vrai", "Faux"])
        else:
            user_answer = st.text_input(f"Votre réponse pour la question {i+1}:")
# Création des collections
collections = ['users', 'chat_messages', 'questions', 'community_questions', 'scores', 'user_answers', 'user_sessions']
collection_name = 'users'
collection = db[collection_name]            
            
# Exemple d'utilisation de la collection 'users'
def create_user(username, password, domain, study_level):
    collection = db['users']
    if collection.find_one({"username": username}):
        return False
    else:
        hashed_password = hash_password(password)
        user_id = str(uuid.uuid4())
        collection.insert_one({
            "user_id": user_id,
            "username": username,
            "password": hashed_password,
            "domain": domain,
            "study_level": study_level,
            "points": 0,
            "community_points": 0,
            "quizzes_completed": 0,
            "registration_date": datetime.now(),
            "badges": {
                "completion_badge": {"level": 0, "emoji": ""},
                "community_badge": {"level": 0, "emoji": ""},
                "quiz_maker_badge": {"level": 0, "emoji": ""},
                "age_badge": {"level": 0, "emoji": ""},
                "moderator_badge": {"level": 0, "emoji": ""},
                "medal_badge": {"level": 0, "emoji": ""}
            },
            "is_moderator": False
        })
        return True
    
    
# MongoDB collections and their fields
collections = {
    'scores': {
        'id': int,
        'username': str,
        'score': int
    },
    'user_answers': {
        'id': int,
        'username': str,
        'question_id': int,
        'answer': str,
        'is_correct': int
    },
    'user_sessions': {
        'id': int,
        'username': str,
        'timestamp': int
    },
    'users': {
        'id': int,
        'username': str,
        'password': str,
        'domain': str,
        'study_level': str,
        'points': int,
        'community_points': int,
        'quizzes_completed': int,
        'registration_date': datetime,
        "badges": {
        "completion_badge": {"level": 0, "emoji": ""},
        "community_badge": {"level": 0, "emoji": ""},
        "quiz_maker_badge": {"level": 0, "emoji": ""},
        "age_badge": {"level": 0, "emoji": ""},
        "moderator_badge": {"level": 0, "emoji": ""},
        "medal_badge": {"level": 0, "emoji": ""}
        },
        "is_moderator": False
    },
    'chat_messages': {
        'id': int,
        'username': str,
        'message': str,
        'timestamp': datetime
    }
}

def create_sidebar():
    with st.sidebar:
        st.title("Menu")

                
        if 'page' not in st.session_state:
            st.session_state.page = "Accueil"
        # Créez des sections dans la sidebar
        st.sidebar.markdown("### Apprentissage")

                    
        if st.sidebar.button("🏠 Accueil", key="home", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Accueil"
            collapse_sidebar()
        if st.sidebar.button("📊 Tableau de bord", key="Tableau de bord", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Tableau de bord"
            collapse_sidebar()
        if st.sidebar.button("📚 Qcm", key="Qcm", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Qcm"
            collapse_sidebar()
        if st.sidebar.button("📝 Créer un Qcm", key="create_question", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Créer une question"
            collapse_sidebar()
        if st.sidebar.button("🖼️ Schémas", key="schemas", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Schémas"
            collapse_sidebar()
        if st.sidebar.button("➕ Ajouter un schéma", key="add_schema", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Ajouter un schéma"
            collapse_sidebar()

        st.sidebar.markdown("### Communauté")
        if st.sidebar.button("💬 Chat", key="chat", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Chat"
            collapse_sidebar()
        if st.sidebar.button("👥 Découvrir", key="discover", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "découvrir"
            collapse_sidebar()

        st.sidebar.markdown("### Compte")
        if st.sidebar.button("👤 Mon compte", key="account", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Mon compte"
            collapse_sidebar()
        if st.sidebar.button("❤️ Nous soutenir", key="support", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Nous soutenir"
            collapse_sidebar()
        if st.sidebar.button("🚪 Déconnexion", key="logout", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Déconnexion"
            collapse_sidebar()
        
        st.write("Développé avec ❤️ par [maxx.abrt](https://www.instagram.com/maxx.abrt/) en **:green[python]** 🐍 avec **:red[streamlit]** et **:grey[perplexity]**")
        st.write("---")
        if st.sidebar.button("🛠️ Modération", key="moderation"):
            st.session_state.page = "Modération"
            collapse_sidebar()
    st.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-image: linear-gradient(#2e7bcf,#2e7bcf);
            color: white;
        }
        .sidebar .sidebar-content .stButton>button {
            width: 100%;
            text-align: left;
            padding: 10px;
            background-color: transparent;
            color: white;
            border: none;
            border-radius: 5px;
        }
        .sidebar .sidebar-content .stButton>button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    return st.session_state.page

def load_schemas():
    collection = db['schemas']  
    schemas = list(collection.find())
    if schemas:
        print("Schemas loaded:", schemas)
    else:
        print("No schemas found.")
    return schemas

def display_help_button(page_name, location="top"):
    help_texts = {
        "Accueil": "Bienvenue sur la page d'accueil. Ici, vous pouvez voir le leaderboard et les informations générales sur la plateforme.",
        "Qcm": "Sur cette page, vous pouvez sélectionner un domaine, un sous-domaine et un sous-système (pour l'anatomie) pour commencer un Qcm.",
        "Créer une question": "Ici, vous pouvez créer une nouvelle question pour la communauté. Choisissez le domaine, le type de question et remplissez les champs nécessaires.",
        "Chat": "Le chat vous permet de discuter en temps réel avec d'autres utilisateurs de la plateforme.",
        "Mon compte": "Consultez et modifiez vos informations personnelles sur cette page.",
        "découvrir": "Découvrez d'autres utilisateurs et leurs contributions sur cette page.",
        "Nous soutenir": "Vous pouvez nous soutenir en visualisant une publicité sur cette page.",
        "Schémas": "Consultez et étudiez les schémas disponibles dans différents domaines.",
        "Ajouter un schéma": "Contribuez à la communauté en ajoutant un nouveau schéma sur cette page."
    }

    if st.button("💡 Aide", key=f"help_button_{page_name}_{location}"):
        st.info(help_texts.get(page_name, "Aide non disponible pour cette page."))

# Fonction pour rechercher des schémas
def search_schemas(schemas, query):
    query = query.lower()
    return [s for s in schemas if 
            query in s.get("title", "").lower() or 
            query in s.get("domain", "").lower() or 
            query in s.get("subdomain", "").lower() or 
            query in s.get("subsystem", "").lower() or 
            any(query in element.lower() for element in s.get("elements", []))]

cloudinary.config( 
        cloud_name = os.getenv('CLOUD_NAME'),
        api_key = os.getenv('API_KEY'),
        api_secret = os.getenv('API_SECRET'),
        secure=True
    )
    
def setup_cloudinary():
 cloudinary.config( 
        cloud_name = os.getenv('CLOUD_NAME'),
        api_key = os.getenv('API_KEY'),
        api_secret = os.getenv('API_SECRET'),
        secure=True
    )
    
def get_adsense_client_id():
    return os.getenv('ADSENSE_CLIENT_ID')

def upload_schema(file_content, file_name, domain, subdomain, subsystem=None):
    random_filename = str(uuid.uuid4())
    file_extension = os.path.splitext(file_name)[1]
    new_filename = f"{random_filename}{file_extension}"
    
    try:
        upload_result = cloudinary.uploader.upload(
            file_content,
            public_id=new_filename,
            folder="schemas"
        )
        
        schema_id = str(uuid.uuid4())
        
        schema_data = {
            "id": schema_id,
            "filename": new_filename,
            "url": upload_result["secure_url"],
            "domain": domain,
            "subdomain": subdomain,
            "subsystem": subsystem,
            "elements": []
        }
        
        return schema_data
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None
    
def add_community_question(question):
    collection = db['questions']
    user = db['users'].find_one({"username": st.session_state.username})
    question['created_by'] = user['username']
    question['creator_id'] = user['user_id']  # Ajout de l'UUID
    question['creation_date'] = datetime.now()
    collection.insert_one(question)
    
def load_community_questions():
    collection = db['community_questions']
    questions = list(collection.find())
    return questions
    
def save_schema_data(schema_data, elements):
    user = db['users'].find_one({"username": st.session_state.username})
    schema_data["elements"] = elements
    schema_data["created_by"] = user['username']
    schema_data["creator_id"] = user['user_id']  # Ajout de l'UUID
    schema_data["creation_date"] = datetime.now()
    db['schemas'].insert_one(schema_data)


def update_user_stats(username, points=0, quizzes_completed=0):
    collection = db['users']
    collection.update_one({"username": username}, {"$inc": {"points": points, "quizzes_completed": quizzes_completed}})
    
    
def display_add_schema_page():
    st.title("Ajouter un schéma")
    
    domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]
    domain = st.selectbox("Domaine", domains)
    
    subdomains = {
        "Anatomie": ["Système osseux", "Système circulatoire", "Système nerveux", "Système urinaire", "Système respiratoire"],
        "Physiologie": ["Physiologie fondamentale", "Physiologie appliquée", "Physiopathologie"],
        "Chimie/Biochimie": ["Chimie organique", "Biochimie structurale", "Métabolisme"],
        "Mathématiques et arithmétique": ["Algèbre", "Géométrie", "Statistiques"],
        "Hygiène": ["Hygiène personnelle", "Hygiène alimentaire", "Hygiène environnementale"],
        "Pharmacologie": ["Pharmacocinétique", "Pharmacodynamique", "Classes de médicaments"],
        "Psychologie": ["Psychologie cognitive", "Psychologie sociale", "Psychopathologie"]
    }
    subdomain = st.selectbox("Sous-domaine", subdomains[domain])
    
    subsystem = None
    if domain == "Anatomie":
        subsystems = {
            "Système osseux": ["Crâne", "Colonne vertébrale", "Membres supérieurs", "Membres inférieurs"],
            "Système circulatoire": ["Cœur", "Artères", "Veines"],
            "Système nerveux": ["Cerveau", "Moelle épinière", "Nerfs périphériques"],
            "Système urinaire": ["Reins", "Vessie", "Urètres"],
            "Système respiratoire": ["Poumons", "Trachée", "Bronches"]
        }
        subsystem = st.selectbox("Sous-système", subsystems[subdomain])
    
    uploaded_file = st.file_uploader("Choisir une image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        
        if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB
            st.error("Le fichier est trop volumineux. La taille maximale est de 10 MB.")
        else:
            st.image(uploaded_file)
    
    title = st.text_input("Titre du schéma")
    st.write("***:red[Pensez à créer au moins une réponse possible avec le bouton 'Ajouter une réponse' en dessous !]***")
    
    # Initialisation de la liste des éléments dans la session state si elle n'existe pas
    if 'schema_elements' not in st.session_state:
        st.session_state.schema_elements = []
    
    # Boutons pour ajouter et retirer des fields
    col1, col2 = st.columns(2)
    with col1:
        if st.button(":green[Ajouter une réponse]"):
            st.session_state.schema_elements.append("")
    with col2:
        if st.button(":red[Retirer une réponse]") and st.session_state.schema_elements:
            st.session_state.schema_elements.pop()
    
    # Affichage et gestion des fields
    for i, element in enumerate(st.session_state.schema_elements):
        st.session_state.schema_elements[i] = st.text_input(f"Élément {i+1} :", value=element, key=f"element_{i}")
    
    if st.button("Soumettre le schéma"):
        if uploaded_file and title and st.session_state.schema_elements:
            file_content = uploaded_file.read()
            schema_data = upload_schema(file_content, uploaded_file.name, domain, subdomain, subsystem)
            if schema_data:
                schema_data["title"] = title
                save_schema_data(schema_data, st.session_state.schema_elements)
                st.success("Schéma ajouté avec succès !")
                # Réinitialiser les éléments après la soumission
                st.session_state.schema_elements = []
            else:
                st.error("Erreur lors de l'upload du schéma.")
        else:
            st.error("Veuillez remplir tous les champs et uploader une image.")
               
def display_schemas_page():
    st.title("Schémas")
    
    # Champ de recherche
    search_query = st.text_input("Rechercher un schéma")
    
    domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]
    domain = st.selectbox("Domaine", domains)
    
    subdomains = {
        "Anatomie": ["Système osseux", "Système circulatoire", "Système nerveux", "Système urinaire", "Système respiratoire"],
        "Physiologie": ["Physiologie fondamentale", "Physiologie appliquée", "Physiopathologie"],
        "Chimie/Biochimie": ["Chimie organique", "Biochimie structurale", "Métabolisme"],
        "Mathématiques et arithmétique": ["Algèbre", "Géométrie", "Statistiques"],
        "Hygiène": ["Hygiène personnelle", "Hygiène alimentaire", "Hygiène environnementale"],
        "Pharmacologie": ["Pharmacocinétique", "Pharmacodynamique", "Classes de médicaments"],
        "Psychologie": ["Psychologie cognitive", "Psychologie sociale", "Psychopathologie"]
    }
    subdomain = st.selectbox("Sous-domaine", subdomains[domain])
    
    subsystem = None
    if domain == "Anatomie":
        subsystems = {
            "Système osseux": ["Crâne", "Colonne vertébrale", "Membres supérieurs", "Membres inférieurs"],
            "Système circulatoire": ["Cœur", "Artères", "Veines"],
            "Système nerveux": ["Cerveau", "Moelle épinière", "Nerfs périphériques"],
            "Système urinaire": ["Reins", "Vessie", "Urètres"],
            "Système respiratoire": ["Poumons", "Trachée", "Bronches"]
        }
        subsystem = st.selectbox("Sous-système", subsystems[subdomain])
    
    schemas = load_schemas()
    
    filtered_schemas = [s for s in schemas if s["domain"] == domain and s["subdomain"] == subdomain and (not subsystem or s["subsystem"] == subsystem)]
    
    if search_query:
        filtered_schemas = search_schemas(filtered_schemas, search_query)
    
    if not filtered_schemas:
        st.info("Aucun schéma disponible pour cette sélection.")
    else:
        # Pagination
        items_per_page = 5
        num_pages = (len(filtered_schemas) - 1) // items_per_page + 1
        page = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for schema in filtered_schemas[start_idx:end_idx]:
            with st.container():
                st.subheader(schema.get("title", "Sans titre"))
                if "url" in schema:
                    st.image(schema["url"])
                else:
                    st.error(f"URL manquante pour le schéma : {schema.get('id', 'ID inconnu')}")
                
                user_answers = []
                for i, element in enumerate(schema.get("elements", [])):
                    user_answer = st.text_input(f"Élément {i+1} :", key=f"{schema.get('id', '')}_{i}")
                    user_answers.append(user_answer)
                
                if st.button("Corriger", key=f"correct_{schema.get('id', '')}"):
                    for i, (user_answer, correct_answer) in enumerate(zip(user_answers, schema.get("elements", []))):
                        if user_answer.lower() == correct_answer.lower():
                            st.success(f"Élément {i+1}. Correct : {correct_answer}")
                        else:
                            st.error(f"Élément {i+1}. Incorrect. La bonne réponse est : {correct_answer}")
                
                st.markdown("---")
        
        st.write(f"Page {page} sur {num_pages}")

def display_support_page():
    st.title("Nous soutenir")
    #st.write("Vous pouvez nous soutenir en visualisant cette publicité :")
    st.subheader("Vous appréciez la plateforme et la gratuité proposée ? Vous pouvez me soutenir avec un petit don, avec le bouton ci-dessous.")
    # Intégration du script Buy Me a Coffee
    bmc_script = """
    <script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" 
            data-name="bmc-button" 
            data-slug="maxx.abrt" 
            data-color="#5F7FFF" 
            data-emoji="☕️" 
            data-font="Lato" 
            data-text="Cliquez ici pour faire un don" 
            data-outline-color="#000000" 
            data-font-color="#ffffff" 
            data-coffee-color="#FFDD00">
    </script>
    """

    # Utilisation de components.html pour afficher le bouton
    components.html(bmc_script, height=90)


    
# Constantes
COOLDOWN_TIME = 15



def get_messages():
    collection = db['chat_messages']
    # Fetch only the required fields
    messages = collection.find({}, {'username': 1, 'message': 1, 'timestamp': 1})
    return [(msg['username'], msg['message'], msg['timestamp']) for msg in messages]


def get_top_users(limit=10):
    # Assurez-vous que la requête inclut les badges
    pipeline = [
        {"$project": {
            "_id": "$username",
            "total_points": "$points",
            "badges": "$badges"
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": limit}
    ]
    return list(users_collection.aggregate(pipeline))

def display_leaderboard():
    top_users = get_top_users()

    st.markdown("## 🏆 Leaderboard")
    
    # Prepare data for display
    leaderboard_data = []
    for user in top_users:
        badges_display = "".join([badge_info["emoji"] for badge_info in user["badges"].values() if badge_info["level"] > 0])
        leaderboard_data.append({
            "Nom d'utilisateur": user['_id'],
            "Points": user['total_points'],
            "Badges": badges_display
        })
    
    # Convert to DataFrame for better display
    df_leaderboard = pd.DataFrame(leaderboard_data)

    # Display the leaderboard as a table
    st.table(df_leaderboard)




def update_messages():
    messages = get_messages()
    for i, message in enumerate(reversed(messages)):
        try:
            username, msg, timestamp = message
            domain = get_user_domain(username)
            time_str = timestamp.strftime("%H:%M")
            message_class = 'message new' if i == 0 else 'message'
            st.markdown(f"""
            <div class='{message_class}' id='message-{i}'>
                <span class='username'>{username}</span>
                <span class='domain'>({domain})</span>
                <span class='timestamp'>{time_str}</span>
                <br>{msg}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
        except ValueError as e:
            st.error(f"Error processing message: {e}")
            



def display_chat():
    st.subheader("Chat en direct")
    st.write("Discutez en temps réel avec d'autres utilisateurs de la plateforme.")

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


    messages = get_messages()

    message = st.text_input("Entrez votre message")
    if st.button("Envoyer"):
        collection = db['chat_messages']
        collection.insert_one({
            "username": st.session_state.username,
            "message": message,
            "timestamp": datetime.now()
        })
        st.success("Message envoyé avec succès!")



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
    
    
    update_messages()
    
    
    # Mise à jour périodique
    if 'update_counter' not in st.session_state:
        st.session_state.update_counter = 0
    
    st.session_state.update_counter += 1
    if st.session_state.update_counter % 10 == 0:  # Mise à jour toutes les 2.5 secondes (10 * 0.25s)
        update_messages()
        time.sleep(0.25)
        st.rerun()
    while True:
            time.sleep(4.5)
            update_messages()
            st.rerun()

def get_user_domain(username):
    user = db['users'].find_one({"username": username})
    return user['domain'] if user else "Non spécifié"
    

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
    collection = db['chat_messages']
    collection.insert_one({
        "username": username,
        "message": message,
        "timestamp": datetime.now()
    })

def change_username(old_username, new_username):
    collection = db['users']
    if collection.find_one({"username": new_username}):
        return False
    else:
        collection.update_one({"username": old_username}, {"$set": {"username": new_username}})
        return True

def display_account_details(username):
    collection = db['users']
    user = collection.find_one({"username": username})
    # Affichez les détails de l'utilisateur
    st.write(f"**Nom d'utilisateur: :blue[{user['username']}]**")
    st.write(f"**Domaine: :blue[{user['domain']}]**")
    st.write(f"**Niveau d'étude: :blue[{user['study_level']}]**")
    st.write(f"**Points: :blue[{user['points']}]**")
    st.write(f"**Points communautaires: :blue[{user['community_points']}]**")
    st.write(f"**QCM complétés: :blue[{user['quizzes_completed']}]**")
    st.write(f"**Date d'inscription: :blue[{user['registration_date']}]**")
        
def update_community_points(username):
    collection = db['users']
    collection.update_one({"username": username}, {"$inc": {"community_points": 1}})

def discover_page():
    st.title("Découvrir")
    username_query = st.text_input("Rechercher un utilisateur par nom:")
    if st.button("Rechercher"):
        if username_query:
            collection = db['users']
            # Utilisez une expression régulière pour effectuer une recherche partielle
            user_info = list(collection.find({"username": {"$regex": username_query, "$options": "i"}}, {"username": 1, "points": 1, "quizzes_completed": 1, "community_points": 1}))

            if user_info:
                for user in user_info:
                    with st.container():
                        st.write(f"**Nom/Pseudo**: **:blue[{user['username']}]**")
                        st.write(f"**Points Quizz**: **:blue[{user['points']}]**")
                        st.write(f"**Quizz Completés**: **:blue[{user['quizzes_completed']}]**")
                        st.write(f"**Points Communautaires** (*nombre de questions soumises aux quizs communautaires*): **:blue[{user['community_points']}]**")
            else:
                st.warning("Utilisateur non trouvé.")

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    collection = db['users']
    hashed_password = hash_password(password)
    user = collection.find_one({"username": username, "password": hashed_password})
    return user is not None

def get_user_stats(username):
    collection = db['users']  # Assurez-vous que 'db' est bien défini et connecté à votre base de données MongoDB
    user = collection.find_one({"username": username}, {"points": 1, "quizzes_completed": 1, "registration_date": 1})
    
    if user:
        return user['points'], user['quizzes_completed'], user['registration_date']
    else:
        return None

# Update user stats
def update_user_stats(username, points=0, quizzes_completed=0):
    collection = db['users']
    collection.update_one({"username": username}, {"$inc": {"points": points, "quizzes_completed": quizzes_completed}})

def load_questions(domain, subdomain, subsystem, source):
    collection = db['questions']
    questions = list(collection.find({"domain": domain, "subdomain": subdomain, "subsystem": subsystem}))
    return questions

def add_question_to_json(question, source):
    collection = db['questions']
    user = db['users'].find_one({"username": st.session_state.username})
    question['created_by'] = user['username']
    question['creator_id'] = user['user_id']
    question['creation_date'] = datetime.now()
    question['likes'] = 0  # Initialiser les likes
    question['dislikes'] = 0  # Initialiser les dislikes
    question['reports'] = []
    collection.insert_one(question)

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
    st.sidebar.write("Développé avec ❤️ par [maxx.abrt](https://www.instagram.com/maxx.abrt/) en **:green[python]** 🐍 avec **:red[streamlit]** et **:grey[perplexity]**")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.get('page', options[0])


# Interface utilisateur Streamlit
def main():
    st.title(":blue[Learn]")

    st.markdown("""
    <script>
    const doc = window.parent.document;
    const sidebar = doc.querySelector('[data-testid="stSidebar"]');
    const toggleButton = doc.querySelector('[data-testid="collapsedControl"]');
    
    function closeSidebar() {
        if (sidebar.classList.contains('--open')) {
            toggleButton.click();
        }
    }
    </script>
    """, unsafe_allow_html=True)


    choice = None


    if 'username' not in st.session_state:
        st.session_state.username = None

    if st.session_state.username is None:
        st.subheader(":blue[Connexion]")
        username = st.text_input("Nom d'utilisateur", key="login_username")
        password = st.text_input("Mot de passe", type="password", key="login_password")

        if st.button("**:blue[Se connecter]**"):
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

        if st.button("**:green[S'inscrire]**"):
            if create_user(new_username, new_password, domain, study_level):
                st.success("Compte créé avec succès! Vous pouvez maintenant vous connecter.")
            else:
                st.error("Ce nom d'utilisateur existe déjà")
                
        st.write("Le projet suivant a pour but de proposer une plateforme de :blue[collaboration] dans le domaine de la :red[santé], et permettre de réviser tous ensemble des **quiz**, des **schémas**, et partager ses **ressources**")
        st.write("---")
        display_leaderboard()
    else:
        choice = create_sidebar()


    if choice == "Accueil":
        st.session_state.page = "Accueil"
        st.session_state.close_sidebar = True
        display_help_button("Accueil")
        st.success(f"Bienvenue, **{st.session_state.username}**!")
        st.write(f"Bienvenue sur cette plateforme d'apprentissage collaboratif ! Le principe est de pouvoir réviser à plusieurs, créer des questions et des Qcm communautaires, et s'entraider dans le domaine de la santé !")
        st.write("*Le développement est toujours actif, n'hésitez pas à contacter le développeur en cas de retour ou problème !*")
        st.write(f"Vous pouvez naviguer sur le site grâce à la side bar, sur téléphone, elle est **:red[accessible en ouvrant la flèche en haut à gauche]** : ")
        st.image("arrow.png")
        display_leaderboard()
        
        
    elif choice == "Nous soutenir":
     display_help_button("Nous soutenir", "content")
     display_support_page()

     
     
    elif choice == "Schémas":
     display_help_button("Schémas", "content")
     display_schemas_page()
    elif choice == "Ajouter un schéma":
     display_help_button("Ajouter un schéma")
     display_add_schema_page()
    
    elif choice == "Déconnexion":
        st.session_state.username = None
        st.success("Vous avez été déconnecté.")
        st.rerun() 

    elif choice == "Qcm":
        display_help_button("Qcm")
        st.subheader("Qcm")
        domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]
        selected_domain = st.selectbox("__Qu'est-ce que vous souhaitez réviser ?__", domains)

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

        questions = []
        difficulty_emojis = {
            1: "🟢",  # Vert clair
            2: "🟢",  # Vert foncé
            3: "🟡",  # Jaune
            4: "🟠",  # Orange
            5: "🔴"   # Rouge
        }
        items_per_page = 10
        total_questions = len(questions)
        num_pages = (total_questions - 1) // items_per_page + 1

        if num_pages > 0:
            page_number = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
            start_idx = (page_number - 1) * items_per_page
            end_idx = start_idx + items_per_page
            current_questions = questions[start_idx:end_idx]
        else:

            current_questions = []


        question_type = st.radio("Source des questions :",[":blue[Questions de la communauté]"],captions=["Questions faites par les membres de la communauté, potentiellemment troll ou inexactes"],)

        if question_type == ":blue[Questions de la communauté]":
            questions = load_questions(selected_domain, selected_subdomain, selected_subsystem, "community")

        if not questions:
            st.warning("")
            
            
        else:
            
            with st.popover("Rechercher une question / filtrer"):
                # Fonctionnalité de recherche
                search_query = st.text_input("Entrez votre recherche ici :")
                
                # Slider pour sélectionner la difficulté
                difficulty_filter = st.slider("Filtrer par difficulté", 1, 5, value=1)
                
                # Bouton pour valider la sélection
                if st.button("Valider"):
                    # Appliquer le filtre de difficulté
                    filtered_questions = [
                        q for q in questions 
                        if search_query.lower() in q["question"].lower() and q.get("difficulty", 1) == difficulty_filter
                    ]
                else:
                    # Si aucun filtre n'est appliqué, afficher toutes les questions correspondant à la recherche
                    filtered_questions = [q for q in questions if search_query.lower() in q["question"].lower()]
            # Pagination setup
            items_per_page = 10
            total_questions = len(filtered_questions)
            num_pages = (total_questions - 1) // items_per_page + 1

            if num_pages > 0:
                page_number = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
                start_idx = (page_number - 1) * items_per_page
                end_idx = start_idx + items_per_page
                current_questions = filtered_questions[start_idx:end_idx]
            else:
                st.warning("Aucune question disponible pour cette sélection.")
                current_questions = []
            # Affichage et gestion des questions
            score = 0
            total_questions = len(questions)
            user_answers = []
                    # Afficher discrètement le créateur et la date
            st.write("---") 
            if current_questions:
                for i, question in enumerate(questions):
                    difficulty = question.get('difficulty', 1)  # Par défaut à 1 si non défini
                    emoji = difficulty_emojis.get(difficulty, "🟢")
                    st.subheader(f"{emoji} Question {i+1}")

                    
                    # Use a container for each question to improve layout control
                    with st.container():
                        username = st.session_state.get('username', None)
                        
                        if username is None:
                            st.warning("Veuillez vous connecter pour accéder au quiz.")
                            return
                            
                        else:
                            all_users = list(users_collection.find({}, {"username": 1, "points": 1, "quizzes_completed": 1, "community_points": 1, "registration_date": 1, "badges": 1}))
                            user_info = random.sample(all_users, min(20, len(all_users)))
                        
                        for user in user_info:
                            with st.container(border=True):
                                

                                # Display badges
                                badges_display = "".join([badge_info["emoji"] for badge_info in user["badges"].values() if badge_info["level"] > 0])
                                if badges_display:
                                    st.write(f"Question créée par : **:blue[{question.get('created_by', 'Inconnu')}]**")
                                    st.write(f"**Badges**: {badges_display}")
                        
                        
                        
                        
                        # Assuming you have a list of questions
                        for question in questions:
                            display_report_interface(question['_id'])
                        # Display creator info in a popover
                        with st.expander(f"Voir le profil de **:blue[{question.get('created_by', 'Inconnu')}]**"):
                            creator_id = question.get('creator_id', 'Inconnu')
                            created_by = question.get('created_by', 'Inconnu')
                            creation_date = question.get('creation_date').strftime('%d %b') if question.get('creation_date') else 'Date inconnue'
                            st.markdown(f"""
                                **Profil du (de la) créateur(ice) de la question :**
                                - Nom de l'utilisateur: **{created_by}**
                                - ID Utilisateur: **{creator_id}**
                                - Question faite le : **{creation_date}**
                            """)

                    st.markdown(
                        f"<span style='color:#60b4ff; font-weight:bold; font-size:18px;'>{question['question']}</span>",
                        unsafe_allow_html=True
                        )



                    if question["type"] == "QCM":
                        user_answer = st.radio(f"*Choisissez la bonne réponse pour la question {start_idx + i + 1}:*", question["options"])
                    elif question["type"] == "Vrai/Faux":
                        user_answer = st.radio(f"*Choisissez la bonne réponse pour la question {start_idx + i + 1}:*", ["Vrai", "Faux"])
                    else:
                        user_answer = st.text_input(f"*Votre réponse pour la question {start_idx + i + 1}:*")
                    
                    user_answers.append(user_answer)
                
                   # Slider pour like/dislike
                    choice = st.select_slider(
                        '*Votre avis :*',
                        options=['👎 Dislike', '🔘 Neutre', '👍 Like'],
                        value='🔘 Neutre',
                        key=f"slider_{i}"
                    )

                    # Vérifier si l'utilisateur a déjà voté
                    existing_interaction = interactions_collection.find_one({
                        'username': username,
                        'question_id': question['_id']
                    })

                    if existing_interaction:
                        st.warning("Vous avez déjà voté pour cette question.")
                    else:
                        if choice == '👍 Like':
                            update_likes_dislikes(question['_id'], 'like', username)
                            st.write(f"*:blue[Likes: {question.get('likes', 0) + 1}]*")
                            st.write(f"*:red[Dislikes: {question.get('dislikes', 0)}]*")
                        elif choice == '👎 Dislike':
                            update_likes_dislikes(question['_id'], 'dislike', username)
                            st.write(f"*:blue[Likes: {question.get('likes', 0)}]*")
                            st.write(f"*:red[Dislikes: {question.get('dislikes', 0) + 1}]*")

                    st.write("---")  # Séparateur entre les questions
                        
            # Initialiser le temps de dernier clic s'il n'existe pas
            if 'last_click_time' not in st.session_state:
                st.session_state.last_click_time = datetime.min

            # Fonction pour calculer le temps restant du cooldown
            def get_cooldown_time():
                elapsed_time = datetime.now() - st.session_state.last_click_time
                remaining_time = max(timedelta(seconds=15) - elapsed_time, timedelta(seconds=0))
                return remaining_time.total_seconds()

            # Vérifier si le cooldown est actif
            cooldown_seconds = get_cooldown_time()
            cooldown_active = cooldown_seconds > 0

            # Afficher un compte à rebours si le cooldown est actif
            ph = st.empty()
            if cooldown_active:
                for secs in range(int(cooldown_seconds), 0, -1):
                    mm, ss = secs // 60, secs % 60
                    ph.metric("Temps restant avant la prochaine soumission", f"{mm:02d}:{ss:02d}")
                    time.sleep(1)
                    if secs == 1:
                        ph.empty()  # Effacer le compteur après la fin du cooldown
                        st.rerun()  # Recharger la page pour réactiver le bouton

            # Désactiver le bouton si le cooldown est actif
            button_clicked = st.button("Terminer le QCM", disabled=cooldown_active)

            if button_clicked and not cooldown_active:
                # Mettre à jour le temps de dernier clic
                st.session_state.last_click_time = datetime.now()

                # Logique de soumission du formulaire
                score = 0
                domain_counts = {}
                subdomain_counts = {}
                subsystem_counts = {}

                for i, (question, user_answer) in enumerate(zip(current_questions, user_answers)):
                    if user_answer.lower() == question["correct_answer"].lower():
                        score += 1
                        st.success(f"Question {i+1}: Correct!")
                    else:
                        st.error(f"Question {i+1}: Incorrect. La bonne réponse était: {question['correct_answer']}")

                    domain = question.get("domain", "Unknown")
                    subdomain = question.get("subdomain", "Unknown")
                    subsystem = question.get("subsystem", "Unknown")

                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1
                    if subsystem:
                        subsystem_counts[subsystem] = subsystem_counts.get(subsystem, 0) + 1

                update_user_stats(st.session_state.username, points=score, quizzes_completed=1)
                st.info(f"Votre score pour cette page: {score}/{len(current_questions)}")
                quiz_interactions_collection.insert_one({
                    "user_id": st.session_state.username,
                    "timestamp": datetime.now(),
                    "domains": domain_counts,
                    "subdomains": subdomain_counts,
                    "subsystems": subsystem_counts
                })





    if choice == "Tableau de bord":
        st.header("Tableau de Bord - Stats")

        # Vérifiez si l'utilisateur est connecté
        user_id = st.session_state.get('username')
        if not user_id:
            st.warning("Veuillez vous connecter pour voir vos statistiques.")
            return

        # Récupération des données utilisateur
        user_data = users_collection.find_one({"username": user_id})

        if not user_data:
            st.warning("Aucune donnée utilisateur trouvée.")
            return

        # Récupération des interactions de quiz
        quiz_data = pd.DataFrame(list(quiz_interactions_collection.find({"user_id": user_id})))

        if quiz_data.empty:
            st.warning("Aucune interaction de quiz trouvée pour cet utilisateur.")
            return

        # Calcul des statistiques
        total_quizzes = user_data.get('quizzes_completed', 0)
        total_points = user_data.get('points', 0)
        community_points = user_data.get('community_points', 0)
        domain_counts = quiz_data['domains'].apply(lambda x: list(x.keys())).explode().value_counts()

        # Filtrer les données pour les 7 derniers jours
        today = pd.to_datetime('today').date()
        one_week_ago = today - timedelta(days=7)


        quiz_data['date'] = pd.to_datetime(quiz_data['timestamp']).dt.date
        last_week_data = quiz_data[quiz_data['date'] >= one_week_ago]

        # Calcul des statistiques pour les 7 derniers jours
        quiz_count_by_date = last_week_data.groupby('date').size().reset_index(name='count')
        points_over_time = last_week_data.groupby('date')['domains'].count().cumsum().reset_index(name='points')

        # Affichage des métriques générales avec une mise en page améliorée
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Nombre Total de Quiz", total_quizzes)
            st.metric("Points Totaux aux Quiz", total_points)
            st.metric("Domaine le plus révisé", domain_counts.idxmax())
            st.metric("Points communautaires", community_points)

        with col2:
            # Afficher l'évolution des quiz complétés sur les 7 derniers jours
            st.write("**Quiz complétés sur les 7 derniers jours :**")
            st.line_chart(quiz_count_by_date.set_index('date')['count'])

        with col1:
            # Afficher les domaines les plus travaillés
            st.write("**Les domaines les plus travaillés :**")
            st.bar_chart(domain_counts)

        # Affichage des graphiques de sous-domaines et points cumulés pour la semaine
        with col2:
            st.write("**Les sous domaines et points cumulés de la semaine :**")
            subdomain_counts = last_week_data['subdomains'].apply(lambda x: list(x.keys())).explode().value_counts()
            st.bar_chart(subdomain_counts)

        with col1:
            # Afficher l'évolution des points cumulés sur les 7 derniers jours
            st.write("**Évolution des points cumulés de la semaine :**")
            st.area_chart(points_over_time.set_index('date')['points'])
        display_advice()
        
        
        
    if choice == "Créer une question":
      display_help_button("Créer une question")
      if 'username' not in st.session_state or st.session_state.username is None:
        st.warning("Vous devez être connecté pour pouvoir créer une question.")
    
      else:
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
        st.write("⬆ Le champ question est à remplir :red[obligatoirement] ⬆")
                
        difficulty = st.slider("Sélectionnez la difficulté de la question (:green[1 = simple] et :red[ 5 = très complexe ou piègeuse] )", 1, 5, value=1)
        
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
        
          
        if question_text.strip():  # Assurez-vous que la question n'est pas vide
            if st.button("Soumettre la question"):
                new_question = {
                    "domain": domain,
                    "subdomain": subdomain,
                    "subsystem": subsystem,
                    "type": question_type,
                    "question": question_text,
                    "options": options if question_type == "QCM" else None,
                    "correct_answer": correct_answer,
                    "explanation": explanation,
                    "difficulty": difficulty 
                }
                add_question_to_json(new_question, "community")

                # Assumer que l’utilisateur connecté est stocké dans st.session_state
                username = st.session_state.username
                # Mise à jour des points de contribution communautaires avec MongoDB
                collection = db['users']
                collection.update_one({"username": username}, {"$inc": {"community_points": 1}})

                st.success("Question ajoutée et points de contribution mis à jour!")
        else:
             st.error("La question ne peut pas être vide (Le champ **:blue[Question]** tout au dessus, ensuite remplissez vos champs d'entrée et configurez votre question).")

    if choice == "Chat":
        display_help_button("Chat")
        display_chat()
  
    elif choice == "Mon compte":
        # Vérifiez si l'utilisateur est connecté
     user_id = st.session_state.get('username')
     if not user_id:
        st.warning("Veuillez vous connecter pour voir vos statistiques.")
        return
     user_data = users_collection.find_one({"username": user_id})
     display_help_button("Mon compte")
     
     if st.session_state.username:
            with st.container(border=True):
             display_account_details(st.session_state.username)
             

     new_username = st.text_input("Nouveau nom d'utilisateur", key="new_username")
     if st.button("Changer le nom d'utilisateur"):
     
      if new_username:
       if change_username(st.session_state.username, new_username):
            st.success("Nom d'utilisateur mis à jour avec succès!")
            st.session_state.username = new_username  # Mettre à jour la session
      else:
            st.error("Ce nom d'utilisateur existe déjà, veuillez en choisir un autre.")
          
     with st.container(border=True):
      display_badge_progress(user_data)
 
    if choice == "découvrir":

      display_help_button("découvrir")
      display_user_cards()
      
    if choice == "Modération":
      display_moderation_page()


    pass
if __name__ == "__main__":
    setup_cloudinary()
    update_all_user_badges()
    main()