import tkinter as tk
from tkinter import ttk

from ui.styles import PALETA, MEDIDAS, configurar_estilos

class App:
    def __init__(self, root):
        self.root = root

        self.contenedor = tk.Frame(root)
        self.contenedor.pack(fill="both", expand=True)

        self.mostrar_pantalla("principal")

    def mostrar_pantalla(self, nombre):
    
        for widget in self.contenedor.winfo_children():
            widget.destroy()

        if nombre == "principal":
            from ui.screens.pantalla_principal import crear_pantalla_principal
            crear_pantalla_principal(self.contenedor, self)


def app():
    root = tk.Tk()
    root.title("Sistema de Control Biométrico – Universidad de Colima")
    root.configure(bg=PALETA["page_bg"])
    root.minsize(MEDIDAS["min_ancho"], MEDIDAS["min_alto"])

    ancho = MEDIDAS["ancho_ventana"]
    alto  = MEDIDAS["alto_ventana"]
    root.geometry(f"{ancho}x{alto}")

    # centrar ventana
    root.update_idletasks()
    px = (root.winfo_screenwidth()  - ancho) // 2
    py = (root.winfo_screenheight() - alto)  // 2
    root.geometry(f"{ancho}x{alto}+{px}+{py}")

    # estilos
    style = ttk.Style()
    configurar_estilos(style)

    App(root)

    root.mainloop()


if __name__ == "__main__":
    app()