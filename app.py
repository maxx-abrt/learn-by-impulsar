_Ao='schema_data'
_An='unique_id'
_Am='API_SECRET'
_Al='CLOUD_NAME'
_Ak='Déconnexion'
_Aj='is_moderator'
_Ai='Aucune donnée utilisateur trouvée.'
_Ah='Utilisateur non trouvé.'
_Ag='Rechercher'
_Af='Rechercher un utilisateur par nom:'
_Ae='Découvrir'
_Ad='Réponse non disponible'
_Ac=':green[Voir la réponse]'
_Ab='recueil_questions_data'
_Aa='Réponse courte'
_AZ='$addToSet'
_AY='selected_questions'
_AX='session_id'
_AW='Système respiratoire'
_AV='Système urinaire'
_AU='Système nerveux'
_AT='Système circulatoire'
_AS='Système osseux'
_AR='Psychologie'
_AQ='Pharmacologie'
_AP='Mathématiques et arithmétique'
_AO='Chimie/Biochimie'
_AN='Physiologie'
_AM='user_sessions'
_AL='community_questions'
_AK='MONGODB_URI'
_AJ='collapsed'
_AI="Nom d'utilisateur"
_AH='total_points'
_AG='Sous-système'
_AF='Sous-domaine'
_AE='Domaine'
_AD='QCM Personnalisé'
_AC='Tableau de bord'
_AB='study_level'
_AA='medal_badge'
_A9='moderator_badge'
_A8='domains'
_A7='Recueil de Questions'
_A6='recueil_started'
_A5='correct_answer'
_A4='Vrai/Faux'
_A3='options'
_A2='Inconnu'
_A1='quiz_finished'
_A0='answered_questions'
_z='$inc'
_y='title'
_x='Mon compte'
_w='découvrir'
_v='Chat'
_u='schemas'
_t='Créer une question'
_s='Texte non disponible'
_r='created_by'
_q='Nous soutenir'
_p='Ajouter un schéma'
_o='Schémas'
_n='password'
_m='levels'
_l='name'
_k='type'
_j='creator_id'
_i='_id'
_h='QCM'
_g='current_question_index'
_f='user_answers'
_e='chat_messages'
_d='elements'
_c='Accueil'
_b='message'
_a='age_badge'
_Z='quiz_maker_badge'
_Y='community_badge'
_X='completion_badge'
_W='creation_date'
_V='quiz_started'
_U='Anatomie'
_T='question'
_S='subsystem'
_R='subdomain'
_Q='timestamp'
_P='questions'
_O='id'
_N=False
_M='user_id'
_L='domain'
_K='registration_date'
_J='community_points'
_I='quizzes_completed'
_H='users'
_G='points'
_F=None
_E=True
_D='badges'
_C='emoji'
_B='level'
_A='username'
import streamlit as st,hashlib,time,pandas as pd
from datetime import datetime,timedelta
import requests
from dotenv import load_dotenv
import os,threading,cloudinary,cloudinary.uploader,uuid
from PIL import Image
from pymongo import MongoClient
import random
from pymongo.mongo_client import MongoClient
import streamlit.components.v1 as components,unicodedata
from bson.objectid import ObjectId
import difflib
load_dotenv()
@st.cache_resource(show_spinner=_N)
def load_image(image_path):return Image.open(image_path)
img=load_image('favicon.png')
igm=load_image('2.png')
st.set_page_config(page_title='Learn par Impulsar',page_icon=img,layout='centered',initial_sidebar_state=_AJ)
def keep_alive():
	A='https://learn.impulsarstudios.xyz'
	while _E:
		try:B=requests.get(A);print(f"Pinged {A}, status code: {B.status_code}")
		except Exception as C:print(f"Error pinging {A}: {C}")
		time.sleep(300)
mongo_uri=os.getenv(_AK)
brevo_api_key=os.getenv('BREVO_API_KEY')
brevo_api_url=os.getenv('BREVO_API_URL')
def get_db_connection():
	if'db'not in st.session_state:
		A=0
		while A<3:
			try:B=MongoClient(os.getenv(_AK));st.session_state.db=B['quiz_app'];print('Database connected');break
			except Exception as C:A+=1;st.error(f"Connection error: {str(C)}. Retrying ({A}/3)...");time.sleep(2)
	return st.session_state.db
db=get_db_connection()
quiz_interactions_collection=db['quiz_interactions']
users_collection=db[_H]
interactions_collection=db['user_interactions']
questions_collection=db[_P]
answered_questions_collection=db[_A0]
recueils_questions_collection=db['recueils_questions']
important_questions_collection=db['important_questions']
collections=[_H,_e,_P,_AL,'scores',_f,_AM]
collection_name=_H
collection=db[collection_name]
if _g not in st.session_state:st.session_state.current_question_index=0
if _f not in st.session_state:st.session_state.user_answers=[]
def collapse_sidebar():st.session_state.sidebar_state=_AJ;st.rerun()
domains=[_U,_AN,_AO,_AP,'Hygiène',_AQ,_AR]
subdomains={_U:[_AS,_AT,_AU,_AV,_AW,'Peau'],_AN:['Physiologie fondamentale','Physiologie appliquée','Physiopathologie'],_AO:['Chimie organique','Biochimie structurale','Métabolisme'],_AP:['Algèbre','Géométrie','Statistiques'],'Hygiène':['Hygiène personnelle','Hygiène alimentaire','Hygiène environnementale'],_AQ:['Pharmacocinétique','Pharmacodynamique','Classes de médicaments'],_AR:['Psychologie cognitive','Psychologie sociale','Psychopathologie']}
subsystems={_AS:['Crâne','Colonne vertébrale','Membres supérieurs','Membres inférieurs','Système global'],_AT:['Cœur','Artères','Veines'],_AU:['Cerveau','Moelle épinière','Nerfs périphériques'],_AV:['Reins','Vessie','Urètres'],_AW:['Poumons','Trachée','Bronches'],'Peau':['Peau']}
@st.cache_data(show_spinner=_N)
def get_user_data(username):return users_collection.find_one({_A:username})
collection_name=_H
try:collection=db[collection_name]
except NameError:st.error("La base de données n'est pas définie correctement.")
def get_session_id():
	if _AX not in st.session_state:st.session_state.session_id=hashlib.sha256(str(datetime.now()).encode()).hexdigest()
	return st.session_state.session_id
