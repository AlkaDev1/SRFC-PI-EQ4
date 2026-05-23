"""
ui/idioma.py
GestorIdioma — traducciones embebidas, sin dependencia de data/lang.json.

API idéntica a la versión anterior:
    idioma.t("topbar.sistema_linea1")   → "SISTEMA DE CONTROL"
    idioma.t("gestion.roles")           → ["Rol", "Alumno", ...]
    idioma.toggle()
    idioma.set("en")
    idioma.registrar(cb) / desregistrar(cb)
"""

from pathlib import Path

_RAIZ     = Path(__file__).resolve().parent.parent
_CFG_FILE = _RAIZ / "data" / "idioma.cfg"
_IDIOMAS  = ("es", "en")
_DEFAULT  = "es"

# ── Traducciones embebidas ────────────────────────────────────────────────────
_LANG: dict = {
  "es": {
    "topbar": {
      "sistema_linea1": "SISTEMA DE CONTROL",
      "sistema_linea2": "BIOMÉTRICO",
      "universidad": "Universidad de Colima"
    },
    "principal": {
      "bienvenidos": "BIENVENIDOS",
      "badge": "Sistema de Control Biométrico",
      "btn_acceder": "ACCEDER",
      "btn_gestion": "GESTIÓN",
      "btn_aviso_privacidad": "AVISO DE\nPRIVACIDAD"
    },
    "login": {
      "instruccion": "Indique su número de trabajador\ny su clave de acceso.",
      "placeholder_usuario": "Número de trabajador",
      "placeholder_clave": "Contraseña",
      "btn_ingresar": "INGRESAR",
      "error_credenciales": "⚠ Credenciales incorrectas"
    },
    "aviso_privacidad": {
      "titulo": "Aviso de Privacidad",
      "btn_aceptar": "     Aceptar"
    },
    "acceso": {
      "iniciando_camara": "Iniciando cámara...",
      "estado_escaneando_titulo": "POR FAVOR NO SE MUEVA",
      "estado_escaneando_sub": "ESCANEANDO ROSTRO...",
      "estado_detectado_titulo": "ROSTRO DETECTADO",
      "estado_detectado_sub": "Verificando identidad...",
      "estado_sin_rostro_titulo": "ACERCATE A LA CAMARA",
      "estado_sin_rostro_sub": "No se detecta ningun rostro",
      "estado_sin_camara_titulo": "CAMARA NO DISPONIBLE",
      "estado_sin_camara_sub": "Verifique la conexion",
      "estado_deny_titulo": "ACCESO DENEGADO",
      "estado_deny_sub": "No autorizado",
      "acceso_concedido": "ACCESO CONCEDIDO",
      "acceso_registrado": "Acceso registrado · "
    },
    "validacion": {
      "iniciando_camara": "Iniciando cámara...",
      "estado_escaneando_titulo": "VALIDACION DE GESTION",
      "estado_escaneando_sub": "ESCANEANDO ROSTRO...",
      "estado_detectado_titulo": "ROSTRO DETECTADO",
      "estado_detectado_sub": "Verificando permisos...",
      "estado_sin_rostro_titulo": "ACERCATE A LA CAMARA",
      "estado_sin_rostro_sub": "No se detecta ningun rostro",
      "estado_sin_camara_titulo": "CAMARA NO DISPONIBLE",
      "estado_sin_camara_sub": "Verifique la conexion",
      "estado_deny_titulo": "ACCESO DENEGADO",
      "estado_deny_sub": "No eres administrador...",
      "usuario_reconocido": "USUARIO RECONOCIDO",
      "admin_reconocido": "ADMINISTRADOR RECONOCIDO",
      "no_autorizado": "USUARIO NO AUTORIZADO",
      "acceso_denegado_label": "ACCESO DENEGADO",
      "solo_personal": "Solo personal autorizado",
      "redir_historial": "Redirigiendo al historial de accesos...",
      "redir_gestion": "Redirigiendo al panel de gestión...",
      "redirigiendo": "Redirigiendo..."
    },
    "gestion": {
      "titulo_tabla": " USUARIOS ",
      "tarjeta_accesos_hoy": "ACCESOS HOY",
      "tarjeta_alumnos": "ALUMNOS",
      "tarjeta_profesores": "PROFESORES",
      "tarjeta_denegados": "ACCESOS DENEGADOS",
      "tarjeta_accesos_sub": "accesos registrados hoy",
      "tarjeta_denegados_sub": "accesos denegados hoy",
      "tarjeta_sin_registros": "Sin registros",
      "sin_usuarios": "Sin usuarios registrados",
      "filtro_rol": "Rol",
      "filtro_mes": "Mes",
      "roles": ["Rol", "Alumno", "Maestro", "Admin", "Super Admin"],
      "meses": ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
      "columnas": ["No. Inst.", "Nombre", "Ap. Paterno", "Ap. Materno",
                   "Programa", "Rol", "Fecha/Hora", "Status", "Editar"],
      "btn_agregar": "  AGREGAR USUARIO",
      "btn_historial": "  HISTORIAL",
      "btn_cerrar_sesion": "  CERRAR SESIÓN",
      "icono_editar": "✏"
    },
    "historial": {
      "titulo": "HISTORIAL DE ACCESOS",
      "filtro_todos_roles": "Todos los roles",
      "filtro_mes": "Mes",
      "roles": ["Todos los roles", "Alumno", "Admin", "Profesor", "SuperAdmin", "SuperUsuario"],
      "meses": ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
      "columnas": ["No. Institucional", "Nombre", "Ap.Paterno", "Ap.Materno",
                   "Programa", "Rol", "Fecha y Hora"],
      "btn_cerrar": "← CERRAR"
    },
    "agregar_usuario": {
      "instruccion": "Ingrese los datos de la persona",
      "panel_titulo": "ESCANEO FACIAL",
      "panel_desc": "Presiona el botón para\ncapturar tu rostro",
      "panel_nota": "La captura se realiza\nen pantalla completa",
      "panel_capturado_titulo": "ROSTRO CAPTURADO",
      "panel_capturado_desc": "Encoding facial listo.\nPuedes confirmar el registro.",
      "btn_capturar": "📷  CAPTURAR ROSTRO",
      "btn_recapturar": "↺  RECAPTURAR",
      "btn_confirmar": "CONFIRMAR",
      "btn_confirmar_guardando": "GUARDANDO...",
      "btn_cancelar": "CANCELAR",
      "campo_cod": "Codigo Institucional",
      "campo_nombre": "Nombre(s)",
      "campo_ap_paterno": "Apellido Paterno",
      "campo_ap_materno": "Apellido Materno",
      "campo_programa": "Programa Académico",
      "campo_rol": "Rol",
      "campo_status": "Status",
      "campo_password": "Contraseña  (mayúscula, minúscula y número)",
      "campo_confirmar_password": "Confirmar contraseña",
      "roles": ["Alumno", "Maestro", "Admin", "Super Admin"],
      "programas": ["Software", "Mecatrónica"],
      "status": ["Activo", "Inactivo"],
      "error_sin_rostro": "Primero captura el rostro.",
      "error_cod": "El código es requerido.",
      "error_nombre": "El nombre es requerido.",
      "error_apellido": "El apellido paterno es requerido.",
      "error_pwd_min": "Mínimo 6 caracteres.",
      "error_pwd_mayus": "Debe incluir al menos una mayúscula.",
      "error_pwd_minus": "Debe incluir al menos una minúscula.",
      "error_pwd_num": "Debe incluir al menos un número.",
      "error_pwd_no_coinciden": "Las contraseñas no coinciden.",
      "modal_exito_titulo": "Registro exitoso"
    },
    "editar_usuario": {
      "titulo": "EDITAR USUARIO",
      "campo_cod": "No. Institucional",
      "campo_nombre": "Nombre",
      "campo_ap_paterno": "Apellido Paterno",
      "campo_ap_materno": "Apellido Materno",
      "campo_programa": "Programa / Carrera",
      "campo_fecha_hora": "Fecha y Hora",
      "campo_rol": "Rol",
      "campo_status": "Status",
      "campo_password": "Nueva Contraseña  (mayúscula, minúscula y número — vacío = no cambiar)",
      "campo_confirmar_password": "Confirmar nueva contraseña",
      "roles": ["Alumno", "Maestro", "Admin", "Super Admin"],
      "programas": ["Software", "Mecatrónica"],
      "status": ["Activo", "Inactivo"],
      "btn_guardar": "GUARDAR CAMBIOS",
      "btn_cancelar": "CANCELAR",
      "error_nombre": "El nombre no puede estar vacío.",
      "error_apellido": "El apellido paterno no puede estar vacío.",
      "error_pwd_min": "Mínimo 6 caracteres.",
      "error_pwd_mayus": "Debe incluir al menos una mayúscula.",
      "error_pwd_minus": "Debe incluir al menos una minúscula.",
      "error_pwd_num": "Debe incluir al menos un número.",
      "error_pwd_no_coinciden": "Las contraseñas no coinciden.",
      "modal_pwd_invalida": "Contraseña inválida",
      "modal_guardado": "Guardado",
      "modal_error_guardar": "Error al guardar"
    },
    "captura_rostro": {
      "registrando": "REGISTRANDO",
      "usuario_default": "Usuario",
      "label_capturas": "CAPTURAS",
      "listo": "Listo para\nescanear",
      "escaneando": "No te muevas\nescaneando...",
      "detenido": "Detenido",
      "completo": "¡Escaneo\ncompleto!",
      "verificando_dup": "Verificando\nduplicados...",
      "incompleto": "Incompleto\n",
      "dup_encontrado": "Rostro ya\nregistrado:\n",
      "btn_iniciar": "▶  INICIAR",
      "btn_detener": "⏹  DETENER",
      "btn_cancelar": "✕  CANCELAR",
      "btn_completado": "✓  COMPLETADO",
      "btn_reintentar": "▶  REINTENTAR",
      "error_camara_titulo": "Error de cámara",
      "error_camara_msg": "No se pudo abrir la cámara."
    },
    "modal": {
      "btn_aceptar": "Aceptar",
      "btn_confirmar": "Confirmar",
      "btn_cancelar": "Cancelar"
    },
    "barra_superior": {
      "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
      "meses": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    }
  },
  "en": {
    "topbar": {
      "sistema_linea1": "BIOMETRIC CONTROL",
      "sistema_linea2": "SYSTEM",
      "universidad": "University of Colima"
    },
    "principal": {
      "bienvenidos": "WELCOME",
      "badge": "Biometric Control System",
      "btn_acceder": "ACCESS",
      "btn_gestion": "MANAGEMENT",
      "btn_aviso_privacidad": "PRIVACY\nNOTICE"
    },
    "login": {
      "instruccion": "Enter your employee number\nand access password.",
      "placeholder_usuario": "Employee number",
      "placeholder_clave": "Password",
      "btn_ingresar": "LOG IN",
      "error_credenciales": "⚠ Incorrect credentials"
    },
    "aviso_privacidad": {
      "titulo": "Privacy Notice",
      "btn_aceptar": "     Accept"
    },
    "acceso": {
      "iniciando_camara": "Starting camera...",
      "estado_escaneando_titulo": "PLEASE DO NOT MOVE",
      "estado_escaneando_sub": "SCANNING FACE...",
      "estado_detectado_titulo": "FACE DETECTED",
      "estado_detectado_sub": "Verifying identity...",
      "estado_sin_rostro_titulo": "MOVE CLOSER TO THE CAMERA",
      "estado_sin_rostro_sub": "No face detected",
      "estado_sin_camara_titulo": "CAMERA NOT AVAILABLE",
      "estado_sin_camara_sub": "Check the connection",
      "estado_deny_titulo": "ACCESS DENIED",
      "estado_deny_sub": "Not authorized",
      "acceso_concedido": "ACCESS GRANTED",
      "acceso_registrado": "Access logged · "
    },
    "validacion": {
      "iniciando_camara": "Starting camera...",
      "estado_escaneando_titulo": "MANAGEMENT VALIDATION",
      "estado_escaneando_sub": "SCANNING FACE...",
      "estado_detectado_titulo": "FACE DETECTED",
      "estado_detectado_sub": "Verifying permissions...",
      "estado_sin_rostro_titulo": "MOVE CLOSER TO THE CAMERA",
      "estado_sin_rostro_sub": "No face detected",
      "estado_sin_camara_titulo": "CAMERA NOT AVAILABLE",
      "estado_sin_camara_sub": "Check the connection",
      "estado_deny_titulo": "ACCESS DENIED",
      "estado_deny_sub": "You are not an administrator...",
      "usuario_reconocido": "USER RECOGNIZED",
      "admin_reconocido": "ADMINISTRATOR RECOGNIZED",
      "no_autorizado": "UNAUTHORIZED USER",
      "acceso_denegado_label": "ACCESS DENIED",
      "solo_personal": "Authorized personnel only",
      "redir_historial": "Redirecting to access history...",
      "redir_gestion": "Redirecting to management panel...",
      "redirigiendo": "Redirecting..."
    },
    "gestion": {
      "titulo_tabla": " USERS ",
      "tarjeta_accesos_hoy": "TODAY'S ACCESSES",
      "tarjeta_alumnos": "STUDENTS",
      "tarjeta_profesores": "TEACHERS",
      "tarjeta_denegados": "DENIED ACCESSES",
      "tarjeta_accesos_sub": "accesses logged today",
      "tarjeta_denegados_sub": "denied accesses today",
      "tarjeta_sin_registros": "No records",
      "sin_usuarios": "No registered users",
      "filtro_rol": "Role",
      "filtro_mes": "Month",
      "roles": ["Role", "Student", "Teacher", "Admin", "Super Admin"],
      "meses": ["Month", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"],
      "columnas": ["Inst. No.", "First Name", "Last Name", "Second Last Name",
                   "Program", "Role", "Date/Time", "Status", "Edit"],
      "btn_agregar": "  ADD USER",
      "btn_historial": "  HISTORY",
      "btn_cerrar_sesion": "  LOG OUT",
      "icono_editar": "✏"
    },
    "historial": {
      "titulo": "ACCESS HISTORY",
      "filtro_todos_roles": "All roles",
      "filtro_mes": "Month",
      "roles": ["All roles", "Student", "Admin", "Teacher", "SuperAdmin", "SuperUser"],
      "meses": ["Month", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"],
      "columnas": ["Inst. Number", "First Name", "Last Name", "Second Last Name",
                   "Program", "Role", "Date and Time"],
      "btn_cerrar": "← CLOSE"
    },
    "agregar_usuario": {
      "instruccion": "Enter the person's information",
      "panel_titulo": "FACIAL SCAN",
      "panel_desc": "Press the button to\ncapture your face",
      "panel_nota": "Capture is done\nin full screen",
      "panel_capturado_titulo": "FACE CAPTURED",
      "panel_capturado_desc": "Facial encoding ready.\nYou can confirm the registration.",
      "btn_capturar": "📷  CAPTURE FACE",
      "btn_recapturar": "↺  RECAPTURE",
      "btn_confirmar": "CONFIRM",
      "btn_confirmar_guardando": "SAVING...",
      "btn_cancelar": "CANCEL",
      "campo_cod": "Institutional Code",
      "campo_nombre": "First Name(s)",
      "campo_ap_paterno": "Last Name",
      "campo_ap_materno": "Second Last Name",
      "campo_programa": "Academic Program",
      "campo_rol": "Role",
      "campo_status": "Status",
      "campo_password": "Password  (uppercase, lowercase and number)",
      "campo_confirmar_password": "Confirm password",
      "roles": ["Student", "Teacher", "Admin", "Super Admin"],
      "programas": ["Software", "Mechatronics"],
      "status": ["Active", "Inactive"],
      "error_sin_rostro": "Please capture the face first.",
      "error_cod": "Code is required.",
      "error_nombre": "First name is required.",
      "error_apellido": "Last name is required.",
      "error_pwd_min": "Minimum 6 characters.",
      "error_pwd_mayus": "Must include at least one uppercase letter.",
      "error_pwd_minus": "Must include at least one lowercase letter.",
      "error_pwd_num": "Must include at least one number.",
      "error_pwd_no_coinciden": "Passwords do not match.",
      "modal_exito_titulo": "Registration successful"
    },
    "editar_usuario": {
      "titulo": "EDIT USER",
      "campo_cod": "Inst. Number",
      "campo_nombre": "First Name",
      "campo_ap_paterno": "Last Name",
      "campo_ap_materno": "Second Last Name",
      "campo_programa": "Program / Major",
      "campo_fecha_hora": "Date and Time",
      "campo_rol": "Role",
      "campo_status": "Status",
      "campo_password": "New Password  (uppercase, lowercase and number — leave empty to keep current)",
      "campo_confirmar_password": "Confirm new password",
      "roles": ["Student", "Teacher", "Admin", "Super Admin"],
      "programas": ["Software", "Mechatronics"],
      "status": ["Active", "Inactive"],
      "btn_guardar": "SAVE CHANGES",
      "btn_cancelar": "CANCEL",
      "error_nombre": "First name cannot be empty.",
      "error_apellido": "Last name cannot be empty.",
      "error_pwd_min": "Minimum 6 characters.",
      "error_pwd_mayus": "Must include at least one uppercase letter.",
      "error_pwd_minus": "Must include at least one lowercase letter.",
      "error_pwd_num": "Must include at least one number.",
      "error_pwd_no_coinciden": "Passwords do not match.",
      "modal_pwd_invalida": "Invalid password",
      "modal_guardado": "Saved",
      "modal_error_guardar": "Error saving"
    },
    "captura_rostro": {
      "registrando": "REGISTERING",
      "usuario_default": "User",
      "label_capturas": "CAPTURES",
      "listo": "Ready to\nscan",
      "escaneando": "Don't move\nscanning...",
      "detenido": "Stopped",
      "completo": "Scan\ncomplete!",
      "verificando_dup": "Checking\nduplicates...",
      "incompleto": "Incomplete\n",
      "dup_encontrado": "Face already\nregistered:\n",
      "btn_iniciar": "▶  START",
      "btn_detener": "⏹  STOP",
      "btn_cancelar": "✕  CANCEL",
      "btn_completado": "✓  COMPLETED",
      "btn_reintentar": "▶  RETRY",
      "error_camara_titulo": "Camera error",
      "error_camara_msg": "Could not open the camera."
    },
    "modal": {
      "btn_aceptar": "Accept",
      "btn_confirmar": "Confirm",
      "btn_cancelar": "Cancel"
    },
    "barra_superior": {
      "dias": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
      "meses": ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
    }
  }
}


class GestorIdioma:

    def __init__(self):
        self._idioma: str        = self._cargar_preferencia()
        self._diccionario: dict  = _LANG.get(self._idioma, _LANG[_DEFAULT])
        self._listeners: list    = []

    # ── API pública ───────────────────────────────────────────────────────────
    def idioma_actual(self) -> str:
        return self._idioma

    def es_ingles(self) -> bool:
        return self._idioma == "en"

    def set(self, codigo: str):
        if codigo not in _IDIOMAS or codigo == self._idioma:
            return
        self._idioma     = codigo
        self._diccionario = _LANG.get(codigo, _LANG[_DEFAULT])
        self._guardar_preferencia()
        self._notificar()

    def toggle(self):
        self.set("en" if self._idioma == "es" else "es")

    def t(self, clave: str, fallback: str = ""):
        """
        Navega el diccionario con notación de punto.
        Ej: t("principal.bienvenidos") → "BIENVENIDOS"
            t("gestion.roles")         → ["Rol", "Alumno", ...]
        """
        nodo = self._diccionario
        for parte in clave.split("."):
            if isinstance(nodo, dict):
                nodo = nodo.get(parte)
            else:
                nodo = None
                break
        if nodo is None:
            return fallback if fallback else clave
        return nodo

    # ── Listeners ─────────────────────────────────────────────────────────────
    def registrar(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def desregistrar(self, callback):
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _notificar(self):
        for cb in list(self._listeners):
            try:
                cb()
            except Exception as e:
                print(f"[GestorIdioma] Error en listener: {e}")
                self._listeners.remove(cb)

    # ── Persistencia (solo guarda "es" o "en") ────────────────────────────────
    def _cargar_preferencia(self) -> str:
        try:
            if _CFG_FILE.exists():
                codigo = _CFG_FILE.read_text(encoding="utf-8").strip()
                if codigo in _IDIOMAS:
                    return codigo
        except Exception:
            pass
        return _DEFAULT

    def _guardar_preferencia(self):
        try:
            _CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
            _CFG_FILE.write_text(self._idioma, encoding="utf-8")
        except Exception as e:
            print(f"[GestorIdioma] No se pudo guardar preferencia: {e}")