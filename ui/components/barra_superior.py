import tkinter as tk
from datetime import datetime
from pathlib import Path

# --- Colores de tu diseño original ---
V_DARK   = "#1B5E20"
V_ACCENT = "#66BB6A"
BLANCO   = "#FFFFFF"
V_LIGHT  = "#43A047"
TEXTO_DIM= "#A5D6A7"

def actualizar_fecha_hora(lbl_fecha: tk.Label, lbl_hora: tk.Label, root: tk.Tk) -> None:
    n = datetime.now()
    DIAS  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    MESES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    
    lbl_fecha.config(text=f"FECHA: {DIAS[n.weekday()]} {n.day} de {MESES[n.month-1]} {n.year}")
    h = n.strftime("%I:%M:%S %p").lower().replace("am","a.m").replace("pm","p.m")
    lbl_hora.config(text=f"Hora: {h}")
    
    root.after(1000, lambda: actualizar_fecha_hora(lbl_fecha, lbl_hora, root))

def crear_encabezado(parent: tk.Frame, root: tk.Tk) -> None:
    top_bar = tk.Frame(parent, bg=V_DARK, height=72)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)

    # --- Logo en pastilla blanca ---
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

    # --- Separador + nombre sistema ---
    tk.Frame(top_bar, bg=V_ACCENT, width=2).pack(side="left", fill="y", pady=14, padx=10)
    col = tk.Frame(top_bar, bg=V_DARK)
    col.pack(side="left")
    tk.Label(col, text="SISTEMA DE CONTROL", font=("Segoe UI", 9, "bold"), fg=V_ACCENT, bg=V_DARK).pack(anchor="w")
    tk.Label(col, text="BIOMÉTRICO", font=("Segoe UI", 10, "bold"), fg=BLANCO, bg=V_DARK).pack(anchor="w")
    tk.Label(col, text="Universidad de Colima", font=("Segoe UI", 8), fg=TEXTO_DIM, bg=V_DARK).pack(anchor="w")

    # --- Derecha: fecha/hora + botones ---
    der = tk.Frame(top_bar, bg=V_DARK)
    der.pack(side="right", padx=14, fill="y")

    # Contenedor para los botones
    btn_f = tk.Frame(der, bg=V_DARK)
    btn_f.pack(side="right", padx=(8,0), pady=18)

    # 1. Botón de Idioma
    ruta_icono_idioma = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "languageIcon.png"
    btn_idioma = tk.Label(btn_f, bg=V_LIGHT, padx=7, pady=2, cursor="hand2")

    if ruta_icono_idioma.exists():
        img_idioma = tk.PhotoImage(file=str(ruta_icono_idioma))
        btn_idioma.config(image=img_idioma)
        btn_idioma.image = img_idioma  # Proteger de recolección de basura
    else:
        btn_idioma.config(text="🌐", font=("Segoe UI", 14), fg=BLANCO)


    btn_idioma.pack(side="right", padx=3)
    btn_idioma.bind("<Enter>", lambda e, w=btn_idioma: w.config(bg=V_ACCENT))
    btn_idioma.bind("<Leave>", lambda e, w=btn_idioma: w.config(bg=V_LIGHT))

    # 2. Botón de Modo Oscuro
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

    # --- Fecha y Hora ---
    dt = tk.Frame(der, bg=V_DARK)
    dt.pack(side="right", pady=10)
    lbl_fecha = tk.Label(dt, text="", font=("Segoe UI", 10, "bold"), fg=BLANCO, bg=V_DARK)
    lbl_fecha.pack(anchor="e")
    lbl_hora = tk.Label(dt, text="", font=("Segoe UI", 10), fg=TEXTO_DIM, bg=V_DARK)
    lbl_hora.pack(anchor="e")

    # Iniciar el reloj
    actualizar_fecha_hora(lbl_fecha, lbl_hora, root)