def manage_session():
	B='session_expiry';get_session_id();A=15
	if B in st.session_state:
		if datetime.now()>st.session_state.session_expiry:st.warning('Votre session a expiré. Veuillez vous reconnecter.');del st.session_state[_AX];del st.session_state[B]
		else:st.session_state.session_expiry=datetime.now()+timedelta(minutes=A)
	else:st.session_state.session_expiry=datetime.now()+timedelta(minutes=A)
	st.session_state.session_id=[];components.html(f'<script>\n            document.cookie = "session_id={st.session_state.session_id}; path=/; max-age={A*60}";\n        </script>',height=0)
manage_session()
def display_custom_qcm_page():
	st.title(_h)
	if _V in st.session_state and st.session_state[_V]and not st.session_state.get(_A1,_N):start_custom_quiz();return
	A=st.selectbox('Choisissez un domaine',domains);C=st.selectbox('Choisissez un sous-domaine',subdomains.get(A,[]));E=st.selectbox('Choisissez un sous-système',subsystems.get(C,[]))if A==_U else _F;H=st.session_state.get(_A);I=get_answered_questions_ids(H,A,C,E);F=list(questions_collection.find({_L:A,_R:C,_S:E}));B=[A for A in F if A[_i]not in I]
	if not B:st.warning('Vous avez déjà répondu à toutes les questions de cette sélection. Vous allez refaire des questions déjà répondues.');B=F
	G=len(B);st.write(f"Nombre de questions disponibles : :blue-background[{G}]");D=st.slider('Nombre de questions à répondre',min_value=0,max_value=G,value=1)
	if st.button(':green[Répondre aux questions sélectionnées]'):
		if D>0:st.session_state[_V]=_E;st.session_state[_AY]=random.sample(B,D);st.session_state[_g]=0;st.session_state[_f]=[_F]*D;st.session_state[_A1]=_N;st.rerun()
		else:st.error('Veuillez sélectionner au moins une question pour commencer le quiz.')
def get_answered_questions_ids(username,domain,subdomain,subsystem):
	A=answered_questions_collection.find_one({_A:username})
	if not A:return[]
	B=f"{domain}_{subdomain}_{subsystem}";return A.get(B,[])
def update_answered_questions(username,question_ids):A=f"{selected_domain}_{selected_subdomain}_{selected_subsystem}";answered_questions_collection.update_one({_A:username},{_AZ:{A:{'$each':question_ids}}},upsert=_E)
def start_custom_quiz():
	if _V not in st.session_state or not st.session_state[_V]:return
	A=st.session_state.current_question_index;C=st.session_state.selected_questions
	if A<len(C):
		B=C[A];I=B.get(_j,_A2);E=B.get(_r,_A2);J=B.get(_W).strftime('%d %b')if B.get(_W)else'Date inconnue';G=get_user_data(E);H=''.join([A[_C]for A in G[_D].values()if A[_B]>0])
		with st.container(border=_E):
			st.subheader(f"Question {A+1}/{len(C)}");st.subheader(f":blue[{B.get(_T,_s)}]");st.write(f"Question créée par : :blue[{E}] - Badges: {H}")
			if B[_k]==_h:D=st.radio('Choisissez une réponse:',B[_A3],key=f"question_{A}")
			elif B[_k]==_A4:D=st.radio('Choisissez:',['Vrai','Faux'],key=f"vrai_faux_{A}")
			elif B[_k]==_Aa:D=st.text_input('Votre réponse:',key=f"reponse_courte_{A}")
			else:st.error(f"Type de question inconnu: {B[_k]}");D=_F
		if D is not _F:st.session_state.user_answers[A]=D
		else:st.session_state.user_answers[A]='Non répondu'
		if A==len(C)-1:F='Finir le QCM'
		else:F='Question suivante'
		if st.button(F):
			if A<len(C)-1:st.session_state.current_question_index+=1;st.rerun()
			else:st.session_state.quiz_finished=_E;display_results()
	else:st.warning('Toutes les questions ont été traitées.')
def get_user_data(username):return users_collection.find_one({_A:username})
def display_results():
	E='bonne réponse';B='votre réponse';C=0;D=[]
	for(J,F)in enumerate(st.session_state.selected_questions):
		G=st.session_state.user_answers[J];H=F.get(_A5,_F);K=F.get(_T,_s)
		if G==H:C+=1
		else:D.append({_T:K,B:G,E:H})
	L=C/len(st.session_state.selected_questions)*100;update_answered_questions(st.session_state.username,[A[_i]for A in st.session_state.selected_questions]);st.title('Résultats du QCM');st.success(f"Votre score: {C}/{len(st.session_state.selected_questions)} ({L:.2f}%)")
	if D:
		st.subheader('Corrections:')
		for A in D:
			with st.container():
				st.write(A[_T])
				if A[B]==A[E]:st.success(f"Votre réponse: {A[B]}")
				else:st.error(f"Votre réponse: {A[B]}");st.success(f"Bonne réponse: {A[E]}")
	if st.button('Terminer le QCM'):
		M=[_V,_AY,_g,_f,_A1]
		for I in M:
			if I in st.session_state:del st.session_state[I]
		display_custom_qcm_page()
