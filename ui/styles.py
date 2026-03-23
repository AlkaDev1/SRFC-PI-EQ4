"""Estilos globales para la interfaz SRFC.

Este archivo concentra colores, tipografias y helpers visuales.
"""

from tkinter import ttk

# [BLOQUE 1] INICIO - Paleta de colores
COLOR_FONDO = "#F4F7FB"
COLOR_TARJETA = "#FFFFFF"
COLOR_PRIMARIO = "#0F4C81"
COLOR_PRIMARIO_HOVER = "#0C3C66"
COLOR_TEXTO = "#1F2937"
COLOR_TEXTO_SUAVE = "#6B7280"
# [BLOQUE 1] FIN - Paleta de colores


# [BLOQUE 2] INICIO - Tipografias
FUENTE_TITULO = ("Segoe UI", 20, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 11)
FUENTE_BOTON = ("Segoe UI", 11, "bold")
# [BLOQUE 2] FIN - Tipografias


# [BLOQUE 3] INICIO - Configuracion de ventana
ANCHO_VENTANA = 900
ALTO_VENTANA = 560
TITULO_APP = "SRFC - Sistema de Registro Facial"
# [BLOQUE 3] FIN - Configuracion de ventana


# [BLOQUE 4] INICIO - Helpers de estilo
def estilo_boton_primario() -> dict:
	"""Retorna un diccionario con estilo uniforme para botones primarios."""
	return {
		"bg": COLOR_PRIMARIO,
		"fg": "white",
		"activebackground": COLOR_PRIMARIO_HOVER,
		"activeforeground": "white",
		"relief": "flat",
		"bd": 0,
		"cursor": "hand2",
		"font": FUENTE_BOTON,
		"padx": 16,
		"pady": 10,
	}


def estilo_frame_tarjeta() -> dict:
	"""Retorna opciones visuales para contenedores tipo tarjeta."""
	return {
		"bg": COLOR_TARJETA,
		"bd": 1,
		"relief": "solid",
		"highlightthickness": 0,
	}
# [BLOQUE 4] FIN - Helpers de estilo


# [BLOQUE 5] INICIO - Temas ttk para vista de gestion
PALETA = {
	"window_bg": "#e6eaef",
	"outer_frame": "#2f3a45",
	"topbar_bg": "#32414d",
	"brand_bg": "#eef1f4",
	"page_bg": "#f5f7f9",
	"title_fg": "#1f2a33",
	"sub_fg": "#2f3c47",
	"date_fg": "#f5f7f9",
	"header_bg": "#6fa67a",
	"header_active": "#5f956a",
	"ghost_bg": "#edf1f5",
	"ghost_active": "#dde4ec",
	"row_a": "#f9fbfc",
	"row_b": "#f1f5f7",
}

PALETA_VERDE_UDEC = {
	"verde_claro": "#64B32E",
	"verde_oscuro": "#527630",
	"gris_oscuro": "#4E4D4D",
	"gris_medio": "#8E8E8E",
	"gris_claro": "#B4B4B4",
	"beige": "#E4BA8B",
	"naranja": "#FBB034",
	"amarillo": "#FFD100",
	"limon": "#C1D82F",
	"azul": "#00A4E4",
	"window_bg": "#B4B4B4",
	"outer_frame": "#527630",
	"topbar_bg": "#4E4D4D",
	"brand_bg": "#E4BA8B",
	"page_bg": "#B4B4B4",
	"title_fg": "#4E4D4D",
	"sub_fg": "#527630",
	"date_fg": "#FFFFFF",
	"header_bg": "#64B32E",
	"header_active": "#527630",
	"ghost_bg": "#E4BA8B",
	"ghost_active": "#FFD100",
	"row_a": "#B4B4B4",
	"row_b": "#8E8E8E",
}

PALETA_OSCURO = {
	"window_bg": "#1a1a1a",
	"outer_frame": "#0f0f0f",
	"topbar_bg": "#1e1e1e",
	"brand_bg": "#2a2a2a",
	"page_bg": "#1f1f1f",
	"title_fg": "#e0e0e0",
	"sub_fg": "#b0b0b0",
	"date_fg": "#ffffff",
	"header_bg": "#27ae60",
	"header_active": "#1e8449",
	"ghost_bg": "#3a3a3a",
	"ghost_active": "#4a4a4a",
	"row_a": "#252525",
	"row_b": "#2f2f2f",
}


def configurar_estilos(style: ttk.Style, paleta: dict | None = None) -> None:
	paleta = paleta or PALETA
	style.theme_use("clam")

	style.configure("TopDark.TFrame", background=paleta["topbar_bg"])
	style.configure("Brand.TFrame", background=paleta["brand_bg"])
	style.configure("Page.TFrame", background=paleta["page_bg"])

	style.configure(
		"BrandTitle.TLabel",
		font=("Segoe UI", 20, "bold"),
		foreground=paleta["title_fg"],
		background=paleta["brand_bg"],
	)
	style.configure(
		"BrandSub.TLabel",
		font=("Segoe UI", 10, "bold"),
		foreground=paleta["sub_fg"],
		background=paleta["brand_bg"],
	)
	style.configure(
		"Date.TLabel",
		font=("Segoe UI", 11, "bold"),
		foreground=paleta["date_fg"],
		background=paleta["topbar_bg"],
	)
	style.configure(
		"MainTitle.TLabel",
		font=("Segoe UI", 30, "bold"),
		foreground=paleta["title_fg"],
		background=paleta["page_bg"],
	)
	style.configure(
		"SectionTitle.TLabel",
		font=("Segoe UI", 18, "bold"),
		foreground=paleta["title_fg"],
		background=paleta["page_bg"],
	)
	style.configure(
		"PageSub.TLabel",
		font=("Segoe UI", 10, "bold"),
		foreground=paleta["sub_fg"],
		background=paleta["page_bg"],
	)
	style.configure(
		"HeaderCell.TLabel",
		font=("Segoe UI", 11, "bold"),
		foreground="#ffffff",
		background=paleta["header_bg"],
	)

	style.configure(
		"Add.TButton",
		font=("Segoe UI", 11, "bold"),
		foreground="#ffffff",
		background=paleta["header_bg"],
		borderwidth=0,
		padding=(16, 8),
	)
	style.map("Add.TButton", background=[("active", paleta["header_active"])])

	style.configure(
		"Ghost.TButton",
		font=("Segoe UI", 10, "bold"),
		foreground=paleta["sub_fg"],
		background=paleta["ghost_bg"],
		borderwidth=1,
		padding=(10, 5),
	)
	style.map("Ghost.TButton", background=[("active", paleta["ghost_active"])])
# [BLOQUE 5] FIN - Temas ttk para vista de gestion
