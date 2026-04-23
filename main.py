import tkinter as tk
from tkinter import ttk
import pyglet

ruta_fuente = "assets/fonts/segoeui.ttf"
pyglet.font.add_file(ruta_fuente)

from ui.styles import PALETA, MEDIDAS, configurar_estilos
# ═════════════════════════════════════════════════════════════════════
# IMPORTAR EL GESTOR DE IDIOMAS
# ═════════════════════════════════════════════════════════════════════
# Este módulo singleton gestiona todos los idiomas de la app
from core.language_manager import LanguageManager


class App:
    """
    CLASE PRINCIPAL DE LA APLICACIÓN
    
    RESPONSABILIDADES:
    1. Inicializar la ventana principal
    2. Mantener referencia al LanguageManager (singleton)
    3. Navegar entre pantallas
    4. Comunicar cambios de idioma a todas las pantallas
    
    FLUJO:
    main() → App(root) → App.__init__() → LanguageManager.obtener_instancia()
    """
    
    def __init__(self, root):
        """
        INICIALIZACIÓN DE LA APP
        
        ORDEN:
        1. Guardar referencia a la ventana raíz
        2. Obtener instancia del LanguageManager (singleton)
        3. Crear contenedor para las pantallas
        4. Mostrar pantalla inicial
        """
        self.root = root
        
        # SINGLETON: Obtener la única instancia del gestor de idiomas
        # Esta instancia persiste durante toda la app
        self.language_manager = LanguageManager.obtener_instancia()
        
        # Frame contenedor donde se cargan las pantallas dinámicamente
        self.contenedor = tk.Frame(root)
        self.contenedor.pack(fill="both", expand=True)
        
        # Mostrar la primera pantalla
        self.mostrar_pantalla("principal")

    
    def mostrar_pantalla(self, nombre):
        """
        CARGA UNA PANTALLA NUEVA
        
        PROCESO:
        1. Destruye todos los widgets del contenedor (limpia la pantalla anterior)
        2. Importa dinámicamente la pantalla solicitada
        3. Pasa referencias de la app y language_manager
        
        PARÁMETROS:
        -----------
        nombre : str
            Nombre de la pantalla: "principal", "login", "acceso", etc.
        
        FLUJO:
        - mostrar_pantalla("principal") → crear_pantalla_principal()
        - Cada función crear_pantalla_X recibe (parent, app)
        - Puede usar app.language_manager para acceder al idioma
        """
        # Destruir todos los widgets previos (limpiar contenedor)
        for widget in self.contenedor.winfo_children():
            widget.destroy()

        # CARGA DINÁMICA DE PANTALLAS
        # Se importan solo cuando se necesitan (ahorra memoria)
        
        if nombre == "principal":
            from ui.screens.pantalla_principal import crear_pantalla_principal
            crear_pantalla_principal(self.contenedor, self)

        elif nombre == "acceso":
            from ui.screens.pantalla_acceso import crear_pantalla_acceso
            crear_pantalla_acceso(self.contenedor, self)

        elif nombre == "gestion":
            from ui.screens.validacionUsrs import crear_pantalla_gestion
            crear_pantalla_gestion(self.contenedor, self)

        elif nombre == "registro":
            from ui.screens.pantalla_registro import crear_pantalla_registro
            crear_pantalla_registro(self.contenedor, self)

        elif nombre == "gestion_real":
            from ui.screens.pantalla_gestion import crear_pantalla_gestion_real
            crear_pantalla_gestion_real(self.contenedor, self)

        elif nombre == "login":                                     # ← NUEVO
            from ui.screens.pantalla_login import crear_pantalla_login
            crear_pantalla_login(self.contenedor, self)


def app():
    root = tk.Tk()
    root.title("Sistema de Control Biométrico – Universidad de Colima")
    root.configure(bg=PALETA["page_bg"])
    root.minsize(MEDIDAS["min_ancho"], MEDIDAS["min_alto"])

    ancho = MEDIDAS["ancho_ventana"]
    alto  = MEDIDAS["alto_ventana"]
    root.geometry(f"{ancho}x{alto}")

    root.update_idletasks()
    px = (root.winfo_screenwidth()  - ancho) // 2
    py = (root.winfo_screenheight() - alto)  // 2
    root.geometry(f"{ancho}x{alto}+{px}+{py}")

    style = ttk.Style()
    configurar_estilos(style)

    App(root)
    root.mainloop()


if __name__ == "__main__":
    app()