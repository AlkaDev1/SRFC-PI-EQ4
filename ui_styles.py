from tkinter import ttk

PALETA = {

    #Ventana principal
    "window_bg":            "#e6eaef",  
    "page_bg":              "#ffffff",  

    #Barra superior (topbar)
    "topbar_bg":            "#ffffff",   
    "topbar_brand_bg":      "#ffffff",  
    "topbar_titulo_fg":     "#003087",   
    "topbar_sistema_fg":    "#3A8C3F",  
    "topbar_fecha_fg":      "#3A8C3F",  
    "topbar_hora_fg":       "#003087",   
    "topbar_separador":     "#cccccc",   
    "topbar_linea_vert":    "#3A8C3F",  

    #Botones de la topbar (modo oscuro / idioma)
    "topbar_btn_bg":        "#e8f5e9",   # Fondo verde muy claro
    "topbar_btn_fg":        "#2A6B2E",   # Texto verde oscuro
    "topbar_btn_hover":     "#c8e6c9",   # Verde claro al pasar el mouse

    #Área central
    "central_fondo":        "#ffffff",   # Fondo blanco detrás de la onda
    "central_onda":         "#4CAF50",   # Verde principal de la onda
    "central_circulo":      "#3A8C3F",   # Verde oscuro del círculo mascota
    "central_texto":        "#ffffff",   # Color del texto "BIENVENIDOS"

    #Botones principales (Acceder / Gestión / Aviso)
    "boton_bg":             "#5cb85c",   # Verde del botón
    "boton_fg":             "#ffffff",   # Texto blanco del botón
    "boton_hover":          "#4cae4c",   # Verde más oscuro al pasar el mouse
    "boton_borde":          "#4cae4c",   # Borde del botón

    #Modal Aviso de Privacidad
    "modal_bg":             "#ffffff",
    "modal_header_bg":      "#4CAF50",   # Encabezado verde
    "modal_header_fg":      "#ffffff",
    "modal_texto_bg":       "#f5f7f9",   # Fondo del cuadro de texto
    "modal_texto_fg":       "#1f2a33",
    "modal_btn_cerrar_bg":  "#e8f0fe",
    "modal_btn_cerrar_fg":  "#2f3c47",

    #Tabla (pantalla de gestión)
    "header_bg":            "#6fa67a",
    "header_active":        "#5f956a",
    "ghost_bg":             "#edf1f5",
    "ghost_active":         "#dde4ec",
    "row_a":                "#f9fbfc",
    "row_b":                "#f1f5f7",
    "sub_fg":               "#2f3c47",
    "title_fg":             "#1f2a33",
}


FUENTES = {
    # Barra superior
    "topbar_institucion":   ("Segoe UI", 13, "bold"),   # "UNIVERSIDAD DE COLIMA"
    "topbar_sistema":       ("Segoe UI", 10, "bold"),   # "SISTEMA DE CONTROL..."
    "topbar_fecha":         ("Segoe UI", 11, "bold"),   # Fecha y hora
    "topbar_boton":         ("Segoe UI", 9,  "bold"),   # Botones modo/idioma

    # Área central
    "bienvenida":           ("Segoe UI", 38, "bold"),   # "BIENVENIDOS"

    # Botones principales
    "boton_principal":      ("Segoe UI", 13, "bold"),

    # Modal
    "modal_titulo":         ("Segoe UI", 14, "bold"),
    "modal_texto":          ("Segoe UI", 11),

    # Gestión
    "tabla_header":         ("Segoe UI", 11, "bold"),
    "tabla_fila":           ("Segoe UI", 11),
    "titulo_pantalla":      ("Segoe UI", 30, "bold"),
}

MEDIDAS = {
    # Ventana - Pantalla de 7 pulgadas (fija, no redimensionable)
    "ancho_ventana":        800,
    "alto_ventana":         480,
    "min_ancho":            800,
    "min_alto":             480,

    # Barra superior
    "alto_topbar":          75,
    "alto_linea_sep":       3,

    # Botones principales
    "alto_boton":           200,
    "ancho_boton":          30,
    "margen_boton":         13,    # Espacio entre botones
    "padding_boton_x":      14,
    "padding_boton_y":      14,
}


#estilos definidos por josue
def configurar_estilos(style: ttk.Style) -> None:
    style.theme_use("clam")

    style.configure("Page.TFrame",  background=PALETA["page_bg"])
    style.configure("TopDark.TFrame", background=PALETA["topbar_bg"])
    style.configure("Brand.TFrame", background=PALETA["topbar_brand_bg"])

    style.configure(
        "Add.TButton",
        font=FUENTES["boton_principal"],
        foreground="#ffffff",
        background=PALETA["header_bg"],
        borderwidth=0,
        padding=(16, 8),
    )
    style.map("Add.TButton", background=[("active", PALETA["header_active"])])

    style.configure(
        "Ghost.TButton",
        font=("Segoe UI", 10, "bold"),
        foreground=PALETA["sub_fg"],
        background=PALETA["ghost_bg"],
        borderwidth=1,
        padding=(10, 5),
    )
    style.map("Ghost.TButton", background=[("active", PALETA["ghost_active"])])

    style.configure(
        "HeaderCell.TLabel",
        font=FUENTES["tabla_header"],
        foreground="#ffffff",
        background=PALETA["header_bg"],
    )
    style.configure(
        "MainTitle.TLabel",
        font=FUENTES["titulo_pantalla"],
        foreground=PALETA["title_fg"],
        background=PALETA["page_bg"],
    )
