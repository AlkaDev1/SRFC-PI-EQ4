"""
core/database.py
Módulo de base de datos SQLite para el sistema SRFC.

CAMBIOS v4:
  - Tabla Acceso ahora tiene columna `denegado` (0=concedido, 1=denegado)
    para registrar accesos denegados correctamente en historial y tarjetas.
  - Nueva función: registrar_acceso_denegado(motivo) — guarda acceso denegado
    con cod_institucional NULL y denegado=1.
  - Nueva función: verificar_credenciales(cod, password) — busca por
    cod_institucional (número de trabajador) y verifica hash bcrypt.
  - conteo_accesos_hoy() separado por denegados vs concedidos.
  - listar_accesos() filtra por denegado=0 (historial normal).
  - listar_accesos_denegados() para panel de gestión.
"""

import sqlite3
import os
import pickle
import hashlib
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


_ROL_ALIAS: dict = {
    "superadmin":    "SuperAdmin",
    "super admin":   "SuperAdmin",
    "superusuario":  "SuperAdmin",
    "admin":         "Admin",
    "maestro":       "Maestro",
    "profesor":      "Maestro",
    "teacher":       "Maestro",
    "alumno":        "Alumno",
    "student":       "Alumno",
}

ROL_NOMBRE_A_ID: dict = {
    "SuperAdmin":  1,
    "Super Admin": 1,
    "Admin":       2,
    "Maestro":     3,
    "Alumno":      4,
}

_ID_ROL_ALUMNO = 4


