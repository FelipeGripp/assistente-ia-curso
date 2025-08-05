import sqlite3
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def buscar_conteudo_relevante(pergunta_embedding, top_k=3):
    conn = sqlite3.connect("vetores.db")
    c = conn.cursor()
    c.execute("SELECT texto, embedding FROM embeddings")
    resultados = c.fetchall()
    conn.close()

    similares = []
    for texto, emb_json in resultados:
        emb = json.loads(emb_json)
        similaridade = cosine_similarity(pergunta_embedding, emb)
        similares.append((similaridade, texto))

    similares.sort(reverse=True)
    return [texto for _, texto in similares[:top_k]]

def responder(pergunta):
    response = client.embeddings.create(
        input=pergunta,
        model="text-embedding-3-small"
    )
    pergunta_emb = response.data[0].embedding

    trechos = buscar_conteudo_relevante(pergunta_emb)

    contexto = "\n\n".join(trechos)
    prompt = f"""
Você é um assistente educacional do curso Rico por Conta Própria. Use o conteúdo abaixo para responder de forma clara e amigável a pergunta do aluno.

CONTEÚDO DO CURSO:
{contexto}

PERGUNTA DO ALUNO:
{pergunta}
"""

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um assistente educacional experiente."},
            {"role": "user", "content": prompt}
        ]
    )

    return resposta.choices[0].message.content
