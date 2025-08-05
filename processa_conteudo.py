import os
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import sqlite3
import tiktoken
import json  

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def contar_tokens(texto, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(texto))

def dividir_em_chunks(texto, max_tokens=300):
    palavras = texto.split()
    chunks = []
    atual = []

    for palavra in palavras:
        atual.append(palavra)
        if contar_tokens(' '.join(atual)) > max_tokens:
            atual.pop()
            chunks.append(' '.join(atual))
            atual = [palavra]
    if atual:
        chunks.append(' '.join(atual))
    return chunks

def extrair_texto_pdf(caminho):
    reader = PdfReader(caminho)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extrair_texto_docx(caminho):
    doc = Document(caminho)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def criar_banco():
    conn = sqlite3.connect("vetores.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT,
            embedding BLOB
        )
    ''')
    conn.commit()
    conn.close()

def processar_texto(texto):
    chunks = dividir_em_chunks(texto)
    conn = sqlite3.connect("vetores.db")
    c = conn.cursor()

    for chunk in chunks:
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        vetor = response.data[0].embedding
        vetor_json = json.dumps(vetor) 
        c.execute("INSERT INTO embeddings (texto, embedding) VALUES (?, ?)", (chunk, vetor_json))

    conn.commit()
    conn.close()


def processar_arquivo(caminho):
    if caminho.endswith(".pdf"):
        texto = extrair_texto_pdf(caminho)
    elif caminho.endswith(".docx"):
        texto = extrair_texto_docx(caminho)
    else:
        print("Formato não suportado.")
        return
    processar_texto(texto)
