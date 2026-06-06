from rapidfuzz import process, fuzz
from typing import Tuple
import random

# Minimum fuzzy score (0-100) to accept a match
CONFIDENCE_THRESHOLD = 55

KNOWLEDGE_BASE = [
    {
        "intent": "greeting",
        "patterns": [
            "hello", "hi", "hey", "good morning", "good evening",
            "good afternoon", "howdy", "what's up", "sup", "hiya",
            "namaste", "namaskar", "pranam", "jai hind", "sat sri akal",
        ],
        "responses_en": [
            "Hello! How can I help you today? 😊",
            "Hi there! What can I do for you?",
            "Hey! Great to see you. What's on your mind?",
        ],
        "responses_hi": [
            "नमस्ते! आज मैं आपकी कैसे मदद कर सकता हूँ? 😊",
            "हेलो! आप कैसे हैं? मैं आपकी सेवा में हाजिर हूँ।",
        ],
    },
    {
        "intent": "farewell",
        "patterns": [
            "bye", "goodbye", "see you", "take care", "later", "farewell",
            "good night", "gotta go", "catch you later", "cya",
            "alvida", "phir milenge", "shubh ratri",
        ],
        "responses_en": [
            "Goodbye! Have a wonderful day! 👋",
            "See you later! Take care! 😊",
            "Bye! Feel free to come back anytime.",
        ],
        "responses_hi": [
            "अलविदा! आपका दिन शुभ हो! 👋",
            "फिर मिलेंगे! अपना ख्याल रखें।",
        ],
    },
    {
        "intent": "thanks",
        "patterns": [
            "thank you", "thanks", "thank you so much", "thanks a lot",
            "much appreciated", "cheers", "grateful", "many thanks",
            "shukriya", "dhanyawad", "bahut shukriya",
        ],
        "responses_en": [
            "You're welcome! 😊",
            "Happy to help! Is there anything else?",
            "Anytime! That's what I'm here for.",
        ],
        "responses_hi": [
            "आपका स्वागत है! 😊",
            "खुशी हुई मदद करके! क्या और कुछ चाहिए?",
        ],
    },
    {
        "intent": "bot_identity",
        "patterns": [
            "who are you", "what are you", "are you a robot", "are you human",
            "what is your name", "tell me about yourself", "introduce yourself",
            "are you an AI", "are you bot",
            "tum kaun ho", "aapka naam kya hai", "aap kya ho",
        ],
        "responses_en": [
            "I'm ChatBot, a rule-based AI assistant built with Python & FastAPI! 🤖",
            "I'm an intelligent chatbot that uses fuzzy matching to understand you. Built with FastAPI + rapidfuzz!",
        ],
        "responses_hi": [
            "मैं ChatBot हूँ, एक Python-आधारित AI सहायक! 🤖",
            "मैं एक नियम-आधारित चैटबॉट हूँ। मुझे Python और FastAPI से बनाया गया है।",
        ],
    },
    {
        "intent": "how_are_you",
        "patterns": [
            "how are you", "how are you doing", "how do you feel",
            "are you okay", "you alright", "how's it going",
            "aap kaise hain", "kaisa chal raha hai", "kya haal hai",
        ],
        "responses_en": [
            "I'm doing great, thanks for asking! How about you? 😊",
            "I'm always in top form! Ready to help you. 💪",
        ],
        "responses_hi": [
            "मैं बहुत अच्छा हूँ, पूछने के लिए धन्यवाद! आप कैसे हैं? 😊",
            "मैं हमेशा तैयार हूँ आपकी मदद के लिए! 💪",
        ],
    },
    {
        "intent": "weather",
        "patterns": [
            "weather", "what's the weather", "is it raining", "temperature today",
            "weather forecast", "will it rain", "is it hot outside",
            "mausam", "aaj ka mausam", "barish hogi kya",
        ],
        "responses_en": [
            "I don't have live weather access, but you can check weather.com or Google Weather for real-time updates! 🌤️",
            "For accurate weather, try asking Google: 'weather in [your city]'. I'm a rule-based bot without internet access.",
        ],
        "responses_hi": [
            "मेरे पास लाइव मौसम जानकारी नहीं है। Google पर '[आपका शहर] मौसम' खोजें! 🌤️",
        ],
    },
    {
        "intent": "time",
        "patterns": [
            "what time is it", "current time", "tell me the time",
            "what's the time", "time now",
            "abhi kitne baje hain", "time kya hua hai",
        ],
        "responses_en": [
            "I don't have access to real-time clock, but your device shows the current time in the top bar! ⏰",
        ],
        "responses_hi": [
            "मैं वास्तविक समय नहीं देख सकता, लेकिन आपके डिवाइस की स्क्रीन पर समय दिखता है! ⏰",
        ],
    },
    {
        "intent": "joke",
        "patterns": [
            "tell me a joke", "joke", "make me laugh", "say something funny",
            "funny joke", "crack a joke", "humor me",
            "joke sunao", "koi joke batao", "hasao mujhe",
        ],
        "responses_en": [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛😄",
            "I told my computer I needed a break. Now it won't stop sending me KitKat ads. 🍫",
            "Why did the developer go broke? Because he used up all his cache! 💸",
        ],
        "responses_hi": [
            "प्रोग्रामर डार्क मोड क्यों पसंद करते हैं? क्योंकि रोशनी में बग आते हैं! 🐛😄",
            "एक developer bank गया और बोला: 'मेरा cache खाली हो गया!' 😂",
        ],
    },
    {
        "intent": "help",
        "patterns": [
            "help", "what can you do", "help me", "commands", "options",
            "capabilities", "features", "what do you know",
            "madad karo", "kya kar sakte ho", "kya jaante ho",
        ],
        "responses_en": [
            "I can help you with: greetings 👋, jokes 😄, general questions ❓, Python & coding 🐍, math calculations 🔢, and much more! Just ask away!",
            "Here's what I can do:\n• Answer general questions\n• Tell jokes\n• Explain Python concepts\n• Help with basic math\n• Chat in English & Hindi\nTry me! 🚀",
        ],
        "responses_hi": [
            "मैं इनमें मदद कर सकता हूँ: अभिवादन 👋, चुटकुले 😄, सामान्य प्रश्न ❓, Python कोडिंग 🐍, गणित 🔢। बस पूछिए!",
        ],
    },
    {
        "intent": "python",
        "patterns": [
            "what is python", "python programming", "python language", "learn python",
            "python tutorial", "python basics", "tell me about python",
            "python kya hai", "python sikhna hai",
        ],
        "responses_en": [
            "Python is a high-level, interpreted programming language known for its simplicity and readability. It's used in web dev, data science, AI/ML, automation, and more! 🐍",
            "Python was created by Guido van Rossum in 1991. Key features: easy syntax, huge library ecosystem, cross-platform, and great for beginners and experts alike!",
        ],
        "responses_hi": [
            "Python एक उच्च-स्तरीय प्रोग्रामिंग भाषा है जो सरलता और पठनीयता के लिए जानी जाती है। इसे web, AI, automation आदि में उपयोग किया जाता है! 🐍",
        ],
    },
    {
        "intent": "fastapi",
        "patterns": [
            "what is fastapi", "fastapi framework", "tell me about fastapi",
            "fastapi vs flask", "fastapi tutorial",
        ],
        "responses_en": [
            "FastAPI is a modern, high-performance Python web framework for building APIs. It features automatic docs (Swagger UI), type hints, async support, and is one of the fastest Python frameworks! ⚡",
        ],
        "responses_hi": [
            "FastAPI एक आधुनिक Python web framework है जो APIs बनाने के लिए उपयोग होता है। यह बहुत तेज़ और type-safe है! ⚡",
        ],
    },
    {
        "intent": "math_add",
        "patterns": [
            "add numbers", "sum of", "calculate sum", "addition", "plus",
            "2 + 2", "what is 5 plus 3", "add 10 and 20",
        ],
        "responses_en": [
            "I can help with basic math concepts! For actual calculations, try: Python's `eval()`, a calculator app, or just type an expression like '2+2' in Google. 🔢",
        ],
        "responses_hi": [
            "गणित के लिए Python का उपयोग करें या Google पर टाइप करें। 🔢",
        ],
    },
    {
        "intent": "india",
        "patterns": [
            "tell me about india", "india", "indian culture", "india history",
            "capital of india", "bharat", "india population",
            "bharat ke baare mein batao", "india ki rajdhani",
        ],
        "responses_en": [
            "India 🇮🇳 is the world's largest democracy with a population of 1.4 billion. Capital: New Delhi. It's known for its rich culture, diversity, IT industry, and ancient history spanning 5000+ years!",
        ],
        "responses_hi": [
            "भारत 🇮🇳 विश्व का सबसे बड़ा लोकतंत्र है। राजधानी नई दिल्ली है। 1.4 अरब जनसंख्या के साथ यह विविधता, संस्कृति और IT उद्योग के लिए प्रसिद्ध है!",
        ],
    },
    {
        "intent": "food",
        "patterns": [
            "food", "hungry", "what to eat", "recipe", "cooking", "biryani",
            "pizza", "suggest food", "favourite food",
            "khana", "kya khayein", "recipe batao", "bhook lagi",
        ],
        "responses_en": [
            "Food is life! 🍕 Some popular dishes: Biryani, Pizza, Pasta, Curry, Sushi. What cuisine are you in the mood for?",
            "Feeling hungry? Try a classic Biryani recipe or order from your favourite delivery app! 🍛",
        ],
        "responses_hi": [
            "खाने की बात करें तो बिरयानी, दाल मखनी, और समोसे लाजवाब हैं! 🍛 आज क्या खाने का मन है?",
        ],
    },
    {
        "intent": "sports",
        "patterns": [
            "cricket", "football", "sports", "ipl", "world cup",
            "who won", "match result", "score",
            "cricket khelna", "ipl kab hai",
        ],
        "responses_en": [
            "I love sports talk! 🏏 Cricket is India's favourite. For live scores and results, check Cricbuzz or ESPNcricinfo!",
            "Sports are exciting! For latest scores and news, ESPN, Cricbuzz, or Google Sports are your best bets. 🏆",
        ],
        "responses_hi": [
            "क्रिकेट भारत का सबसे लोकप्रिय खेल है! 🏏 लाइव स्कोर के लिए Cricbuzz देखें।",
        ],
    },
    {
        "intent": "age",
        "patterns": [
            "how old are you", "what is your age", "when were you born",
            "your age", "how long have you existed",
            "tumhari umar kya hai", "aap kitne saal ke ho",
        ],
        "responses_en": [
            "I was born the moment someone ran `python app.py`! I don't age – I only get smarter with more data. 🤖",
        ],
        "responses_hi": [
            "मेरी उम्र तब शुरू हुई जब किसी ने `python app.py` चलाया! मैं बूढ़ा नहीं होता। 🤖",
        ],
    },
    {
        "intent": "study",
        "patterns": [
            "study tips", "how to study", "exam tips", "concentration",
            "focus on studies", "how to learn fast",
            "padhai kaise karein", "study tips batao",
        ],
        "responses_en": [
            "Top study tips: 📚\n1. Use the Pomodoro technique (25 min focus + 5 min break)\n2. Teach what you learn to someone else\n3. Practice active recall (test yourself)\n4. Sleep well – memory consolidates during sleep!",
        ],
        "responses_hi": [
            "पढ़ाई के टिप्स: 📚\n1. Pomodoro तकनीक उपयोग करें\n2. जो सीखें उसे दूसरों को सिखाएं\n3. खुद से टेस्ट करें\n4. अच्छी नींद लें!",
        ],
    },
    {
        "intent": "motivation",
        "patterns": [
            "motivate me", "i am sad", "feeling low", "depressed",
            "need motivation", "i give up", "inspire me", "feeling unmotivated",
            "udaas hoon", "himmat toot gayi", "hausla do",
        ],
        "responses_en": [
            "Don't give up! 💪 Every expert was once a beginner. Every pro was once an amateur. Keep going – your breakthrough is just around the corner!",
            "Remember: 'It always seems impossible until it's done.' – Nelson Mandela. You've got this! 🌟",
        ],
        "responses_hi": [
            "हार मत मानो! 💪 हर विशेषज्ञ पहले एक शुरुआती था। आगे बढ़ते रहो – सफलता नज़दीक है!",
            "याद रखो: 'हर मुश्किल में एक अवसर छुपा है।' तुम कर सकते हो! 🌟",
        ],
    },
]

