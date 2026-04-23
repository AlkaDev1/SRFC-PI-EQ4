import tkinter as tk
from datetime import datetime
from pathlib import Path

# Importar el gestor de idiomas SINGLETON
from core.language_manager import LanguageManager
from core.translations import obtener_texto

# --- Colores de tu diseño original ---
V_DARK   = "#1B5E20"
V_ACCENT = "#66BB6A"
BLANCO   = "#FFFFFF"
V_LIGHT  = "#43A047"
TEXTO_DIM= "#A5D6A7"

# ═════════════════════════════════════════════════════════════════════
# FUNCIONES DE ACTUALIZACIÓN DINÁMICA
# ═════════════════════════════════════════════════════════════════════

def actualizar_fecha_hora(lbl_fecha: tk.Label, lbl_hora: tk.Label, root: tk.Tk) -> None:
    """
    ACTUALIZA LA FECHA Y HORA CADA SEGUNDO
    
    ORDEN DE EJECUCIÓN:
    1. Verifica que los widgets existan (no hayan sido destruidos)
    2. Obtiene la fecha/hora actual
    3. Formatea según el idioma actual
    4. Actualiza las etiquetas
    5. Se programa a sí misma para ejecutar en 1000ms
    
    NOTA: Los días y meses se traduce según el idioma actual
    """
    if not lbl_fecha.winfo_exists() or not lbl_hora.winfo_exists():
        return  # Si alguna etiqueta fue destruida, no continua
    
    n = datetime.now()
    
    # ══════════════════════════════════════════════════════════════
    # NOMBRES EN ESPAÑOL - Se usan cuando idioma es "es"
    # ══════════════════════════════════════════════════════════════
    DIAS_ES  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    
    # ══════════════════════════════════════════════════════════════
    # NOMBRES EN INGLÉS - Se usan cuando idioma es "en"
    # ══════════════════════════════════════════════════════════════
    DIAS_EN  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    MESES_EN = ["January","February","March","April","May","June",
            "July","August","September","October","November","December"]
    
    # Obtener idioma actual desde el gestor
    manager = LanguageManager.obtener_instancia()
    idioma = manager.obtener_idioma_actual()
    
    # Seleccionar nombres según idioma
    if idioma == "en":
        DIAS = DIAS_EN
        MESES = MESES_EN
    else:
        DIAS = DIAS_ES
        MESES = MESES_ES
    
    # Formar la fecha
    fecha = f"{DIAS[n.weekday()]} {n.day} {MESES[n.month-1]} {n.year}"
    lbl_fecha.config(text=fecha)

    # Hora en formato 12h con am/pm
    hora = n.strftime("%I:%M:%S %p").lower().replace("am", "a.m.").replace("pm", "p.m.")
    lbl_hora.config(text=hora)
    
    # Programar próxima actualización en 1 segundo
    root.after(1000, lambda: actualizar_fecha_hora(lbl_fecha, lbl_hora, root))

