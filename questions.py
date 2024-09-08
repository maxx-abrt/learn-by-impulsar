import streamlit as st
import random

# Définition des systèmes anatomiques et leurs composants
systemes = {
    "Système osseux": {
        "Crâne": ["Frontal", "Pariétal", "Temporal", "Occipital", "Sphénoïde", "Ethmoïde"],
        "Colonne vertébrale": ["Cervicales", "Thoraciques", "Lombaires", "Sacrum", "Coccyx"],
        "Cage thoracique": ["Sternum", "Côtes", "Vertèbres thoraciques"],
        "Membres supérieurs": ["Humérus", "Radius", "Cubitus", "Carpe", "Métacarpe", "Phalanges"],
        "Membres inférieurs": ["Fémur", "Tibia", "Péroné", "Tarse", "Métatarse", "Phalanges"]
    },
    "Système digestif": {
        "Tube digestif": ["Bouche", "Œsophage", "Estomac", "Intestin grêle", "Gros intestin", "Rectum", "Anus"],
        "Organes annexes": ["Foie", "Vésicule biliaire", "Pancréas"],
        "Glandes salivaires": ["Parotide", "Sous-maxillaire", "Sublinguale"]
    },
    "Système respiratoire": {
        "Voies aériennes supérieures": ["Nez", "Pharynx", "Larynx"],
        "Voies aériennes inférieures": ["Trachée", "Bronches", "Poumons", "Alvéoles pulmonaires"]
    },
    "Système cardiovasculaire": {
        "Cœur": ["Oreillette droite", "Ventricule droit", "Oreillette gauche", "Ventricule gauche"],
        "Vaisseaux sanguins": ["Artères", "Veines", "Capillaires"],
        "Circulation": ["Circulation pulmonaire", "Circulation systémique"]
    },
    "Système nerveux": {
        "Système nerveux central": ["Cerveau", "Moelle épinière"],
        "Système nerveux périphérique": ["Nerfs crâniens", "Nerfs rachidiens"],
        "Système nerveux autonome": ["Sympathique", "Parasympathique"]
    }
}

