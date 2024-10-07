import streamlit as st
import hashlib
import time
import pandas as pd
from datetime import datetime, timedelta, date
import requests
from dotenv import load_dotenv
import os
import threading
import cloudinary
import cloudinary.uploader
import uuid
from PIL import Image
from pymongo import MongoClient
import random
from pymongo.mongo_client import MongoClient
import streamlit.components.v1 as components
import unicodedata
from bson.objectid import ObjectId

load_dotenv()


mongo_uri = os.getenv('MONGODB_URI')


@st.cache_resource(show_spinner=False)
def load_image(image_path):
    return Image.open(image_path)

img = load_image('favicon.png')
igm = load_image('2.png')

st.set_page_config(
    page_title="Learn par Impulsar",
    page_icon=img,
    layout="centered",
    initial_sidebar_state="collapsed"
    
)

def get_db_connection():
    if 'db' not in st.session_state:
        attempts = 0
        while attempts < 3:
            try:
                client = MongoClient(os.getenv('MONGODB_URI'))
                st.session_state.db = client['quiz_app']
                print('Database connected')
                break
            except Exception as e:
                attempts += 1
                st.error(f"Connection error: {str(e)}. Retrying ({attempts}/3)...")
                time.sleep(2)
    return st.session_state.db

db = get_db_connection()
quiz_interactions_collection = db['quiz_interactions']
users_collection = db['users']
interactions_collection = db['user_interactions']
questions_collection = db['questions']
answered_questions_collection = db['answered_questions']
def get_todolist_collection():
    return db['todolist']

    
# Déclarations globales
domains = ["Anatomie", "Physiologie", "Chimie/Biochimie", "Mathématiques et arithmétique", "Hygiène", "Pharmacologie", "Psychologie"]

subdomains = {
    "Anatomie": ["Système osseux", "Système circulatoire", "Système nerveux", "Système urinaire", "Système respiratoire"],
    "Physiologie": ["Physiologie fondamentale", "Physiologie appliquée", "Physiopathologie"],
    "Chimie/Biochimie": ["Chimie organique", "Biochimie structurale", "Métabolisme"],
    "Mathématiques et arithmétique": ["Algèbre", "Géométrie", "Statistiques"],
    "Hygiène": ["Hygiène personnelle", "Hygiène alimentaire", "Hygiène environnementale"],
    "Pharmacologie": ["Pharmacocinétique", "Pharmacodynamique", "Classes de médicaments"],
    "Psychologie": ["Psychologie cognitive", "Psychologie sociale", "Psychopathologie"]
}

subsystems = {
    "Système osseux": ["Crâne", "Colonne vertébrale", "Membres supérieurs", "Membres inférieurs"],
    "Système circulatoire": ["Cœur", "Artères", "Veines"],
    "Système nerveux": ["Cerveau", "Moelle épinière", "Nerfs périphériques"],
    "Système urinaire": ["Reins", "Vessie", "Urètres"],
    "Système respiratoire": ["Poumons", "Trachée", "Bronches"]
}


@st.cache_data(show_spinner=False)
def get_user_data(username):
    return users_collection.find_one({"username": username})


# Assurez-vous que 'db' est défini avant d'utiliser des collections
collection_name = 'users'
try:
    collection = db[collection_name]
except NameError:
    st.error("La base de données n'est pas définie correctement.")
# Create a new collection for storing user interactions


def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    return st.session_state.session_id  
    
    
        
def manage_session():
    # Assurez-vous que le session_id est initialisé
    get_session_id()
    
    session_duration = 15  # Durée d'expiration de la session en minutes
    
    # Vérifier si la session est déjà en cours
    if 'session_expiry' in st.session_state:
        # Vérifier si la session a expiré
        if datetime.now() > st.session_state.session_expiry:
            st.warning("Votre session a expiré. Veuillez vous reconnecter.")
            del st.session_state['session_id']
            del st.session_state['session_expiry']
        else:
            # Réinitialiser le temps d'expiration à chaque interaction
            st.session_state.session_expiry = datetime.now() + timedelta(minutes=session_duration)
    else:
        # Créer une nouvelle session
        st.session_state.session_expiry = datetime.now() + timedelta(minutes=session_duration)
    st.session_state.session_id = []
    # Utiliser un cookie pour stocker l'état de la session côté client
    components.html(
        f"""<script>
            document.cookie = "session_id={st.session_state.session_id}; path=/; max-age={session_duration * 60}";
        </script>""",
        height=0,
    )

