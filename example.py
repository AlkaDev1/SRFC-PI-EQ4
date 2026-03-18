
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from ui_styles import PALETA, configurar_estilos

#de nahum: los comentarios los puse con copilot (despues los resumi porque era mas comentario que codigo)

def actualizar_fecha_hora(label: ttk.Label, root: tk.Tk) -> None:
    # aca se actualiza la fecha y hora cada segundo
    fecha = datetime.now().strftime("Fecha: %d/%m/%Y")
    hora = datetime.now().strftime("Hora: %I:%M:%S %p")
    label.config(text=f"{fecha}\n{hora}") #aqui es cuando se muestra en la pantalla
    root.after(1000, lambda: actualizar_fecha_hora(label, root)) #se llama a si misma cada 1000 milisegundos (1 segundo) para actualizar la hora y haga ese efecto 


def crear_encabezado(parent: ttk.Frame, root: tk.Tk) -> None: 
    """Construye la barra superior similar a la referencia (marca + fecha + acciones)."""
    top_bar = ttk.Frame(parent, style="TopDark.TFrame")#crea un contenedor como el div de html
    top_bar.pack(fill="x") #lo hace horizontal y que ocupe todo el ancho disponible, como un header de pagina web, la "x" se refiere a que use todo

    # Bloque izquierdo con identidad institucional.
    brand = ttk.Frame(top_bar, style="Brand.TFrame") #el .Frame es un c9ntenedor 
    brand.pack(side="left", fill="y", ipadx=16, ipady=10) #brand pack es para ponerlo hasta la izquierda de la pantalla

    logo_path = Path(__file__).resolve().parent / "src" / "img" / "logoUDEC.png"
    if logo_path.exists():
        logo_img = tk.PhotoImage(file=str(logo_path)).subsample(8, 8) #aca se define el tamaño de la imagen de la Udeidad
        logo_label = ttk.Label(brand, image=logo_img, style="BrandTitle.TLabel")
        logo_label.image = logo_img
        logo_label.pack(side="left", padx=(12, 20))
    else:
        ttk.Label(brand, text="UNIVERSIDAD\nDE COLIMA", style="BrandTitle.TLabel").pack(side="left", padx=(12, 20))
    tk.Frame(brand, bg="#666666", width=5, height=60).pack(side="left", padx=10) #puse este y no tkkSeparator pq no soporta el width para hacer la linea mas gruesa 
    ttk.Label(brand, text="SISTEMA DE\nCONTROL\nBIOMETRICO", style="BrandSub.TLabel").pack(side="left", padx=10)


    # Bloque derecho con fecha/hora y botones auxiliares.
    right = ttk.Frame(top_bar, style="TopDark.TFrame")
    right.pack(side="left", fill="y", padx=(20, 0), pady=10)

    # contenedor con borde rojo para resaltar el bloque de fecha/hora, esto luego lo quito 
    caja_fecha_hora = tk.Frame(
        right,
        bg=PALETA["topbar_bg"], #se toma de los estilos (de PALETA) y abajo se le pone le color q quieras
        highlightbackground="red",
        highlightthickness=2, #grosor del borde
        bd=0, #sin borde adicional
        padx=8, #separacion horizontal 
        pady=6, #separaicon vertical
    )
    caja_fecha_hora.pack(side="left", padx=(0, 14))

    date_label = ttk.Label(caja_fecha_hora, style="Date.TLabel", justify="center")
    date_label.pack()
    actualizar_fecha_hora(date_label, root)

#botones de modo oscuro e idioma (sin funcionalidad por ahora)
    ttk.Button(right, text="modo oscuro", style="Ghost.TButton").pack(side="left", padx=5)
    ttk.Button(right, text="Idioma", style="Ghost.TButton").pack(side="left", padx=5)
    cambio_tema= ttk.Combobox(right, values=["Gris neutro(actual)", "Verde UdeC"], state="readonly", width=10)
    cambio_tema.current(0)

def crear_fila(parent: ttk.Frame, style: ttk.Style, valores: tuple[str, str, str, str, str], zebra: bool) -> None:
    """Dibuja una fila de la tabla y agrega botones de editar/eliminar."""
    color_fila = PALETA["row_a"] if zebra else PALETA["row_b"]

    fila = ttk.Frame(parent)
    fila.pack(fill="x")

    frame_estilo = f"Row{abs(hash(valores))}.TFrame"
    label_estilo = f"Row{abs(hash(valores))}.TLabel"
    style.configure(frame_estilo, background=color_fila)
    style.configure(label_estilo, background=color_fila, foreground=PALETA["title_fg"], font=("Segoe UI", 11))
    fila.configure(style=frame_estilo)

    anchos = [16, 18, 16, 16, 14]
    for idx, valor in enumerate(valores):
        ttk.Label(
            fila,
            text=valor,
            style=label_estilo,
            anchor="center",
            width=anchos[idx],
            padding=(6, 16),
        ).pack(side="left")

    acciones = ttk.Frame(fila)
    acciones.pack(side="left", padx=(8, 16))
    style.configure(f"Actions{abs(hash(valores))}.TFrame", background=color_fila)
    acciones.configure(style=f"Actions{abs(hash(valores))}.TFrame")

    ttk.Button(acciones, text="Editar", style="Ghost.TButton").pack(side="left", padx=6)
    ttk.Button(acciones, text="Eliminar", style="Ghost.TButton").pack(side="left", padx=6)