def get_answered_questions(username,domain,subdomain,subsystem):A=users_collection.find_one({_A:username});B=A.get(_A0,{});C=f"{domain}_{subdomain}_{subsystem}";return B.get(C,[])
def update_answered_questions(username,question_ids):users_collection.update_one({_A:username},{_AZ:{_A0:{'$each':question_ids}}})
if _A6 not in st.session_state:st.session_state.recueil_started=_N
if _g not in st.session_state:st.session_state.current_question_index=0
if _Ab not in st.session_state:st.session_state.recueil_questions_data=[]
def get_recueil_questions(domaine,ue):A=recueils_questions_collection.find_one({'domaine':domaine,'ue':ue});return A[_P]if A else[]
def display_recueil_questions_page():
	st.title(_A7);B=st.empty()
	if not st.session_state.get(_A6,_N):
		with B.container():
			C=st.selectbox("Choisissez un domaine d'étude",['Infirmier','Médecine'],key='recueil_domaine_selector');D=st.selectbox("Choisissez l'unité d'enseignement",['2.1','2.2'],key='recueil_ue_selector');E=st.checkbox('Lancer les questions en ordre aléatoire',key='random_order_checkbox');A=get_recueil_questions(C,D);F=len(A);st.write(f"Nombre de questions disponibles dans le recueil sélectionné : :blue-background[{F}]")
			if not A:st.warning('Aucune question trouvée pour cette sélection.');return
			if E:random.shuffle(A)
			st.session_state.recueil_questions_data=A
			if st.button(':green[Lancer le recueil]',key='lancer_recueil_button'):
				if not A:st.error('Aucune question à lancer.');return
				st.session_state.recueil_started=_E;st.session_state.current_question_index=0;st.rerun()
	else:
		with B.container():display_current_question()
def display_current_question():
	A=st.session_state.current_question_index;B=st.session_state.recueil_questions_data
	if not isinstance(B,list):st.error('Les questions du recueil ne sont pas au format attendu.');return
	if A<len(B):
		C=B[A];D=st.empty()
		with D.container(border=_E):
			E=(st.session_state.current_question_index+1)/len(st.session_state.recueil_questions_data);st.progress(E);st.subheader(f"Question {A+1}/{len(B)}");F=C.get(_T,_s);st.info(F)
			if st.button(_Ac,key=f"voir_reponse_{A}"):G=C.get('réponse',_Ad);st.success(G)
			H=':red[Terminer le recueil]'if A==len(B)-1 else':orange[Question suivante]'
			if st.button(H,key=f"next_button_{A}"):
				if A<len(B)-1:st.session_state.current_question_index+=1;st.rerun()
				else:del st.session_state[_g];del st.session_state[_A6];del st.session_state[_Ab];st.success('Recueil terminé.');st.rerun()
def display_important_questions(username):
	E='question_index';C=list(important_questions_collection.find({_A:username}))
	if not C:st.warning('Aucune question importante trouvée.');return
	for A in C:
		B=recueils_questions_collection.find_one({_i:A['recueil_id']})
		if B and _P in B:
			D=B[_P][A[E]];st.subheader(D.get(_T,_s))
			if st.button(_Ac,key=f"voir_reponse_importante_{A[E]}"):F=D.get('réponse',_Ad);st.success(F)
def create_question(text,options,correct_answer):return{'text':text,_A3:options,_A5:correct_answer}
def display_user_cards():
	st.title(_Ae);D=st.text_input(_Af)
	if st.button(_Ag)and D:
		C=list(users_collection.find({_A:{'$regex':D,'$options':'i'}},{_A:1,_G:1,_I:1,_J:1,_K:1,_D:1}))
		if not C:st.warning(_Ah);return
	else:E=list(users_collection.find({},{_A:1,_G:1,_I:1,_J:1,_K:1,_D:1}));C=random.sample(E,min(20,len(E)))
	for A in C:
		with st.container(border=_E):
			st.markdown(f"**Nom d'utilisateur**: **:blue[{A[_A]}]**");st.markdown(f"**Points aux Quiz**: **:blue[{A[_G]}]**");st.markdown(f"**Quiz Complétés**: **:blue[{A[_I]}]**");st.markdown(f"**Points Communautaires**: **:blue[{A[_J]}]**");B=A.get(_K)
			if B:B=B.strftime('%d %b %Y');st.markdown(f"**Date d'inscription**: **:blue[{B}]**")
			F=''.join([A[_C]for A in A[_D].values()if A[_B]>0])
			if F:st.markdown(f"**Badges**: {F}")
