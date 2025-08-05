from flask import Flask, request, jsonify
from responder_ia import responder

app = Flask(__name__)

@app.route("/responder", methods=["POST"])
def responder_endpoint():
    data = request.get_json()

    pergunta = data.get("pergunta", "")
    if not pergunta:
        return jsonify({"erro": "Pergunta não fornecida"}), 400

    try:
        resposta = responder(pergunta)
        return jsonify({"resposta": resposta})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