def crear_tabla(parent: ttk.Frame, style: ttk.Style) -> None:
    """Arma cabecera y filas de ejemplo para practicar diseño tipo CRUD."""
    header = ttk.Frame(parent)
    header.pack(fill="x")
    style.configure("HeaderRow.TFrame", background=PALETA["header_bg"])
    header.configure(style="HeaderRow.TFrame")

    headers = ["No. Institucional", "Nombre", "Fecha de registro", "Hora de registro", "Rol", "Acciones"]
    anchos = [16, 18, 16, 16, 14, 16]
    for i, texto in enumerate(headers):
        ttk.Label(
            header,
            text=texto,
            style="HeaderCell.TLabel",
            anchor="center",
            width=anchos[i],
            padding=(6, 12),
        ).pack(side="left")

    body = ttk.Frame(parent)
    body.pack(fill="x")

    rows = [
        ("20203455", "Nombre1", "01/03/26", "08:30 a.m", "Alumno"),
        ("20203456", "Nombre2", "01/03/26", "08:32 a.m", "Alumno"),
        ("20203457", "Nombre3", "01/03/26", "08:33 a.m", "Profesor"),
    ]

    for idx, row in enumerate(rows):
        crear_fila(body, style, row, zebra=(idx % 2 == 0))


def app() -> None:
    #__________________________1__________________________#
    #configuraciones generales de la ventana
    root = tk.Tk()
    root.title("Sistema de Control Biometrico")
    root.geometry("1200x760")
    root.minsize(1000, 650)
    root.configure(bg=PALETA["window_bg"])
    #__________________________FIN_1______________________#



    #__________________________2__________________________#
    #creacion y configuracion de estilos ttk
    style = ttk.Style()
    configurar_estilos(style)
    #__________________________FIN_2______________________#



    #__________________________3__________________________#
    #contenedor externo tipo marco de tablet
    frame_externo = tk.Frame(root, bg=PALETA["outer_frame"], padx=18, pady=18)
    frame_externo.pack(fill="both", expand=True)
    #__________________________FIN_3______________________#



    #__________________________4__________________________#
    #contenedor interno donde vive toda la interfaz
    pantalla = ttk.Frame(frame_externo, style="Page.TFrame")
    pantalla.pack(fill="both", expand=True)
    #__________________________FIN_4______________________#



    #__________________________5__________________________#
    #encabezado superior (marca, fecha y botones)
    crear_encabezado(pantalla, root)
    #__________________________FIN_5______________________#



    #__________________________6__________________________#
    #area principal de contenido
    contenido = ttk.Frame(pantalla, style="Page.TFrame", padding=30)
    contenido.pack(fill="both", expand=True)

    ttk.Label(contenido, text="GESTION DE USUARIOS", style="MainTitle.TLabel").pack(anchor="w", pady=(0, 20))
    #__________________________FIN_6______________________#



    #__________________________7__________________________#
    #barra de filtros y boton de agregar usuario
    barra = ttk.Frame(contenido, style="Page.TFrame")
    barra.pack(fill="x", pady=(0, 18))

    search = ttk.Entry(barra, width=24)
    search.insert(0, "Buscar...")
    search.pack(side="left", padx=(0, 12), ipady=4)

    rol_combo = ttk.Combobox(barra, values=["Todos los roles", "Alumno", "Profesor"], state="readonly", width=20)
    rol_combo.current(0)
    rol_combo.pack(side="left", padx=6)

    anio_combo = ttk.Combobox(barra, values=["2026", "2025", "2024"], state="readonly", width=10)
    anio_combo.current(0)
    anio_combo.pack(side="left", padx=6)

    ttk.Button(barra, text="+ Agregar usuario", style="Add.TButton").pack(side="right")
    #__________________________FIN_7______________________#



    #__________________________8__________________________#
    #tabla de usuarios
    tabla = ttk.Frame(contenido, style="Page.TFrame")
    tabla.pack(fill="x")
    crear_tabla(tabla, style)
    #__________________________FIN_8______________________#



    #__________________________9__________________________#
    #boton inferior para cerrar o regresar
    ttk.Button(contenido, text="< Regresar", style="Ghost.TButton", command=root.destroy).pack(anchor="w", pady=(24, 0))
    #__________________________FIN_9______________________#



    #__________________________10__________________________#
    #bucle principal de la aplicacion
    root.mainloop()
    #__________________________FIN_10______________________#




if __name__ == "__main__":
    #__________________________11__________________________#
    #punto de entrada del archivo
    app()
    #__________________________FIN_11______________________#