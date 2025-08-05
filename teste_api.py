import requests

resposta = requests.post(
    "http://127.0.0.1:5000/responder",
    json={"pergunta": "O que é Bitcoin?"}
)

print("Resposta da IA:")
print(resposta.json())
