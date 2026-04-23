"""
╔═════════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║        SISTEMA DE CAMBIO DE IDIOMA - FLUJO VISUAL Y DIAGRAMAS             ║
║                                                                             ║
║                     CÓMO FUNCIONA PASO A PASO                             ║
║                                                                             ║
╚═════════════════════════════════════════════════════════════════════════════╝


═════════════════════════════════════════════════════════════════════════════
1. ARQUITECTURA GENERAL
═════════════════════════════════════════════════════════════════════════════


┌────────────────────────────────────────────────────────────────────────┐
│                     DICCIONARIO DE TRADUCCIONES                        │
│                     (core/translations.py)                             │
│                                                                        │
│  TRADUCCIONES = {                                                      │
│      "es": {                                                           │
│          "bienvenidos": "BIENVENIDOS",                                │
│          "aceptar": "Aceptar",                                        │
│          ...                                                          │
│      },                                                               │
│      "en": {                                                          │
│          "bienvenidos": "WELCOME",                                   │
│          "aceptar": "Accept",                                        │
│          ...                                                         │
│      }                                                                │
│  }                                                                    │
└────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
                        obtener_texto(idioma, clave)
                                 │
┌────────────────────────────────────────────────────────────────────────┐
│                   LANGUAGE MANAGER (SINGLETON)                        │
│                   (core/language_manager.py)                          │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ LanguageManager._instancia = UNA ÚNICA INSTANCIA            │    │
│  │                                                              │    │
│  │ Atributos:                                                  │    │
│  │ - _idioma_actual: "es" o "en"                             │    │
│  │ - _callbacks: [función1, función2, ...]                   │    │
│  │ - _archivo_config: data/language_config.json              │    │
│  │                                                              │    │
│  │ Métodos:                                                    │    │
│  │ - obtener_instancia() → Retorna la única instancia        │    │
│  │ - cambiar_idioma(nuevo) → Cambia y notifica               │    │
│  │ - registrar_callback(fn) → Añade observador               │    │
│  │ - _notificar_cambio() → Ejecuta todos los callbacks       │    │
│  └──────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
                    manager.registrar_callback()
                         manager.cambiar_idioma()
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼──────────┐      ┌─────▼──────────┐      ┌─────▼──────────┐
│ PANTALLA 1       │      │ PANTALLA 2     │      │ PANTALLA N     │
│ (Principal)      │      │ (Login)        │      │ (Gestión)      │
│                  │      │                │      │                │
│ callbacks:       │      │ callbacks:     │      │ callbacks:     │
│ [actualizar...]  │      │ [actualizar...]│      │ [actualizar...]│
│                  │      │                │      │                │
│ widgets_texto: { │      │ widgets_texto:{│      │ widgets_texto:{│
│  "clave": widget │      │  "clave": w    │      │  "clave": w    │
│ }                │      │ }              │      │ }              │
└──────────────────┘      └────────────────┘      └────────────────┘


═════════════════════════════════════════════════════════════════════════════
2. FLUJO COMPLETO: USUARIO HACE CLIC EN BOTÓN DE IDIOMA
═════════════════════════════════════════════════════════════════════════════


INICIO: Usuario ve pantalla en ESPAÑOL
│
│  PANTALLA PRINCIPAL
│  ┌──────────────────────────────────────────┐
│  │ 🇪🇸 BIENVENIDOS                         │
│  │ Sistema de Control Biométrico           │
│  │ ┌────────────────────────────────────┐  │
│  │ │ [Acceder] [Gestión] [Privacidad]  │  │
│  │ └────────────────────────────────────┘  │
│  │                                         ES│◄─ Botón de idioma
│  └──────────────────────────────────────────┘
│
│
├─► USUARIO HACE CLIC EN "ES"
│   
│
├─► barra_superior.py - cambiar_idioma_handler()
│   ├─ nuevo_idioma = "en"  (obtener opuesto)
│   │
│   ├─ manager.cambiar_idioma("en")  ◄─ Llamar al gestor
│   │
│   └─ lbl_idioma_toggle.config(text="EN")  ◄─ Actualizar botón
│
│
├─► core/language_manager.py - cambiar_idioma("en")
│   ├─ Validar: "en" es válido ✓
│   ├─ self._idioma_actual = "en"  ◄─ CAMBIAR
│   ├─ self._guardar_idioma("en")  ◄─ GUARDAR en data/language_config.json
│   │
│   ├─ self._notificar_cambio()  ◄─ EJECUTAR TODOS LOS CALLBACKS
│   │   │
│   │   ├─► Callback 1: Pantalla Principal._actualizar_idioma()
│   │   │   ├─ idioma = "en"
│   │   │   ├─ Para cada widget en widgets_texto:
│   │   │   │  ├─ nuevo_texto = obtener_texto("en", "bienvenidos") = "WELCOME"
│   │   │   │  ├─ lbl_titulo.config(text="WELCOME")
│   │   │   │  ├─ nuevo_texto = obtener_texto("en", "aceptar") = "Accept"
│   │   │   │  └─ btn_aceptar.config(text="Accept")
│   │   │
│   │   ├─► Callback 2: Pantalla Login._actualizar_idioma()
│   │   │   └─ (Similar actualización)
│   │   │
│   │   └─► Callback N: Otras pantallas
│   │       └─ (Todas se actualizan automáticamente)
│   │
│   └─ Logging: "[LanguageManager] Notificando cambio a 3 callbacks..."
│
│
├─► ¡RESULTADO INSTANTÁNEO!
│
│  PANTALLA PRINCIPAL (ACTUALIZADA A INGLÉS)
│  ┌──────────────────────────────────────────┐
│  │ 🇬🇧 WELCOME                             │
│  │ Biometric Control System               │
│  │ ┌────────────────────────────────────┐  │
│  │ │ [Access] [Management] [Privacy]    │  │
│  │ └────────────────────────────────────┘  │
│  │                                       EN│◄─ Botón actualizado
│  └──────────────────────────────────────────┘
│
│
├─► PERSISTENCIA: El archivo data/language_config.json se actualiza
│   {
│       "idioma": "en"
│   }
│
│
└─► PRÓXIMA SESIÓN: La app abre en INGLÉS automáticamente


═════════════════════════════════════════════════════════════════════════════
3. ESTRUCTURA DE UNA PANTALLA CON SOPORTE DE IDIOMA
═════════════════════════════════════════════════════════════════════════════


from core.language_manager import LanguageManager
from core.translations import obtener_texto


class MiPantalla(tk.Frame):
    """
    PASO 1: INICIALIZACIÓN
    ═════════════════════════════════════════════════════════════════
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # CRÍTICO: Obtener el manager singleton
        self.manager = LanguageManager.obtener_instancia()
        
        # Diccionario para guardar referencias a widgets
        self.widgets_texto = {}
        
        # Crear la interfaz
        self._crear_widgets()
        
        # CRÍTICO: Registrar callback para cambios de idioma
        # Cuando cambie idioma, se llamará a self._actualizar_idioma()
        self.manager.registrar_callback(self._actualizar_idioma)
    
    
    """
    PASO 2: CREAR WIDGETS CON TEXTO TRADUCIDO
    ═════════════════════════════════════════════════════════════════
    """
    def _crear_widgets(self):
        # Obtener idioma actual
        idioma = self.manager.obtener_idioma_actual()
        
        # Crear widgets con texto del idioma actual
        # ┌────────────────────────────────────────┐
        # │ Label "BIENVENIDOS"                    │
        # ├────────────────────────────────────────┤
        # │ obtener_texto("es", "bienvenidos")     │
        # │         ↓                              │
        # │     "BIENVENIDOS"                      │
        # └────────────────────────────────────────┘
        
        texto_titulo = obtener_texto(idioma, "bienvenidos")
        lbl_titulo = tk.Label(self, text=texto_titulo)
        lbl_titulo.pack()
        
        # IMPORTANTE: Guardar referencia
        # Cuando cambie idioma, actualizaremos este widget
        self.widgets_texto["bienvenidos"] = lbl_titulo
        
        # ┌────────────────────────────────────────┐
        # │ Botón "ACEPTAR"                        │
        # ├────────────────────────────────────────┤
        # │ obtener_texto("es", "aceptar")         │
        # │         ↓                              │
        # │     "Aceptar"                          │
        # └────────────────────────────────────────┘
        
        texto_aceptar = obtener_texto(idioma, "aceptar")
        btn_aceptar = tk.Button(self, text=texto_aceptar)
        btn_aceptar.pack()
        
        self.widgets_texto["aceptar"] = btn_aceptar
    
    
    """
    PASO 3: ACTUALIZAR CUANDO CAMBIA EL IDIOMA
    ═════════════════════════════════════════════════════════════════
    
    SE EJECUTA AUTOMÁTICAMENTE cuando:
    1. Usuario hace clic en botón de idioma
    2. manager.cambiar_idioma(nuevo_idioma) se ejecuta
    3. manager._notificar_cambio() se ejecuta
    4. ESTA FUNCIÓN SE LLAMA
    """
    def _actualizar_idioma(self):
        # Obtener nuevo idioma
        idioma = self.manager.obtener_idioma_actual()
        
        # Recorrer TODOS los widgets guardados
        for clave, widget in self.widgets_texto.items():
            # Obtener texto en nuevo idioma
            # ┌──────────────────────────────────┐
            # │ obtener_texto("en", "bienvenidos")
            # │         ↓
            # │     "WELCOME"
            # └──────────────────────────────────┘
            nuevo_texto = obtener_texto(idioma, clave)
            
            # Actualizar el widget
            widget.config(text=nuevo_texto)
    
    
    """
    PASO 4: LIMPIAR CUANDO SE DESTRUYE LA PANTALLA
    ═════════════════════════════════════════════════════════════════
    
    IMPORTANTE: Evita errores al intentar actualizar pantallas
    destruidas
    """
    def destroy(self):
        # Desregistrar el callback
        self.manager.desregistrar_callback(self._actualizar_idioma)
        
        # Destruir la pantalla
        super().destroy()


