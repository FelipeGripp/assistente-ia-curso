import sqlite3
import json

conn = sqlite3.connect("vetores.db")
c = conn.cursor()

c.execute("SELECT id, texto FROM embeddings LIMIT 5")
resultados = c.fetchall()

for r in resultados:
    print(f"\n--- ID: {r[0]} ---")
    print(f"Texto:\n{r[1][:300]}...")  # Exibe só o início do texto

conn.close()