def generate_unique_question_id(creator_name,creator_id):A=''.join(A for A in unicodedata.normalize('NFD',creator_name)if unicodedata.category(A)!='Mn').upper()[:3];B=questions_collection.count_documents({_j:creator_id})+1;C=random.randint(10,99);D=''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ',k=4));E=f"{A}{B:03d}{C}{D}";return E
def display_advice():
	I='Révision Espacée';st.header('Tableau de Bord - Conseils');B=st.session_state.get(_A)
	if not B:st.warning('Veuillez vous connecter pour voir vos conseils.');return
	A=users_collection.find_one({_A:B})
	if not A:st.warning(_Ai);return
	C=A.get(_I,0);J=A.get(_G,0);D=pd.DataFrame(list(quiz_interactions_collection.find({_M:B})))
	if not D.empty:
		E=D[_A8].apply(lambda x:list(x.keys())).explode().value_counts();R=E.nsmallest(3).index.tolist();st.subheader('Conseils personnalisés suivant vos données')
		if C<5:st.info("Essayez d'augmenter le nombre de quiz par jour pour améliorer vos résultats ! (nous vous conseillons 5 quiz par jour !)")
		else:st.success('Félicitations ! Vous suivez un bon rythme de révision.')
		K=(datetime.now()-A[_K]).days;L=max(K/7,1);F=C/L;st.markdown('### Suggestions Basées sur Vos Statistiques')
		if C<8:st.write('- **Augmentez la fréquence** : Essayez de compléter au moins un quiz par jour.')
		if J<50:st.write('- **Améliorez votre score** : Concentrez-vous sur les domaines où vous avez le moins de points.')
		if E.max()>5:M=E.idxmax();st.write(f"- **Diversifiez vos études** : Vous avez beaucoup travaillé sur **:blue[{M}]**. Essayez d'explorer d'autres domaines pour un apprentissage équilibré.")
		if F<10:st.write(f"- **Soyez plus régulier** : Essayez de maintenir une moyenne d'au moins 10 quiz par semaine pour garder vos connaissances fraîches. Vous êtes actuellement à : **:blue[{F}]** quiz par semaine.")
		G=A.get(_J,0)
		if G<5:st.write(f"- **Participez à la communauté** : Contribuez aux questions communautaires pour améliorer vos points et bénéficier des retours des autres utilisateurs. Vous êtes actuellement à : **:blue[{G}]** points.")
		N=pd.to_datetime(D[_Q]).dt.hour.value_counts();O=N.idxmax();st.write(f"- **Optimisez votre temps d'étude** : Vous semblez être plus actif autour de **:blue[{O} h]**. Essayez de planifier vos sessions d'étude à ces heures pour une efficacité maximale.")
	st.subheader('Stratégies de Révision Recommandées');P=[(I,"Étalez vos sessions d'étude sur plusieurs jours pour améliorer la rétention."),('Test Pratique','Utilisez des quiz pour tester vos connaissances et identifier les lacunes.'),('Interleaving',"Alternez entre différents sujets pour renforcer l'apprentissage."),('Auto-explication','Expliquez ce que vous avez appris avec vos propres mots.'),('Utilisation de Cartes Mémoire','Créez des cartes mémoire pour mémoriser des concepts clés.')]
	for(H,Q)in P:
		with st.expander(f"**{H}**"):
			st.write(Q)
			if H==I:st.image('spaced_repetition.png',use_column_width=_E,caption='Diagramme de révision espacée')
def update_all_user_badges():
	B=users_collection.find()
	for A in B:assign_badges(A);users_collection.update_one({_A:A[_A]},{'$set':{_D:A[_D]}})
badge_thresholds={_X:{_l:'Points de quiz 🏆',_m:[30,500,1000,5000,10000]},_Y:{_l:'Communauté 🤝',_m:[10,50,100,500,1000]},_Z:{_l:'Compléteur(euse) de quiz 📚',_m:[5,20,50,100,200]},_a:{_l:'Ancienneté ⏳',_m:[30,180,365]}}
def assign_badges(user):
	A=user
	if _D not in A or not isinstance(A[_D],dict):A[_D]={_X:{_B:0,_C:''},_Y:{_B:0,_C:''},_Z:{_B:0,_C:''},_a:{_B:0,_C:''},_A9:{_B:0,_C:''},_AA:{_B:0,_C:''}}
	D=[30,500,1000,5000,10000];E=[10,50,100,500,1000];F=[5,20,50,100,200];G=[30,180,365];H=(datetime.now()-A[_K]).days
	for(B,C)in enumerate(D):
		if A[_G]>=C:A[_D][_X]={_B:B+1,_C:f"🏆{B+1}"}
	for(B,C)in enumerate(E):
		if A[_J]>=C:A[_D][_Y]={_B:B+1,_C:f"🤝{B+1}"}
	for(B,I)in enumerate(F):
		if A[_I]>=I:A[_D][_Z]={_B:B+1,_C:f"📚{B+1}"}
	for(B,J)in enumerate(G):
		if H>=J:A[_D][_a]={_B:B+1,_C:f"⏳{B+1}"}
def display_badge_progress(user_data):
	B=user_data;st.subheader('Progression des Badges')
	for(C,E)in badge_thresholds.items():
		F=E[_m];G=E[_l];D=B[_D].get(C,{}).get(_B,0);A=_F
		if C==_X:A=B.get(_G,0)
		elif C==_Y:A=B.get(_J,0)
		elif C==_Z:A=B.get(_I,0)
		elif C==_a:A=(datetime.now()-B.get(_K)).days
		if D<len(F):H=F[D];I=min(A/H,1.);st.markdown(f"**{G}** - Niveau actuel: {D} - Progrès: {A}/{H}");st.progress(I)
		else:st.markdown(f"**{G}** - Niveau maximum atteint!")
def create_user(username,password,domain,study_level):
	A=username;B=db[_H]
	if B.find_one({_A:A}):return _N
	else:C=hash_password(password);D=str(uuid.uuid4());B.insert_one({_M:D,_A:A,_n:C,_L:domain,_AB:study_level,_G:0,_J:0,_I:0,_K:datetime.now(),_D:{_X:{_B:0,_C:''},_Y:{_B:0,_C:''},_Z:{_B:0,_C:''},_a:{_B:0,_C:''},_A9:{_B:0,_C:''},_AA:{_B:0,_C:''}},_Aj:_N});return _E