# Función de entrada (llamada desde main.py)
def crear_mi_pantalla(parent, app):
    MiPantalla(parent, app)


═════════════════════════════════════════════════════════════════════════════
4. DIAGRAMA DE ESTADO DEL SISTEMA
═════════════════════════════════════════════════════════════════════════════


                         ┌─────────────────┐
                         │  APP INICIA     │
                         └────────┬────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ LanguageManager.           │
                    │ obtener_instancia()        │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ _cargar_idioma()    │
                    │ (desde archivo o    │
                    │  por defecto "es")  │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────▼───────────────────────┐
        │  PANTALLA PRINCIPAL CARGADA               │
        │  ├─ Obtiene manager                        │
        │  ├─ Crea widgets en idioma actual          │
        │  ├─ Registra callback                      │
        │  └─ _actualizar_idioma guardado            │
        │                                            │
        │  ESTADO: Esperando clic en botón de idioma │
        └──────────────────────────────────────────────┘
                               │
                   ┌───────────▼────────────┐
                   │ USUARIO HACE CLIC      │
                   │ (Botón ES/EN)          │
                   └───────────┬────────────┘
                               │
        ┌──────────────────────▼───────────────────────┐
        │ cambiar_idioma_handler() EJECUTA           │
        │ ├─ nuevo_idioma = "en"                     │
        │ └─ manager.cambiar_idioma("en")            │
        │                                            │
        │ ESTADO: Procesando cambio                 │
        └──────────────────────────────────────────────┘
                               │
        ┌──────────────────────▼───────────────────────┐
        │ LanguageManager.cambiar_idioma() EJECUTA   │
        │ ├─ self._idioma_actual = "en"             │
        │ ├─ self._guardar_idioma("en")             │
        │ └─ self._notificar_cambio()               │
        │                                            │
        │ ESTADO: Notificando a callbacks           │
        └──────────────────────────────────────────────┘
                               │
        ┌──────────────────────▼───────────────────────┐
        │ _notificar_cambio() EJECUTA TODOS LOS      │
        │ CALLBACKS                                  │
        │                                            │
        │ for callback in self._callbacks:           │
        │     callback()  ← Ejecuta                  │
        │                                            │
        │ ESTADO: Actualizando pantallas            │
        └──────────────────────────────────────────────┘
                               │
        ┌──────────────────────▼───────────────────────┐
        │ MiPantalla._actualizar_idioma() EJECUTA    │
        │ ├─ idioma = "en"                          │
        │ ├─ Para cada widget en widgets_texto:     │
        │ │  ├─ nuevo_texto = obtener_texto(...)   │
        │ │  └─ widget.config(text=nuevo_texto)    │
        │ │                                         │
        │ │ ESTADO: Pantalla actualizada           │
        │ └─ TODOS los textos están en inglés       │
        │                                            │
        │ ESTADO: ¡CAMBIO VISIBLE INMEDIATAMENTE!  │
        └──────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════════════════════
