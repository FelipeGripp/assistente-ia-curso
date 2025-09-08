from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/responder", methods=["POST"])
def responder():
    try:
        data = request.get_json()
        pergunta = data.get("pergunta", "")

        if not pergunta:
            return jsonify({"resposta": "Nenhuma pergunta recebida."}), 400

        # Chamada para OpenAI
        resposta_ai = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente de investimentos do curso 'Rico por conta própria'."},
                {"role": "user", "content": pergunta}
            ],
            max_tokens=300
        )

        resposta_texto = resposta_ai.choices[0].message.content
        return jsonify({"resposta": resposta_texto})

    except Exception as e:
        return jsonify({"resposta": f"Erro no servidor: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