collections={'scores':{_O:int,_A:str,'score':int},_f:{_O:int,_A:str,'question_id':int,'answer':str,'is_correct':int},_AM:{_O:int,_A:str,_Q:int},_H:{_O:int,_A:str,_n:str,_L:str,_AB:str,_G:int,_J:int,_I:int,_K:datetime,_D:{_X:{_B:0,_C:''},_Y:{_B:0,_C:''},_Z:{_B:0,_C:''},_a:{_B:0,_C:''},_A9:{_B:0,_C:''},_AA:{_B:0,_C:''}},_Aj:_N},_e:{_O:int,_A:str,_b:str,_Q:datetime}}
def create_sidebar():
	with st.sidebar:
		st.title('Menu')
		if'page'not in st.session_state:st.session_state.page=_c
		st.sidebar.markdown('## Principal')
		if st.sidebar.button('🏠 Accueil',key='home'):st.session_state.page=_c;collapse_sidebar()
		if st.sidebar.button('📊 Tableau de bord',key=_AC):st.session_state.page=_AC;collapse_sidebar()
		st.sidebar.markdown('#### QCM')
		if st.sidebar.button('📚 Qcm',key=_AD):st.session_state.page=_AD;collapse_sidebar()
		if st.sidebar.button('📝 Créer un Qcm',key='create_question'):st.session_state.page=_t;collapse_sidebar()
		st.sidebar.markdown('#### Recueils de questions')
		if st.sidebar.button('📖 Recueil de Questions',key='recueil_questions_button'):st.session_state.page=_A7;collapse_sidebar()
		st.sidebar.markdown('#### Schémas')
		if st.sidebar.button('🖼️ Schémas',key=_u):st.session_state.page=_o;collapse_sidebar()
		if st.sidebar.button('➕ Ajouter un schéma',key='add_schema'):st.session_state.page=_p;collapse_sidebar()
		st.sidebar.markdown('## Communauté')
		if st.sidebar.button('💬 Chat',key='chat'):st.session_state.page=_v;collapse_sidebar()
		if st.sidebar.button('👥 Découvrir',key='discover'):st.session_state.page=_w;collapse_sidebar()
		st.sidebar.markdown('## Compte')
		if st.sidebar.button('👤 Mon compte',key='account'):st.session_state.page=_x;collapse_sidebar()
		if st.sidebar.button('❤️ Nous soutenir',key='support'):st.session_state.page=_q;collapse_sidebar()
		if st.sidebar.button('🚪 Déconnexion',key='logout'):st.session_state.page=_Ak;collapse_sidebar()
		st.write('Développé avec ❤️ par [maxx.abrt](https://www.instagram.com/maxx.abrt/) en **:green[python]** 🐍 avec **:red[streamlit]** et **:grey[perplexity]**')
	return st.session_state.page
def load_schemas():
	B=db[_u];A=list(B.find())
	if A:print('1 schema loaded')
	else:print('No schemas found.')
	return A
def display_help_button(page_name,location='top'):
	A=page_name;B={_c:"Bienvenue sur la page d'accueil. Ici, vous pouvez voir le leaderboard et les informations générales sur la plateforme.",'Qcm':"Sur cette page, vous pouvez sélectionner un domaine, un sous-domaine et un sous-système (pour l'anatomie) pour commencer un Qcm.",_t:'Ici, vous pouvez créer une nouvelle question pour la communauté. Choisissez le domaine, le type de question et remplissez les champs nécessaires.',_v:"Le chat vous permet de discuter en temps réel avec d'autres utilisateurs de la plateforme.",_x:'Consultez et modifiez vos informations personnelles sur cette page.',_w:"Découvrez d'autres utilisateurs et leurs contributions sur cette page.",_q:'Vous pouvez nous soutenir en visualisant une publicité sur cette page.',_o:'Consultez et étudiez les schémas disponibles dans différents domaines.',_p:'Contribuez à la communauté en ajoutant un nouveau schéma sur cette page.'}
	if st.button('💡 Aide',key=f"help_button_{A}_{location}"):st.info(B.get(A,'Aide non disponible pour cette page.'))
def search_schemas(schemas,query):A=query;A=A.lower();return[B for B in schemas if A in B.get(_y,'').lower()or A in B.get(_L,'').lower()or A in B.get(_R,'').lower()or A in B.get(_S,'').lower()or any(A in B.lower()for B in B.get(_d,[]))]
cloudinary.config(cloud_name=os.getenv(_Al),api_key=os.getenv('API_KEY'),api_secret=os.getenv(_Am),secure=_E)
def setup_cloudinary():cloudinary.config(cloud_name=os.getenv(_Al),api_key=os.getenv('API_KEY'),api_secret=os.getenv(_Am),secure=_E)
def upload_schema(file_content,file_name,domain,subdomain,subsystem=_F):
	B=str(uuid.uuid4());C=os.path.splitext(file_name)[1];A=f"{B}{C}"
	try:D=cloudinary.uploader.upload(file_content,public_id=A,folder=_u);E=str(uuid.uuid4());F={_O:E,'filename':A,'url':D['secure_url'],_L:domain,_R:subdomain,_S:subsystem,_d:[]};return F
	except Exception as G:st.error(f"Upload failed: {str(G)}");return
def add_community_question(question):A=question;C=db[_P];B=db[_H].find_one({_A:st.session_state.username});A[_r]=B[_A];A[_j]=B[_M];A[_An]=generate_unique_question_id(B[_A],B[_M]);A[_W]=datetime.now();C.insert_one(A)
def load_community_questions():A=db[_AL];B=list(A.find());return B
def save_schema_data(schema_data,elements):A=schema_data;B=db[_H].find_one({_A:st.session_state.username});A[_d]=elements;A[_r]=B[_A];A[_j]=B[_M];A[_W]=datetime.now();db[_u].insert_one(A)
def update_user_stats(username,points=0,quizzes_completed=0):A=db[_H];A.update_one({_A:username},{_z:{_G:points,_I:quizzes_completed}})
def auto_save_schema():
	while _E:
		if _Ao in st.session_state:save_schema_to_db(st.session_state.schema_data)
		threading.Event().wait(60)