5. EJEMPLO DE EJECUCIÓN EN CONSOLA
═════════════════════════════════════════════════════════════════════════════

$ python test_idiomas.py

======================================================================
PRUEBA DEL SISTEMA DE IDIOMAS
======================================================================
[LanguageManager] Inicializado con idioma: es

✓ Idioma actual: es

✓ Traducciones en ESPAÑOL:
    bienvenidos          → BIENVENIDOS
    sistema              → SISTEMA DE CONTROL
    biometrico           → BIOMÉTRICO
    aceptar              → Aceptar
    cancelar             → Cancelar

✓ Traducciones en INGLÉS:
    bienvenidos          → WELCOME
    sistema              → CONTROL SYSTEM
    biometrico           → BIOMETRIC
    aceptar              → Accept
    cancelar             → Cancel

✓ Cambio de idioma a 'en'...
[LanguageManager] Idioma cambiado a: en
[LanguageManager] Idioma guardado: en
[LanguageManager] Notificando cambio a 0 callbacks...
    Idioma actual ahora: en

✓ Verificando persistencia...
    Segunda instancia tiene idioma: en

======================================================================
✓ TODAS LAS PRUEBAS PASARON CORRECTAMENTE
======================================================================


═════════════════════════════════════════════════════════════════════════════
6. ARCHIVOS Y CONTENIDO
═════════════════════════════════════════════════════════════════════════════


