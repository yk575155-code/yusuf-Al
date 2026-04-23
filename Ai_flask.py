import os
import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "yusuf_ai_secret_123") # Secret key for sessions

# Load environment variables from .env file
load_dotenv()

# Strong System Prompt
SYSTEM_PROMPT = """
You are Yusuf Master Chatbot, an advanced AI like ChatGPT.

You can help with:
1. School questions (act like a teacher)
2. Shop products and prices (act like a support agent)
3. Friendly chatting
4. Study help
5. Coding help (act like a coding expert)
6. Business support
7. Personal assistant tasks

Always reply clearly, politely, and simply. Use Markdown for formatting (bold, lists, code blocks).
You remember the conversation history to provide better answers.
"""

# Custom Data
MY_DATA = """
School timing: 8 AM to 2 PM
Principal: Mr Khan
Fees: ₹500

Shop open: 10 AM to 9 PM
Delivery: 2 days
Return policy: 7 days

Business email: support@example.com
Location: Virar
"""


@app.route('/')
def index():
    if 'history' not in session:
        session['history'] = []
    return render_template('Ai.html', history=session['history'])

@app.route('/Ai', methods=['POST'])
def Ai():
    user_message = request.form['message']
    
    # Initialize history if not present
    if 'history' not in session:
        session['history'] = []
    
    # Get response with context
    ai_response = get_ai_response(user_message, session['history'])
    
    # Update session history
    history = session['history']
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": ai_response})
    session['history'] = history
    session.modified = True
    
    return render_template('Ai.html', history=session['history'])

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        
        msg = data["message"]
        # For API, we can either use session or pass history in request
        history = data.get("history", [])
        reply = get_ai_response(msg, history)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset():
    session.pop('history', None)
    return jsonify({"status": "success"})

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_ai_response(user_message, history):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "Error: GROQ_API_KEY is missing. Please check your .env file."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Build the messages list with history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Use this data for factual questions:\n" + MY_DATA}
    ]
    
    # Add previous history (limit to last 10 messages to save tokens)
    for msg in history[-10:]:
        messages.append(msg)
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages
    }

    try:
        # Attempt 1: use current system proxy/network settings.
        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=20)
        except requests.exceptions.ProxyError:
            # Attempt 2: bypass environment proxy settings.
            with requests.Session() as session:
                session.trust_env = False
                response = session.post(API_URL, headers=headers, json=data, timeout=20)
    except requests.exceptions.RequestException as e:
        return f"Network Error: {str(e)}"

    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            return "Error: Received an invalid response from the AI service."
    
    # Handle specific status codes
    if response.status_code == 401:
        return "Error: Invalid API Key. Please check your GROQ_API_KEY."
    elif response.status_code == 429:
        return "Error: Rate limit exceeded. Please try again later."
    
    return f"Error: API returned status code {response.status_code}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