manage_session()




def display_custom_qcm_page():
    st.title("QCM Personnalisé")

    if 'quiz_started' in st.session_state and st.session_state['quiz_started'] and not st.session_state.get('quiz_finished', False):
        start_custom_quiz()
        return

    # Sélection des critères
    selected_domain = st.selectbox("Choisissez un domaine", domains)
    selected_subdomain = st.selectbox("Choisissez un sous-domaine", subdomains.get(selected_domain, []))
    selected_subsystem = st.selectbox("Choisissez un sous-système",
                                      subsystems.get(selected_subdomain, [])) if selected_domain == 'Anatomie' else None

    # Récupérer l'utilisateur actuel
    username = st.session_state.get('username')

    # Récupérer les questions auxquelles l'utilisateur a déjà répondu
    answered_questions_ids = get_answered_questions_ids(username, selected_domain, selected_subdomain, selected_subsystem)

    # Compter les questions disponibles
    all_questions = list(questions_collection.find({
        'domain': selected_domain,
        'subdomain': selected_subdomain,
        'subsystem': selected_subsystem
    }))
    
    available_questions = [q for q in all_questions if q['_id'] not in answered_questions_ids]
    
    if not available_questions:
        st.warning("Vous avez déjà répondu à toutes les questions de cette sélection. Vous allez refaire des questions déjà répondues.")
        available_questions = all_questions  # Réinitialiser pour permettre de refaire les questions

    num_questions = len(available_questions)
    st.write(f"Nombre de questions disponibles : :blue-background[{num_questions}]")

    # Slider pour sélectionner le nombre de questions
    num_selected_questions = st.slider(
        'Nombre de questions à répondre',
        min_value=0,
        max_value=num_questions,
        value=1
    )

    # Bouton pour démarrer le quiz
    if st.button("Répondre aux questions sélectionnées"):
        if num_selected_questions > 0:  # Vérifie qu'au moins une question est sélectionnée
            st.session_state['quiz_started'] = True
            st.session_state['selected_questions'] = random.sample(available_questions, num_selected_questions)
            st.session_state['current_question_index'] = 0
            st.session_state['user_answers'] = [None] * num_selected_questions
            st.session_state['quiz_finished'] = False  # Réinitialiser l'état du quiz terminé
            st.rerun()
        else:
            st.error("Veuillez sélectionner au moins une question pour commencer le quiz.")

def get_answered_questions_ids(username, domain, subdomain, subsystem):
    user_data = answered_questions_collection.find_one({"username": username})
    
    if not user_data:
        return []

    key = f"{domain}_{subdomain}_{subsystem}"
    
    return user_data.get(key, [])

def update_answered_questions(username, question_ids):
    key = f"{selected_domain}_{selected_subdomain}_{selected_subsystem}"
    
    answered_questions_collection.update_one(
        {"username": username},
        {"$addToSet": {key: {"$each": question_ids}}},
        upsert=True  # Crée un document si l'utilisateur n'existe pas encore dans la collection
    )





def start_custom_quiz():
    if 'quiz_started' not in st.session_state or not st.session_state['quiz_started']:
        return

    current_index = st.session_state.current_question_index
    questions = st.session_state.selected_questions

    if current_index < len(questions):
        question = questions[current_index]
            # Display creator information
        creator_id = question.get('creator_id', 'Inconnu')
        created_by = question.get('created_by', 'Inconnu')
        creation_date = question.get('creation_date').strftime('%d %b') if question.get('creation_date') else 'Date inconnue'
            
        user_info = get_user_data(created_by)  # Fetch user data from the database
        badges_display = "".join([badge_info["emoji"] for badge_info in user_info["badges"].values() if badge_info["level"] > 0])

                
        with st.container(border=True):
            
            st.subheader(f"Question {current_index + 1}/{len(questions)}")
            st.subheader(f":blue[{question.get('question', 'Texte non disponible')}]")
            st.write(f"Question créée par : :blue[{created_by}] - Badges: {badges_display}")



                

            if question['type'] == "QCM":
                user_answer = st.radio(
                    "Choisissez une réponse:",
                    question['options'],
                    key=f"question_{current_index}"
                )
            elif question['type'] == "Vrai/Faux":
                user_answer = st.radio(
                    "Choisissez:",
                    ["Vrai", "Faux"],
                    key=f"vrai_faux_{current_index}"
                )


            # Stocker la réponse de l'utilisateur
            st.session_state.user_answers[current_index] = user_answer

        # Vérifier si c'est la dernière question
        if current_index == len(questions) - 1:
            button_label = "Finir le QCM"
        else:
            button_label = "Question suivante"


        # Bouton pour passer à la question suivante ou finir le quiz
        if st.button(button_label):
            if current_index < len(questions) - 1:
                st.session_state.current_question_index += 1
                st.rerun()
            else:
                # Marquer le quiz comme terminé
                st.session_state.quiz_finished = True
                display_results()



