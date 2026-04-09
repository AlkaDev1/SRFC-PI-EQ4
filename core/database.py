"""
core/database.py
Módulo de base de datos SQLite para el sistema SRFC.
"""

import sqlite3
import os
import pickle
import numpy as np


def _ruta_db() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "SRFC.db")


def obtener_conexion():
    try:
        con = sqlite3.connect(_ruta_db())
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con
    except sqlite3.Error as e:
        print(f"[DB] Error de conexión: {e}")
        return None


# ══════════════════════════════════════════════
#  Inicialización
# ══════════════════════════════════════════════
def inicializar_bd() -> bool:
    sql = """
    CREATE TABLE IF NOT EXISTS Roles (
        id_rol              INTEGER PRIMARY KEY,
        nombre              VARCHAR(30) NOT NULL,
        estado              INTEGER DEFAULT 1,
        fecha_registro      DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion DATETIME,
        usuario_registro    VARCHAR(50),
        usuario_actualizacion VARCHAR(50)
    );
    CREATE TABLE IF NOT EXISTS Usuarios (
        cod_institucional     VARCHAR(20) PRIMARY KEY,
        id_rol                INTEGER,
        primer_nombre         VARCHAR(50) NOT NULL,
        segundo_nombre        VARCHAR(50),
        apellido_paterno      VARCHAR(50) NOT NULL,
        apellido_materno      VARCHAR(50),
        password_hash         TEXT,
        estado                INTEGER DEFAULT 1,
        fecha_registro        DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion   DATETIME,
        usuario_registro      VARCHAR(50),
        usuario_actualizacion VARCHAR(50),
        FOREIGN KEY (id_rol) REFERENCES Roles(id_rol)
    );
    CREATE TABLE IF NOT EXISTS Alumnos_Detalle (
        cod_institucional VARCHAR(20) PRIMARY KEY,
        grado             VARCHAR(10),
        grupo             VARCHAR(10),
        carrera           VARCHAR(100),
        FOREIGN KEY (cod_institucional)
            REFERENCES Usuarios(cod_institucional) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS Rostros_encoding (
        cod_institucional VARCHAR(20) PRIMARY KEY,
        face_encoding     BLOB NOT NULL,
        fecha_registro    DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cod_institucional)
            REFERENCES Usuarios(cod_institucional) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS Acceso (
        id_acceso         INTEGER PRIMARY KEY AUTOINCREMENT,
        cod_institucional VARCHAR(20),
        fecha             DATE DEFAULT (DATE('now','localtime')),
        hora              TIME DEFAULT (TIME('now','localtime')),
        FOREIGN KEY (cod_institucional) REFERENCES Usuarios(cod_institucional)
    );
    """
    con = obtener_conexion()
    if not con:
        return False
    try:
        con.executescript(sql)
        con.executemany(
            "INSERT OR IGNORE INTO Roles (id_rol, nombre, usuario_registro) VALUES (?,?,?)",
            [(1,"SuperAdmin","Sistema"),(2,"Admin","Sistema"),
             (3,"SuperUsuario","Sistema"),(4,"Alumno","Sistema")]
        )
        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error inicializando: {e}")
        return False
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Roles
# ══════════════════════════════════════════════
def obtener_roles() -> list:
    con = obtener_conexion()
    if not con: return []
    try:
        cur = con.execute("SELECT id_rol, nombre FROM Roles WHERE estado=1 ORDER BY id_rol")
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Usuarios
# ══════════════════════════════════════════════
def registrar_usuario(datos: dict) -> tuple:
    """
    Inserta usuario + detalle + encoding en una transacción.
    datos: cod_institucional, id_rol, primer_nombre, segundo_nombre,
           apellido_paterno, apellido_materno, carrera, grado, grupo,
           face_encoding (np.ndarray o None)
    Retorna (bool, str)
    """
    con = obtener_conexion()
    if not con:
        return False, "No se pudo conectar a la base de datos."
    try:
        existe = con.execute(
            "SELECT 1 FROM Usuarios WHERE cod_institucional=?",
            (datos["cod_institucional"],)
        ).fetchone()
        if existe:
            return False, f"El código '{datos['cod_institucional']}' ya está registrado."

        con.execute("""
            INSERT INTO Usuarios
                (cod_institucional, id_rol, primer_nombre, segundo_nombre,
                 apellido_paterno, apellido_materno, estado, usuario_registro)
            VALUES (?,?,?,?,?,?,1,'Sistema')
        """, (
            datos["cod_institucional"], datos["id_rol"],
            datos["primer_nombre"],    datos.get("segundo_nombre") or None,
            datos["apellido_paterno"], datos.get("apellido_materno") or None,
        ))

        con.execute("""
            INSERT INTO Alumnos_Detalle (cod_institucional, grado, grupo, carrera)
            VALUES (?,?,?,?)
        """, (datos["cod_institucional"], datos.get("grado"),
              datos.get("grupo"),        datos.get("carrera")))

        if datos.get("face_encoding") is not None:
            con.execute("""
                INSERT INTO Rostros_encoding (cod_institucional, face_encoding)
                VALUES (?,?)
            """, (datos["cod_institucional"], _enc_a_blob(datos["face_encoding"])))

        con.commit()
        return True, "Usuario registrado correctamente."
    except sqlite3.Error as e:
        con.rollback()
        return False, f"Error al guardar: {e}"
    finally:
        con.close()


