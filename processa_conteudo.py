import os
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import psycopg2
import tiktoken
import json  

# 🔑 Carregar API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ⚡ Configuração do Postgres
DB_NAME = os.getenv("PGDATABASE")
DB_USER = os.getenv("PGUSER")
DB_PASSWORD = os.getenv("PGPASSWORD")
DB_HOST = os.getenv("PGHOST")
DB_PORT = os.getenv("PGPORT", "5432")

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
    """Cria tabela embeddings no PostgreSQL se não existir"""
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            texto TEXT,
            embedding JSONB
        )
    ''')
    conn.commit()
    conn.close()

def processar_texto(texto):
    """Divide em chunks, gera embeddings e insere no PostgreSQL"""
    chunks = dividir_em_chunks(texto)
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    for chunk in chunks:
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        vetor = response.data[0].embedding
        vetor_json = json.dumps(vetor)

        cur.execute(
            "INSERT INTO embeddings (texto, embedding) VALUES (%s, %s)",
            (chunk, vetor_json)
        )

    conn.commit()
    conn.close()

def processar_arquivo(caminho):
    """Detecta extensão e processa arquivo"""
    if caminho.endswith(".pdf"):
        texto = extrair_texto_pdf(caminho)
    elif caminho.endswith(".docx"):
        texto = extrair_texto_docx(caminho)
    else:
        print(f"Formato não suportado: {caminho}")
        return
    
    print(f"📄 Processando: {caminho}...")
    processar_texto(texto)
    print(f"✅ Finalizado: {caminho}")
