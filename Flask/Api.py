import os
import requests

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
