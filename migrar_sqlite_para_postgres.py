import sqlite3
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB

# Conexão SQLite
sqlite_conn = sqlite3.connect("vetores.db")
sqlite_cursor = sqlite_conn.cursor()

# Conexão PostgreSQL (substitua com seus dados do Render)
postgres_url = "postgresql://assistente_ia_db_user:RXsNOzi7GLRfb4RKjvhtv8IF91ppcrZn@dpg-d2i68um3jp1c7393idfg-a.oregon-postgres.render.com/assistente_ia_db"
postgres_engine = create_engine(postgres_url)
postgres_conn = postgres_engine.connect()
postgres_metadata = MetaData()

# Definir tabela no PostgreSQL
embeddings_table = Table(
    "embeddings",
    postgres_metadata,
    Column("id", Integer, primary_key=True),
    Column("texto", Text),
    Column("embedding", JSONB),
)

# Criar tabela no PostgreSQL
postgres_metadata.create_all(postgres_engine)

print("Migrando tabela embeddings...")

# Ler dados do SQLite
sqlite_cursor.execute("SELECT id, texto, embedding FROM embeddings")
dados = sqlite_cursor.fetchall()

for id_, texto, embedding in dados:
    # Limpa caracteres NUL (\x00) do texto e embedding
    if isinstance(texto, str):
        texto = texto.replace("\x00", "")
    if isinstance(embedding, str):
        embedding = embedding.replace("\x00", "")

        # Converte string do embedding para lista JSON (se ainda não for lista)
        try:
            embedding = json.loads(embedding)
        except Exception:
            embedding = []

    # Inserir no PostgreSQL
    postgres_conn.execute(
        embeddings_table.insert(),
        {"id": id_, "texto": texto, "embedding": embedding}
    )

print("Migração concluída com sucesso!")

# Fechar conexões
sqlite_conn.close()
postgres_conn.close()
