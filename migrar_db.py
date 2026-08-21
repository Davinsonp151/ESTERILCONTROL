import sqlite3
import json
import os
import shutil
from datetime import datetime

# Archivos de origen (JSON actuales)
DB_CICLOS_FILE = "ciclos_db.json"
DB_IB_FILE = "ib_db.json"
CONFIG_MAESTRA_FILE = "sistema_config.json"

# Carpeta de respaldo
BACKUP_DIR = "backup_json_2026"

def hacer_respaldo_y_migracion():
    print("--- INICIANDO RESPALDO Y MIGRACIÓN A SQLITE ---")
    
    # 1. Crear respaldo en carpeta dedicada
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    archivos_a_respaldar = [DB_CICLOS_FILE, DB_IB_FILE, CONFIG_MAESTRA_FILE]
    for archivo in archivos_a_respaldar:
        if os.path.exists(archivo):
            shutil.copy(archivo, os.path.join(BACKUP_DIR, archivo))
            print(f" [OK] Respaldo creado para: {archivo}")
        else:
            print(f" [AVISO] El archivo {archivo} no se encontró en el directorio actual.")

    # 2. Inicializar base de datos SQLite
    db_name = "esteril_control.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ciclos (
            n_ciclo INTEGER PRIMARY KEY,
            fecha TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            equipo TEXT,
            tot_unidades INTEGER,
            tot_peso REAL,
            res_ib TEXT,
            carga_liberada TEXT,
            fecha_liberacion TEXT,
            datos_json TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ib_registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciclo INTEGER,
            resultado TEXT,
            datos_json TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_sistema (
            clave TEXT PRIMARY KEY,
            valor_json TEXT
        )
    ''')
    conn.commit()

    # 3. Migrar Ciclos
    ciclos_migrados = 0
    if os.path.exists(DB_CICLOS_FILE):
        with open(DB_CICLOS_FILE, "r", encoding="utf-8") as f:
            ciclos_data = json.load(f)
            for c in ciclos_data:
                n_ciclo = int(c.get('n_ciclo', 0))
                fecha = c.get('fecha', '')
                h_ini = c.get('hora_inicio', '')
                h_fin = c.get('hora_fin', '')
                equipo = c.get('equipo', '')
                unidades = int(c.get('tot_unidades', 0))
                peso = float(c.get('tot_peso', 0.0))
                res_ib = c.get('res_ib', 'Negativo')
                liberada = c.get('carga_liberada', 'No')
                f_lib = c.get('fecha_liberacion', 'Pendiente')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ciclos 
                    (n_ciclo, fecha, hora_inicio, hora_fin, equipo, tot_unidades, tot_peso, res_ib, carga_liberada, fecha_liberacion, datos_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (n_ciclo, fecha, h_ini, h_fin, equipo, unidades, peso, res_ib, liberada, f_lib, json.dumps(c, ensure_ascii=False)))
                ciclos_migrados += 1
        conn.commit()
        print(f" [ÉXITO] Se migraron {ciclos_migrados} ciclos a SQLite.")

    # 4. Migrar Indicadores Biológicos (IB)
    ibs_migrados = 0
    if os.path.exists(DB_IB_FILE):
        with open(DB_IB_FILE, "r", encoding="utf-8") as f:
            ibs_data = json.load(f)
            for ib in ibs_data:
                ciclo_n = int(ib.get('ciclo', 0))
                resultado = ib.get('resultado', 'Negativo')
                
                cursor.execute('''
                    INSERT INTO ib_registros (ciclo, resultado, datos_json)
                    VALUES (?, ?, ?)
                ''', (ciclo_n, resultado, json.dumps(ib, ensure_ascii=False)))
                ibs_migrados += 1
        conn.commit()
        print(f" [ÉXITO] Se migraron {ibs_migrados} registros de IB a SQLite.")

    conn.close()
    print("--- ¡RESPALDO Y MIGRACIÓN COMPLETADOS CON ÉXITO! ---")

if __name__ == "__main__":
    hacer_respaldo_y_migracion()