def get_user_data(username):
    # Simulate fetching user data from a database
    return users_collection.find_one({"username": username})

def display_results():
    score = 0
    corrections = []
    
    for i, question in enumerate(st.session_state.selected_questions):
        user_answer = st.session_state.user_answers[i]
        correct_answer = question.get('correct_answer', None)
        question_text = question.get('question', 'Texte non disponible')

        if user_answer == correct_answer:
            score += 1
        else:
            corrections.append({
                "question": question_text,
                "votre réponse": user_answer,
                "bonne réponse": correct_answer
            })

    success_rate = (score / len(st.session_state.selected_questions)) * 100

    # Mise à jour des questions répondues dans la base de données après avoir terminé le quiz
    update_answered_questions(st.session_state.username, [q['_id'] for q in st.session_state.selected_questions])

    st.title("Résultats du QCM")
    st.success(f"Votre score: {score}/{len(st.session_state.selected_questions)} ({success_rate:.2f}%)")

    # Afficher les corrections si nécessaire
    if corrections:
        st.subheader("Corrections:")
        for correction in corrections:
            with st.container():
                st.write(correction['question'])
                if correction['votre réponse'] == correction['bonne réponse']:
                    st.success(f"Votre réponse: {correction['votre réponse']}")
                else:
                    st.error(f"Votre réponse: {correction['votre réponse']}")
                    st.success(f"Bonne réponse: {correction['bonne réponse']}")

    # Ajouter un bouton pour terminer le QCM et revenir à la page principale
    if st.button("Terminer le QCM"):
        keys_to_delete = ['quiz_started', 'selected_questions', 'current_question_index', 'user_answers', 'quiz_finished']
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        display_custom_qcm_page()
    

def get_answered_questions(username, domain, subdomain, subsystem):
    user_data = users_collection.find_one({"username": username})
    answered_questions = user_data.get('answered_questions', {})
    
    key = f"{domain}_{subdomain}_{subsystem}"
    
    return answered_questions.get(key, [])

def update_answered_questions(username, question_ids):
    users_collection.update_one(
        {"username": username},
        {"$addToSet": {"answered_questions": {"$each": question_ids}}}
    )


def calculate_score():
    score = 0
    corrections = []
    
    for i, question in enumerate(st.session_state.selected_questions):
        user_answer = st.session_state.user_answers[i]
        correct_answer = question.get('correct_answer', None)
        
        question_text = question.get('text', 'Texte non disponible')
        
        if user_answer == correct_answer:
            score += 1
        else:
            corrections.append({
                "question": question_text,
                "votre réponse": user_answer,
                "bonne réponse": correct_answer
            })
    
    success_rate = (score / len(st.session_state.selected_questions)) * 100
    st.success(f"Votre score: {score}/{len(st.session_state.selected_questions)} ({success_rate:.2f}%)")
    
    # Afficher les corrections si nécessaire
    if corrections:
        st.subheader("Corrections:")
        for correction in corrections:
            with st.container():
                st.write(correction['question'])
                if correction['votre réponse'] == correction['bonne réponse']:
                    st.success(f"Votre réponse: {correction['votre réponse']}")
                else:
                    st.error(f"Votre réponse: {correction['votre réponse']}")
                    st.success(f"Bonne réponse: {correction['bonne réponse']}")

    # Ajouter un bouton pour terminer le QCM et revenir à la page principale
    if st.button("Terminer le QCM"):
        del st.session_state.quiz_started
        del st.session_state.selected_questions
        del st.session_state.current_question_index
        del st.session_state.user_answers
        
        # Retourner à la page principale des questions personnalisées
        display_custom_qcm_page()
    
    
    
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
        
        
def create_question(text, options, correct_answer):
    return {
        "text": text,
        "options": options,
        "correct_answer": correct_answer
    }
     
     
     
# Initialisation de session_state
if 'selected_set_id' not in st.session_state:
    st.session_state.selected_set_id = None
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
    



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
            
            



#TODOLIST



