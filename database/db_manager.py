import sqlite3
import os

DB_PATH = "esterilcontrol.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Registro de Ciclos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ciclos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_ciclo INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            operador TEXT NOT NULL,
            estado TEXT NOT NULL,
            observaciones TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")