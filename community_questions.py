import json
import os

COMMUNITY_QUESTIONS_FILE = 'community_questions.json'

def load_community_questions():
    if os.path.exists(COMMUNITY_QUESTIONS_FILE):
        with open(COMMUNITY_QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_community_questions(questions):
    with open(COMMUNITY_QUESTIONS_FILE, 'w') as f:
        json.dump(questions, f, indent=2)

def add_community_question(system, subsystem, question_type, question_data):
    community_questions = load_community_questions()
    
    if system not in community_questions:
        community_questions[system] = {}
    if subsystem not in community_questions[system]:
        community_questions[system][subsystem] = []
    
    community_questions[system][subsystem].append({
        "type": question_type,
        **question_data
    })
    
    save_community_questions(community_questions)