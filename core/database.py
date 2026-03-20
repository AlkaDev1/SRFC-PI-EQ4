import sqlite3
import os

def obtener_conexion():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_db = os.path.join(os.path.dirname(directorio_actual), 'data', 'SRFC.db')

    try:
        conexion = sqlite3.connect(ruta_db)
        print("¡Conexión exitosa a la base de datos SRFC!") 
        return conexion
    except sqlite3.Error as error:
        print(f" Error al conectar con SQLite: {error}")
        return None

if __name__ == "__main__":
    print("Probando conexión...")
    conexion_prueba = obtener_conexion()
    
    if conexion_prueba:
        conexion_prueba.close()
        print("Conexión cerrada correctamente. ¡Todo listo!")