import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)


def load_local_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_local_env()


@app.route('/')
def index():
    return render_template('Ai.html')

@app.route('/Ai', methods=['POST'])
def Ai():
    user_message = request.form['message']
    ai_response = get_ai_response(user_message)  # call Groq API
    return render_template('Ai.html', user_message=user_message, ai_response=ai_response)

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_offline_response(user_message):
    text = (user_message or "").strip().lower()
    if not text:
        return "Please type a message and I will help you."
    if text in {"hi", "hii", "hello", "hey"}:
        return "Hi! I am ready to help. Ask me anything."
    return (
        "I am running in offline mode right now.\n"
        f"You said: {user_message}"
    )


def call_groq(headers, data):
    # Attempt 1: use current system proxy/network settings.
    try:
        return requests.post(API_URL, headers=headers, json=data, timeout=20)
    except requests.exceptions.ProxyError:
        # Attempt 2: bypass environment proxy settings.
        with requests.Session() as session:
            session.trust_env = False
            return session.post(API_URL, headers=headers, json=data, timeout=20)


def get_ai_response(user_message):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return get_offline_response(user_message)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = call_groq(headers, data)
    except requests.exceptions.RequestException:
        return get_offline_response(user_message)

    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            return get_offline_response(user_message)

    return get_offline_response(user_message)


if __name__ == "__main__":
    app.run(debug=True)
