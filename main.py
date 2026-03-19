import tkinter as tk
from tkinter import ttk

from ui_styles import PALETA, MEDIDAS, configurar_estilos
from ui.screens.pantalla_principal import crear_pantalla_principal


def app() -> None:

    #Ventana principal
    root = tk.Tk()
    root.title("Sistema de Control Biométrico – Universidad de Colima")
    root.configure(bg=PALETA["page_bg"])
    root.minsize(MEDIDAS["min_ancho"], MEDIDAS["min_alto"])

    ancho = MEDIDAS["ancho_ventana"]
    alto  = MEDIDAS["alto_ventana"]
    root.geometry(f"{ancho}x{alto}")

    # Centrar en pantalla
    root.update_idletasks()
    px = (root.winfo_screenwidth()  - ancho) // 2
    py = (root.winfo_screenheight() - alto)  // 2
    root.geometry(f"{ancho}x{alto}+{px}+{py}")

    # ── Estilos ttk ───────────────────────────────────────────────────────────
    style = ttk.Style()
    configurar_estilos(style)

    # ── Pantalla principal ────────────────────────────────────────────────────
    crear_pantalla_principal(root)

    # ── Loop de eventos ───────────────────────────────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    app()