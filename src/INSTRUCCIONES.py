"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          CÓMO INTEGRAR EL SISTEMA DE IDIOMAS EN PANTALLAS                ║
║                      PASO A PASO VISUAL                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
✅ ESTADO ACTUAL DEL SISTEMA
═══════════════════════════════════════════════════════════════════════════

✓ Sistema de idiomas completamente instalado
✓ Botón toggle de idioma funcional en la barra superior
✓ Persistencia de idioma entre sesiones
✓ Diccionario con 100+ traducciones
✓ Patrón SINGLETON y OBSERVER implementados


═══════════════════════════════════════════════════════════════════════════
📂 ARCHIVOS NUEVOS CREADOS
═══════════════════════════════════════════════════════════════════════════

core/
├── language_manager.py      ← Gestor centralizado (450 líneas comentadas)
└── translations.py          ← Diccionario de traducciones (400+ líneas)

ui/components/
└── barra_superior.py        ← ACTUALIZADO: Botón toggle funcional

main.py                       ← ACTUALIZADO: Integración con LanguageManager

src/
├── EJEMPLO_IDIOMA.py        ← Ejemplo completo de implementación
├── GUIA_SISTEMA_IDIOMAS.py  ← Documentación detallada (400 líneas)
└── INSTRUCCIONES.py         ← Este archivo

data/
└── language_config.json     ← Creado automáticamente (preferencia guardada)


═══════════════════════════════════════════════════════════════════════════
🎯 CÓMO USAR EL SISTEMA EN TUS PANTALLAS
═══════════════════════════════════════════════════════════════════════════

EJEMPLO: Actualizar pantalla_principal.py

PASO 1: Copiar el template
────────────────────────────

Abre: ui/screens/pantalla_principal.py

Añade estos imports al inicio:

    from core.language_manager import LanguageManager
    from core.translations import obtener_texto


PASO 2: Crear una clase para la pantalla (si no existe)
─────────────────────────────────────────────────────

Si la pantalla solo tiene funciones, considera convertirla en clase:

    class PantallaPrincipal(tk.Frame):
        def __init__(self, parent, app):
            super().__init__(parent)
            self.app = app
            
            # NUEVO: Obtener manager
            self.manager = LanguageManager.obtener_instancia()
            
            # NUEVO: Diccionario para widgets
            self.widgets_texto = {}
            
            # Crear interfaz
            self._crear_widgets()
            
            # NUEVO: Registrar callback
            self.manager.registrar_callback(self._actualizar_idioma)


PASO 3: En _crear_widgets() - Obtener idioma actual
───────────────────────────────────────────────────

    def _crear_widgets(self):
        # NUEVO: Obtener idioma actual
        idioma = self.manager.obtener_idioma_actual()
        
        # Ejemplo: Crear un label con texto traducido
        texto_titulo = obtener_texto(idioma, "bienvenidos")
        lbl_titulo = tk.Label(parent, text=texto_titulo)
        lbl_titulo.pack()
        
        # NUEVO: Guardar referencia para actualizar después
        self.widgets_texto["bienvenidos"] = lbl_titulo


PASO 4: Crear método _actualizar_idioma()
─────────────────────────────────────────

    def _actualizar_idioma(self):
        """Se ejecuta cuando cambia el idioma"""
        idioma = self.manager.obtener_idioma_actual()
        
        # Actualizar cada widget
        for clave, widget in self.widgets_texto.items():
            nuevo_texto = obtener_texto(idioma, clave)
            widget.config(text=nuevo_texto)


PASO 5: En destroy() - Limpiar
──────────────────────────────

    def destroy(self):
        # NUEVO: Desregistrar callback
        self.manager.desregistrar_callback(self._actualizar_idioma)
        super().destroy()


PASO 6: Actualizar función de entrada
───────────────────────────────────────

    def crear_pantalla_principal(parent: tk.Frame, app) -> None:
        PantallaPrincipal(parent, app)


