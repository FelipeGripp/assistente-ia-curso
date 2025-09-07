import os
import psycopg2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Inicializa Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para o frontend acessar

# Configurações do PostgreSQL (Render ou local)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

# Inicializa cliente da OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Conexão com PostgreSQL
def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

# Rota de teste
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API do assistente de IA está rodando com PostgreSQL!"})

# Função para buscar a resposta mais próxima no banco
def buscar_resposta(pergunta):
    # Gera embedding da pergunta
    embedding_pergunta = client.embeddings.create(
        model="text-embedding-3-small",
        input=pergunta
    ).data[0].embedding

    conn = get_connection()
    cur = conn.cursor()

    # Busca todos os embeddings no banco
    cur.execute("SELECT id, texto, embedding FROM embeddings")
    registros = cur.fetchall()

    melhor_id = None
    melhor_texto = None
    melhor_similaridade = -1

    pergunta_vec = np.array(embedding_pergunta)

    for r in registros:
        id_, texto, embedding = r
        vetor_banco = np.array(embedding)  # já está em JSON/array
        sim = np.dot(pergunta_vec, vetor_banco) / (
            np.linalg.norm(pergunta_vec) * np.linalg.norm(vetor_banco)
        )
        if sim > melhor_similaridade:
            melhor_similaridade = sim
            melhor_id = id_
            melhor_texto = texto

    conn.close()

    # Gera resposta final usando GPT
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é o Agente de IA da equipe Rico por Conta Própria, especializado "
                    "em atendimento ao cliente e apoio educacional para alunos do curso sobre investimentos. "
                    "Seu tom é sempre amigável, respeitoso, claro e acessível, como um instrutor paciente "
                    "que entende as dificuldades de quem está começando do zero."
                ),
            },
            {"role": "user", "content": f"Pergunta: {pergunta}\n\nContexto: {melhor_texto}"},
        ],
    )

    return resposta.choices[0].message.content

# Rota para responder perguntas
@app.route("/responder", methods=["POST"])
def responder():
    dados = request.get_json()
    pergunta = dados.get("pergunta")
    if not pergunta:
        return jsonify({"erro": "Campo 'pergunta' é obrigatório"}), 400

    try:
        resposta = buscar_resposta(pergunta)
        return jsonify({"resposta": resposta})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)