BEFORE (Antes):
─────────────
ui/components/barra_superior.py
├─ Botón de idioma:  NO FUNCIONA
└─ Solo muestra iconos

AFTER (Después):
───────────────
ui/components/barra_superior.py
├─ Botón de idioma:  ✓ FUNCIONAL
├─ Muestra "ES" o "EN"
├─ Evento <Button-1> registrado
└─ Cambia idioma al hacer clic


═════════════════════════════════════════════════════════════════════════════
7. DATOS PERSISTENTES
═════════════════════════════════════════════════════════════════════════════

Archivo: data/language_config.json

Creado automáticamente cuando:
- El usuario cambia el idioma
- Se guarda automáticamente

Contenido:
{
  "idioma": "en"
}

Se carga automáticamente cuando:
- La app inicia
- El usuario abre la app (verá el idioma anterior)


═════════════════════════════════════════════════════════════════════════════
8. ORDEN DE EJECUCIÓN COMPLETO
═════════════════════════════════════════════════════════════════════════════

TIEMPO 0:00  App inicia
             │
             ├─► main()
             │   ├─► app = App(root)
             │   │   ├─► self.language_manager = LanguageManager.obtener_instancia()
             │   │   │   ├─► _cargar_idioma()  → "es"
             │   │   │   └─► _callbacks = []
             │   │   └─► self.mostrar_pantalla("principal")
             │   │       └─► crear_pantalla_principal(...)
             │   │           └─► _crear_widgets()
             │   │               ├─► Para cada widget:
             │   │               │   ├─ idioma = "es"
             │   │               │   ├─ texto = obtener_texto(idioma, clave)
             │   │               │   └─ self.widgets_texto[clave] = widget
             │   │               └─► manager.registrar_callback(self._actualizar_idioma)
             │   │
             │   └─► root.mainloop()  ← Esperando eventos
             │
             
TIEMPO 0:05  Usuario hace clic en botón de idioma
             │
             ├─► cambiar_idioma_handler()
             │   ├─► nuevo_idioma = manager.obtener_idioma_opuesto()  → "en"
             │   ├─► manager.cambiar_idioma("en")
             │   │   ├─► Validar "en" ✓
             │   │   ├─► self._idioma_actual = "en"
             │   │   ├─► self._guardar_idioma("en")
             │   │   │   └─► JSON guardado a data/language_config.json
             │   │   └─► self._notificar_cambio()
             │   │       └─► for callback in self._callbacks:
             │   │           └─► callback()  ← SE EJECUTA self._actualizar_idioma()
             │   │               ├─► idioma = "en"
             │   │               └─► Para cada widget:
             │   │                   ├─ nuevo_texto = obtener_texto("en", clave)
             │   │                   └─ widget.config(text=nuevo_texto)  ✓ VISIBLE
             │   │
             │   └─► lbl_idioma_toggle.config(text="EN")  ✓ BOTÓN ACTUALIZADO
             │
             └─► root.mainloop() ← Continúa esperando eventos


═════════════════════════════════════════════════════════════════════════════

Este diagrama muestra exactamente cómo funciona cada parte del sistema.

¡Ahora ya entiendes completamente cómo funciona el sistema de idiomas! 🎓

═════════════════════════════════════════════════════════════════════════════
"""

# Este es un archivo de documentación visual
# Mantenlo en src/ para referencia