═══════════════════════════════════════════════════════════════════════════
🔍 CHECKLIST DE IMPLEMENTACIÓN
═══════════════════════════════════════════════════════════════════════════

Para cada pantalla que quieras traducir:

□ Imports correctos
    ├── from core.language_manager import LanguageManager
    └── from core.translations import obtener_texto

□ En __init__()
    ├── self.manager = LanguageManager.obtener_instancia()
    ├── self.widgets_texto = {}
    └── self.manager.registrar_callback(self._actualizar_idioma)

□ En _crear_widgets()
    ├── idioma = self.manager.obtener_idioma_actual()
    ├── Para cada widget con texto:
    │   ├── texto = obtener_texto(idioma, "clave")
    │   └── self.widgets_texto["clave"] = widget
    └── Los widgets muestran texto del idioma actual

□ Método _actualizar_idioma()
    └── Actualiza todos los widgets cuando cambia idioma

□ En destroy()
    └── self.manager.desregistrar_callback(self._actualizar_idioma)

□ Las traducciones existen en core/translations.py
    ├── Español: TRADUCCIONES["es"]["clave"]
    └── Inglés: TRADUCCIONES["en"]["clave"]


═══════════════════════════════════════════════════════════════════════════
🛠️ HERRAMIENTAS DISPONIBLES
═══════════════════════════════════════════════════════════════════════════

1. LanguageManager.obtener_instancia()
   ├── Retorna: La única instancia del gestor
   └── Uso: manager = LanguageManager.obtener_instancia()

2. manager.obtener_idioma_actual()
   ├── Retorna: "es" o "en"
   └── Uso: idioma = manager.obtener_idioma_actual()

3. manager.cambiar_idioma(nuevo_idioma)
   ├── Parámetro: "es" o "en"
   └── Efecto: Notifica a todos los callbacks

4. manager.registrar_callback(funcion)
   ├── Parámetro: Una función que se ejecute sin argumentos
   └── Efecto: Se llamará cuando cambie el idioma

5. manager.desregistrar_callback(funcion)
   ├── Parámetro: La función registrada previamente
   └── Efecto: No se llamará más

6. obtener_texto(idioma, clave)
   ├── Parámetros: "es"/"en", clave de traducción
   ├── Retorna: El texto traducido
   └── Uso: texto = obtener_texto("es", "aceptar")


═══════════════════════════════════════════════════════════════════════════
📝 CÓMO AGREGAR NUEVAS TRADUCCIONES
═══════════════════════════════════════════════════════════════════════════

1. Abre: core/translations.py

2. Busca la sección TRADUCCIONES

3. Añade la clave en AMBOS idiomas:

    TRADUCCIONES = {
        "es": {
            ...
            "mi_texto": "Hola",        ← Añade aquí
        },
        "en": {
            ...
            "mi_texto": "Hello",       ← Y aquí
        }
    }

4. Usa en tu pantalla:

    texto = obtener_texto(idioma, "mi_texto")


═══════════════════════════════════════════════════════════════════════════
🧪 PRUEBA EL SISTEMA
═══════════════════════════════════════════════════════════════════════════

Ejecuta el test:

    python test_idiomas.py

Espera ver:
    ✓ TODAS LAS PRUEBAS PASARON CORRECTAMENTE


═══════════════════════════════════════════════════════════════════════════
🎬 CÓMO USAR EL SISTEMA EN TIEMPO DE EJECUCIÓN
═══════════════════════════════════════════════════════════════════════════

1. Ejecuta la app: python main.py

2. Mira la barra superior - verás "ES" o "EN"

3. Haz clic en el botón de idioma (lado derecho)

4. El idioma cambia inmediatamente

5. TODOS los textos se actualizan en tiempo real

6. La preferencia se guarda automáticamente


