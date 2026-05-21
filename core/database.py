"""
core/database.py
Módulo de base de datos SQLite para el sistema SRFC.

CAMBIOS v2:
  - Tabla Roles corregida: id_rol=3 ahora es "Maestro" (antes "SuperUsuario")
  - inicializar_bd() incluye migración automática: renombra "SuperUsuario"→"Maestro"
    en registros existentes para no romper datos ya guardados
  - actualizar_usuario() normaliza variantes de nombre de rol antes de buscar
    (soporta "Maestro", "maestro", "SuperAdmin", "Super Admin", "SuperUsuario", etc.)
  - _ROL_ALIAS centraliza el mapeo para reutilizarlo
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


# ── Mapeo canónico de variantes de rol → nombre en BD ────────────────────────
# Usado en actualizar_usuario() y registrar_usuario() para tolerar
# distintas formas en que la UI puede enviar el rol.
_ROL_ALIAS: dict[str, str] = {
    "superadmin":    "SuperAdmin",
    "super admin":   "SuperAdmin",
    "superusuario":  "SuperAdmin",   # registros viejos con id_rol=3 que era SuperUsuario
    "admin":         "Admin",
    "maestro":       "Maestro",
    "profesor":      "Maestro",
    "teacher":       "Maestro",
    "alumno":        "Alumno",
    "student":       "Alumno",
}

# Mapa numérico que usa pantalla_agregar_usuario.py (rol_map)
# Centralizado aquí para no duplicarlo en la UI
ROL_NOMBRE_A_ID: dict[str, int] = {
    "SuperAdmin":  1,
    "Super Admin": 1,
    "Admin":       2,
    "Maestro":     3,
    "Alumno":      4,
}


def _normalizar_rol(rol: str) -> str:
    """Devuelve el nombre canónico del rol para buscar en BD."""
    return _ROL_ALIAS.get((rol or "Alumno").lower().strip(), rol or "Alumno")


# ══════════════════════════════════════════════
#  inicialización
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

        # Roles canónicos — INSERT OR IGNORE para no pisar datos existentes
        con.executemany(
            "INSERT OR IGNORE INTO Roles (id_rol, nombre, usuario_registro) VALUES (?,?,?)",
            [
                (1, "SuperAdmin", "Sistema"),
                (2, "Admin",      "Sistema"),
                (3, "Maestro",    "Sistema"),
                (4, "Alumno",     "Sistema"),
            ]
        )

        # ── Migración silenciosa ──────────────────────────────────────────────
        # Solo actualiza si el nombre sigue siendo "SuperUsuario" (registros viejos).
        # NO toca fecha_actualizacion ni usuario_actualizacion si ya está migrado,
        # por eso los campos de auditoría de Roles quedan limpios tras la 1ª ejecución.
        necesita_migrar = con.execute(
            "SELECT 1 FROM Roles WHERE id_rol = 3 AND nombre = 'SuperUsuario'"
        ).fetchone()

        if necesita_migrar:
            con.execute("""
                UPDATE Roles
                SET nombre = 'Maestro'
                WHERE id_rol = 3 AND nombre = 'SuperUsuario'
            """)
            print("[DB] Migración v2: 'SuperUsuario' → 'Maestro' completada.")

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
    """
    Inserta usuario + detalle + encoding en una transacción.
    Usa INSERT OR REPLACE en Alumnos_Detalle para evitar UNIQUE constraint
    en caso de registros huérfanos previos.
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
                 apellido_paterno, apellido_materno, password_hash,
                 estado, usuario_registro)
            VALUES (?,?,?,?,?,?,?,1,'Sistema')
        """, (
            datos["cod_institucional"], datos["id_rol"],
            datos["primer_nombre"],    datos.get("segundo_nombre") or None,
            datos["apellido_paterno"], datos.get("apellido_materno") or None,
            datos.get("password_hash") or None,
        ))

        # INSERT OR REPLACE evita el UNIQUE constraint si existía un registro
        # huérfano en Alumnos_Detalle del mismo cod_institucional
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
    """
    Devuelve lista de dicts con las claves que espera PantallaGestion:
      cod_institucional, nombre, apellido_paterno, apellido_materno,
      carrera, rol, fecha_registro, hora_registro, status
    """
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT
                u.cod_institucional,
                u.primer_nombre          AS nombre,
                u.apellido_paterno       AS apellido_paterno,
                COALESCE(u.apellido_materno, '') AS apellido_materno,
                COALESCE(a.carrera, '')  AS carrera,
                COALESCE(r.nombre, 'Sin rol') AS rol,
                DATE(u.fecha_registro)   AS fecha_registro,
                TIME(u.fecha_registro)   AS hora_registro,
                CASE WHEN u.estado = 1 THEN 'Activo' ELSE 'Inactivo' END AS status,
                CASE WHEN re.cod_institucional IS NOT NULL THEN 1 ELSE 0 END AS tiene_encoding
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
    """
    Actualiza nombre, apellidos, carrera, rol y status de un usuario.

    datos esperados:
      cod_institucional, nombre, apellido_paterno, apellido_materno,
      carrera, rol (cualquier variante), status
    Retorna (bool, str)
    """
    con = obtener_conexion()
    if not con:
        return False, "No se pudo conectar a la base de datos."
    try:
        # ── Normalizar el nombre del rol antes de buscar en BD ────────────────
        # Tolera: "Maestro", "maestro", "Super Admin", "SuperAdmin",
        #         "SuperUsuario" (registros viejos), etc.
        rol_raw  = (datos.get("rol") or "Alumno").strip()
        rol_norm = _normalizar_rol(rol_raw)

        row_rol = con.execute(
            "SELECT id_rol FROM Roles WHERE nombre = ? COLLATE NOCASE",
            (rol_norm,)
        ).fetchone()

        if not row_rol:
            # Último recurso: buscar por id si la UI mandó un número
            return False, (
                f"Rol '{rol_raw}' no encontrado en la base de datos. "
                f"Roles disponibles: SuperAdmin, Admin, Maestro, Alumno."
            )

        id_rol = row_rol["id_rol"]
        estado = 1 if datos.get("status", "Activo") == "Activo" else 0

        con.execute("""
            UPDATE Usuarios
            SET primer_nombre         = ?,
                apellido_paterno      = ?,
                apellido_materno      = ?,
                id_rol                = ?,
                estado                = ?,
                fecha_actualizacion   = CURRENT_TIMESTAMP,
                usuario_actualizacion = 'Sistema'
            WHERE cod_institucional = ?
        """, (
            datos.get("nombre", ""),
            datos.get("apellido_paterno", ""),
            datos.get("apellido_materno", ""),
            id_rol,
            estado,
            datos["cod_institucional"],
        ))

        con.execute("""
            INSERT INTO Alumnos_Detalle (cod_institucional, carrera)
            VALUES (?, ?)
            ON CONFLICT(cod_institucional)
            DO UPDATE SET carrera = excluded.carrera
        """, (datos["cod_institucional"], datos.get("carrera", "")))

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
    """
    Retorna lista de dicts {cod, nombre, encoding, id_rol, rol}
    listos para reconocimiento.
    """
    con = obtener_conexion()
    if not con:
        return []
    try:
        rows = con.execute("""
            SELECT re.cod_institucional,
                   u.primer_nombre || ' ' || u.apellido_paterno AS nombre,
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
    con = obtener_conexion()
    if not con:
        return False
    try:
        con.execute(
            "INSERT INTO Acceso (cod_institucional) VALUES (?)", (cod,))
        con.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] Error registrando acceso: {e}")
        return False
    finally:
        con.close()


def listar_accesos(limite: int = 100) -> list:
    con = obtener_conexion()
    if not con:
        return []
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