def listar_usuarios() -> list:
    con = obtener_conexion()
    if not con: return []
    try:
        rows = con.execute("""
            SELECT u.cod_institucional,
                   u.primer_nombre || ' ' || u.apellido_paterno AS nombre_completo,
                   r.nombre  AS rol,
                   a.carrera, a.grado, a.grupo,
                   CASE WHEN re.cod_institucional IS NOT NULL THEN 1 ELSE 0 END AS tiene_encoding
            FROM Usuarios u
            LEFT JOIN Roles r            ON u.id_rol = r.id_rol
            LEFT JOIN Alumnos_Detalle a  ON u.cod_institucional = a.cod_institucional
            LEFT JOIN Rostros_encoding re ON u.cod_institucional = re.cod_institucional
            WHERE u.estado = 1
            ORDER BY u.fecha_registro DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Encodings
# ══════════════════════════════════════════════
def cargar_todos_encodings() -> list:
    """
    Retorna lista de dicts {cod, nombre, encoding} listos para reconocimiento.
    """
    con = obtener_conexion()
    if not con: return []
    try:
        rows = con.execute("""
            SELECT re.cod_institucional,
                   u.primer_nombre || ' ' || u.apellido_paterno AS nombre,
                   re.face_encoding
            FROM Rostros_encoding re
            JOIN Usuarios u ON re.cod_institucional = u.cod_institucional
            WHERE u.estado = 1
        """).fetchall()
        resultado = []
        for r in rows:
            try:
                resultado.append({
                    "cod":      r["cod_institucional"],
                    "nombre":   r["nombre"],
                    "encoding": _blob_a_enc(r["face_encoding"]),
                })
            except Exception as e:
                print(f"[DB] Error decodificando {r['cod_institucional']}: {e}")
        return resultado
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Accesos
# ══════════════════════════════════════════════
def registrar_acceso(cod: str) -> bool:
    con = obtener_conexion()
    if not con: return False
    try:
        con.execute("INSERT INTO Acceso (cod_institucional) VALUES (?)", (cod,))
        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error registrando acceso: {e}")
        return False
    finally:
        con.close()


def listar_accesos(limite: int = 100) -> list:
    con = obtener_conexion()
    if not con: return []
    try:
        rows = con.execute("""
            SELECT a.id_acceso, a.cod_institucional,
                   u.primer_nombre || ' ' || u.apellido_paterno AS nombre,
                   a.fecha, a.hora
            FROM Acceso a
            LEFT JOIN Usuarios u ON a.cod_institucional = u.cod_institucional
            ORDER BY a.id_acceso DESC LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════
def _enc_a_blob(encoding: np.ndarray) -> bytes:
    return pickle.dumps(encoding.astype(np.float64))

def _blob_a_enc(blob: bytes) -> np.ndarray:
    return pickle.loads(blob)


if __name__ == "__main__":
    print("Inicializando BD...")
    print("OK" if inicializar_bd() else "ERROR")
