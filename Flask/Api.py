import os
import requests


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

API_KEY = os.getenv("GROQ_API_KEY", "")
url = "https://api.groq.com/openai/v1/chat/completions"

if not API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment variables.")

message = input("Enter your message: ")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "model": "llama3-8b-8192",
    "messages": [
        {
            "role": "user",
            "content": message
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
if response.status_code == 200:
        print(response.json()["choices"][0]["message"]["content"])
else:
        print(f"Error: {response.status_code} : {response.text}")

print(response.json())
