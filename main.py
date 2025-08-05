from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Você é um assistente educacional do curso Rico por Conta Própria."},
        {"role": "user", "content": "O que é renda fixa?"}
    ],
    temperature=0.7
)


print(response.choices[0].message.content)
