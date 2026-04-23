"""
EJEMPLO DE USO DEL SISTEMA DE IDIOMAS EN UNA PANTALLA
═════════════════════════════════════════════════════════════════════

Este archivo muestra PASO A PASO cómo implementar el sistema de idiomas
en cualquier pantalla de la aplicación.

FLUJO GENERAL:
1. Importar el LanguageManager y obtener traducciones
2. En la función crear_pantalla(), guardar referencias a los widgets con texto
3. Registrar un callback que actualice los textos cuando cambie idioma
4. Desregistrar el callback cuando se destruya la pantalla
"""

import tkinter as tk
from pathlib import Path

# ═════════════════════════════════════════════════════════════════════
# PASO 1: IMPORTAR LO NECESARIO
# ═════════════════════════════════════════════════════════════════════

from core.language_manager import LanguageManager
from core.translations import obtener_texto
from ui.components.barra_superior import crear_encabezado

# ═════════════════════════════════════════════════════════════════════
# CLASE PARA LA PANTALLA
# ═════════════════════════════════════════════════════════════════════

class PantallaDemoIdioma(tk.Frame):
    """
    EJEMPLO DE PANTALLA CON SOPORTE PARA CAMBIO DE IDIOMA DINÁMICO
    
    ATRIBUTOS IMPORTANTES:
    ──────────────────────
    - self.manager : LanguageManager
        La instancia singleton del gestor de idiomas
    - self.widgets_texto : dict
        Diccionario con referencias a widgets que contienen texto
        Estructura: {"clave_traduccion": widget_tk_label}
    
    MÉTODOS PRINCIPALES:
    ────────────────────
    - __init__() : Inicializa la pantalla
    - _crear_widgets() : Crea todos los componentes visuales
    - _actualizar_idioma() : Se ejecuta cuando cambia el idioma
    - destroy() : Limpia recursos
    """
    
    def __init__(self, parent, app):
        """
        INICIALIZACIÓN DE LA PANTALLA
        
        ORDEN DE EJECUCIÓN:
        1. Llamar al init del Frame padre
        2. Obtener referencia al LanguageManager
        3. Crear diccionario para guardar referencias de widgets
        4. Crear los widgets visuales
        5. REGISTRAR CALLBACK para cambios de idioma
        
        PARÁMETROS:
        -----------
        parent : tk.Frame
            El frame padre donde se añadirá esta pantalla
        app : App
            La aplicación principal (para navegar entre pantallas)
        """
        super().__init__(parent, bg="#ffffff")
        self.pack(fill="both", expand=True)
        
        # Guardar referencia a la app
        self.app = app
        
        # ═══════════════════════════════════════════════════════════
        # OBTENER INSTANCIA DEL LANGUAGE MANAGER (SINGLETON)
        # ═══════════════════════════════════════════════════════════
        # Esta es LA CLAVE del sistema:
        # - Existe UNA SOLA instancia durante toda la app
        # - Se accede desde cualquier parte del código
        # - Contiene el idioma actual y el sistema de callbacks
        self.manager = LanguageManager.obtener_instancia()
        
        # ═══════════════════════════════════════════════════════════
        # DICCIONARIO PARA GUARDAR REFERENCIAS A WIDGETS
        # ═══════════════════════════════════════════════════════════
        # Estructura: {"clave_traduccion": widget}
        # Ejemplo: {"titulo": lbl_titulo, "boton": btn_ok}
        # Se usa para actualizar textos cuando cambia idioma
        self.widgets_texto = {}
        
        # Crear la interfaz
        self._crear_widgets()
        
        # ═══════════════════════════════════════════════════════════
        # REGISTRAR CALLBACK
        # ═══════════════════════════════════════════════════════════
        # Cuando el idioma cambie:
        # 1. El LanguageManager ejecuta ALL los callbacks registrados
        # 2. Se llama a self._actualizar_idioma()
        # 3. Esta función actualiza TODOS los textos
        self.manager.registrar_callback(self._actualizar_idioma)
        
        print(f"[PantallaDemoIdioma] Inicializada - Idioma actual: {self.manager.obtener_idioma_actual()}")
    
    def _crear_widgets(self):
        """
        CREA TODOS LOS WIDGETS DE LA PANTALLA
        
        IMPORTANTE:
        - Cada widget que tenga texto debe guardarse en self.widgets_texto
        - La clave debe coincidir con la clave en translations.py
        - Se almacena como: self.widgets_texto["clave"] = widget
        
        EJEMPLO:
        - En translations.py: "titulo_pantalla": "Gestión de Usuarios"
        - Aquí: self.widgets_texto["titulo_pantalla"] = lbl_titulo
        - Cuando cambia idioma: lbl_titulo.config(text=nuevo_texto)
        """
        
        # Obtener idioma actual
        idioma = self.manager.obtener_idioma_actual()
        
        # ═══════════════════════════════════════════════════════════
        # ENCABEZADO
        # ═══════════════════════════════════════════════════════════
        crear_encabezado(self, self.app.root)
        
        # ═══════════════════════════════════════════════════════════
        # CONTENIDO PRINCIPAL
        # ═══════════════════════════════════════════════════════════
        
        # Frame central
        contenido = tk.Frame(self, bg="#ffffff")
        contenido.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ───────────────────────────────────────────────────────────
        # TÍTULO
        # ───────────────────────────────────────────────────────────
        # Obtener texto en el idioma actual
        texto_titulo = obtener_texto(idioma, "gestion_titulo")
        
        # Crear label
        lbl_titulo = tk.Label(
            contenido,
            text=texto_titulo,
            font=("Segoe UI", 24, "bold"),
            fg="#003087",
            bg="#ffffff"
        )
        lbl_titulo.pack(pady=(0, 20))
        
        # GUARDAR REFERENCIA para actualizar después
        # Clave: "gestion_titulo" (debe existir en translations.py)
        # Valor: el label que contiene el texto
        self.widgets_texto["gestion_titulo"] = lbl_titulo
        
        # ───────────────────────────────────────────────────────────
        # DESCRIPCIÓN
        # ───────────────────────────────────────────────────────────
        texto_descripcion = obtener_texto(idioma, "gestion_buscar")
        
        lbl_descripcion = tk.Label(
            contenido,
            text=f"{texto_descripcion}...",
            font=("Segoe UI", 12),
            fg="#555555",
            bg="#ffffff"
        )
        lbl_descripcion.pack(pady=10)
        
        self.widgets_texto["gestion_buscar"] = lbl_descripcion
        
        # ───────────────────────────────────────────────────────────
        # BOTONES
        # ───────────────────────────────────────────────────────────
        frame_botones = tk.Frame(contenido, bg="#ffffff")
        frame_botones.pack(pady=20)
        
        # Botón "Agregar"
        texto_agregar = obtener_texto(idioma, "gestion_agregar")
        btn_agregar = tk.Button(
            frame_botones,
            text=texto_agregar,
            font=("Segoe UI", 11),
            bg="#4CAF50",
            fg="#ffffff",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        btn_agregar.pack(side="left", padx=5)
        
        self.widgets_texto["gestion_agregar"] = btn_agregar
        
        # Botón "Eliminar"
        texto_eliminar = obtener_texto(idioma, "gestion_eliminar")
        btn_eliminar = tk.Button(
            frame_botones,
            text=texto_eliminar,
            font=("Segoe UI", 11),
            bg="#ff6b6b",
            fg="#ffffff",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        btn_eliminar.pack(side="left", padx=5)
        
        self.widgets_texto["gestion_eliminar"] = btn_eliminar
        
        # Botón "Volver"
        texto_volver = obtener_texto(idioma, "volver")
        btn_volver = tk.Button(
            frame_botones,
            text=texto_volver,
            font=("Segoe UI", 11),
            bg="#808080",
            fg="#ffffff",
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.app.mostrar_pantalla("principal")
        )
        btn_volver.pack(side="left", padx=5)
        
        self.widgets_texto["volver"] = btn_volver
        
        # ───────────────────────────────────────────────────────────
        # INFORMACIÓN
        # ───────────────────────────────────────────────────────────
        info_frame = tk.Frame(contenido, bg="#f0f0f0", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=20)
        
        idioma_texto = "ESPAÑOL" if idioma == "es" else "ENGLISH"
        info_text = f"Idioma actual: {idioma_texto}\n\nHaz clic en el botón 'ES/EN' en la barra superior para cambiar de idioma.\nTodos los textos se actualizarán automáticamente."
        
        lbl_info = tk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 10),
            fg="#333333",
            bg="#f0f0f0",
            justify="left"
        )
        lbl_info.pack(padx=10, pady=10)
        
        self.widgets_texto["idioma_info"] = lbl_info
    
    def _actualizar_idioma(self):
        """
        SE EJECUTA AUTOMÁTICAMENTE CUANDO CAMBIA EL IDIOMA
        
        ORDEN DE EJECUCIÓN:
        1. El usuario hace clic en el botón de idioma
        2. LanguageManager.cambiar_idioma() se ejecuta
        3. Se llama a _notificar_cambio()
        4. SE EJECUTA ESTA FUNCIÓN
        5. Actualiza TODOS los widgets en self.widgets_texto
        
        CÓMO FUNCIONA:
        - Itera sobre cada widget guardado en self.widgets_texto
        - Obtiene el nuevo texto en el idioma actual
        - Lo asigna al widget con .config(text=...)
        - Los cambios son visibles al instante
        
        IMPORTANCIA:
        ¡Sin esta función, la pantalla no cambiaría de idioma!
        """
        # Obtener idioma actual
        idioma = self.manager.obtener_idioma_actual()
        
        print(f"[PantallaDemoIdioma._actualizar_idioma] Actualizando a: {idioma}")
        
        # Actualizar cada widget
        for clave, widget in self.widgets_texto.items():
            try:
                # Obtener el nuevo texto
                nuevo_texto = obtener_texto(idioma, clave)
                
                # Si es un botón, usar su método .config()
                if isinstance(widget, tk.Button):
                    widget.config(text=nuevo_texto)
                else:
                    # Si es un Label, también usar .config()
                    widget.config(text=nuevo_texto)
                
                print(f"  ✓ Actualizado: {clave}")
                
            except Exception as e:
                print(f"  ✗ Error al actualizar {clave}: {e}")
        
        # Actualizar info
        idioma_texto = "ESPAÑOL" if idioma == "es" else "ENGLISH"
        info_text = f"Idioma actual: {idioma_texto}\n\nHaz clic en el botón 'ES/EN' en la barra superior para cambiar de idioma.\nTodos los textos se actualizarán automáticamente."
        if "idioma_info" in self.widgets_texto:
            self.widgets_texto["idioma_info"].config(text=info_text)
    
    def destroy(self):
        """
        SE EJECUTA CUANDO SE DESTRUYE LA PANTALLA
        
        IMPORTANTE:
        - Desregistra el callback para evitar errores
        - Evita llamar a funciones de una pantalla que ya no existe
        - Es buena práctica limpiar recursos
        """
        # Desregistrar el callback
        self.manager.desregistrar_callback(self._actualizar_idioma)
        print("[PantallaDemoIdioma] Pantalla destruida, callback desregistrado")
        
        # Llamar a destroy del padre
        super().destroy()


# ═════════════════════════════════════════════════════════════════════
# FUNCIÓN DE ENTRADA (llamada desde main.py)
# ═════════════════════════════════════════════════════════════════════

def crear_pantalla_ejemplo(parent: tk.Frame, app) -> None:
    """
    FUNCIÓN DE ENTRADA PARA ESTA PANTALLA
    
    Esta es la función que se llama desde main.py:
    app.mostrar_pantalla("ejemplo")
    
    PARÁMETROS:
    -----------
    parent : tk.Frame
        El contenedor donde se añade esta pantalla
    app : App
        La aplicación principal
    """
    PantallaDemoIdioma(parent, app)
