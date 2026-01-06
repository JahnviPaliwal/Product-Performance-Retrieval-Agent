import openai
import joblib

openai.api_key = "openai-api-key"


# Function to handle user input and extract the intent using GPT
def get_intent_from_gpt(user_input):
    # prompt = f"User asked: {user_input}\n\nWhat is the user's intent? What data is needed to answer this query?"
    #
    # # Query GPT for intent analysis
    # response = openai.Completion.create(
    #     model="text-davinci-003",
    #     prompt=prompt,
    #     max_tokens=100,
    #     temperature=0.5,
    # )
    intent = []
    for i in user_input:
        if 'nps score' in user_input.lower():
            intent[0] = 'nps score'
            intent[0] = 0

        if 'nps score' in user_input.lower():
            intent[0] = 'nps score'
            intent[0] = 0

        if 'nps score' in user_input.lower():
            intent[0] = 'nps score'
            intent[0] = 0

        if 'nps score' in user_input.lower():
            intent[0] = 'nps score'
            intent[0] = 0

        if 'nps score' in user_input.lower():
            intent[0] = 'nps score'
            intent[0] = 0
    return intent


# Detect future/present based on keywords
def detect_time_context(text):
    text = text.lower()
    future_keywords = ["next", "upcoming", "forecast", "projection", "month", "days", "weeks"]
    present_keywords = ["today", "now", "currently", "current", "present"]
    for word in future_keywords:
        if word in text:
            return "future"
    for word in present_keywords:
        if word in text:
            return "present"
    return "present"  # default

# Detect graphical intent based on keywords
def detect_graphical(text):
    text = text.lower()
    graphical_keywords = ["graph", "chart", "trend", "growth", "visual"]
    for word in graphical_keywords:
        if word in text:
            return True
    return False

#this is for v control
def predict_intents_with_time(user_prompt):
    # Load model
    print("1st step")
    model, vectorizer, mlb = joblib.load("../models/multi_intent_full_model.pkl")
    # print("2nd step")
    # Vectorize text
    X_test = vectorizer.transform([user_prompt])

    # Predict intents
    y_pred = model.predict(X_test)
    predicted_intents = list(mlb.inverse_transform(y_pred)[0])

    # Add graphical if detected
    if detect_graphical(user_prompt) and "graphical" not in predicted_intents:
        predicted_intents.append("graphical")

    # Detect time context
    time_context = detect_time_context(user_prompt)

    # Return list of dicts
    result = [{intent: time_context} for intent in predicted_intents]
    # print("3rd step")
    return result