# Questions et réponses pour chaque système et sous-système
questions = {
    "Système osseux": {
        "Crâne": [
            {"question": "Combien d'os composent le crâne adulte ?", "reponse": "22"},
            {"question": "Quel os forme le front ?", "reponse": "Frontal"},
            {"question": "Nommez les deux os pariétaux.", "reponse": "Pariétal gauche et droit"},
            {"question": "Quel os contient la cochlée de l'oreille interne ?", "reponse": "Temporal"},
            {"question": "Quel os forme la base du crâne ?", "reponse": "Sphénoïde"},
            {"question": "Quel os forme la partie postérieure et inférieure du crâne ?", "reponse": "Occipital"},
            {"question": "Quel os forme la cloison nasale ?", "reponse": "Ethmoïde"},
            {"question": "Combien de sinus paranasaux y a-t-il ?", "reponse": "4"},
            {"question": "Quel os contient la selle turcique qui abrite l'hypophyse ?", "reponse": "Sphénoïde"},
            {"question": "Quel est le seul os mobile du crâne ?", "reponse": "Mandibule"},
            {"question": "Quel os forme le palais dur ?", "reponse": "Maxillaire et palatin"},
            {"question": "Où se trouve le foramen magnum ?", "reponse": "Os occipital"},
            {"question": "Quel os contient les sinus frontaux ?", "reponse": "Frontal"},
            {"question": "Quel os forme les pommettes ?", "reponse": "Zygomatique"},
            {"question": "Quel os forme la partie supérieure de l'orbite ?", "reponse": "Frontal"}
        ],
        "Colonne vertébrale": [
            {"question": "Combien de vertèbres cervicales y a-t-il ?", "reponse": "7"},
            {"question": "Combien de vertèbres thoraciques y a-t-il ?", "reponse": "12"},
            {"question": "Combien de vertèbres lombaires y a-t-il ?", "reponse": "5"},
            {"question": "Quelle est la fonction principale du sacrum ?", "reponse": "Transfert du poids du tronc aux membres inférieurs"},
            {"question": "Combien de vertèbres fusionnées forment le sacrum ?", "reponse": "5"},
            {"question": "Combien de vertèbres fusionnées forment le coccyx ?", "reponse": "4"},
            {"question": "Quelle est la première vertèbre cervicale ?", "reponse": "Atlas"},
            {"question": "Quelle est la deuxième vertèbre cervicale ?", "reponse": "Axis"},
            {"question": "Quelle est la courbure de la colonne cervicale ?", "reponse": "Lordose"},
            {"question": "Quelle est la courbure de la colonne thoracique ?", "reponse": "Cyphose"},
            {"question": "Quelle est la courbure de la colonne lombaire ?", "reponse": "Lordose"},
            {"question": "Quel est le nom du disque fibro-cartilagineux entre les vertèbres ?", "reponse": "Disque intervertébral"},
            {"question": "Quelle structure passe à l'intérieur du canal vertébral ?", "reponse": "Moelle épinière"},
            {"question": "Quelle vertèbre est aussi appelée 'vertèbre proéminente' ?", "reponse": "C7"},
            {"question": "Quel ligament relie les processus épineux des vertèbres ?", "reponse": "Ligament supra-épineux"}
        ]
    },
    "Système digestif": {
        "Tube digestif": [
            {"question": "Quelle est la longueur approximative de l'intestin grêle ?", "reponse": "6-7 mètres"},
            {"question": "Où se produit la majorité de l'absorption des nutriments ?", "reponse": "Intestin grêle"},
            {"question": "Quel est le rôle principal de l'estomac ?", "reponse": "Stockage temporaire et début de la digestion des protéines"},
            {"question": "Quelle est la fonction principale de l'œsophage ?", "reponse": "Transport des aliments de la bouche à l'estomac"},
            {"question": "Quel sphincter sépare l'œsophage de l'estomac ?", "reponse": "Sphincter œsophagien inférieur"},
            {"question": "Quelle partie de l'intestin grêle est directement connectée à l'estomac ?", "reponse": "Duodénum"},
            {"question": "Quelle est la fonction principale du gros intestin ?", "reponse": "Absorption de l'eau et formation des selles"},
            {"question": "Où se trouve l'appendice ?", "reponse": "Attaché au cæcum"},
            {"question": "Quel est le nom de la valve entre l'intestin grêle et le gros intestin ?", "reponse": "Valve iléo-cæcale"},
            {"question": "Quelle hormone stimule la sécrétion d'acide gastrique ?", "reponse": "Gastrine"},
            {"question": "Quel est le pH approximatif de l'estomac ?", "reponse": "1-2"},
            {"question": "Quelle est la fonction des villosités intestinales ?", "reponse": "Augmenter la surface d'absorption"},
            {"question": "Quel type de tissu recouvre l'intérieur du tube digestif ?", "reponse": "Muqueuse"},
            {"question": "Quelle est la fonction du péristaltisme ?", "reponse": "Propulser le contenu du tube digestif"},
            {"question": "Quelle partie du tube digestif est responsable de la défécation ?", "reponse": "Rectum et anus"}
        ],
        "Organes annexes": [
            {"question": "Quelle est la fonction principale du foie dans la digestion ?", "reponse": "Production de bile"},
            {"question": "Où est stockée la bile ?", "reponse": "Vésicule biliaire"},
            {"question": "Quelles sont les deux principales fonctions du pancréas ?", "reponse": "Production d'enzymes digestives et d'hormones (insuline, glucagon)"},
            {"question": "Quel est le rôle de la bile dans la digestion ?", "reponse": "Émulsification des graisses"},
            {"question": "Quelle enzyme pancréatique digère les protéines ?", "reponse": "Trypsine"},
            {"question": "Quelle hormone pancréatique régule la glycémie ?", "reponse": "Insuline"},
            {"question": "Combien de lobes a le foie ?", "reponse": "4"},
            {"question": "Quel est le nom du conduit qui relie le foie à la vésicule biliaire ?", "reponse": "Canal cystique"},
            {"question": "Quelle est la fonction des cellules de Kupffer dans le foie ?", "reponse": "Phagocytose des débris cellulaires et des bactéries"},
            {"question": "Quel nutriment est stocké dans le foie sous forme de glycogène ?", "reponse": "Glucose"},
            {"question": "Quelle partie du pancréas produit les hormones ?", "reponse": "Îlots de Langerhans"},
            {"question": "Quel est le nom du conduit principal du pancréas ?", "reponse": "Canal de Wirsung"},
            {"question": "Quelle enzyme pancréatique digère les lipides ?", "reponse": "Lipase"},
            {"question": "Quel est le rôle du foie dans le métabolisme des protéines ?", "reponse": "Synthèse des protéines plasmatiques"},
            {"question": "Quelle hormone stimule la contraction de la vésicule biliaire ?", "reponse": "Cholécystokinine"}
        ]
    },
    "Système respiratoire": {
        "Voies aériennes supérieures": [
            {"question": "Quelle est la fonction du larynx autre que le passage de l'air ?", "reponse": "Production de la voix"},
            {"question": "Où se situe l'épiglotte et quelle est sa fonction ?", "reponse": "Au-dessus du larynx, empêche les aliments d'entrer dans les voies respiratoires"},
            {"question": "Quel est le rôle des cornets nasaux ?", "reponse": "Réchauffer, humidifier et filtrer l'air inspiré"},
            {"question": "Quelle structure sépare les fosses nasales ?", "reponse": "Septum nasal"},
            {"question": "Quel est le nom des cordes vocales ?", "reponse": "Plis vocaux"},
            {"question": "Quelle est la fonction des sinus paranasaux ?", "reponse": "Alléger le crâne et résonner la voix"},
            {"question": "Quel muscle principal est responsable de la déglutition ?", "reponse": "Muscle constricteur du pharynx"},
            {"question": "Quelle est la fonction des amygdales ?", "reponse": "Défense immunitaire"},
            {"question": "Quel cartilage forme la pomme d'Adam ?", "reponse": "Cartilage thyroïde"},
            {"question": "Quelle est la fonction des cils dans les voies respiratoires ?", "reponse": "Piéger et éliminer les particules"},
            {"question": "Quel nerf contrôle les mouvements de la langue ?", "reponse": "Nerf hypoglosse"},
            {"question": "Quelle est la fonction de la luette ?", "reponse": "Fermer le nasopharynx pendant la déglutition"},
            {"question": "Quel est le nom de l'ouverture entre les cordes vocales ?", "reponse": "Glotte"},
            {"question": "Quelle est la fonction de la trompe d'Eustache ?", "reponse": "Équilibrer la pression dans l'oreille moyenne"},
            {"question": "Quel muscle abaisse l'épiglotte pendant la déglutition ?", "reponse": "Muscle ary-épiglottique"}
        ],
        "Voies aériennes inférieures": [
            {"question": "Combien de lobes ont les poumons (droit et gauche) ?", "reponse": "3 lobes à droite, 2 lobes à gauche"},
            {"question": "Où se produit l'échange gazeux ?", "reponse": "Dans les alvéoles pulmonaires"},
            {"question": "Quel est le rôle du surfactant pulmonaire ?", "reponse": "Réduire la tension superficielle dans les alvéoles pour faciliter la respiration"},
            {"question": "Quelle est la structure qui sépare les deux poumons ?", "reponse": "Médiastin"},
            {"question": "Quel muscle est le principal responsable de l'inspiration ?", "reponse": "Diaphragme"},
            {"question": "Quelle est la fonction de la plèvre ?", "reponse": "Faciliter le glissement des poumons pendant la respiration"},
            {"question": "Combien de divisions principales (bronches souches) la trachée a-t-elle ?", "reponse": "2"},
            {"question": "Quel gaz est principalement échangé dans les alvéoles ?", "reponse": "Oxygène et dioxyde de carbone"},
            {"question": "Quelle est la capacité pulmonaire totale moyenne d'un adulte ?", "reponse": "Environ 6 litres"},
            {"question": "Quel est le nom de la membrane qui entoure les poumons ?", "reponse": "Plèvre"},
            {"question": "Quelle est la fonction des muscles intercostaux ?", "reponse": "Aider à l'inspiration et à l'expiration"},
            {"question": "Quel est le nom du passage entre le pharynx et le larynx ?", "reponse": "Laryngopharynx"},
            {"question": "Quelle est la fonction des cellules caliciformes dans les voies respiratoires ?", "reponse": "Produire du mucus"},
            {"question": "Quel est le nom du muscle qui forme le plancher de la cavité buccale ?", "reponse": "Muscle mylo-hyoïdien"},
            {"question": "Quelle est la pression négative normale dans la cavité pleurale ?", "reponse": "Environ -5 cm H2O"}
        ]
    },
    "Système cardiovasculaire": {
        "Cœur": [
            {"question": "Quelle est la fonction principale du cœur ?", "reponse": "Pomper le sang"},
            {"question": "Combien de chambres compte le cœur humain ?", "reponse": "4"},
            {"question": "Quel est le nom de la valve entre l'oreillette gauche et le ventricule gauche ?", "reponse": "Valve mitrale"},
            {"question": "Quelle partie du cœur est responsable de l'initiation du battement cardiaque ?", "reponse": "Nœud sinusal"},
            {"question": "Quel vaisseau transporte le sang du ventricule droit aux poumons ?", "reponse": "Artère pulmonaire"},
            {"question": "Quelle est la fonction du péricarde ?", "reponse": "Protéger et lubrifier le cœur"},
            {"question": "Quel est le nom de la valve entre le ventricule droit et l'artère pulmonaire ?", "reponse": "Valve pulmonaire"},
            {"question": "Quelle est la fonction des cordages tendineux ?", "reponse": "Empêcher le prolapsus des valves auriculo-ventriculaires"},
            {"question": "Quel est le nom du tissu qui sépare les oreillettes des ventricules ?", "reponse": "Septum auriculo-ventriculaire"},
            {"question": "Quelle artère nourrit le muscle cardiaque ?", "reponse": "Artère coronaire"},
            {"question": "Quel est le nom du faisceau qui conduit l'impulsion électrique des oreillettes aux ventricules ?", "reponse": "Faisceau de His"},
            {"question": "Quelle hormone augmente la fréquence cardiaque ?", "reponse": "Adrénaline"},
            {"question": "Quel est le volume moyen de sang éjecté par le ventricule gauche à chaque battement ?", "reponse": "70-80 ml"},
            {"question": "Quelle est la fréquence cardiaque moyenne au repos chez un adulte ?", "reponse": "60-100 battements par minute"},
            {"question": "Quel est le nom de la couche musculaire du cœur ?", "reponse": "Myocarde"}
        ],
        "Vaisseaux sanguins": [
            {"question": "Quel type de vaisseau sanguin transporte le sang du cœur vers les organes ?", "reponse": "Artères"},
            {"question": "Quelle est la plus grande artère du corps humain ?", "reponse": "Aorte"},
            {"question": "Où se produit l'échange de nutriments et de gaz entre le sang et les tissus ?", "reponse": "Capillaires"},
            {"question": "Quelle est la fonction des valvules dans les veines ?", "reponse": "Empêcher le reflux sanguin"},
            {"question": "Quel vaisseau sanguin a les parois les plus épaisses ?", "reponse": "Artères"},
            {"question": "Quelle est la fonction de l'endothélium dans les vaisseaux sanguins ?", "reponse": "Réguler les échanges et le tonus vasculaire"},
            {"question": "Quel type de vaisseau sanguin a le plus grand diamètre total combiné ?", "reponse": "Capillaires"},
            {"question": "Quelle est la principale différence entre les artères et les veines ?", "reponse": "La direction du flux sanguin et la structure de la paroi"},
            {"question": "Quel est le nom des plus petites artères ?", "reponse": "Artérioles"},
            {"question": "Quelle est la fonction des sphincters précapillaires ?", "reponse": "Réguler le flux sanguin dans les capillaires"},
            {"question": "Quel type de tissu compose principalement la paroi des artères ?", "reponse": "Tissu musculaire lisse et tissu élastique"},
            {"question": "Quelle est la pression sanguine moyenne normale chez un adulte ?", "reponse": "120/80 mmHg"},
            {"question": "Quel est le nom du réseau de capillaires dans les reins ?", "reponse": "Glomérule"},
            {"question": "Quelle est la fonction des anastomoses artério-veineuses ?", "reponse": "Réguler la température corporelle"},
            {"question": "Quel est le nom du liquide qui s'échappe des capillaires dans les tissus ?", "reponse": "Liquide interstitiel"}
        ],
        "Circulation": [
            {"question": "Quel côté du cœur pompe le sang vers les poumons ?", "reponse": "Droit"},
            {"question": "Quel vaisseau transporte le sang oxygéné des poumons vers le cœur ?", "reponse": "Veine pulmonaire"},
            {"question": "Qu'est-ce que la circulation systémique ?", "reponse": "Circulation du sang dans tout le corps"},
            {"question": "Quelle est la fonction principale de la circulation pulmonaire ?", "reponse": "Oxygénation du sang"},
            {"question": "Quel organe reçoit le plus grand pourcentage du débit cardiaque au repos ?", "reponse": "Reins"},
            {"question": "Qu'est-ce que le système porte hépatique ?", "reponse": "Circulation spéciale entre l'intestin et le foie"},
            {"question": "Quelle est la fonction de la circulation lymphatique ?", "reponse": "Retourner le liquide interstitiel dans le sang"},
            {"question": "Quel facteur influence principalement la pression artérielle ?", "reponse": "Résistance périphérique et débit cardiaque"},
            {"question": "Qu'est-ce que la microcirculation ?", "reponse": "Circulation dans les plus petits vaisseaux (artérioles, capillaires, veinules)"},
            {"question": "Quelle est la fonction des shunts artério-veineux ?", "reponse": "Réguler le flux sanguin dans certains organes"},
            {"question": "Qu'est-ce que le temps de circulation ?", "reponse": "Temps nécessaire pour qu'une molécule fasse un tour complet du système circulatoire"},
            {"question": "Quel est le rôle de la circulation coronaire ?", "reponse": "Apporter du sang au muscle cardiaque"},
            {"question": "Qu'est-ce que la circulation collatérale ?", "reponse": "Voies de circulation alternatives en cas d'obstruction"},
            {"question": "Quel est le rôle de la circulation cérébrale ?", "reponse": "Apporter du sang au cerveau"},
            {"question": "Qu'est-ce que l'effet Windkessel ?", "reponse": "Amortissement de la pulsation du flux sanguin par l'élasticité des grosses artères"}
        ]
    },
    "Système nerveux": {
        "Système nerveux central": [
            {"question": "Quelle est la principale fonction du cerveau ?", "reponse": "Traiter les informations et contrôler les fonctions corporelles"},
            {"question": "Quel lobe du cerveau est principalement responsable de la vision ?", "reponse": "Occipital"},
            {"question": "Quelle est la fonction principale du liquide céphalo-rachidien ?", "reponse": "Protection contre les chocs"},
            {"question": "Quelle partie du cerveau est responsable de l'équilibre et de la coordination ?", "reponse": "Cervelet"},
            {"question": "Quelle est la fonction du thalamus ?", "reponse": "Relais et intégration des informations sensorielles"},
            {"question": "Quelle partie du cerveau contrôle les fonctions autonomes comme la respiration ?", "reponse": "Tronc cérébral"},
            {"question": "Qu'est-ce que la substance grise dans le cerveau ?", "reponse": "Corps cellulaires des neurones"},
            {"question": "Quelle est la fonction de l'hypothalamus ?", "reponse": "Régulation de l'homéostasie"},
            {"question": "Quel est le rôle du corps calleux ?", "reponse": "Connecter les deux hémisphères cérébraux"},
            {"question": "Quelle est la fonction de l'hippocampe ?", "reponse": "Formation de nouveaux souvenirs"},
            {"question": "Qu'est-ce que la barrière hémato-encéphalique ?", "reponse": "Barrière sélective entre le sang et le cerveau"},
            {"question": "Quelle est la fonction des méninges ?", "reponse": "Protection du cerveau et de la moelle épinière"},
            {"question": "Quel est le rôle du cortex moteur ?", "reponse": "Contrôle des mouvements volontaires"},
            {"question": "Qu'est-ce que la neuroplasticité ?", "reponse": "Capacité du cerveau à se réorganiser"},
            {"question": "Quelle est la fonction de l'amygdale ?", "reponse": "Traitement des émotions, en particulier la peur"}
        ],
        "Système nerveux périphérique": [
            {"question": "Combien de paires de nerfs crâniens existent chez l'humain ?", "reponse": "12"},
            {"question": "Quel nerf est responsable de la sensation du toucher dans la main ?", "reponse": "Nerf médian"},
            {"question": "Quelle est la fonction principale des nerfs sensitifs ?", "reponse": "Transmettre des informations sensorielles au cerveau"},
            {"question": "Qu'est-ce qu'un ganglion nerveux ?", "reponse": "Groupe de corps cellulaires de neurones hors du SNC"},
            {"question": "Quel nerf contrôle les mouvements de l'œil ?", "reponse": "Nerf oculomoteur"},
            {"question": "Quelle est la différence entre un nerf et un tract ?", "reponse": "Les nerfs sont dans le SNP, les tracts dans le SNC"},
            {"question": "Qu'est-ce que le plexus brachial ?", "reponse": "Réseau de nerfs innervant le bras"},
            {"question": "Quel est le plus long nerf du corps humain ?", "reponse": "Nerf sciatique"},
            {"question": "Quelle est la fonction du nerf vague ?", "reponse": "Innervation parasympathique de nombreux organes"},
            {"question": "Qu'est-ce qu'une synapse ?", "reponse": "Junction entre deux neurones"},
            {"question": "Quel est le rôle de la gaine de myéline ?", "reponse": "Accélérer la transmission de l'influx nerveux"},
            {"question": "Qu'est-ce qu'un neurotransmetteur ?", "reponse": "Molécule chimique transmettant l'information entre neurones"},
            {"question": "Quel nerf est responsable de l'odorat ?", "reponse": "Nerf olfactif"},
            {"question": "Qu'est-ce que le nerf phrénique innerve ?", "reponse": "Le diaphragme"},
            {"question": "Quelle est la fonction des cellules de Schwann ?", "reponse": "Former la gaine de myéline dans le SNP"}
        ],
        "Système nerveux autonome": [
            {"question": "Quelle branche du système nerveux autonome est responsable de la réponse 'combat ou fuite' ?", "reponse": "Sympathique"},
            {"question": "Quel effet le système nerveux parasympathique a-t-il sur le rythme cardiaque ?", "reponse": "Il le diminue"},
            {"question": "Quel neurotransmetteur est principalement utilisé par le système nerveux parasympathique ?", "reponse": "Acétylcholine"},
            {"question": "Quelle est la fonction principale du système nerveux autonome ?", "reponse": "Contrôler les fonctions involontaires"},
            {"question": "Où se trouvent les corps cellulaires des neurones sympathiques préganglionnaires ?", "reponse": "Moelle épinière thoraco-lombaire"},
            {"question": "Quel est l'effet du système sympathique sur la digestion ?", "reponse": "Il la ralentit"},
            {"question": "Quel neurotransmetteur est libéré par les terminaisons nerveuses sympathiques post-ganglionnaires ?", "reponse": "Noradrénaline"},
            {"question": "Quelle est la fonction du système nerveux entérique ?", "reponse": "Contrôler le système digestif"},
            {"question": "Quel effet le système parasympathique a-t-il sur les pupilles ?", "reponse": "Il les contracte"},
            {"question": "Où se trouvent les corps cellulaires des neurones parasympathiques préganglionnaires ?", "reponse": "Tronc cérébral et moelle sacrée"},
            {"question": "Quel est l'effet du système sympathique sur la bronchodilatation ?", "reponse": "Il l'augmente"},
            {"question": "Qu'est-ce que la loi de Cannon ?", "reponse": "Principe de l'innervation réciproque"},
            {"question": "Quel est l'effet du système parasympathique sur la salivation ?", "reponse": "Il l'augmente"},
            {"question": "Quel neurotransmetteur est utilisé dans les ganglions autonomes ?", "reponse": "Acétylcholine"},
            {"question": "Quel est l'effet du système sympathique sur la glycogénolyse hépatique ?", "reponse": "Il l'augmente"}
        ]
    }
}