def create_todo_item(user_id, username, content, due_date, category, priority):
    collection = get_todolist_collection()
    item_id = str(uuid.uuid4())
    creation_date = datetime.now()
    
    if isinstance(due_date, date):
        due_date = datetime.combine(due_date, datetime.min.time())
    
    item = {
        'item_id': item_id,
        'user_id': user_id,
        'username': username,
        'creation_date': creation_date,
        'due_date': due_date,
        'status': 'non commencé',
        'content': content,
        'category': category,
        'priority': priority
    }
    collection.insert_one(item)

def display_create_todo_form():
    st.header("Ajouter une nouvelle tâche")
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    content = st.text_input("Contenu de la tâche")
    due_date = st.date_input("Date de fin", min_value=datetime.now())
    category = st.selectbox("Catégorie", ["Travail", "Personnel", "Urgent"])
    priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"])
    
    if st.button("Ajouter la tâche"):
        create_todo_item(user_id, username, content, due_date, category, priority)
        st.success("Tâche ajoutée avec succès!")






def get_user_todos(user_id):
    collection = get_todolist_collection()
    todos_cursor = collection.find({'user_id': user_id}).sort([('due_date', 1), ('status', 1)])
    return list(todos_cursor)

def update_todo_item(item_id, update_fields):
    collection = get_todolist_collection()
    
    if 'due_date' in update_fields and isinstance(update_fields['due_date'], date):
        update_fields['due_date'] = datetime.combine(update_fields['due_date'], datetime.min.time())
    
    collection.update_one({'item_id': item_id}, {'$set': update_fields})

def delete_todo_item(item_id):
    collection = get_todolist_collection()
    collection.delete_one({'item_id': item_id})


def display_todolist_page():
    st.title("Todolist - Études")
    
    display_create_todo_form()
    
    user_id = st.session_state.get('user_id')
    todos = get_user_todos(user_id)
    
    status_emojis = {
        "non commencé": "🔴",
        "en cours": "🟠",
        "terminé": "✅"
    }
    
    priority_emojis = {
        "Basse": "🟢",
        "Moyenne": "🟡",
        "Haute": "🔴"
    }
    
    for todo in todos:
        status_emoji = status_emojis[todo['status']]
        priority_emoji = priority_emojis[todo['priority']]
        
        # Checkbox to mark task as completed
        is_checked = todo['status'] == 'terminé'
        
        # Display task with checkbox
        with st.container(border=True):
            col1, col2 = st.columns([0.01, 0.09])
            with col1:
                checked = st.checkbox("", value=is_checked, key=f"check_{todo['item_id']}")
                if checked and not is_checked:
                    update_todo_item(todo['item_id'], {'status': 'terminé'})
                elif not checked and is_checked:
                    update_todo_item(todo['item_id'], {'status': 'non commencé'})
            
            with col2:
                task_content_style = f"text-decoration: line-through;" if checked else ""
                st.markdown(f"<div style='{task_content_style}'>"
                            f"{priority_emoji} {todo['content']}</div>", unsafe_allow_html=True)
                st.write("")
                with st.expander("Plus d'informations"):
                    
                    una_key = f"{uuid.uuid4()}"
                    unb_key = f"{uuid.uuid4()}"
                    unc_key = f"{uuid.uuid4()}"
                    
                    
                    new_status = st.selectbox("Changer le statut", ["non commencé", "en cours", "terminé"], index=["non commencé", "en cours", "terminé"].index(todo['status']), key=una_key)
                    new_due_date = st.date_input("Nouvelle date de fin", value=todo['due_date'], key=unb_key)
                    new_content = st.text_area("Modifier le contenu", value=todo['content'], max_chars=50, key=unc_key)
                    
                    if st.button("Mettre à jour", key=f"update_{todo['item_id']}"):
                        update_todo_item(todo['item_id'], {'status': new_status, 'due_date': new_due_date, 'content': new_content})
                        st.success("Élément mis à jour avec succès!")
                    
                    if st.button("Supprimer définitivement", key=f"delete_{todo['item_id']}"):
                        delete_todo_item(todo['item_id'])
                        st.success("Élément supprimé!")