def save_schema_to_db(schema_data):print('Schéma sauvegardé:',schema_data)
def display_add_schema_page():
	st.title(_p);B=st.selectbox(_AE,domains);C=st.selectbox(_AF,subdomains[B]);D=_F
	if B==_U:D=st.selectbox(_AG,subsystems[C])
	A=st.file_uploader('Choisir une image',type=['png','jpg','jpeg'])
	if A is not _F:
		H={'FileName':A.name,'FileType':A.type,'FileSize':A.size};st.write(H)
		if A.size>10*1024*1024:st.error('Le fichier est trop volumineux. La taille maximale est de 10 MB.')
		else:st.image(A)
	E=st.text_input('Titre du schéma');st.write("***:red[Pensez à créer au moins une réponse possible avec le bouton 'Ajouter une réponse' en dessous !]***")
	if'schema_elements'not in st.session_state:st.session_state.schema_elements=[]
	def I():st.session_state.schema_elements.append('')
	def J():
		if st.session_state.schema_elements:st.session_state.schema_elements.pop()
	K,L=st.columns(2)
	with K:st.button(':green[Ajouter une réponse]',on_click=I)
	with L:st.button(':red[Retirer une réponse]',on_click=J)
	for(F,M)in enumerate(st.session_state.schema_elements):st.session_state.schema_elements[F]=st.text_input(f"Élément {F+1} :",value=M,key=f"element_{F}")
	st.session_state.schema_data={_L:B,_R:C,_S:D,_y:E,_d:st.session_state.schema_elements,'file_details':H if A else _F}
	if st.button('Soumettre le schéma'):
		if A and E and st.session_state.schema_elements:
			N=A.read();G=upload_schema(N,A.name,B,C,D)
			if G:G[_y]=E;save_schema_data(G,st.session_state.schema_elements);st.success('Schéma ajouté avec succès !');del st.session_state[_Ao];st.session_state.schema_elements=[]
			else:st.error("Erreur lors de l'upload du schéma.")
		else:st.error('Veuillez remplir tous les champs et uploader une image.')
def normalize_answer(answer):A=answer;A=A.lower();A=''.join(A for A in unicodedata.normalize('NFD',A)if unicodedata.category(A)!='Mn');A=' '.join(A.split());A=''.join(A for A in A if A.isalnum()or A.isspace());return A
def is_correct(user_answer,correct_answer,tolerance=1):B=correct_answer;A=user_answer;A=normalize_answer(A);B=normalize_answer(B);C=difflib.SequenceMatcher(_F,A,B).ratio();return C>=tolerance
def display_schemas_page():
	st.title(_o);I=st.text_input('Rechercher un schéma');D=st.selectbox(_AE,domains);J=st.selectbox(_AF,subdomains[D]);E=_F
	if D==_U:E=st.selectbox(_AG,subsystems[J])
	O=load_schemas();B=[A for A in O if A[_L]==D and A[_R]==J and(not E or A[_S]==E)]
	if I:B=search_schemas(B,I)
	if not B:st.info('Aucun schéma disponible pour cette sélection.')
	else:
		F=1;K=(len(B)-1)//F+1;L=st.number_input('Page',min_value=1,max_value=K,value=1);M=(L-1)*F;P=M+F
		for A in B[M:P]:
			with st.container(border=_E):
				st.subheader(A.get(_y,'Sans titre'))
				if'url'in A:st.image(A['url'])
				else:st.error(f"URL manquante pour le schéma : {A.get(_O,'ID inconnu')}")
				N=[]
				for(C,Q)in enumerate(A.get(_d,[])):G=st.text_input(f"Élément {C+1} :",key=f"{A.get(_O,'')}_{C}");N.append(G)
				if st.button('Corriger',key=f"correct_{A.get(_O,'')}"):
					for(C,(G,H))in enumerate(zip(N,A.get(_d,[]))):
						if is_correct(G,H):st.success(f"Élément {C+1}. Correct : {H}")
						else:st.error(f"Élément {C+1}. Incorrect. La bonne réponse est : {H}")
			st.markdown('---')
		st.write(f"Page {L} sur {K}")
def display_support_page():st.title(_q);st.subheader('Vous appréciez la plateforme et la gratuité proposée ? Vous pouvez me soutenir financièrement ici :');st.link_button('Soutenez moi en cliquant ici','https://buymeacoffee.com/maxx.abrt');st.success("Les dons vont entièrement être utilisés dans l'app, pour payer l'hébergement ou alors développer d'autres fonctionnalités !")
def get_messages():A=db[_e];B=A.find({},{_A:1,_b:1,_Q:1});return[(A[_A],A[_b],A[_Q])for A in B]
def get_top_users(limit=10):A=[{'$project':{_i:'$username',_AH:'$points',_D:'$badges'}},{'$sort':{_AH:-1}},{'$limit':limit}];return list(users_collection.aggregate(A))
def display_leaderboard():
	C=get_top_users();st.markdown('## 🏆 Leaderboard');B=[]
	for A in C:D=''.join([A[_C]for A in A[_D].values()if A[_B]>0]);B.append({_AI:A[_i],'Points':A[_AH],'Badges':D})
	E=pd.DataFrame(B);st.table(E)
def update_messages():
	C=get_messages()
	for(A,D)in enumerate(reversed(C)):
		try:B,E,F=D;G=get_user_domain(B);H=F.strftime('%H:%M');I='message new'if A==0 else _b;st.markdown(f"""
            <div class='{I}' id='message-{A}'>
                <span class='username'>{B}</span>
                <span class='domain'>({G})</span>
                <span class='timestamp'>{H}</span>
                <br>{E}
            </div>
            """,unsafe_allow_html=_E);st.markdown('---')
		except ValueError as J:st.error(f"Error processing message: {J}")
