import tkinter as tk
from pathlib import Path
import math

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from ui.components.aviso_privacidad import mostrar_aviso

def dibujar_area_central(canvas: tk.Canvas, ancho: int, alto: int) -> None:
    canvas.delete("all")

    if ancho < 2 or alto < 2:
        return

    # Fondo blanco
    canvas.create_rectangle(0, 0, ancho, alto,
                            fill=PALETA["central_fondo"], outline="")

    # Área verde que se ve curveada
    inicio_y  = int(alto * 0.10)
    base_onda = int(alto * 0.80)
    amplitud  = int(alto * 0.10)

    puntos = [0, inicio_y]
    for i in range(61):
        x = ancho * i / 60
        y = base_onda + int(amplitud * math.sin(math.pi * i / 60))
        puntos += [x, y]
    puntos += [ancho, inicio_y, 0, inicio_y]

    canvas.create_polygon(puntos, fill=PALETA["central_onda"], outline="")

    # Texto BIENVENIDOS
    canvas.create_text(
        int(ancho * 0.65), int(alto * 0.38),
        text="BIENVENIDOS",
        font=FUENTES["bienvenida"],
        fill=PALETA["central_texto"],
        anchor="center",
    )

    # Círculo
    cx    = int(ancho * 0.22)
    cy    = int(alto  * 0.42)
    radio = int(min(ancho, alto) * 0.20)

    canvas.create_oval(
        cx - radio, cy - radio,
        cx + radio, cy + radio,
        fill=PALETA["central_circulo"],
        outline="",
    )

    # Logo en circulo
    ruta = Path(__file__).resolve().parent.parent.parent.parent / "src" / "img" / "pericos.png"
    if ruta.exists():
        img = tk.PhotoImage(file=str(ruta))
        canvas._img_mascota = img 
        canvas.create_image(cx, cy, image=img, anchor="center")
    else:
        canvas.create_text(
            cx, cy,
            text="🦜",
            font=("Segoe UI", int(radio * 0.7)),
            fill="#ffffff",
            anchor="center",
        )



def presionar_gestion() -> None:
    print("[BCK] Gestión → pendiente")

def aviso_aceptado() -> None:
    print("[BCK] Aviso aceptado")


# Patntalla principal

def crear_pantalla_principal(root, app) -> None:
    # Un solo frame que llena toda la ventana, pegado arriba
    pantalla = tk.Frame(root, bg=PALETA["page_bg"])
    pantalla.pack(fill="both", expand=True, side="top")

    #Barra superior
    crear_encabezado(pantalla, root)

    #Línea verde bajo la barra
    tk.Frame(
        pantalla,
        bg=PALETA["topbar_sistema_fg"],
        height=MEDIDAS["alto_linea_sep"],
    ).pack(fill="x")

    canvas = tk.Canvas(pantalla, bg=PALETA["central_fondo"], highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.bind(
        "<Configure>",
        lambda e: dibujar_area_central(canvas, e.width, e.height)
    )

    #Barra inferior de botones
    barra_botones = tk.Frame(pantalla, bg=PALETA["page_bg"], pady=14)
    barra_botones.pack(fill="x")

    contenedor = tk.Frame(barra_botones, bg=PALETA["page_bg"])
    contenedor.pack(anchor="center")

    # Estilo compartido de los tres botones
    estilo = dict(
        font=FUENTES["boton_principal"],
        fg=PALETA["boton_fg"],
        bg=PALETA["boton_bg"],
        activebackground=PALETA["boton_hover"],
        activeforeground="#ffffff",
        bd=0,
        padx=MEDIDAS["padding_boton_x"],
        pady=MEDIDAS["padding_boton_y"],
        cursor="hand2",
        relief="flat",
        width=18,
    )

    tk.Button(contenedor, text=" 🔑 ACCEDER",
              command=lambda: app.mostrar_pantalla("acceso"),
              **estilo).pack(side="left", padx=MEDIDAS["margen_boton"])

    tk.Button(contenedor, text=" ⚙ GESTIÓN",
              command=presionar_gestion,
              **estilo).pack(side="left", padx=MEDIDAS["margen_boton"])

    tk.Button(contenedor, text=" 🔒 AVISO DE PRIVACIDAD",
              command=lambda: mostrar_aviso(root, al_aceptar=aviso_aceptado),
              **estilo).pack(side="left", padx=MEDIDAS["margen_boton"])