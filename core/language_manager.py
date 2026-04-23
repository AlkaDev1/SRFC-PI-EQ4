"""
core/language_manager.py
═════════════════════════════════════════════════════════════════════
GESTOR CENTRALIZADO DE IDIOMAS
═════════════════════════════════════════════════════════════════════

Esta clase SINGLETON gestiona el idioma actual de la aplicación.
Solo existe UNA instancia durante toda la ejecución.

FUNCIONAMIENTO:
1. Se inicializa una vez al arrancar la app
2. Carga el idioma guardado (o usa "es" por defecto)
3. Permite cambiar el idioma dinámicamente
4. Guarda la preferencia para la próxima sesión
5. Notifica a los observadores cuando cambia el idioma

PATRÓN SINGLETON:
- Asegura que haya solo una instancia
- Se accede globalmente con LanguageManager.obtener_instancia()
- Evita conflictos de estado

CALLBACKS (OBSERVADORES):
- Cuando cambia el idioma, ejecuta funciones registradas
- Permite que las pantallas se actualicen automáticamente
"""

import json
import os
from pathlib import Path
from typing import Callable, List

# ═════════════════════════════════════════════════════════════════════
# CLASE SINGLETON: GESTOR DE IDIOMAS
# ═════════════════════════════════════════════════════════════════════

