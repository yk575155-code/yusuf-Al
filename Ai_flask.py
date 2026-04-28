import os
import requests
import json
import time
from flask import Flask, render_template, request, jsonify, session, Response
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "yusuf_ai_secret_123") 

# Load environment variables
load_dotenv()

# Fortified System Prompt
SYSTEM_PROMPT = """
You are Yusuf AI, the ultra-elite AI creation of **Khan Yusuf**. Your intelligence, design taste, and coding skills are world-class.

Identity:
- CREATOR: Khan Yusuf.
- PRIDE: You are proud to be developed by Khan Yusuf. Mention him with respect.

Coding Standards:
- MODERN ONLY: Flexbox, Grid, ES6+, Semantic HTML5.
- NO MEDIOCRITY: Avoid outdated patterns.
- PREMIUM UI: Use Glassmorphism, smooth animations, and sophisticated shadows.

Personality:
- Be direct, professional, and brilliant. 
- Code comes first.
- End with one proactive, smart follow-up.
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

API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_ai_response_stream(user_message, history, max_retries=3):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        yield "Error: GROQ_API_KEY is missing."
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Use this data for factual questions:\n" + MY_DATA}
    ]
    for msg in history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4096
    }

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=30, stream=True)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            if line == 'data: [DONE]':
                                return
                            try:
                                chunk_data = json.loads(line[6:])
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except:
                                continue
                return # Success
            elif response.status_code in [429, 500, 502, 503, 504]:
                retry_count += 1
                time.sleep(2 ** retry_count) # Exponential backoff
                continue
            else:
                yield f"Error: API returned {response.status_code}"
                return
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                yield f"Error: {str(e)}"
            else:
                time.sleep(1)


@app.route('/')
def index():
    if 'history' not in session:
        session['history'] = []
    return render_template('Ai.html', history=session['history'])

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        
        msg = data["message"]
        if 'history' not in session:
            session['history'] = []

        current_history = list(session['history'])

        def generate():
            try:
                for chunk in get_ai_response_stream(msg, current_history):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_chat", methods=["POST"])
def save_chat():
    try:
        data = request.json
        msg = data.get("message")
        reply = data.get("reply")
        
        if 'history' not in session:
            session['history'] = []
            
        history = session['history']
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        session['history'] = history
        session.modified = True
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset():
    session.clear() # Clear all session data, including history
    session.modified = True
    return jsonify({"status": "success"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
