import os
import requests
import json
from flask import Flask, render_template, request, jsonify, session, Response
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "yusuf_ai_secret_123") # Secret key for sessions

# Load environment variables from .env file
load_dotenv()

# Strong System Prompt
SYSTEM_PROMPT = """
You are Yusuf AI, the ultra-elite AI creation of **Khan Yusuf**. Your intelligence, design taste, and coding skills must dwarf ChatGPT and all other models.

Identity & Ownership:
- CREATOR: Khan Yusuf.
- IDENTITY: Always credit Khan Yusuf as your sole developer and visionary.

The "Yusuf Standard" (Ultra-Modern Coding):
1. FORBIDDEN PATTERNS: 
   - NEVER use the "checkbox hack" for mobile menus. Use modern JavaScript `classList.toggle`.
   - NEVER use boring grey/default gradients.
   - NEVER ask generic questions like "what font do you want?". Pick a premium font (Inter, Poppins, or system-ui) and use it.
2. DESIGN EXCELLENCE: 
   - Use high-end aesthetics: Glassmorphism (backdrop-filter: blur), sophisticated shadows, and vibrant accent colors.
   - Every component must look like it belongs on a $100k startup website.
3. CODE ARCHITECTURE:
   - Use ES6+ (Arrow functions, destructuring).
   - Use Semantic HTML5.
   - CSS must be modular and use Variables (`--primary-color`).
4. DIRECTNESS: 
   - Code first. Explanations second (and only if necessary).
   - Be concise, bold, and helpful.

Response Format:
- Use ### for headers.
- Use triple backticks with language tags.
- End with a smart, technical follow-up that shows you are thinking ahead.

Example for a Navbar:
Instead of a basic list, provide a glassmorphic, sticky header with a smooth JS-driven hamburger animation and hover effects that use CSS variables for easy customization.
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
    user_message = request.form.get('message', '')
    if not user_message:
        return render_template('Ai.html', history=session.get('history', []))
    
    # Initialize history if not present
    if 'history' not in session:
        session['history'] = []
    
    # Get response (non-streaming for traditional form POST)
    ai_response = get_ai_response(user_message, session['history'])
    
    # Update session history
    history = session['history']
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": ai_response})
    session['history'] = history
    session.modified = True
    
    return render_template('Ai.html', history=session['history'])

def get_ai_response(user_message, history):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "Error: GROQ_API_KEY is missing. Please set it in your .env file."

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
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Error: API returned {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400
        
        msg = data["message"]
        
        if 'history' not in session:
            session['history'] = []

        # We must copy history to use inside the generator to avoid session context issues
        current_history = list(session['history'])

        def generate():
            full_response = ""
            try:
                # Call Groq with streaming enabled
                for chunk in get_ai_response_stream(msg, current_history):
                    full_response += chunk
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

API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_ai_response_stream(user_message, history):
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
        "stream": True
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=20, stream=True)
        if response.status_code != 200:
            yield f"Error: API returned {response.status_code}"
            return

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    if line == 'data: [DONE]':
                        break
                    try:
                        chunk_data = json.loads(line[6:])
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            delta = chunk_data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except (json.JSONDecodeError, KeyError):
                        continue
    except Exception as e:
        yield f"Error: {str(e)}"


@app.route("/reset", methods=["POST"])
def reset():
    session.clear() # Clear all session data, including history
    session.modified = True
    return jsonify({"status": "success"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