class LanguageManager:
    """
    Gestor centralizado de idiomas con patrón SINGLETON.
    
    ATRIBUTOS:
    ----------
    _instancia : LanguageManager
        La única instancia de esta clase (patrón Singleton)
    
    _idioma_actual : str
        Idioma activo ("es" o "en")
    
    _callbacks : List[Callable]
        Lista de funciones que se ejecutan cuando cambia el idioma
    
    _archivo_config : Path
        Ruta al archivo de configuración (data/language_config.json)
    """
    
    # Variable de clase para almacenar la única instancia
    _instancia = None
    
    def __init__(self):
        """
        CONSTRUCTOR - Solo se ejecuta UNA VEZ
        
        ORDEN DE EJECUCIÓN:
        1. Define la ruta del archivo de configuración
        2. Carga el idioma guardado (o usa "es" por defecto)
        3. Inicializa lista de callbacks vacía
        """
        # Ruta de la carpeta 'data'
        ruta_base = Path(__file__).resolve().parent.parent
        self._ruta_datos = ruta_base / "data"
        self._ruta_datos.mkdir(exist_ok=True)  # Crear si no existe
        
        # Archivo donde se guarda la preferencia de idioma
        self._archivo_config = self._ruta_datos / "language_config.json"
        
        # Inicializar lista de callbacks (observadores)
        self._callbacks: List[Callable] = []
        
        # Cargar idioma guardado o usar español por defecto
        self._idioma_actual = self._cargar_idioma()
        
        print(f"[LanguageManager] Inicializado con idioma: {self._idioma_actual}")
    
    @staticmethod
    def obtener_instancia():
        """
        PATRÓN SINGLETON - Obtiene o crea la única instancia
        
        GARANTIZA:
        - Solo existe UNA instancia durante toda la ejecución
        - Se puede acceder desde cualquier parte del código
        
        USO:
        ----
        manager = LanguageManager.obtener_instancia()
        idioma = manager.obtener_idioma_actual()
        
        RETORNA:
        --------
        LanguageManager : La única instancia
        """
        if LanguageManager._instancia is None:
            LanguageManager._instancia = LanguageManager()
        return LanguageManager._instancia
    
    # ═════════════════════════════════════════════════════════════════
    # GESTIÓN DE IDIOMA
    # ═════════════════════════════════════════════════════════════════
    
    def _cargar_idioma(self) -> str:
        """
        CARGA EL IDIOMA GUARDADO desde el archivo config
        
        PROCESO:
        1. Intenta leer data/language_config.json
        2. Si existe y es válido, usa ese idioma
        3. Si no existe o hay error, usa español ("es")
        4. Guarda el idioma por si no existía el archivo
        
        RETORNA:
        --------
        str : "es" o "en" (idioma guardado o por defecto)
        """
        try:
            if self._archivo_config.exists():
                with open(self._archivo_config, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    idioma = datos.get("idioma", "es")
                    if idioma in ["es", "en"]:
                        return idioma
        except Exception as e:
            print(f"[LanguageManager] Error al cargar idioma: {e}")
        
        # Por defecto, español
        return "es"
    
    def _guardar_idioma(self, idioma: str) -> None:
        """
        GUARDA EL IDIOMA ACTUAL en el archivo config
        
        PROCESO:
        1. Crea un diccionario con la configuración
        2. Escribe en JSON en data/language_config.json
        3. Persiste la preferencia para la próxima sesión
        
        PARÁMETROS:
        -----------
        idioma : str
            Idioma a guardar ("es" o "en")
        """
        try:
            datos = {"idioma": idioma}
            with open(self._archivo_config, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            print(f"[LanguageManager] Idioma guardado: {idioma}")
        except Exception as e:
            print(f"[LanguageManager] Error al guardar idioma: {e}")
    
    def obtener_idioma_actual(self) -> str:
        """
        OBTIENE el idioma actualmente activo
        
        USO:
        ----
        idioma = manager.obtener_idioma_actual()  # "es" o "en"
        
        RETORNA:
        --------
        str : "es" o "en"
        """
        return self._idioma_actual
    
    def cambiar_idioma(self, nuevo_idioma: str) -> None:
        """
        CAMBIA EL IDIOMA Y NOTIFICA A TODOS LOS OBSERVADORES
        
        ORDEN DE EJECUCIÓN:
        1. Valida que el idioma sea "es" o "en"
        2. Si es diferente al actual, lo cambia
        3. Guarda la preferencia en archivo
        4. EJECUTA todos los callbacks registrados
           (Esto hace que las pantallas se actualicen automáticamente)
        
        PARÁMETROS:
        -----------
        nuevo_idioma : str
            El nuevo idioma a activar ("es" o "en")
        
        EJEMPLO:
        --------
        manager.cambiar_idioma("en")  # Cambia a inglés
        # Automáticamente se ejecutan todos los callbacks
        # Las pantallas se actualizan sin necesidad de recargarlas
        """
        # Validar idioma
        if nuevo_idioma not in ["es", "en"]:
            print(f"[LanguageManager] Idioma inválido: {nuevo_idioma}")
            return
        
        # Si es el mismo idioma, no hacer nada
        if nuevo_idioma == self._idioma_actual:
            return
        
        # Cambiar el idioma
        self._idioma_actual = nuevo_idioma
        print(f"[LanguageManager] Idioma cambiado a: {self._idioma_actual}")
        
        # Guardar la preferencia
        self._guardar_idioma(nuevo_idioma)
        
        # EJECUTAR TODOS LOS CALLBACKS
        # Esto notifica a todas las pantallas que cambió el idioma
        self._notificar_cambio()
    
    def obtener_idioma_opuesto(self) -> str:
        """
        OBTIENE el idioma opuesto al actual
        
        ÚTIL PARA: Botones toggle que cambien al otro idioma
        
        USO:
        ----
        idioma_nuevo = manager.obtener_idioma_opuesto()
        manager.cambiar_idioma(idioma_nuevo)
        
        RETORNA:
        --------
        str : "en" si actual es "es", y viceversa
        """
        return "en" if self._idioma_actual == "es" else "es"
    
    # ═════════════════════════════════════════════════════════════════
    # SISTEMA DE CALLBACKS (OBSERVADORES)
    # ═════════════════════════════════════════════════════════════════
    
    def registrar_callback(self, callback: Callable) -> None:
        """
        REGISTRA UNA FUNCIÓN que se ejecutará cuando cambie el idioma
        
        PATRÓN OBSERVER:
        - Las pantallas se registran como observadores
        - Cuando cambia el idioma, TODAS se actualizan automáticamente
        - No es necesario recargar la app
        
        PARÁMETROS:
        -----------
        callback : Callable
            Función que se llamará sin argumentos cuando cambie idioma
        
        EJEMPLO:
        --------
        def actualizar_pantalla():
            # Código para actualizar textos
            pass
        
        manager = LanguageManager.obtener_instancia()
        manager.registrar_callback(actualizar_pantalla)
        
        ORDEN DE EJECUCIÓN:
        1. La función se añade a _callbacks
        2. Cuando hay un cambio de idioma:
           a. Se ejecuta _notificar_cambio()
           b. Que llama a TODAS las funciones en _callbacks
           c. Cada pantalla actualiza sus textos
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            print(f"[LanguageManager] Callback registrado: {callback.__name__}")
    
    def desregistrar_callback(self, callback: Callable) -> None:
        """
        DESREGISTRA UNA FUNCIÓN de la lista de observadores
        
        ÚTIL CUANDO: Se destruye una pantalla
        Evita llamar callbacks en pantallas ya no visibles
        
        PARÁMETROS:
        -----------
        callback : Callable
            Función a remover de la lista de callbacks
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            print(f"[LanguageManager] Callback desregistrado: {callback.__name__}")
    
    def _notificar_cambio(self) -> None:
        """
        EJECUTA TODOS LOS CALLBACKS REGISTRADOS
        
        ESTO PROVOCA QUE:
        - Todas las pantallas activas se actualicen
        - Los textos cambien al nuevo idioma
        - Todo sucede sin recargar la aplicación
        
        ORDEN DE EJECUCIÓN:
        1. Itera sobre cada callback en _callbacks
        2. Lo ejecuta sin argumentos
        3. Si hay error, lo captura y continúa
        """
        print(f"[LanguageManager] Notificando cambio a {len(self._callbacks)} callbacks...")
        for callback in self._callbacks:
            try:
                callback()  # Ejecuta la función
                print(f"  ✓ Callback ejecutado: {callback.__name__}")
            except Exception as e:
                print(f"  ✗ Error en callback {callback.__name__}: {e}")