def display_chat():
	st.subheader('Chat en direct');st.markdown('\n    <style>\n    .message {\n        padding: 10px;\n        margin-bottom: 10px;\n        border-radius: 10px;\n        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);\n\n    }\n    .message.new {\n        animation: slideIn 0.5s ease-out;\n    }\n    @keyframes slideIn {\n        from {\n            opacity: 0;\n            transform: translateX(-100%);\n        }\n        to {\n            opacity: 1;\n            transform: translateX(0);\n        }\n    }\n    .username {\n        font-weight: bold;\n        color: #2196F3;\n        margin-right: 5px;\n    }\n    .domain {\n        font-style: italic;\n        color: #4CAF50;\n        margin-left: 5px;\n    }\n    .timestamp {\n        font-size: 0.8em;\n        color: #888;\n        float: right;\n    }\n.input-container {\n    display: flex;\n    align-items: center;\n    margin-bottom: 10px;\n}\n.input-container > div {\n    display: flex;\n    flex-grow: 1;\n}\n.input-container .stTextInput {\n    flex-grow: 1;\n}\n.input-container .stButton {\n    margin-left: 10px;\n}\n    </style>\n    ',unsafe_allow_html=_E);C=get_messages();st.write("Discutez en temps réel avec d'autres utilisateurs de la plateforme.");A=st.text_input('Entrez votre message')
	if st.button('Envoyer'):B=db[_e];B.insert_one({_A:st.session_state.username,_b:A,_Q:datetime.now()});st.success('Message envoyé avec succès!')
	st.markdown("\n    <script>\n    function animateNewMessage() {\n        var messages = document.querySelectorAll('.message');\n        if (messages.length > 0) {\n            var latestMessage = messages[0];\n            latestMessage.classList.add('new');\n        }\n    }\n\n    // Animer le dernier message au chargement de la page\n    document.addEventListener('DOMContentLoaded', animateNewMessage);\n    </script>\n    ",unsafe_allow_html=_E);update_messages()
def get_user_domain(username):A=db[_H].find_one({_A:username});return A[_L]if A else'Non spécifié'
def add_message(username,message):A=db[_e];A.insert_one({_A:username,_b:message,_Q:datetime.now()})
def display_account_details(username):B=db[_H];A=B.find_one({_A:username});st.write(f"**Nom d'utilisateur: :blue[{A[_A]}]**");st.write(f"**Domaine: :blue[{A[_L]}]**");st.write(f"**Niveau d'étude: :blue[{A[_AB]}]**");st.write(f"**Points: :blue[{A[_G]}]**");st.write(f"**Points communautaires: :blue[{A[_J]}]**");st.write(f"**QCM complétés: :blue[{A[_I]}]**");st.write(f"**Date d'inscription: :blue[{A[_K]}]**")
def update_community_points(username):A=db[_H];A.update_one({_A:username},{_z:{_J:1}})
def discover_page():
	st.title(_Ae);C=st.text_input(_Af)
	if st.button(_Ag):
		if C:
			F=db[_H];B=list(F.find({_A:{'$regex':C,'$options':'i'}},{_A:1,_G:1,_I:1,_J:1}))
			if B:
				for A in B:
					with st.container():
						st.write(f"**Nom/Pseudo**: **:blue[{A[_A]}]**");st.write(f"**Points Quizz**: **:blue[{A[_G]}]**");st.write(f"**Quizz Completés**: **:blue[{A[_I]}]**");st.write(f"**Points Communautaires** (*nombre de questions soumises aux quizs communautaires*): **:blue[{A[_J]}]**");D=list(users_collection.find({},{_A:1,_G:1,_I:1,_J:1,_K:1,_D:1}));B=random.sample(D,min(20,len(D)))
						for A in B:
							E=''.join([A[_C]for A in A[_D].values()if A[_B]>0])
							if E:st.write(f"**Badges**: {E}")
			else:st.warning(_Ah)
hide_streamlit_style='\n<style>\n#MainMenu {visibility: hidden;}\nfooter {visibility: hidden;}\n</style>\n'
st.markdown(hide_streamlit_style,unsafe_allow_html=_E)
def hash_password(password):return hashlib.sha256(password.encode()).hexdigest()
def verify_user(username,password):A=db[_H];B=hash_password(password);C=A.find_one({_A:username,_n:B});return C is not _F
def get_user_stats(username):
	B=db[_H];A=B.find_one({_A:username},{_G:1,_I:1,_K:1})
	if A:return A[_G],A[_I],A[_K]
	else:return