def update_questions_with_unique_ids():
    questions = list(questions_collection.find())
    for question in questions:
        
        if 'unique_id' not in question or not question['unique_id']:
            creator_name = question.get('created_by', 'Unknown')
            creator_id = question.get('creator_id', None)
            
            if creator_id:
                # Générer l'identifiant unique
                unique_id = generate_unique_question_id(creator_name, creator_id)
                
                # Mettre à jour la question avec l'identifiant unique
                questions_collection.update_one(
                    {'_id': question['_id']},
                    {'$set': {'unique_id': unique_id}}
                )
                print(f"Updated question ID: {question['_id']} with unique ID: {unique_id}")
            else:
                print(f"Skipping question ID: {question['_id']} due to missing creator ID.")


           
           
def generate_unique_question_id(creator_name, creator_id):
    # Normaliser le nom du créateur
    normalized_name = ''.join(
        c for c in unicodedata.normalize('NFD', creator_name) if unicodedata.category(c) != 'Mn'
    ).upper()[:3]

    # Compter le nombre de questions existantes par l'utilisateur
    question_count = questions_collection.count_documents({'creator_id': creator_id}) + 1

    # Générer l'identifiant unique
    random_digits = random.randint(10, 99)
    random_letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
    unique_id = f"{normalized_name}{question_count:03d}{random_digits}{random_letters}"

    return unique_id
           
           
           
           
           
           
           
           
           
            
def report_question(unique_id, username, reason):
    try:
        user_data = users_collection.find_one({"username": username}, {"user_id": 1})
        if user_data:
            report_data = {
                'username': username,
                'user_id': user_data['user_id'],
                'reason': reason,
                'timestamp': datetime.now()
            }
            result = questions_collection.update_one(
                {'unique_id': unique_id},
                {'$push': {'reports': report_data}}
            )
            return result.modified_count > 0
    except Exception as e:
        print(f"Error reporting question: {e}")
    return False


                
