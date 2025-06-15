#finalized without quiz
import nltk
from nltk.corpus import wordnet
import spacy
import language_tool_python
import random
import re
from flask import Flask, request, jsonify, render_template,url_for,redirect
from fuzzywuzzy import process
from textblob import TextBlob,Word


app = Flask(__name__)

# Load necessary resources
nlp = spacy.load("en_core_web_sm")
tool = language_tool_python.LanguageTool('en-US')

def get_word_info_offline(word):
    synonyms = wordnet.synsets(word)
    definitions = [syn.definition() for syn in synonyms]
    lemmas = set(lemma.name() for syn in synonyms for lemma in syn.lemmas())
    antonyms = [antonym.name() for syn in synonyms for lemma in syn.lemmas() if lemma.antonyms() for antonym in lemma.antonyms()]
    examples = [f"Example usage of '{word}': {syn.examples()}" for syn in synonyms]
    return {
        'definition': definitions,
        'synonyms': list(lemmas),
        'antonyms': antonyms,
        'examples': examples
    }
# Function to provide grammar check and writing tips for longer texts
def analyze_text(text):
    # Perform grammar check using LanguageTool
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    
    # Analyze text for writing tips
    writing_tips = []
    
    # Example tips
    # Check for passive voice
    doc = nlp(text)
    if any(token.dep_ == 'nsubjpass' for token in doc):
        writing_tips.append("Consider revising passive constructions to active voice for clarity.")
    
    # Check for overly complex sentences
    if any(len(sent) > 20 for sent in [sent.string.strip() for sent in doc.sents]):
        writing_tips.append("Try to break up long sentences for better readability.")
    
    return {
        'corrected_text': corrected_text,
        'writing_tips': writing_tips,
        'grammar_errors': [match.ruleId for match in matches]
    }
def classify_parts_of_speech_offline(psentence):
    doc = nlp(psentence)
    pos_tags = {token.text: token.pos_ for token in doc}
    return pos_tags

def correct_sentence(csentence):
    matches = tool.check(csentence)
    corrected_text = language_tool_python.utils.correct(csentence, matches)
    return corrected_text

def find_best_response(user_input):
    best_pattern, score = process.extractOne(user_input, patterns)
    if score >= 60:
        index = patterns.index(best_pattern)
        return random.choice(responses[index])  # Return a random response from the list
    else:
        return ["I'm sorry, I don't understand that. Can you please rephrase?"]

pairs = [
    (r"hi|hello|hey", ["Hello!", "Hi there!", "Hey!"]),
    (r"how are you\?", ["I'm doing well, thank you! How can I assist you today?"]),
    (r"what is your name\?", ["I'm a chatbot here to help you with English!"]),
    (r"what can you do\?", ["I can answer questions about grammar, vocabulary, and provide assistance with writing."]),
    (r"define (\w+)|meaning of (\w+)", lambda match: get_word_info_offline(match.group(1) or match.group(2))['definition']),
    (r"synonym of (\w+)", lambda match: get_word_info_offline(match.group(1))['synonyms']),
    (r"antonym of (\w+)", lambda match: get_word_info_offline(match.group(1))['antonyms']),
    (r"what part of speech is (\w+)", lambda match: classify_parts_of_speech_offline(match.group(1))),
    (r"identify the part of speech of (\w+)", lambda match: classify_parts_of_speech_offline(match.group(1))),
    (r"how to use (\w+) in a sentence", lambda match: f"The word '{match.group(1)}' can be used in various ways depending on context."),
    (r"what is the past tense of (\w+)", lambda match: f"The past tense of '{match.group(1)}' is usually formed by adding 'ed', but some verbs are irregular."),
    (r"correct this sentence: (.*)", lambda match: correct_sentence(match.group(1))),
    (r"bye|goodbye|see you later", ["Goodbye! Have a great day!"]),
]

patterns = [pair[0] for pair in pairs]
responses = [pair[1] for pair in pairs]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    output = []

    if user_input.lower() in ["bye", "goodbye", "good night", "exit", "thank you", "stop"]:
        output.append("Chatbot: Goodbye! Have a great day!")
    elif "quiz" in user_input.lower():
        return redirect(url_for('quiz')) 
    elif "correct this sentence" in user_input:
        sentence = extract_sentence(user_input)
        corrected_sentence = correct_sentence(sentence)
        output.append(f"Corrected Sentence: {corrected_sentence}")
    elif "check this text" in user_input.lower():
        # Extract the text after the command
        text_to_check = extract_text(user_input, "check this text")
        if text_to_check:  # Ensure we got some text to check
            analysis_result = analyze_text(text_to_check)
            output.append(f"Corrected Text: {analysis_result['corrected_text']}")
            
            if analysis_result['writing_tips']:
                output.append("Writing Tips: " + ', '.join(analysis_result['writing_tips']))
            else:
                output.append("No specific writing tips available.")
        else:
            output.append("Please provide text after the command.")
    elif "parts of speech of" in user_input:
        sentence=extract_psent(user_input)
        parts_of_speech=classify_parts_of_speech_offline(sentence)
        output.append(f"Parts of speech: {parts_of_speech}")
    elif "synonym of" in user_input:
        word = extract_word(user_input, "synonym of")
        if word:
            info = get_word_info_offline(word)
            output.append(f"Synonyms of '{word}': {', '.join(info['synonyms'])}")
            if info['examples']:
                output.append(f"Examples: {', '.join(info['examples'][:2])}")  # Show two examples
        
        else:
            output.append("Please specify a word for the synonym.")
    elif "antonym of" in user_input:
        word = extract_word(user_input, "antonym of")
        if word:
            info = get_word_info_offline(word)
            output.append(f"Antonyms of '{word}': {', '.join(info['antonyms'])}")
            if info['examples']:
                output.append(f"Examples: {', '.join(info['examples'][:2])}")  # Show two examples
        else:
            output.append("Please specify a word for the antonym.")
     
    elif "define" in user_input:
        word=extract_word(user_input,"define ")
        synsets=wordnet.synsets(word)
        for syn in synsets:
            output.append(f"{syn.definition()}")
        
        
    else:
        response = find_best_response(user_input)
        output.append(response)  # Directly add the response

    return jsonify({'response': output})

def extract_word(request, keyword):
    try:
        return request.split(keyword)[-1].strip()
    except IndexError:
        return None

def extract_sentence(user_input):
    prompt="correct this sentence"
    if prompt in user_input.lower():
        # Split the input to find the sentence to correct
        parts = user_input.split(prompt, 1)
        # Extract the sentence after the prompt, strip whitespace
        sentence = parts[1].strip()
        return sentence
    return None  # Return None if the prompt isn't found
def extract_psent(user_input):

     prompt="parts of speech of"
     if prompt in user_input.lower():
         parts=user_input.split(prompt,1)
         sentence=parts[1].strip()
         return sentence

def extract_text(user_input, keyword):
    """Helper function to extract text after a specific keyword."""
    if keyword in user_input.lower():
        parts = user_input.split(keyword, 1)
        
    return parts[1].strip()  # Return the text after the keyword
      # Return None if the keyword isn't found

verb_word="information about verb"
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found. Please check the URL."

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)
