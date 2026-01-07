from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": [
            "https://front-rico.onrender.com",  # Sua URL do frontend
            "http://localhost:5173",             # Para desenvolvimento local
            "http://localhost:3000"              # Para desenvolvimento local
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Conexão com o MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["assistenteIA"]
aulas_collection = db["aulas"]

# Testar conexão
try:
    mongo_client.server_info()
    print("✅ MongoDB conectado!")
except Exception as e:
    print(f"❌ Erro no MongoDB: {e}")

# Configuração do OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def verificar_restricoes(pergunta):
    """
    Verifica se a pergunta viola as restrições do assistente.
    Retorna uma mensagem de erro se violar, ou None se estiver ok.
    """
    pergunta_lower = pergunta.lower()
    
    # Lista de palavras/frases que indicam pedido de montagem de carteira
    palavras_carteira = [
        "montar carteira",
        "monte uma carteira",
        "criar carteira",
        "montar minha carteira",
        "criar minha carteira",
        "fazer carteira",
        "construir carteira",
        "como montar carteira",
        "ajuda a montar",
        "monta minha carteira"
    ]
    
    # Lista de palavras/frases que indicam pedido de indicação
    palavras_indicacao = [
        "indicar investimento",
        "indica investimento",
        "indique investimento",
        "qual investimento",
        "onde investir",
        "o que investir",
        "melhor investimento",
        "recomenda investimento",
        "recomende investimento",
        "sugere investimento",
        "sugira investimento",
        "devo investir em",
        "vale a pena investir",
        "comprar ações",
        "qual ação",
        "que ação",
        "indica ação",
        "indica fundo",
        "indica cdb",
        "indica tesouro"
    ]
    
    # Verifica pedidos de montagem de carteira
    for palavra in palavras_carteira:
        if palavra in pergunta_lower:
            return """Desculpe, mas eu não tenho capacidade de montar carteiras de investimentos. 

Como assistente educacional do curso 'Rico por Conta Própria', meu papel é ensinar conceitos e estratégias de investimentos, mas não posso criar uma carteira personalizada para você.

Posso te ajudar a:
✅ Entender diferentes tipos de investimentos
✅ Aprender sobre diversificação
✅ Compreender seu perfil de investidor
✅ Estudar conceitos das aulas do curso

Para montar sua carteira, recomendo consultar um assessor de investimentos certificado."""
    
    # Verifica pedidos de indicação de investimentos
    for palavra in palavras_indicacao:
        if palavra in pergunta_lower:
            return """Desculpe, mas eu não posso indicar investimentos específicos.

Como assistente educacional, meu objetivo é ensinar conceitos e ajudar você a entender o conteúdo do curso 'Rico por Conta Própria', mas não posso recomendar produtos financeiros específicos.

Posso te ajudar a:
✅ Entender características de diferentes tipos de investimento
✅ Aprender a analisar investimentos
✅ Compreender riscos e retornos
✅ Estudar estratégias de investimento

Para indicações personalizadas, consulte um assessor de investimentos certificado."""
    
    return None  # Nenhuma restrição violada


def buscar_aula_no_banco(pergunta):
    """Procura no MongoDB uma aula relacionada à pergunta."""
    palavras_chave = [p for p in pergunta.lower().split() if len(p) > 3]
    
    if not palavras_chave:
        return None
    
    # Busca usando regex (mais eficiente)
    query = {
        "$or": [
            {"titulo": {"$regex": palavra, "$options": "i"}} 
            for palavra in palavras_chave
        ] + [
            {"conteudo": {"$regex": palavra, "$options": "i"}} 
            for palavra in palavras_chave
        ]
    }
    
    return aulas_collection.find_one(query)


@app.route("/responder", methods=["POST"])
def responder():
    try:
        data = request.get_json()
        pergunta = data.get("pergunta", "")

        if not pergunta:
            return jsonify({"resposta": "Nenhuma pergunta recebida."}), 400

        # 1. VERIFICAR RESTRIÇÕES PRIMEIRO
        mensagem_restricao = verificar_restricoes(pergunta)
        if mensagem_restricao:
            return jsonify({"resposta": mensagem_restricao})

        # 2. Busca no banco
        aula = buscar_aula_no_banco(pergunta)

        if aula:
            # Usa o GPT para responder baseado na aula encontrada
            prompt = f"""Responda a pergunta: "{pergunta}"

Baseie-se no seguinte conteúdo da aula "{aula.get('titulo', '')}":

{aula['conteudo'][:3000]}

IMPORTANTE: 
- NÃO indique investimentos específicos
- NÃO monte carteiras de investimentos
- Seja educacional e didático
- Ensine conceitos, não dê recomendações financeiras"""

            resposta_ai = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """Você é um assistente educacional do curso 'Rico por conta própria'. 
                    
REGRAS IMPORTANTES:
- NUNCA indique investimentos específicos (ações, fundos, CDBs específicos)
- NUNCA monte carteiras de investimentos
- SEMPRE ensine conceitos de forma educacional
- Se perguntarem sobre indicações ou montagem de carteira, explique que não pode fazer isso e sugira consultar um assessor certificado"""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            resposta_texto = resposta_ai.choices[0].message.content
        else:
            # 3. Se não encontrar, usa conhecimento geral do GPT (com restrições)
            resposta_ai = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """Você é um assistente educacional de investimentos.
                    
REGRAS IMPORTANTES:
- NUNCA indique investimentos específicos
- NUNCA monte carteiras de investimentos  
- SEMPRE seja educacional
- Ensine conceitos, não dê recomendações financeiras"""},
                    {"role": "user", "content": pergunta}
                ],
                max_tokens=300
            )
            resposta_texto = resposta_ai.choices[0].message.content

        return jsonify({"resposta": resposta_texto})

    except Exception as e:
        print("Erro:", e)
        return jsonify({"resposta": f"Erro no servidor: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)