import sqlite3
import json

conn = sqlite3.connect("vetores.db")
c = conn.cursor()

c.execute("SELECT id, texto, embedding FROM embeddings LIMIT 3")
resultados = c.fetchall()

for r in resultados:
    print(f"\n--- ID: {r[0]} ---")
    print(f"Texto:\n{r[1][:100]}...")  # Só o começo do texto
    print("Tipo do embedding:", type(r[2]))
    
    # Tentar imprimir o começo do embedding
    if isinstance(r[2], (bytes, bytearray, memoryview)):
        print("Embedding (bytes):", r[2][:20], "...")
    else:
        print("Embedding (conteúdo):", str(r[2])[:100], "...")

conn.close()
