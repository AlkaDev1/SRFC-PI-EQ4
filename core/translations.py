"""
core/translations.py
═════════════════════════════════════════════════════════════════════
DICCIONARIO CENTRALIZADO DE TRADUCCIONES
═════════════════════════════════════════════════════════════════════

Este archivo contiene todos los textos de la aplicación en español e inglés.
Estructura: TRADUCCIONES[idioma][clave] = texto

Ejemplo de uso:
    idioma_actual = "es"  # o "en"
    texto = TRADUCCIONES[idioma_actual]["bienvenida"]

VENTAJAS:
- Todas las traducciones en UN solo archivo
- Fácil de mantener y actualizar
- Soporta múltiples idiomas
- No requiere archivos externos (JSON, etc.)
"""

# ═════════════════════════════════════════════════════════════════════
# DICCIONARIO CENTRALIZADO: TRADUCCIONES[IDIOMA][CLAVE] = VALOR
# ═════════════════════════════════════════════════════════════════════

TRADUCCIONES = {
    # ─────────────────────────────────────────────────────────────────
    # ESPAÑOL
    # ─────────────────────────────────────────────────────────────────
    "es": {
        # BARRA SUPERIOR (Top Bar)
        "sistema": "SISTEMA DE CONTROL",
        "biometrico": "BIOMÉTRICO",
        "universidad": "Universidad de Colima",
        
        # PANTALLA PRINCIPAL
        "bienvenidos": "BIENVENIDOS",
        "subtitulo_principal": "Sistema de Control Biométrico",
        "boton_acceder": "Acceder",
        "boton_gestion": "Gestión",
        "boton_aviso": "Aviso de Privacidad",
        
        # MODAL AVISO PRIVACIDAD
        "aviso_titulo": "Aviso de Privacidad",
        "aviso_contenido": (
            "AVISO DE PRIVACIDAD\n\n"
            "La Universidad de Colima, a través de la Facultad de Ingeniería "
            "Electromecánica, es responsable del tratamiento de sus datos biométricos.\n\n"
            "DATOS QUE RECOPILAMOS\n"
            "  • Imagen facial para reconocimiento biométrico\n"
            "  • Registros de acceso (fecha, hora, laboratorio)\n"
            "  • Datos de identificación (nombre, matrícula o número de empleado)\n\n"
            "FINALIDAD\n"
            "Los datos recabados se utilizarán exclusivamente para:\n"
            "  • Control de acceso a laboratorios\n"
            "  • Trazabilidad de uso de instalaciones\n"
            "  • Seguridad institucional\n\n"
            "ALMACENAMIENTO\n"
            "Toda la información se procesa y almacena de forma local en el dispositivo. "
            "No se transmite ningún dato a servidores externos ni servicios en la nube.\n\n"
            "DERECHOS ARCO\n"
            "Usted tiene derecho a Acceder, Rectificar, Cancelar u Oponerse al tratamiento "
            "de sus datos personales, conforme a la Ley Federal de Protección de Datos "
            "Personales en Posesión de los Particulares.\n\n"
            "Al presionar 'Aceptar', usted otorga su consentimiento para el tratamiento "
            "de sus datos biométricos bajo los términos descritos."
        ),
        "boton_aceptar": "Aceptar",
        "boton_rechazar": "Rechazar",
        
        # PANTALLA LOGIN
        "login_titulo": "Iniciar Sesión",
        "usuario": "Usuario",
        "contrasena": "Contraseña",
        "ingresar": "Ingresar",
        "error_credenciales": "Usuario o contraseña incorrectos",
        
        # PANTALLA ACCESO
        "acceso_titulo": "Control de Acceso",
        "acceso_instrucciones": "Coloque su rostro frente a la cámara",
        "acceso_cargando": "Escaneando...",
        "acceso_exitoso": "Acceso Permitido",
        "acceso_denegado": "Acceso Denegado",
        
        # PANTALLA REGISTRO
        "registro_titulo": "Registro de Usuario",
        "registro_instrucciones": "Capture su rostro",
        "boton_registrar": "Registrar",
        "registro_exitoso": "Usuario registrado correctamente",
        
        # PANTALLA GESTIÓN
        "gestion_titulo": "Gestión de Usuarios",
        "gestion_buscar": "Buscar usuario",
        "gestion_agregar": "Agregar",
        "gestion_eliminar": "Eliminar",
        "gestion_editar": "Editar",
        "tabla_id": "ID",
        "tabla_nombre": "Nombre",
        "tabla_rol": "Rol",
        "tabla_estado": "Estado",
        "tabla_acciones": "Acciones",
        "activo": "Activo",
        "inactivo": "Inactivo",
        
        # BOTONES COMUNES
        "aceptar": "Aceptar",
        "cancelar": "Cancelar",
        "guardar": "Guardar",
        "salir": "Salir",
        "volver": "Volver",
        "siguiente": "Siguiente",
        "anterior": "Anterior",
        
        # MENSAJES COMUNES
        "cargando": "Cargando...",
        "error": "Error",
        "exito": "Éxito",
        "confirmar": "¿Está seguro?",
        "sin_resultados": "Sin resultados",
    },
    
    # ─────────────────────────────────────────────────────────────────
    # ENGLISH
    # ─────────────────────────────────────────────────────────────────
    "en": {
        # TOP BAR
        "sistema": "CONTROL SYSTEM",
        "biometrico": "BIOMETRIC",
        "universidad": "University of Colima",
        
        # MAIN SCREEN
        "bienvenidos": "WELCOME",
        "subtitulo_principal": "Biometric Control System",
        "boton_acceder": "Access",
        "boton_gestion": "Management",
        "boton_aviso": "Privacy Notice",
        
        # PRIVACY NOTICE MODAL
        "aviso_titulo": "Privacy Notice",
        "aviso_contenido": (
            "PRIVACY NOTICE\n\n"
            "The University of Colima, through the Faculty of Electrical Engineering, "
            "is responsible for processing your biometric data.\n\n"
            "DATA WE COLLECT\n"
            "  • Facial image for biometric recognition\n"
            "  • Access records (date, time, laboratory)\n"
            "  • Identification data (name, student or employee ID)\n\n"
            "PURPOSE\n"
            "The collected data will be used exclusively for:\n"
            "  • Laboratory access control\n"
            "  • Facility usage traceability\n"
            "  • Institutional security\n\n"
            "STORAGE\n"
            "All information is processed and stored locally on the device. "
            "No data is transmitted to external servers or cloud services.\n\n"
            "DATA RIGHTS\n"
            "You have the right to Access, Rectify, Cancel or Object to the processing "
            "of your personal data, in accordance with the Federal Law for the Protection "
            "of Personal Data held by Private Parties.\n\n"
            "By pressing 'Accept', you grant your consent for the processing "
            "of your biometric data under the terms described."
        ),
        "boton_aceptar": "Accept",
        "boton_rechazar": "Reject",
        
        # LOGIN SCREEN
        "login_titulo": "Sign In",
        "usuario": "User",
        "contrasena": "Password",
        "ingresar": "Sign In",
        "error_credenciales": "Invalid user or password",
        
        # ACCESS SCREEN
        "acceso_titulo": "Access Control",
        "acceso_instrucciones": "Place your face in front of the camera",
        "acceso_cargando": "Scanning...",
        "acceso_exitoso": "Access Granted",
        "acceso_denegado": "Access Denied",
        
        # REGISTRATION SCREEN
        "registro_titulo": "User Registration",
        "registro_instrucciones": "Capture your face",
        "boton_registrar": "Register",
        "registro_exitoso": "User registered successfully",
        
        # MANAGEMENT SCREEN
        "gestion_titulo": "User Management",
        "gestion_buscar": "Search user",
        "gestion_agregar": "Add",
        "gestion_eliminar": "Delete",
        "gestion_editar": "Edit",
        "tabla_id": "ID",
        "tabla_nombre": "Name",
        "tabla_rol": "Role",
        "tabla_estado": "Status",
        "tabla_acciones": "Actions",
        "activo": "Active",
        "inactivo": "Inactive",
        
        # COMMON BUTTONS
        "aceptar": "Accept",
        "cancelar": "Cancel",
        "guardar": "Save",
        "salir": "Exit",
        "volver": "Back",
        "siguiente": "Next",
        "anterior": "Previous",
        
        # COMMON MESSAGES
        "cargando": "Loading...",
        "error": "Error",
        "exito": "Success",
        "confirmar": "Are you sure?",
        "sin_resultados": "No results",
    }
}


# ═════════════════════════════════════════════════════════════════════
# FUNCIÓN AUXILIAR PARA OBTENER TRADUCCIÓN
# ═════════════════════════════════════════════════════════════════════

def obtener_texto(idioma: str, clave: str, valor_defecto: str = "???") -> str:
    """
    Obtiene un texto traducido de forma segura.
    
    PARÁMETROS:
    -----------
    idioma : str
        Código de idioma ("es" o "en")
    clave : str
        Clave del texto a traducir
    valor_defecto : str
        Texto a retornar si la clave no existe
        
    RETORNA:
    --------
    str : El texto traducido o valor_defecto
    
    EJEMPLO:
    --------
    texto = obtener_texto("es", "bienvenidos")
    # Retorna: "BIENVENIDOS"
    """
    if idioma not in TRADUCCIONES:
        idioma = "es"  # Por defecto español si el idioma no existe
    
    diccionario = TRADUCCIONES[idioma]
    return diccionario.get(clave, valor_defecto)
