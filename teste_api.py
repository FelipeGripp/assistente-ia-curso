import requests

url = "http://127.0.0.1:5000/responder"
dados = {"pergunta": "O que é Bitcoin?"}

resposta = requests.post(url, json=dados)

print("Status:", resposta.status_code)
print("Resposta:", resposta.json())
