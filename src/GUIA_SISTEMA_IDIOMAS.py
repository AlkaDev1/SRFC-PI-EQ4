"""
╔═════════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║              GUÍA COMPLETA: SISTEMA DE CAMBIO DE IDIOMA (I18N)            ║
║                                                                             ║
║  Sistema multinacional para cambiar entre español e inglés en tiempo real  ║
║  sin necesidad de reiniciar la aplicación.                                ║
║                                                                             ║
║  Autor: Sistema SRFC-PI-EQ4                                                ║
║  Fecha: 2026                                                               ║
║  Versión: 1.0                                                              ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝


═════════════════════════════════════════════════════════════════════════════
1. ARQUITECTURA GENERAL DEL SISTEMA
═════════════════════════════════════════════════════════════════════════════

El sistema está dividido en 3 componentes principales:


    ┌──────────────────────────────────────────────────────────────────┐
    │                    TRANSLATIONS.PY                              │
    │              (Diccionario de traducciones)                       │
    │                                                                  │
    │  TRADUCCIONES["es"]["clave"] = "Texto en español"              │
    │  TRADUCCIONES["en"]["clave"] = "Text in English"               │
    │                                                                  │
    │  - Todos los textos en UN solo archivo                          │
    │  - Fácil de mantener y actualizar                              │
    │  - Función helper: obtener_texto(idioma, clave)                │
    └──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Consulta
                              │
    ┌──────────────────────────────────────────────────────────────────┐
    │               LANGUAGE_MANAGER.PY                                │
    │         (Gestor centralizado - SINGLETON)                        │
    │                                                                  │
    │  LanguageManager.obtener_instancia()                            │
    │  ↓                                                               │
    │  - Mantiene el idioma actual                                    │
    │  - Carga/guarda preferencia (data/language_config.json)        │
    │  - Sistema de callbacks (observadores)                          │
    │  - Método: cambiar_idioma(nuevo_idioma)                        │
    │  - Método: registrar_callback(funcion)                         │
    └──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Notifica
                              │
    ┌──────────────────────────────────────────────────────────────────┐
    │              LAS PANTALLAS (OBSERVADORES)                        │
    │                                                                  │
    │  Cada pantalla:                                                 │
    │  1. Se registra como callback                                   │
    │  2. Guarda referencias a widgets con texto                      │
    │  3. Cuando hay cambio, actualiza TODOS los textos              │
    │  4. Se desregistra cuando se destruye                          │
    └──────────────────────────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════════════════════
2. COMPONENTES DEL SISTEMA
═════════════════════════════════════════════════════════════════════════════

📁 core/
├── translations.py          ← Diccionario de traducciones
├── language_manager.py      ← Gestor centralizado (SINGLETON)
└── database.py              ← Existente

📁 ui/
├── components/
│   └── barra_superior.py    ← Botón de idioma funcional
└── screens/
    ├── pantalla_principal.py
    ├── pantalla_login.py
    └── (tus otras pantallas)

📁 main.py                   ← Punto de entrada


═════════════════════════════════════════════════════════════════════════════
3. FLUJO DE FUNCIONAMIENTO PASO A PASO
═════════════════════════════════════════════════════════════════════════════

ESCENARIO: Usuario hace clic en el botón de idioma


┌─────────────────────────────────────────────────────────────────────────┐
│ PASO 1: USUARIO HACE CLIC EN BOTÓN "ES/EN"                            │
└─────────────────────────────────────────────────────────────────────────┘

    Ubicación: ui/components/barra_superior.py
    Función: cambiar_idioma_handler()
    
    def cambiar_idioma_handler():
        nuevo_idioma = manager.obtener_idioma_opuesto()  # "es" → "en" o viceversa
        manager.cambiar_idioma(nuevo_idioma)              # Llamar al gestor
        lbl_idioma_toggle.config(text=nuevo_idioma.upper())  # Actualizar botón


┌─────────────────────────────────────────────────────────────────────────┐
│ PASO 2: LANGUAGE MANAGER CAMBIA EL IDIOMA                              │
└─────────────────────────────────────────────────────────────────────────┘

    Ubicación: core/language_manager.py
    Método: cambiar_idioma(nuevo_idioma)
    
    1. Valida que idioma sea "es" o "en"
    2. Asigna: self._idioma_actual = nuevo_idioma
    3. Guarda en archivo: self._guardar_idioma(nuevo_idioma)
    4. EJECUTA TODOS LOS CALLBACKS: self._notificar_cambio()


┌─────────────────────────────────────────────────────────────────────────┐
│ PASO 3: TODAS LAS PANTALLAS SE ACTUALIZAN AUTOMÁTICAMENTE              │
└─────────────────────────────────────────────────────────────────────────┘

    Ubicación: Las pantallas (cada una con su _actualizar_idioma())
    
    for callback in self._callbacks:  # Todos los callbacks registrados
        callback()  # Ejecuta: pantalla._actualizar_idioma()
    
    En cada pantalla:
    - Obtiene idioma actual
    - Para cada widget guardado en self.widgets_texto:
        * Obtiene nuevo texto: obtener_texto(idioma, clave)
        * Actualiza widget: widget.config(text=nuevo_texto)
    - Los cambios son visibles al instante


┌─────────────────────────────────────────────────────────────────────────┐
│ PASO 4: PERSISTENCIA - GUARDAR PREFERENCIA                             │
└─────────────────────────────────────────────────────────────────────────┘

    Ubicación: data/language_config.json
    Contenido:
    {
        "idioma": "en"
    }
    
    - Se guarda automáticamente en cambiar_idioma()
    - Se carga al iniciar en _cargar_idioma()
    - El usuario siempre ve su idioma preferido


═════════════════════════════════════════════════════════════════════════════
4. CÓMO IMPLEMENTAR EN TUS PANTALLAS
═════════════════════════════════════════════════════════════════════════════

PASO A PASO para convertir una pantalla existente:


PASO 1: IMPORTS
────────────────

    # Al inicio del archivo de la pantalla
    from core.language_manager import LanguageManager
    from core.translations import obtener_texto


PASO 2: EN LA CLASE DE LA PANTALLA - __init__()
─────────────────────────────────────────────────

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # IMPORTANTE: Obtener el manager
        self.manager = LanguageManager.obtener_instancia()
        
        # Diccionario para guardar widgets
        self.widgets_texto = {}
        
        # Crear widgets
        self._crear_widgets()
        
        # REGISTRAR CALLBACK - Crítico!
        self.manager.registrar_callback(self._actualizar_idioma)


PASO 3: AL CREAR CADA WIDGET CON TEXTO
──────────────────────────────────────

    # En _crear_widgets():
    
    # Obtener idioma actual
    idioma = self.manager.obtener_idioma_actual()
    
    # Obtener texto en ese idioma
    texto = obtener_texto(idioma, "bienvenidos")
    
    # Crear widget
    lbl = tk.Label(parent, text=texto)
    lbl.pack()
    
    # GUARDAR REFERENCIA
    self.widgets_texto["bienvenidos"] = lbl


PASO 4: CREAR MÉTODO _actualizar_idioma()
──────────────────────────────────────────

    def _actualizar_idioma(self):
        """Se ejecuta cuando cambia el idioma"""
        idioma = self.manager.obtener_idioma_actual()
        
        for clave, widget in self.widgets_texto.items():
            nuevo_texto = obtener_texto(idioma, clave)
            widget.config(text=nuevo_texto)


PASO 5: EN destroy() - LIMPIAR CALLBACK
─────────────────────────────────────────

    def destroy(self):
        """Se ejecuta cuando se destruye la pantalla"""
        # Desregistrar para evitar errores
        self.manager.desregistrar_callback(self._actualizar_idioma)
        super().destroy()


═════════════════════════════════════════════════════════════════════════════
5. EJEMPLO PRÁCTICO MÍNIMO
═════════════════════════════════════════════════════════════════════════════

from core.language_manager import LanguageManager
from core.translations import obtener_texto
import tkinter as tk


class MiPantalla(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = LanguageManager.obtener_instancia()
        self.widgets_texto = {}
        
        self._crear_widgets()
        
        # REGISTRAR CALLBACK
        self.manager.registrar_callback(self._actualizar_idioma)
    
    def _crear_widgets(self):
        idioma = self.manager.obtener_idioma_actual()
        
        # Label principal
        lbl_titulo = tk.Label(self, text=obtener_texto(idioma, "bienvenidos"))
        lbl_titulo.pack()
        self.widgets_texto["bienvenidos"] = lbl_titulo
        
        # Botón
        btn = tk.Button(self, text=obtener_texto(idioma, "aceptar"))
        btn.pack()
        self.widgets_texto["aceptar"] = btn
    
    def _actualizar_idioma(self):
        idioma = self.manager.obtener_idioma_actual()
        for clave, widget in self.widgets_texto.items():
            widget.config(text=obtener_texto(idioma, clave))
    
    def destroy(self):
        self.manager.desregistrar_callback(self._actualizar_idioma)
        super().destroy()


def crear_mi_pantalla(parent, app):
    MiPantalla(parent, app)


═════════════════════════════════════════════════════════════════════════════
6. AGREGAR NUEVAS TRADUCCIONES
═════════════════════════════════════════════════════════════════════════════

Para agregar un nuevo texto:

PASO 1: Abrir core/translations.py
PASO 2: Añadir la clave en TRADUCCIONES["es"] y TRADUCCIONES["en"]

Ejemplo:

    TRADUCCIONES = {
        "es": {
            ...
            "mi_nuevo_texto": "Hola mundo",
        },
        "en": {
            ...
            "mi_nuevo_texto": "Hello world",
        }
    }

PASO 3: Usarlo en la pantalla

    texto = obtener_texto(idioma, "mi_nuevo_texto")


═════════════════════════════════════════════════════════════════════════════
7. DEBUGGING Y TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════════════

PROBLEMA: Los textos no cambian cuando presiono el botón
─────────────────────────────────────────────────────────
✓ Verificar que _actualizar_idioma() está registrado
✓ Confirmar que los widgets están en self.widgets_texto
✓ Revisar que la clave existe en translations.py

PROBLEMA: Error "AttributeError: 'NoneType'"
──────────────────────────────────────────
✓ Probablemente el widget fue destruido
✓ Verificar que no hay referencias a widgets después de destroy()

PROBLEMA: El idioma no se guarda para la próxima sesión
────────────────────────────────────────────────────
✓ Verificar que data/ existe (se crea automáticamente)
✓ Revisar permisos de escritura en data/language_config.json


═════════════════════════════════════════════════════════════════════════════
8. CONSOLAS Y LOGS
═════════════════════════════════════════════════════════════════════════════

El sistema imprime mensajes útiles en consola:

[LanguageManager] Inicializado con idioma: es
[LanguageManager] Idioma cambiado a: en
[LanguageManager] Idioma guardado: en
[LanguageManager] Notificando cambio a 2 callbacks...
  ✓ Callback ejecutado: _actualizar_idioma
  ✓ Callback ejecutado: _actualizar_idioma


═════════════════════════════════════════════════════════════════════════════
9. ARQUITECTURA EN TIEMPO DE EJECUCIÓN
═════════════════════════════════════════════════════════════════════════════

Cuando la app está corriendo:

    ┌─────────────────────────────────────┐
    │     APLICACIÓN PRINCIPAL            │
    │     (main.py - App class)           │
    │                                     │
    │  self.language_manager = ←─────────────────┐
    │      LanguageManager.obtener_instancia()   │
    └─────────────────────────────────────┘     │
                       │                        │
                       │                 ┌──────┴──────────────────┐
                       │                 │                         │
    ┌──────────────────▼──────────┐      │  ┌────────────────────┐ │
    │   BARRA SUPERIOR            │      └─→│ Language Manager   │ │
    │   (barra_superior.py)       │         │ (SINGLETON)        │ │
    │                             │         │                    │ │
    │ Botón ES/EN                 │         │ idioma_actual: "es"│ │
    │ ↓                           │         │ callbacks: [...]   │ │
    │ cambiar_idioma_handler()────┼─────────→ cambiar_idioma()   │ │
    │                             │         │ _notificar_cambio()│ │
    └─────────────────────────────┘         └────────────────────┘ │
                                                    │               │
                              ┌─────────────────────┼───────────────┤
                              │                     │               │
              ┌───────────────▼──────┐  ┌───────────▼──────┐  ...  │
              │  Pantalla Principal  │  │  Pantalla Login  │      │
              │                      │  │                  │      │
              │ _actualizar_idioma() │  │_actualizar_idioma()    │
              │ widgets_texto: {...} │  │widgets_texto: {...}    │
              └──────────────────────┘  └──────────────────┘      │
                                                                   │
                                  (todos conectados por callbacks) │
                                                                   │
                                  Se notifican automáticamente ←───┘
                                  cuando cambia el idioma


═════════════════════════════════════════════════════════════════════════════
10. PATRÓN OBSERVER - POR QUÉ FUNCIONA ASÍ
═════════════════════════════════════════════════════════════════════════════

El sistema usa el PATRÓN OBSERVER:

    1. Las pantallas se "suscriben" registrando un callback
    2. El LanguageManager es el "publicador"
    3. Cuando cambia el idioma, notifica a TODOS
    4. Cada uno se actualiza de forma independiente

VENTAJAS:
✓ Las pantallas son independientes entre sí
✓ No hay acoplamiento fuerte
✓ Fácil de escalar a más pantallas
✓ No requiere recargar la app


═════════════════════════════════════════════════════════════════════════════
11. ARCHIVOS GENERADOS AUTOMÁTICAMENTE
═════════════════════════════════════════════════════════════════════════════

La app crea automáticamente:

data/
└── language_config.json      ← Preferencia de idioma guardada

Contenido ejemplo:
{
  "idioma": "en"
}

Este archivo es:
- Creado automáticamente al cambiar idioma
- Cargado al iniciar la app
- Permite persistencia de la preferencia


═════════════════════════════════════════════════════════════════════════════
12. RESUMEN RÁPIDO
═════════════════════════════════════════════════════════════════════════════

✓ Sistema de idiomas 100% funcional
✓ Cambio de idioma en tiempo real (sin reiniciar)
✓ Persistencia de preferencia
✓ Barra superior con botón toggle funcional
✓ Totalmente documentado con comentarios
✓ Patrón SINGLETON para el gestor
✓ Patrón OBSERVER para las pantallas
✓ Fácil de implementar en nuevas pantallas
✓ Escalable a más idiomas

Para cambiar de idioma:
1. Haz clic en el botón "ES/EN" en la barra superior
2. El idioma cambia instantáneamente en TODAS las pantallas
3. La preferencia se guarda automáticamente


═════════════════════════════════════════════════════════════════════════════

¡Sistema listo para usar! 🎉

═════════════════════════════════════════════════════════════════════════════
"""

# Este es un archivo de documentación, no contiene código ejecutable
# Mantenlo en src/ para referencia
