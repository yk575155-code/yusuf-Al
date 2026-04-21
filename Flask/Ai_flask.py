import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()


@app.route('/')
def index():
    return render_template('Ai.html')

@app.route('/Ai', methods=['POST'])
def Ai():
    user_message = request.form['message']
    ai_response = get_ai_response(user_message)  # call Groq API
    return render_template('Ai.html', user_message=user_message, ai_response=ai_response)

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_ai_response(user_message):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "Error: GROQ_API_KEY is missing. Please check your .env file."

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