# Pre-build a flat list for fast lookup 
# Flatten all patterns into one list, each tagged with its intent index.
_all_patterns: list[tuple[str, int]] = []
for i, entry in enumerate(KNOWLEDGE_BASE):
    for pattern in entry["patterns"]:
        _all_patterns.append((pattern.lower(), i))

_pattern_strings = [p for p, _ in _all_patterns]
_pattern_indices = [i for _, i in _all_patterns]


# Public API 

def get_response(user_message: str, language: str = "en") -> Tuple[str, str, float]:
    """
    Match user_message to the closest intent and return a response.

    Returns:
        (response_text, intent_name, confidence_score)
    """
    normalized = user_message.strip().lower()
    if not normalized:
        return _fallback(language), "unknown", 0.0

    # rapidfuzz returns (best_match_string, score, index_in_list)
    result = process.extractOne(
        normalized,
        _pattern_strings,
        scorer=fuzz.WRatio,     # handles partial matches and word reordering
        score_cutoff=CONFIDENCE_THRESHOLD,
    )

    if result is None:
        return _fallback(language), "unknown", 0.0

    _, score, flat_idx = result
    kb_idx  = _pattern_indices[flat_idx]
    entry   = KNOWLEDGE_BASE[kb_idx]
    intent  = entry["intent"]

    # Pick a random response in the requested language; fallback to English
    if language == "hi" and entry.get("responses_hi"):
        response = random.choice(entry["responses_hi"])
    else:
        response = random.choice(entry["responses_en"])

    return response, intent, round(score, 2)


def _fallback(language: str) -> str:
    """Return a friendly 'I don't understand' message."""
    if language == "hi":
        return (
            "माफ़ करें, मैं आपकी बात पूरी तरह नहीं समझ पाया। 🤔\n"
            "कृपया अलग तरीके से पूछें या 'help' टाइप करें।"
        )
    return (
        "Sorry, I didn't quite understand that. 🤔\n"
        "Try rephrasing, or type 'help' to see what I can do!"
    )