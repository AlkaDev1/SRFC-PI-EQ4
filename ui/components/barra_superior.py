import tkinter as tk
from datetime import datetime
from pathlib import Path

from ui.styles import PALETA, FUENTES, MEDIDAS


def actualizar_fecha_hora(lbl_fecha: tk.Label, lbl_hora: tk.Label, root: tk.Tk) -> None:
    ahora = datetime.now()

    fecha_str = ahora.strftime("%A %d de %B %Y").capitalize()
    lbl_fecha.config(text=f"FECHA: {fecha_str}")

    hora_str = ahora.strftime("%I:%M:%S %p").lower()
    hora_str = hora_str.replace("am", "a.m").replace("pm", "p.m")
    lbl_hora.config(text=f"Hora: {hora_str}")

    root.after(1000, lambda: actualizar_fecha_hora(lbl_fecha, lbl_hora, root))


def crear_encabezado(parent: tk.Frame, root: tk.Tk) -> None:
    top_bar = tk.Frame(parent, bg=PALETA["topbar_bg"], height=MEDIDAS["alto_topbar"])
    top_bar.pack(fill="x", side="top") 
    top_bar.pack_propagate(False)

    bloque_izq = tk.Frame(top_bar, bg=PALETA["topbar_brand_bg"])
    bloque_izq.pack(side="left", fill="y")

    #Logo
    ruta_logo = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "logoudc.png"

    #imprime la ruta para verificar que sea correcta
    print(f"Buscando logo en: {ruta_logo}")
    print(f"Existe: {ruta_logo.exists()}")

    if ruta_logo.exists():
        img_logo = tk.PhotoImage(file=str(ruta_logo))
        
        # Ajustar tamaño según qué tan grande sea la imagen
        ancho_img = img_logo.width()
        if ancho_img > 200:
            img_logo = img_logo.subsample(3, 3) 
        elif ancho_img > 100:
            img_logo = img_logo.subsample(2, 2)
        
        lbl_logo = tk.Label(bloque_izq, image=img_logo, bg=PALETA["topbar_brand_bg"])
        lbl_logo.image = img_logo
        lbl_logo.pack(side="left", padx=(14, 8), pady=8)

    # Separador vertical verde
    tk.Frame(
        bloque_izq,
        bg=PALETA["topbar_linea_vert"],
        width=4,
    ).pack(side="left", fill="y", pady=10)

    # Nombre del sistema
    tk.Label(
        bloque_izq,
        text="SISTEMA DE\nCONTROL\nBIOMÉTRICO",
        font=FUENTES["topbar_sistema"],
        fg=PALETA["topbar_sistema_fg"],
        bg=PALETA["topbar_brand_bg"],
        justify="left",
    ).pack(side="left", padx=12, pady=8)


    # Fecha, hora , boton de modo oscuro e idioma
    bloque_der = tk.Frame(top_bar, bg=PALETA["topbar_bg"])
    bloque_der.pack(side="right", fill="y", padx=16)

    #Boton idioma
    tk.Button(
        bloque_der,
        text="ES | EN",
        font=FUENTES["topbar_boton"],
        fg=PALETA["topbar_btn_fg"],
        bg=PALETA["topbar_btn_bg"],
        activebackground=PALETA["topbar_btn_hover"],
        activeforeground=PALETA["topbar_btn_fg"],
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
        relief="flat",
    ).pack(side="right", padx=(6, 0), pady=20)

    #Botón modo oscuro
    tk.Button(
        bloque_der,
        text="☀",
        font=("Segoe UI", 14),
        fg=PALETA["topbar_sistema_fg"],
        bg=PALETA["topbar_btn_bg"],
        activebackground=PALETA["topbar_btn_hover"],
        activeforeground=PALETA["topbar_btn_fg"],
        bd=0,
        padx=8,
        pady=4,
        cursor="hand2",
        relief="flat",
    ).pack(side="right", padx=6, pady=20)

    #Fecha y hora
    frame_fecha = tk.Frame(bloque_der, bg=PALETA["topbar_bg"])
    frame_fecha.pack(side="right", padx=(0, 16), pady=8)

    lbl_fecha = tk.Label(
        frame_fecha,
        text="",
        font=FUENTES["topbar_fecha"],
        fg=PALETA["topbar_fecha_fg"],
        bg=PALETA["topbar_bg"],
        justify="center",
    )
    lbl_fecha.pack()

    lbl_hora = tk.Label(
        frame_fecha,
        text="",
        font=FUENTES["topbar_fecha"],
        fg=PALETA["topbar_hora_fg"],
        bg=PALETA["topbar_bg"],
        justify="center",
    )
    lbl_hora.pack()

    # Iniciar el reloj
    actualizar_fecha_hora(lbl_fecha, lbl_hora, root)