def display_report_interface(unique_id):
    with st.expander("Signaler la question"):
        reason_key = f"report_reason_{unique_id}_{uuid.uuid4()}"
        button_key = f"send_report_{unique_id}_{uuid.uuid4()}"
        
        reason = st.text_input("Raison du signalement (50 caractères max)", max_chars=50, key=reason_key)
        
        if st.button("Envoyer le signalement", key=button_key):
            username = st.session_state.get('username')
            
            if not username:
                st.warning("Veuillez vous connecter pour signaler une question.")
                return
            
            if reason.strip():
                try:
                    success = report_question(unique_id, username, reason)
                    
                    if success:
                        st.success("Signalement envoyé.")
                    else:
                        st.error("Erreur lors de l'envoi du signalement.")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement du signalement : {str(e)}")
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
    username = st.session_state.get('username')
    if not username:
        st.warning("Veuillez vous connecter pour accéder à cette page.")
        return
    
    user_data = users_collection.find_one({"username": username}, {"is_moderator": 1})
    
    if not (user_data and user_data.get('is_moderator', False)):
        st.warning("Vous n'avez pas les droits d'accès à cette page.")
        return
    
    st.header("Modération des Signalements")
    
    reported_questions = questions_collection.find({'reports.0': {'$exists': True}})
    
    for question in reported_questions:
        with st.container():
            st.write(f"**Question:** {question['question']}")
            st.write(f"**ID de la Question:** {question['_id']}")
            
            for report in question['reports']:
                st.write(f"**Signalé par:** {report['username']} (ID: {report['user_id']})")
                st.write(f"**Motif du signalement:** {report['reason']}")
                st.write(f"**Date du signalement:** {report['timestamp'].strftime('%d %b %Y %H:%M')}")
            
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
        st.sidebar.markdown("## Principal")

                    
        if st.sidebar.button("🏠 Accueil", key="home", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Accueil"
            collapse_sidebar()
        if st.sidebar.button("📋 Todolist", key="todolist"):
            st.session_state.page = "Todolist"
            collapse_sidebar()
        if st.sidebar.button("📊 Tableau de bord", key="Tableau de bord", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Tableau de bord"
            collapse_sidebar()
        st.sidebar.markdown("#### QCM")
        if st.sidebar.button("📚 Qcm", key="Qcm", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Qcm"
            collapse_sidebar()
        if st.sidebar.button("📝 Créer un Qcm", key="create_question", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Créer une question"
            collapse_sidebar()
        # Nouveaux boutons pour les sets de questions
        st.sidebar.markdown("#### Sets de questions")
            
        if st.sidebar.button("🗂️ Sets de questions", key="QCM Personnalisé"):
            st.session_state.page = "QCM Personnalisé"
            collapse_sidebar() 

        st.sidebar.markdown("#### Schémas")
        if st.sidebar.button("🖼️ Schémas", key="schemas", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Schémas"
            collapse_sidebar()
        if st.sidebar.button("➕ Ajouter un schéma", key="add_schema", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Ajouter un schéma"
            collapse_sidebar()

        st.sidebar.markdown("## Communauté")
        if st.sidebar.button("💬 Chat", key="chat", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "Chat"
            collapse_sidebar()
        if st.sidebar.button("👥 Découvrir", key="discover", on_click=lambda: st.markdown("<script>closeSidebar()</script>", unsafe_allow_html=True)):
            st.session_state.page = "découvrir"
            collapse_sidebar()

        st.sidebar.markdown("## Compte")
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
    question['creator_id'] = user['user_id']
    
    # Ajout de l'identifiant unique
    question['unique_id'] = generate_unique_question_id(user['username'], user['user_id'])
    
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
    
    
    
    
def auto_save_schema():
    # Fonction pour sauvegarder périodiquement le schéma
    while True:
        if 'schema_data' in st.session_state:
            # Sauvegarder les données du schéma en cours
            save_schema_to_db(st.session_state.schema_data)
        threading.Event().wait(60)  # Sauvegarde toutes les 60 secondes

def save_schema_to_db(schema_data):
    # Simuler la sauvegarde dans une base de données
    # Remplacez ceci par votre logique de sauvegarde réelle
    print("Schéma sauvegardé:", schema_data)
    
    
def display_add_schema_page():
    st.title("Ajouter un schéma")
    
    domain = st.selectbox("Domaine", domains)
    
    subdomain = st.selectbox("Sous-domaine", subdomains[domain])
    
    subsystem = None
    if domain == "Anatomie":
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
    
    if 'schema_elements' not in st.session_state:
        st.session_state.schema_elements = []
    
    def add_field():
        st.session_state.schema_elements.append("")
    
    def remove_field():
        if st.session_state.schema_elements:
            st.session_state.schema_elements.pop()
    
    col1, col2 = st.columns(2)
    with col1:
        st.button(":green[Ajouter une réponse]", on_click=add_field)
    with col2:
        st.button(":red[Retirer une réponse]", on_click=remove_field)
    
    for i, element in enumerate(st.session_state.schema_elements):
        st.session_state.schema_elements[i] = st.text_input(f"Élément {i+1} :", value=element, key=f"element_{i}")
    
    # Sauvegarder l'état actuel du schéma dans session_state pour la sauvegarde automatique
    st.session_state.schema_data = {
        'domain': domain,
        'subdomain': subdomain,
        'subsystem': subsystem,
        'title': title,
        'elements': st.session_state.schema_elements,
        'file_details': file_details if uploaded_file else None
    }
    
    if st.button("Soumettre le schéma"):
        if uploaded_file and title and st.session_state.schema_elements:
            file_content = uploaded_file.read()
            schema_data = upload_schema(file_content, uploaded_file.name, domain, subdomain, subsystem)
            if schema_data:
                schema_data["title"] = title
                save_schema_data(schema_data, st.session_state.schema_elements)
                st.success("Schéma ajouté avec succès !")
                # Réinitialiser les éléments après la soumission
                del st.session_state['schema_data']
                st.session_state.schema_elements = []
            else:
                st.error("Erreur lors de l'upload du schéma.")
        else:
            st.error("Veuillez remplir tous les champs et uploader une image.")

# Démarrer le thread de sauvegarde automatique si ce n'est pas déjà fait

               
               
               
               
def display_schemas_page():
    st.title("Schémas")
    
    # Champ de recherche
    search_query = st.text_input("Rechercher un schéma")
    domain = st.selectbox("Domaine", domains)
    
    subdomain = st.selectbox("Sous-domaine", subdomains[domain])
    
    subsystem = None
    if domain == "Anatomie":
        subsystem = st.selectbox("Sous-système", subsystems[subdomain])
    
    schemas = load_schemas()
    
    filtered_schemas = [s for s in schemas if s["domain"] == domain and s["subdomain"] == subdomain and (not subsystem or s["subsystem"] == subsystem)]
    
    if search_query:
        filtered_schemas = search_schemas(filtered_schemas, search_query)
    
    if not filtered_schemas:
        st.info("Aucun schéma disponible pour cette sélection.")
    else:
        # Pagination
        items_per_page = 1
        num_pages = (len(filtered_schemas) - 1) // items_per_page + 1
        page = st.number_input("Page", min_value=1, max_value=num_pages, value=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for schema in filtered_schemas[start_idx:end_idx]:
            with st.container(border=True):
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
    st.subheader("Vous appréciez la plateforme et la gratuité proposée ? Vous pouvez me soutenir financièrement ici :")

    # Générer un ID utilisateur unique avec UUID4
    user_id = str(uuid.uuid4())

    # Code HTML et JavaScript pour l'intégration d'AppLixir
    applixir_html = f"""
    <div id="applixir_vanishing_div" hidden>
        <iframe id="applixir_parent"></iframe>
    </div>
    <script type="text/javascript" src="https://cdn.applixir.com/applixir.sdk4.0m.js"></script>
    <script type='application/javascript'>
        function adStatusCallback(status) {{
            console.log('Ad Status: ' + status);
            // Vous pouvez ajouter ici des actions spécifiques en fonction du statut de l'annonce
            if (status === 'ad-rewarded') {{
                alert('Merci d\'avoir regardé la publicité !');
            }}
        }}

        var options = {{
            zoneId: 2050,  // Utiliser 2050 pour les tests
            userId: '{user_id}',  // Recommandé d'utiliser UUID4
            accountId: '8394',  // Remplacez par votre ID de compte
            siteId: '8923',  // Remplacez par votre ID de site
            adStatusCb: adStatusCallback
        }};

        document.getElementById('showRewardAdButton').onclick = function() {{
            invokeApplixirVideoUnit(options);  // Lire la vidéo publicitaire
        }};
    </script>
    """
    st.link_button("Soutenez moi en cliquant ici", "https://buymeacoffee.com/maxx.abrt")
    st.success("Les dons vont entièrement être utilisés dans l'app, pour payer l'hébergement ou alors développer d'autres fonctionnalités !")
    components.html(applixir_html, height=300)


    
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
    st.title("Chat")
    st.write("Discutez en temps réel avec d'autres utilisateurs de la plateforme.")

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
    

def get_user_domain(username):
    user = db['users'].find_one({"username": username})
    return user['domain'] if user else "Non spécifié"
    

# Fonction pour ajouter un message au chat
def add_message(username, message):
    collection = db['chat_messages']
    collection.insert_one({
        "username": username,
        "message": message,
        "timestamp": datetime.now()
    })

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
                        all_users = list(users_collection.find({}, {"username": 1, "points": 1, "quizzes_completed": 1, "community_points": 1, "registration_date": 1, "badges": 1}))
                        user_info = random.sample(all_users, min(20, len(all_users)))
                        for user in user_info: 
                             badges_display = "".join([badge_info["emoji"] for badge_info in user["badges"].values() if badge_info["level"] > 0])
                             if badges_display:
                              st.write(f"**Badges**: {badges_display}")
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
    # Fetch questions sorted by creation date to ensure chronological order
    questions = list(collection.find(
        {"domain": domain, "subdomain": subdomain, "subsystem": subsystem}
    ).sort("creation_date", 1))  # Sort by creation_date in ascending order
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
    question['unique_id'] = generate_unique_question_id(user['username'], user['user_id'])
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
        st.write("Bienvenue sur cette plateforme d'apprentissage collaboratif !")
        st.write(":blue-background[Veuillez remplir le formulaire ci-dessous pour vous **connecter** ou alors vous **inscrire** !]")
    
        st.subheader(":blue[Connexion]")
        username = st.text_input("Nom d'utilisateur", key="login_username")
        password = st.text_input("Mot de passe", type="password", key="login_password")

        if st.button("**:blue[Se connecter]**"):
            if verify_user(username, password):
                st.session_state.username = username
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
        st.title("Bienvenue sur votre application")

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
        selected_domain = st.selectbox("__Qu'est-ce que vous souhaitez réviser ?__", domains)


        selected_subdomain = st.selectbox("Choisissez un sous-domaine", subdomains[selected_domain])

        if selected_domain == "Anatomie":

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
        filtered_questions = []   

        # Assuming this block is within a function or the main logic
        question_type = st.radio("Source des questions :", [":blue[Questions de la communauté]"], captions=["Questions faites par les membres de la communauté, potentiellement troll ou inexactes"])

        if question_type == ":blue[Questions de la communauté]":
            questions = load_questions(selected_domain, selected_subdomain, selected_subsystem, "community")
            if not questions:
                st.warning("Aucune question disponible pour cette sélection.")
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
                            q for q in questions if search_query.lower() in q["question"].lower() and q.get("difficulty", 1) == difficulty_filter
                        ]
                    else:
                        # Si aucun filtre n'est appliqué, afficher toutes les questions correspondant à la recherche
                        filtered_questions = [q for q in questions if search_query.lower() in q["question"].lower()]
            # Pagination setup
            items_per_page = 5
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
                for i, question in enumerate(current_questions):
                    unique_id = question.get('unique_id')
                    difficulty = question.get('difficulty', 1)
                    emoji = difficulty_emojis.get(difficulty, "🟢")
                    st.subheader(f"{emoji} - Question {i+1}")
                    
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
                        
                        
                        
                        
                        unique_id = question.get('unique_id')
                        display_report_interface(unique_id)
                        
                         # Display creator info in a popover
                        with st.expander(f"Voir le profil de **:blue[{question.get('created_by', 'Inconnu')}]** *(créateur de la question)*"):
                            creator_id = question.get('creator_id', 'Inconnu')
                            created_by = question.get('created_by', 'Inconnu')
                            creation_date = question.get('creation_date').strftime('%d %b') if question.get('creation_date') else 'Date inconnue'
                            st.markdown(f"""
                                **Profil du (de la) créateur(ice) de la question :**
                                - Nom de l'utilisateur: **{created_by}**
                                - ID Utilisateur: **{creator_id}**
                                - Question faite le : **{creation_date}**
                                - ID de la question : **{question.get('unique_id')}**
                            """)
                    st.write(f"**:blue[{question.get('question', 'Texte de la question non disponible')}]**")
                    def display_question(question, index):
                     key = (f"question_{index}_answer")
                     if key not in st.session_state:
                      st.session_state[key] = None
                      st.subheader(f"Question {index + 1}: {question['question']}")
                      selected_option = st.radio(
                            "Choisissez une réponse:",
                            question['options'],
                            index=question['options'].index(st.session_state[key]) if st.session_state[key] else 0,
                            key=key
                        )

                        # Mettre à jour session_state avec la réponse sélectionnée
                     st.session_state[key] = selected_option
                     display_question(question, i)



                        
                        
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
                        st.write(f"Explication - Question {i+1} : {question.get('explanation', 'Aucune explication fournie.')}")
                    else:
                        st.error(f"Question {i+1}: Incorrect. La bonne réponse était: {question['correct_answer']}")
                        st.write(f"Explication - Question {i+1} : {question.get('explanation', 'Aucune explication fournie.')}")
                    domain = question.get("domain", "Unknown")
                    subdomain = question.get("subdomain", "Unknown")
                    subsystem = question.get("subsystem", "Unknown")

                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1
                    if subsystem:
                        subsystem_counts[subsystem] = subsystem_counts.get(subsystem, 0) + 1

                update_user_stats(st.session_state.username, points=score, quizzes_completed=1)
                st.write("---")
                st.success(f"Votre score pour cette page: {score}/{len(current_questions)}")
                quiz_interactions_collection.insert_one({
                    "user_id": st.session_state.username,
                    "timestamp": datetime.now(),
                    "domains": domain_counts,
                    "subdomains": subdomain_counts,
                    "subsystems": subsystem_counts
                })


    if choice == "QCM Personnalisé":
        display_custom_qcm_page()

    elif choice == "Todolist":
        display_todolist_page()
        
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
        domain = st.selectbox("Domaine", domains)
        
        subdomain = st.selectbox("Sous-domaine", subdomains[domain])
        
        if domain == "Anatomie":
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
             all_users = list(users_collection.find({}, {"username": 1, "user_id": 1, "points": 1, "quizzes_completed": 1, "community_points": 1, "registration_date": 1, "badges": 1}))
             user_info = random.sample(all_users, min(20, len(all_users)))
             for user in user_info: 
                             badges_display = "".join([badge_info["emoji"] for badge_info in user["badges"].values() if badge_info["level"] > 0])
                             if badges_display:
                              st.write(f"**Badges**: {badges_display}")

             

     with st.container(border=True):
      display_badge_progress(user_data)
     user_id = user.get('user_id', 'Inconnu')
     with st.expander("Infos pour les nerds 🤓 :"):
         st.info(f"Session ID: {get_session_id()}")
         st.info(f"User ID : {user_id}")
    
    if choice == "découvrir":

      display_help_button("découvrir")
      display_user_cards()
      
    if choice == "Modération":
      display_moderation_page()


    pass
if __name__ == "__main__":
    setup_cloudinary()
    main()