from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# -------------------------------
# 1️⃣ Carregar variáveis de ambiente
# -------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# -------------------------------
# 2️⃣ Conexão com o MongoDB Atlas
# -------------------------------
MONGO_URI = os.getenv("MONGO_URI")  # Adicione essa variável no seu .env
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["assistenteIA"]
aulas_collection = db["aulas"]

# -------------------------------
# 3️⃣ Configuração do OpenAI
# -------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# 4️⃣ Função utilitária — Buscar aula no banco
# -------------------------------
def buscar_aula_no_banco(pergunta):
    """Procura no MongoDB uma aula que tenha o tema relacionado à pergunta."""
    resultados = aulas_collection.find()
    melhor_correspondencia = None

    for aula in resultados:
        titulo = aula.get("titulo", "").lower()
        conteudo = aula.get("conteudo", "").lower()
        if any(p in conteudo or p in titulo for p in pergunta.lower().split()):
            melhor_correspondencia = aula
            break

    return melhor_correspondencia

# -------------------------------
# 5️⃣ Rota principal
# -------------------------------
@app.route("/responder", methods=["POST"])
def responder():
    try:
        data = request.get_json()
        pergunta = data.get("pergunta", "")

        if not pergunta:
            return jsonify({"resposta": "Nenhuma pergunta recebida."}), 400

        # 1. Tenta achar resposta no banco
        aula = buscar_aula_no_banco(pergunta)

        if aula:
            resposta_texto = f"Encontrei algo sobre isso nas aulas:\n\n{aula['conteudo']}"
        else:
            # 2. Caso não encontre, chama o ChatGPT
            resposta_ai = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente de investimentos do curso 'Rico por conta própria'. Responda de forma didática e baseada nas aulas do curso."},
                    {"role": "user", "content": pergunta}
                ],
                max_tokens=300
            )
            resposta_texto = resposta_ai.choices[0].message.content

        return jsonify({"resposta": resposta_texto})

    except Exception as e:
        print("Erro:", e)
        return jsonify({"resposta": f"Erro no servidor: {str(e)}"}), 500

# -------------------------------
# 6️⃣ Executar servidor
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