def _normalizar_rol(rol: str) -> str:
    return _ROL_ALIAS.get((rol or "Alumno").lower().strip(), rol or "Alumno")


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
        denegado          INTEGER DEFAULT 0,
        FOREIGN KEY (cod_institucional) REFERENCES Usuarios(cod_institucional)
    );
    """
    con = obtener_conexion()
    if not con:
        return False
    try:
        con.executescript(sql)

        # Migración: agregar columna denegado si no existe (BD existente)
        cols = [r[1] for r in con.execute("PRAGMA table_info(Acceso)").fetchall()]
        if "denegado" not in cols:
            con.execute("ALTER TABLE Acceso ADD COLUMN denegado INTEGER DEFAULT 0")
            print("[DB] Migración v4: columna 'denegado' agregada a Acceso.")

        con.executemany(
            "INSERT OR IGNORE INTO Roles (id_rol, nombre, usuario_registro) VALUES (?,?,?)",
            [
                (1, "SuperAdmin", "Sistema"),
                (2, "Admin",      "Sistema"),
                (3, "Maestro",    "Sistema"),
                (4, "Alumno",     "Sistema"),
            ]
        )

        necesita_migrar = con.execute(
            "SELECT 1 FROM Roles WHERE id_rol = 3 AND nombre = 'SuperUsuario'"
        ).fetchone()
        if necesita_migrar:
            con.execute(
                "UPDATE Roles SET nombre='Maestro' WHERE id_rol=3 AND nombre='SuperUsuario'"
            )
            print("[DB] Migración v2: 'SuperUsuario' → 'Maestro' completada.")

        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error inicializando: {e}")
        return False
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Autenticación
# ══════════════════════════════════════════════
def _hash_password(password: str) -> str:
    """SHA-256 simple. Compatible con lo que ya existe en la BD."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verificar_credenciales(cod_institucional: str, password: str):
    """
    Verifica usuario por cod_institucional (número de trabajador) y contraseña.

    Intenta primero con SHA-256 directo.  Si el hash guardado empieza con '$2'
    asume bcrypt e intenta con bcrypt (si está instalado).

    Retorna dict con datos del usuario o None si las credenciales son inválidas.
    """
    if not cod_institucional or not password:
        return None
    con = obtener_conexion()
    if not con:
        return None
    try:
        row = con.execute("""
            SELECT u.cod_institucional, u.primer_nombre, u.segundo_nombre,
                   u.apellido_paterno, u.id_rol, u.password_hash, u.estado,
                   r.nombre AS rol
            FROM Usuarios u
            LEFT JOIN Roles r ON u.id_rol = r.id_rol
            WHERE u.cod_institucional = ? AND u.estado = 1
        """, (cod_institucional,)).fetchone()

        if not row:
            return None

        stored = row["password_hash"] or ""
        ok = False

        if stored.startswith("$2"):
            # bcrypt
            try:
                import bcrypt
                ok = bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
            except ImportError:
                # bcrypt no instalado: fallback SHA-256
                ok = _hash_password(password) == stored
        else:
            ok = _hash_password(password) == stored

        if not ok:
            return None

        return {
            "cod_institucional": row["cod_institucional"],
            "nombre":            row["primer_nombre"],
            "segundo_nombre":    row["segundo_nombre"],
            "apellido_paterno":  row["apellido_paterno"],
            "id_rol":            row["id_rol"],
            "rol":               row["rol"],
        }
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Roles
# ══════════════════════════════════════════════
def obtener_roles() -> list:
    con = obtener_conexion()
    if not con:
        return []
    try:
        cur = con.execute(
            "SELECT id_rol, nombre FROM Roles WHERE estado=1 ORDER BY id_rol")
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Usuarios
# ══════════════════════════════════════════════
def registrar_usuario(datos: dict) -> tuple:
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
                 apellido_paterno, apellido_materno, password_hash,
                 estado, usuario_registro)
            VALUES (?,?,?,?,?,?,?,1,'Sistema')
        """, (
            datos["cod_institucional"], datos["id_rol"],
            datos["primer_nombre"],    datos.get("segundo_nombre") or None,
            datos["apellido_paterno"], datos.get("apellido_materno") or None,
            datos.get("password_hash") or None,
        ))

        if datos.get("id_rol") == _ID_ROL_ALUMNO:
            con.execute("""
                INSERT OR REPLACE INTO Alumnos_Detalle
                    (cod_institucional, grado, grupo, carrera)
                VALUES (?,?,?,?)
            """, (
                datos["cod_institucional"],
                datos.get("grado")   or None,
                datos.get("grupo")   or None,
                datos.get("carrera") or None,
            ))

        if datos.get("face_encoding") is not None:
            con.execute("""
                INSERT OR REPLACE INTO Rostros_encoding
                    (cod_institucional, face_encoding)
                VALUES (?,?)
            """, (
                datos["cod_institucional"],
                _enc_a_blob(datos["face_encoding"]),
            ))

        con.commit()
        return True, "Usuario registrado correctamente."
    except sqlite3.Error as e:
        con.rollback()
        return False, f"Error al guardar: {e}"
    finally:
        con.close()


def listar_usuarios() -> list:
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT
                u.cod_institucional,
                CASE
                    WHEN u.segundo_nombre IS NOT NULL AND TRIM(u.segundo_nombre) != ''
                    THEN u.primer_nombre || ' ' || u.segundo_nombre
                    ELSE u.primer_nombre
                END                          AS nombre,
                u.apellido_paterno           AS apellido_paterno,
                COALESCE(u.apellido_materno, '') AS apellido_materno,
                COALESCE(a.carrera, '')      AS carrera,
                COALESCE(r.nombre, 'Sin rol') AS rol,
                DATE(u.fecha_registro)       AS fecha_registro,
                TIME(u.fecha_registro)       AS hora_registro,
                CASE WHEN u.estado = 1 THEN 'Activo' ELSE 'Inactivo' END AS status,
                CASE WHEN re.cod_institucional IS NOT NULL THEN 1 ELSE 0 END AS tiene_encoding,
                u.id_rol
            FROM Usuarios u
            LEFT JOIN Roles r             ON u.id_rol = r.id_rol
            LEFT JOIN Alumnos_Detalle a   ON u.cod_institucional = a.cod_institucional
            LEFT JOIN Rostros_encoding re ON u.cod_institucional = re.cod_institucional
            WHERE u.estado IN (0, 1)
            ORDER BY u.fecha_registro DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def actualizar_usuario(datos: dict) -> tuple:
    con = obtener_conexion()
    if not con:
        return False, "No se pudo conectar a la base de datos."
    try:
        rol_raw  = (datos.get("rol") or "Alumno").strip()
        rol_norm = _normalizar_rol(rol_raw)

        row_rol = con.execute(
            "SELECT id_rol FROM Roles WHERE nombre = ? COLLATE NOCASE",
            (rol_norm,)
        ).fetchone()

        if not row_rol:
            return False, (
                f"Rol '{rol_raw}' no encontrado. "
                f"Roles disponibles: SuperAdmin, Admin, Maestro, Alumno."
            )

        id_rol = row_rol["id_rol"]
        estado = 1 if datos.get("status", "Activo") in ("Activo", "Active") else 0
        segundo_nombre = datos.get("segundo_nombre") or None

        con.execute("""
            UPDATE Usuarios
            SET primer_nombre         = ?,
                segundo_nombre        = ?,
                apellido_paterno      = ?,
                apellido_materno      = ?,
                id_rol                = ?,
                estado                = ?,
                fecha_actualizacion   = CURRENT_TIMESTAMP,
                usuario_actualizacion = 'Sistema'
            WHERE cod_institucional = ?
        """, (
            datos.get("nombre", ""),
            segundo_nombre,
            datos.get("apellido_paterno", ""),
            datos.get("apellido_materno", ""),
            id_rol,
            estado,
            datos["cod_institucional"],
        ))

        if id_rol == _ID_ROL_ALUMNO:
            carrera = datos.get("carrera", "") or None
            if carrera == "Ninguno":
                carrera = None
            grado = datos.get("grado") or None
            grupo = datos.get("grupo") or None
            con.execute("""
                INSERT INTO Alumnos_Detalle (cod_institucional, grado, grupo, carrera)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cod_institucional)
                DO UPDATE SET grado=excluded.grado, grupo=excluded.grupo,
                              carrera=excluded.carrera
            """, (datos["cod_institucional"], grado, grupo, carrera))
        else:
            con.execute(
                "DELETE FROM Alumnos_Detalle WHERE cod_institucional = ?",
                (datos["cod_institucional"],)
            )

        if datos.get("password_hash"):
            con.execute("""
                UPDATE Usuarios SET password_hash = ?
                WHERE cod_institucional = ?
            """, (datos["password_hash"], datos["cod_institucional"]))

        con.commit()
        return True, "Usuario actualizado correctamente."
    except sqlite3.Error as e:
        con.rollback()
        return False, f"Error al actualizar: {e}"
    finally:
        con.close()


# ══════════════════════════════════════════════
#  Encodings
# ══════════════════════════════════════════════
def cargar_todos_encodings() -> list:
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT re.cod_institucional,
                   CASE
                       WHEN u.segundo_nombre IS NOT NULL AND TRIM(u.segundo_nombre) != ''
                       THEN u.primer_nombre || ' ' || u.segundo_nombre || ' ' || u.apellido_paterno
                       ELSE u.primer_nombre || ' ' || u.apellido_paterno
                   END                          AS nombre,
                   re.face_encoding,
                   u.id_rol,
                   COALESCE(r.nombre, 'Sin rol') AS rol
            FROM Rostros_encoding re
            JOIN Usuarios u ON re.cod_institucional = u.cod_institucional
            LEFT JOIN Roles r ON u.id_rol = r.id_rol
            WHERE u.estado = 1
        """).fetchall()
        resultado = []
        for r in rows:
            try:
                resultado.append({
                    "cod":      r["cod_institucional"],
                    "nombre":   r["nombre"],
                    "encoding": _blob_a_enc(r["face_encoding"]),
                    "id_rol":   r["id_rol"],
                    "rol":      r["rol"],
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
    """Registra acceso concedido (denegado=0)."""
    con = obtener_conexion()
    if not con:
        return False
    try:
        con.execute(
            "INSERT INTO Acceso (cod_institucional, denegado) VALUES (?, 0)", (cod,))
        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error registrando acceso: {e}")
        return False
    finally:
        con.close()


def registrar_acceso_denegado(cod: str = None) -> bool:
    """
    Registra un acceso denegado (denegado=1).
    cod puede ser None si la persona no está registrada.
    """
    con = obtener_conexion()
    if not con:
        return False
    try:
        con.execute(
            "INSERT INTO Acceso (cod_institucional, denegado) VALUES (?, 1)", (cod,))
        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error registrando acceso denegado: {e}")
        return False
    finally:
        con.close()


def conteo_accesos_hoy() -> dict:
    """
    Retorna conteos del día actual separados por tipo.
    {
      "total":     int,   # accesos concedidos
      "denegados": int,   # accesos denegados
      "alumnos":   int,
      "profesores": int,
    }
    """
    con = obtener_conexion()
    if not con:
        return {"total": 0, "denegados": 0, "alumnos": 0, "profesores": 0}
    try:
        hoy = con.execute(
            "SELECT COUNT(*) FROM Acceso WHERE fecha = DATE('now','localtime') AND denegado=0"
        ).fetchone()[0]
        denegados = con.execute(
            "SELECT COUNT(*) FROM Acceso WHERE fecha = DATE('now','localtime') AND denegado=1"
        ).fetchone()[0]
        alumnos = con.execute("""
            SELECT COUNT(*) FROM Acceso a
            JOIN Usuarios u ON a.cod_institucional = u.cod_institucional
            WHERE a.fecha = DATE('now','localtime') AND a.denegado=0
              AND u.id_rol = 4
        """).fetchone()[0]
        profesores = con.execute("""
            SELECT COUNT(*) FROM Acceso a
            JOIN Usuarios u ON a.cod_institucional = u.cod_institucional
            WHERE a.fecha = DATE('now','localtime') AND a.denegado=0
              AND u.id_rol = 3
        """).fetchone()[0]
        return {
            "total":      hoy,
            "denegados":  denegados,
            "alumnos":    alumnos,
            "profesores": profesores,
        }
    finally:
        con.close()


def listar_accesos(limite: int = 200) -> list:
    """Retorna historial de accesos CONCEDIDOS (denegado=0)."""
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT a.id_acceso, a.cod_institucional,
                   CASE
                       WHEN u.segundo_nombre IS NOT NULL AND TRIM(u.segundo_nombre) != ''
                       THEN u.primer_nombre || ' ' || u.segundo_nombre || ' ' || u.apellido_paterno
                       ELSE u.primer_nombre || ' ' || u.apellido_paterno
                   END AS nombre,
                   COALESCE(u.apellido_paterno, '') AS apellido_paterno,
                   COALESCE(u.apellido_materno, '') AS apellido_materno,
                   COALESCE(ad.carrera, '')         AS carrera,
                   COALESCE(r.nombre, '')           AS rol,
                   a.fecha, a.hora
            FROM Acceso a
            LEFT JOIN Usuarios u      ON a.cod_institucional = u.cod_institucional
            LEFT JOIN Alumnos_Detalle ad ON u.cod_institucional = ad.cod_institucional
            LEFT JOIN Roles r         ON u.id_rol = r.id_rol
            WHERE a.denegado = 0
            ORDER BY a.id_acceso DESC LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def listar_accesos_denegados(limite: int = 200) -> list:
    """Retorna historial de accesos DENEGADOS (denegado=1)."""
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT a.id_acceso, a.cod_institucional,
                   COALESCE(
                       CASE
                           WHEN u.segundo_nombre IS NOT NULL AND TRIM(u.segundo_nombre) != ''
                           THEN u.primer_nombre || ' ' || u.segundo_nombre || ' ' || u.apellido_paterno
                           ELSE u.primer_nombre || ' ' || u.apellido_paterno
                       END, 'Desconocido') AS nombre,
                   a.fecha, a.hora
            FROM Acceso a
            LEFT JOIN Usuarios u ON a.cod_institucional = u.cod_institucional
            WHERE a.denegado = 1
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