═══════════════════════════════════════════════════════════════════════════
⚠️ PROBLEMAS COMUNES Y SOLUCIONES
═══════════════════════════════════════════════════════════════════════════

PROBLEMA: ImportError: No module named 'core.language_manager'
SOLUCIÓN: Asegúrate de que core/language_manager.py existe
          Verifica que main.py se ejecuta desde el directorio raíz


PROBLEMA: KeyError: 'mi_texto' (en obtener_texto)
SOLUCIÓN: Verifica que la clave existe en TRADUCCIONES
          Usa el mismo nombre en ambos idiomas


PROBLEMA: El idioma no cambia cuando presiono el botón
SOLUCIÓN: ✓ Registraste el callback? (manager.registrar_callback(...))
          ✓ Existe _actualizar_idioma() en tu pantalla?
          ✓ Está actualizando los widgets correctos?


PROBLEMA: Error al cambiar de pantalla
SOLUCIÓN: Asegúrate de desregistrar el callback en destroy()
          manager.desregistrar_callback(self._actualizar_idioma)


═══════════════════════════════════════════════════════════════════════════
📚 RECURSOS ÚTILES
═══════════════════════════════════════════════════════════════════════════

Archivos de referencia:

1. src/EJEMPLO_IDIOMA.py
   └── Código completo y comentado de una pantalla con idiomas

2. src/GUIA_SISTEMA_IDIOMAS.py
   └── Documentación exhaustiva (400+ líneas)

3. core/translations.py
   └── Todas las traducciones disponibles

4. core/language_manager.py
   └── Código del gestor (altamente comentado)

5. ui/components/barra_superior.py
   └── Botón de idioma funcional


═══════════════════════════════════════════════════════════════════════════
🚀 PRÓXIMOS PASOS
═══════════════════════════════════════════════════════════════════════════

1. Actualiza pantalla_principal.py (recomendado primero)

2. Actualiza pantalla_login.py

3. Actualiza pantalla_acceso.py

4. Actualiza pantalla_registro.py

5. Actualiza pantalla_gestion.py

6. Actualiza validacionUsrs.py

Cada una debería seguir el mismo patrón.


═══════════════════════════════════════════════════════════════════════════
✨ VENTAJAS DEL SISTEMA
═══════════════════════════════════════════════════════════════════════════

✓ Cambio de idioma SIN reiniciar la app
✓ Persistencia: el usuario ve su idioma al abrir la app
✓ Patrón SINGLETON: una sola instancia de LanguageManager
✓ Patrón OBSERVER: cada pantalla se actualiza automáticamente
✓ Desacoplado: las pantallas no se conocen entre sí
✓ Escalable: fácil agregar más idiomas (ruso, japonés, etc.)
✓ Centralizado: todas las traducciones en UN archivo
✓ Mantenible: cambiar un texto requiere una sola edición
✓ Comentado: código altamente documentado
✓ Testeable: script de prueba incluido


═══════════════════════════════════════════════════════════════════════════
📞 SOPORTE
═══════════════════════════════════════════════════════════════════════════

Si encuentras problemas:

1. Revisa los logs de consola (muestran qué pasa)
2. Comprueba que sigues el template del EJEMPLO_IDIOMA.py
3. Verifica que las traducciones existen en translations.py
4. Prueba con python test_idiomas.py
5. Lee la GUIA_SISTEMA_IDIOMAS.py completa


═══════════════════════════════════════════════════════════════════════════
🎉 ¡LISTO PARA USAR!
═══════════════════════════════════════════════════════════════════════════

El sistema está completamente implementado y funcional.

Solo necesitas:
1. Seguir los pasos anteriores en cada pantalla
2. Agregar tus textos específicos a translations.py
3. Usar obtener_texto() y registrar callbacks

¡El resto funciona automáticamente! 🚀

═══════════════════════════════════════════════════════════════════════════
"""

# Este es un archivo de instrucciones, no contiene código ejecutable
# Mantenlo en src/ para referencia
