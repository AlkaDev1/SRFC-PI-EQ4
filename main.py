import tkinter as tk
from tkinter import ttk
import pyglet
import platform
import subprocess

ruta_fuente = "assets/fonts/segoeui.ttf"
pyglet.font.add_file(ruta_fuente)

from ui.styles import PALETA, MEDIDAS, configurar_estilos
from ui.tema import GestorTema

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")


class App:
    def __init__(self, root):
        self.root = root
        self.tema = GestorTema()

        self.contenedor = tk.Frame(root)
        self.contenedor.pack(fill="both", expand=True)
        self.mostrar_pantalla("principal")

    def mostrar_pantalla(self, nombre, datos=None):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

        if nombre == "principal":
            from ui.screens.pantalla_principal import crear_pantalla_principal
            crear_pantalla_principal(self.contenedor, self)

        elif nombre == "acceso":
            from ui.screens.pantalla_acceso import crear_pantalla_acceso
            crear_pantalla_acceso(self.contenedor, self)

        elif nombre == "gestion":
            from ui.screens.validacionUsrs import crear_pantalla_gestion
            crear_pantalla_gestion(self.contenedor, self)

        elif nombre == "gestion_real":
            from ui.screens.pantalla_gestion import crear_pantalla_gestion_real
            crear_pantalla_gestion_real(self.contenedor, self)

        elif nombre == "login":
            from ui.screens.pantalla_login import crear_pantalla_login
            crear_pantalla_login(self.contenedor, self)

        elif nombre == "historial":
            from ui.screens.historial_accesos import crear_pantalla_historial_accesos
            crear_pantalla_historial_accesos(self.contenedor, self, datos)

        elif nombre == "agregar_usuario":
            from ui.screens.pantalla_agregar_usuario import crear_pantalla_agregar_usuario
            crear_pantalla_agregar_usuario(self.contenedor, self)

        elif nombre == "editar_usuario":
            from ui.screens.pantalla_editar_usuario import crear_pantalla_editar_usuario
            crear_pantalla_editar_usuario(self.contenedor, self, datos)

        elif nombre == "aviso_privacidad":
            from ui.screens.pantalla_aviso_privacidad import crear_pantalla_aviso_privacidad
            crear_pantalla_aviso_privacidad(self.contenedor, self)


def _iniciar_teclado_virtual():
    """
    Lanza onboard solo en Raspberry Pi.
    onboard se mostrará automáticamente al tocar cualquier campo de texto
    si está configurado con 'Auto-show when editing text'.
    """
    if not _ES_RASPBERRY:
        return
    try:
        subprocess.Popen(
            ["onboard",
             "--size=800x200",      # ancho completo 800px, alto 200px
             "--layout=Phone",      # layout compacto para pantalla pequeña
             "--theme=Nightshade",  # tema oscuro que combina con el sistema
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[TECLADO] onboard iniciado correctamente")
    except FileNotFoundError:
        print("[TECLADO] onboard no encontrado. Instala con: sudo apt install onboard")
    except Exception as e:
        print(f"[TECLADO] Error al iniciar onboard: {e}")


def app():
    root = tk.Tk()
    root.title("Sistema de Control Biométrico – Universidad de Colima")
    root.configure(bg=PALETA["page_bg"])

    if _ES_RASPBERRY:
        root.overrideredirect(True)
        root.geometry("800x480+0+0")
        root.resizable(False, False)
    else:
        ancho = MEDIDAS["ancho_ventana"]
        alto  = MEDIDAS["alto_ventana"]
        root.geometry(f"{ancho}x{alto}")
        root.minsize(MEDIDAS["min_ancho"], MEDIDAS["min_alto"])
        root.update_idletasks()
        px = (root.winfo_screenwidth()  - ancho) // 2
        py = (root.winfo_screenheight() - alto)  // 2
        root.geometry(f"{ancho}x{alto}+{px}+{py}")

    style = ttk.Style()
    configurar_estilos(style)

    # ── Iniciar teclado virtual (solo RPi) ────────────────────────────────────
    _iniciar_teclado_virtual()

    App(root)
    root.mainloop()


if __name__ == "__main__":
    app()