def is_answer_close(user_answer, correct_answer):
    """
    Vérifie si la réponse de l'utilisateur est proche de la réponse correcte.
    Retourne:
    2 - si la réponse est exacte
    1 - si la réponse est proche
    0 - si la réponse est trop éloignée
    """
    user_answer = user_answer.lower().strip()
    correct_answer = correct_answer.lower().strip()
    
    if user_answer == correct_answer:
        return 2
    
    # Diviser les réponses en mots
    user_words = set(user_answer.split())
    correct_words = set(correct_answer.split())
    
    # Vérifier si au moins la moitié des mots sont corrects ou proches
    correct_word_count = sum(1 for word in user_words if any(levenshtein_distance(word, correct_word) <= 2 for correct_word in correct_words))
    
    if correct_word_count >= len(correct_words) / 2:
        return 1
    
    return 0

def qcm_quiz(systeme, sous_systeme):
    st.subheader(f"QCM et Quiz : {systeme} - {sous_systeme}")
    
    if systeme in questions and sous_systeme in questions[systeme]:
        user_answers = {}
        for i, q in enumerate(questions[systeme][sous_systeme]):
            st.write(f"Question {i+1}: {q['question']}")
            user_answers[i] = st.text_input(f"Votre réponse pour la question {i+1}", key=f"q{i}")
        
        if st.button("Vérifier les réponses"):
            score = 0
            for i, q in enumerate(questions[systeme][sous_systeme]):
                answer_score = is_answer_close(user_answers[i], q['reponse'])
                if answer_score == 2:
                    st.success(f"Question {i+1}: Correct ! (1 point)")
                    score += 1
                elif answer_score == 1:
                    st.warning(f"Question {i+1}: Proche. La bonne réponse est : {q['reponse']} (0.5 point)")
                    score += 0.5
                else:
                    st.error(f"Question {i+1}: Incorrect. La bonne réponse est : {q['reponse']} (0 point)")
            st.write(f"Votre score : {score}/{len(questions[systeme][sous_systeme])}")

# Page principale
st.title("Révisions Anatomiques et QCM")

choix = st.sidebar.radio("Choisissez votre mode de révision", ["QCM et Quizz"])

systeme = st.selectbox("Choisissez un système pour le QCM", list(questions.keys()))
sous_systeme = st.selectbox("Choisissez une partie spécifique", list(questions[systeme].keys()))
qcm_quiz(systeme, sous_systeme)

st.sidebar.markdown("Application de révision anatomique")