def crear_encabezado(parent: tk.Frame, root: tk.Tk) -> None:
    """
    CREA LA BARRA SUPERIOR (TOP BAR)
    
    COMPONENTES:
    1. Logo de la Universidad
    2. Título del sistema
    3. Botón de idioma (TOGGLE)
    4. Botón de modo oscuro
    5. Fecha y hora (actualiza cada segundo)
    
    ORDEN DE EJECUCIÓN:
    1. Crea frame principal para la barra
    2. Añade logo
    3. Añade nombre del sistema
    4. Añade botones (lado derecho)
    5. Inicia actualización de fecha/hora
    """
    # ═════════════════════════════════════════════════════════════════
    # FRAME PRINCIPAL DE LA BARRA
    # ═════════════════════════════════════════════════════════════════
    top_bar = tk.Frame(parent, bg=V_DARK, height=72)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)  # Mantener altura fija

    # ═════════════════════════════════════════════════════════════════
    # SECCIÓN IZQUIERDA: LOGO
    # ═════════════════════════════════════════════════════════════════
    logo_wrap = tk.Frame(top_bar, bg=V_DARK)
    logo_wrap.pack(side="left", padx=(14, 0), pady=0, fill="y")
    
    ruta_logo = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "logoudc.png"
    if ruta_logo.exists():
        try:
            raw = tk.PhotoImage(file=str(ruta_logo))
            lbl_logo = tk.Label(logo_wrap, image=raw, bg=V_DARK) 
            lbl_logo.image = raw # Proteger de recolección de basura
            lbl_logo.pack()
        except Exception as e:
            tk.Label(logo_wrap, text="UdC", font=("Segoe UI", 12, "bold"), fg=V_DARK, bg=BLANCO).pack()
    else:
        tk.Label(logo_wrap, text="UdC", font=("Segoe UI", 12, "bold"), fg=V_DARK, bg=BLANCO).pack()

    # ═════════════════════════════════════════════════════════════════
    # SECCIÓN IZQUIERDA-CENTRO: NOMBRE DEL SISTEMA
    # ═════════════════════════════════════════════════════════════════
    tk.Frame(top_bar, bg=V_ACCENT, width=2).pack(side="left", fill="y", pady=14, padx=10)
    col = tk.Frame(top_bar, bg=V_DARK)
    col.pack(side="left")
    
    # Obtener el gestor de idiomas
    manager = LanguageManager.obtener_instancia()
    idioma = manager.obtener_idioma_actual()
    
    # Mostrar textos en el idioma actual
    texto_sistema = obtener_texto(idioma, "sistema")
    texto_biometrico = obtener_texto(idioma, "biometrico")
    texto_universidad = obtener_texto(idioma, "universidad")
    
    lbl_sistema = tk.Label(col, text=texto_sistema, font=("Segoe UI", 9, "bold"), fg=V_ACCENT, bg=V_DARK)
    lbl_sistema.pack(anchor="w")
    lbl_biometrico = tk.Label(col, text=texto_biometrico, font=("Segoe UI", 10, "bold"), fg=BLANCO, bg=V_DARK)
    lbl_biometrico.pack(anchor="w")
    lbl_universidad = tk.Label(col, text=texto_universidad, font=("Segoe UI", 8), fg=TEXTO_DIM, bg=V_DARK)
    lbl_universidad.pack(anchor="w")

    # ═════════════════════════════════════════════════════════════════
    # SECCIÓN DERECHA: BOTONES Y FECHA/HORA
    # ═════════════════════════════════════════════════════════════════
    der = tk.Frame(top_bar, bg=V_DARK)
    der.pack(side="right", padx=14, fill="y")

    # Contenedor para los botones (lado derecho)
    btn_f = tk.Frame(der, bg=V_DARK)
    btn_f.pack(side="right", padx=(8,0), pady=18)

    # ═════════════════════════════════════════════════════════════════
    # BOTÓN DE IDIOMA (TOGGLE)
    # ═════════════════════════════════════════════════════════════════
    # Este botón cambia entre español e inglés
    # FLUJO:
    # 1. Usuario hace clic
    # 2. Se obtiene idioma opuesto
    # 3. Se llama a cambiar_idioma()
    # 4. LanguageManager notifica a todos los callbacks
    # 5. Las pantallas se actualizan automáticamente
    
    ruta_icono_idioma = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "languageIcon.png"
    
    # Frame para el toggle de idioma (mostrará "ES" o "EN")
    idioma_frame = tk.Frame(btn_f, bg=V_LIGHT, padx=7, pady=2)
    idioma_frame.pack(side="right", padx=3)
    
    # Obtener idioma actual
    idioma_actual = manager.obtener_idioma_actual()
    
    # Label que mostrará "ES" o "EN"
    lbl_idioma_toggle = tk.Label(
        idioma_frame,
        text=idioma_actual.upper(),
        font=("Segoe UI", 11, "bold"),
        fg=BLANCO,
        bg=V_LIGHT,
        cursor="hand2"
    )
    lbl_idioma_toggle.pack()
    
    def cambiar_idioma_handler():
        """
        MANEJADOR DE CLIC DEL BOTÓN DE IDIOMA
        
        ORDEN DE EJECUCIÓN:
        1. Obtiene el idioma opuesto (es → en, en → es)
        2. Llama al LanguageManager para cambiar
        3. LanguageManager guarda la preferencia
        4. LanguageManager ejecuta TODOS los callbacks
        5. Las pantallas activas se actualizan
        6. Actualizar el texto del botón
        """
        # Obtener idioma opuesto
        nuevo_idioma = manager.obtener_idioma_opuesto()
        
        # Cambiar el idioma (esto notifica a todos)
        manager.cambiar_idioma(nuevo_idioma)
        
        # Actualizar el texto del botón para reflejar el nuevo estado
        lbl_idioma_toggle.config(text=nuevo_idioma.upper())
        
        # Actualizar los textos en la barra si existen (comentado por si no están disponibles)
        try:
            lbl_sistema.config(text=obtener_texto(nuevo_idioma, "sistema"))
            lbl_biometrico.config(text=obtener_texto(nuevo_idioma, "biometrico"))
            lbl_universidad.config(text=obtener_texto(nuevo_idioma, "universidad"))
        except:
            pass  # Si hay error, simplemente continuar
    
    # Bind del evento de clic
    lbl_idioma_toggle.bind("<Button-1>", lambda e: cambiar_idioma_handler())
    
    # Efectos de hover
    lbl_idioma_toggle.bind("<Enter>", lambda e, w=idioma_frame: w.config(bg=V_ACCENT))
    lbl_idioma_toggle.bind("<Leave>", lambda e, w=idioma_frame: w.config(bg=V_LIGHT))

    # ═════════════════════════════════════════════════════════════════
    # BOTÓN DE MODO OSCURO (Placeholder - no implementado aún)
    # ═════════════════════════════════════════════════════════════════
    ruta_icono_dia = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "lightModeIcon.png"
    btn_modo_oscuro = tk.Label(btn_f, bg=V_LIGHT, padx=7, pady=2, cursor="hand2")
    
    if ruta_icono_dia.exists():
        img_dia = tk.PhotoImage(file=str(ruta_icono_dia))
        btn_modo_oscuro.config(image=img_dia)
        btn_modo_oscuro.image = img_dia  # Proteger de recolección de basura
    else:
        btn_modo_oscuro.config(text="☀", font=("Segoe UI", 14), fg=BLANCO)
        
    btn_modo_oscuro.pack(side="right", padx=3)

    btn_modo_oscuro.bind("<Enter>", lambda e, w=btn_modo_oscuro: w.config(bg=V_ACCENT))
    btn_modo_oscuro.bind("<Leave>", lambda e, w=btn_modo_oscuro: w.config(bg=V_LIGHT))

    # ═════════════════════════════════════════════════════════════════
    # SECCIÓN: FECHA Y HORA
    # ═════════════════════════════════════════════════════════════════
    # Se actualiza cada segundo automáticamente
    
    dt = tk.Frame(der, bg=V_DARK)
    dt.pack(side="right", pady=10)

    # Fila de fecha
    fila_fecha = tk.Frame(dt, bg=V_DARK)
    fila_fecha.pack(anchor="e")

    ruta_calendar_icon = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "calendar_Icon.png"
    if ruta_calendar_icon.exists():
        raw_calendar = tk.PhotoImage(file=str(ruta_calendar_icon))
        factor_c = max(1, round(raw_calendar.height() / 18))
        img_calendar = raw_calendar.subsample(factor_c, factor_c)

        lbl_ico_fecha = tk.Label(fila_fecha, image=img_calendar, bg=V_DARK)
        lbl_ico_fecha.image = img_calendar  # Proteger de recolección de basura
        lbl_ico_fecha.pack(side="left", padx=(0,4), pady=(2,0))

    lbl_fecha = tk.Label(fila_fecha, text= "",  font=("Segoe UI", 10, "bold"), fg=BLANCO, bg=V_DARK)
    lbl_fecha.pack(side="left")

    # Fila de hora
    fila_hora = tk.Frame(dt, bg=V_DARK)
    fila_hora.pack(anchor="e")

    ruta_clock_icon = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "clockIcon.png"
    if ruta_clock_icon.exists():
        raw_clock = tk.PhotoImage(file=str(ruta_clock_icon))
        factor_h = max(1, round(raw_clock.height() / 18))
        img_clock = raw_clock.subsample(factor_h, factor_h)

        lbl_ico_hora = tk.Label(fila_hora, image=img_clock, bg=V_DARK)
        lbl_ico_hora.image = img_clock  # Proteger de recolección de basura
        lbl_ico_hora.pack(side="left", padx=(0,4))
    
    lbl_hora = tk.Label(fila_hora, text="", font=("Segoe UI", 10), fg=TEXTO_DIM, bg=V_DARK)
    lbl_hora.pack(side="left")

    # Iniciar el reloj (se actualiza cada segundo)
    actualizar_fecha_hora(lbl_fecha, lbl_hora, root)