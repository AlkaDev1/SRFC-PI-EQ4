from tkinter import ttk


#__________________________1__________________________#
#paleta de color suave (baja fatiga visual)
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
#__________________________FIN_1______________________#


#__________________________2__________________________#
#configuracion general de estilos ttk

def configurar_estilos(style: ttk.Style) -> None:
    style.theme_use("clam")

    #__________________________2_1__________________________#
    #frames base
    style.configure("TopDark.TFrame", background=PALETA["topbar_bg"])
    style.configure("Brand.TFrame", background=PALETA["brand_bg"])
    style.configure("Page.TFrame", background=PALETA["page_bg"])
    #__________________________FIN_2_1______________________#

    #__________________________2_2__________________________#
    #labels tipograficos
    style.configure(
        "BrandTitle.TLabel",
        font=("Segoe UI", 20, "bold"),
        foreground=PALETA["title_fg"],
        background=PALETA["brand_bg"],
    )
    style.configure(
        "BrandSub.TLabel",
        font=("Segoe UI", 10, "bold"),
        foreground=PALETA["sub_fg"],
        background=PALETA["brand_bg"],
    )
    style.configure(
        "Date.TLabel",
        font=("Segoe UI", 11, "bold"),
        foreground=PALETA["date_fg"],
        background=PALETA["topbar_bg"],
    )
    style.configure(
        "MainTitle.TLabel",
        font=("Segoe UI", 30, "bold"),
        foreground=PALETA["title_fg"],
        background=PALETA["page_bg"],
    )
    style.configure(
        "HeaderCell.TLabel",
        font=("Segoe UI", 11, "bold"),
        foreground="#ffffff",
        background=PALETA["header_bg"],
    )
    #__________________________FIN_2_2______________________#

    #__________________________2_3__________________________#
    #botones principales y auxiliares
    style.configure(
        "Add.TButton",
        font=("Segoe UI", 11, "bold"),
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
    #__________________________FIN_2_3______________________#
#__________________________FIN_2______________________#