def update_user_stats(username,points=0,quizzes_completed=0):A=db[_H];A.update_one({_A:username},{_z:{_G:points,_I:quizzes_completed}})
def load_questions(domain,subdomain,subsystem,source):A=db[_P];B=list(A.find({_L:domain,_R:subdomain,_S:subsystem}).sort(_W,1));return B
def add_question_to_json(question,source):A=question;C=db[_P];B=db[_H].find_one({_A:st.session_state.username});A[_r]=B[_A];A[_j]=B[_M];A[_W]=datetime.now();A['likes']=0;A['dislikes']=0;A['reports']=[];A[_An]=generate_unique_question_id(B[_A],B[_M]);C.insert_one(A)
def main():
	Y='count';X='Veuillez vous connecter pour voir vos statistiques.';W='content';V='Mot de passe';M='Réponse correcte';E='date';st.title(':blue[Learn]');A=_F
	if _A not in st.session_state:st.session_state.username=_F
	if st.session_state.username is _F:
		st.write("Bienvenue sur cette plateforme d'apprentissage collaboratif !");st.write(':blue-background[Veuillez remplir le formulaire ci-dessous pour vous **connecter** ou alors vous **inscrire** !]');st.subheader(':blue[Connexion]');H=st.text_input(_AI,key='login_username');Z=st.text_input(V,type=_n,key='login_password')
		if st.button('**:blue[Se connecter]**'):
			if verify_user(H,Z):st.session_state.username=H;st.rerun()
			else:st.error("Nom d'utilisateur ou mot de passe incorrect")
		st.subheader(':green[Inscription]');a=st.text_input(_AI,key='signup_username');b=st.text_input(V,type=_n,key='signup_password');F=st.selectbox("Domaine d'étude",['Médecine','Paramédical','Autre']);c=st.text_input("Niveau d'étude (ex: Première année)")
		if st.button("**:green[S'inscrire]**"):
			if create_user(a,b,F,c):st.success('Compte créé avec succès! Vous pouvez maintenant vous connecter.')
			else:st.error("Ce nom d'utilisateur existe déjà")
		st.write('Le projet suivant a pour but de proposer une plateforme de :blue[collaboration] dans le domaine de la :red[santé], et permettre de réviser tous ensemble des **quiz**, des **schémas**, et partager ses **ressources**');st.write('---');display_leaderboard()
	else:A=create_sidebar()
	if A==_c:st.session_state.page=_c;display_help_button(_c);st.title('Bienvenue sur Learn');st.success(f"Bonjour, **{st.session_state.username}**!");st.write(f"Bienvenue sur cette plateforme d'apprentissage collaboratif ! Le principe est de pouvoir réviser à plusieurs, créer des questions et des Qcm communautaires, et s'entraider dans le domaine de la santé !");st.write("*Le développement est toujours actif, n'hésitez pas à contacter le développeur en cas de retour ou problème !*");st.write(f"Vous pouvez naviguer sur le site grâce à la side bar, elle est **:red[accessible en ouvrant la flèche en haut à gauche]** : ");st.image('arrow.png');display_leaderboard()
	elif A==_q:display_help_button(_q,W);display_support_page()
	elif A==_o:display_help_button(_o,W);display_schemas_page()
	elif A==_p:display_help_button(_p);display_add_schema_page()
	elif A==_Ak:st.session_state.username=_F;st.success('Vous avez été déconnecté.');st.rerun()
	if A==_AD:display_custom_qcm_page()
	if A==_AC:
		st.header('Tableau de Bord - Stats');B=st.session_state.get(_A)
		if not B:st.warning(X);return
		C=users_collection.find_one({_A:B})
		if not C:st.warning(_Ai);return
		D=pd.DataFrame(list(quiz_interactions_collection.find({_M:B})))
		if D.empty:st.warning('Aucune interaction de quiz trouvée pour cet utilisateur.');return
		d=C.get(_I,0);e=C.get(_G,0);f=C.get(_J,0);N=D[_A8].apply(lambda x:list(x.keys())).explode().value_counts();g=pd.to_datetime('today').date();h=g-timedelta(days=7);D[E]=pd.to_datetime(D[_Q]).dt.date;J=D[D[E]>=h];i=J.groupby(E).size().reset_index(name=Y);j=J.groupby(E)[_A8].count().cumsum().reset_index(name=_G);K,O=st.columns(2)
		with K:st.metric('Nombre Total de Quiz',d);st.metric('Points Totaux aux Quiz',e);st.metric('Domaine le plus révisé',N.idxmax());st.metric('Points communautaires',f)
		with O:st.write('**Quiz complétés sur les 7 derniers jours :**');st.line_chart(i.set_index(E)[Y])
		with K:st.write('**Les domaines les plus travaillés :**');st.bar_chart(N)
		with O:st.write('**Les sous domaines et points cumulés de la semaine :**');k=J['subdomains'].apply(lambda x:list(x.keys())).explode().value_counts();st.bar_chart(k)
		with K:st.write('**Évolution des points cumulés de la semaine :**');st.area_chart(j.set_index(E)[_G])
		display_advice()
	if A==_t:
		display_help_button(_t)
		if _A not in st.session_state or st.session_state.username is _F:st.warning('Vous devez être connecté pour pouvoir créer une question.')
		else:
			F=st.selectbox(_AE,domains);P=st.selectbox(_AF,subdomains[F])
			if F==_U:Q=st.selectbox(_AG,subsystems[P])
			else:Q=_F
			I=st.selectbox('Type de question',[_h,_A4,_Aa]);R=st.text_area('Question');st.write('⬆ Le champ question est à remplir :red[obligatoirement] ⬆');l=st.slider('Sélectionnez la difficulté de la question (:green[1 = simple] et :red[ 5 = très complexe ou piègeuse] )',1,5,value=1)
			if I==_h:
				G=[]
				for m in range(4):n=st.text_input(f"Option {m+1}");G.append(n)
				L=st.selectbox(M,G)
			elif I==_A4:G=['Vrai','Faux'];L=st.selectbox(M,G)
			else:L=st.text_input(M)
			o=st.text_area('Explication')
			if R.strip():
				if st.button('Soumettre la question'):p={_L:F,_R:P,_S:Q,_k:I,_T:R,_A3:G if I==_h else _F,_A5:L,'explanation':o,'difficulty':l};add_question_to_json(p,'community');H=st.session_state.username;q=db[_H];q.update_one({_A:H},{_z:{_J:1}});st.success('Question ajoutée et points de contribution mis à jour!')
			else:st.error("La question ne peut pas être vide (Le champ **:blue[Question]** tout au dessus, ensuite remplissez vos champs d'entrée et configurez votre question).")
	if A==_v:display_help_button(_v);display_chat()
	elif A==_x:
		B=st.session_state.get(_A)
		if not B:st.warning(X);return
		C=users_collection.find_one({_A:B});display_help_button(_x)
		if st.session_state.username:
			with st.container(border=_E):
				display_account_details(st.session_state.username);S=list(users_collection.find({},{_A:1,_M:1,_G:1,_I:1,_J:1,_K:1,_D:1}));r=random.sample(S,min(20,len(S)))
				for T in r:
					U=''.join([A[_C]for A in T[_D].values()if A[_B]>0])
					if U:st.write(f"**Badges**: {U}")
		with st.container(border=_E):display_badge_progress(C)
		B=T.get(_M,_A2)
		with st.expander('Infos pour les nerds 🤓 :'):st.info(f"Session ID: {get_session_id()}");st.info(f"User ID : {B}")
	if A==_w:display_help_button(_w);display_user_cards()
	if A==_A7:display_recueil_questions_page()
if __name__=='__main__':setup_cloudinary();main()