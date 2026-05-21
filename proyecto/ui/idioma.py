"""
ui/idioma.py
GestorIdioma — manejo de idiomas para SRFC-PI-EQ4

Uso:
    from ui.idioma import GestorIdioma

    # En App.__init__:
    self.idioma = GestorIdioma()

    # Obtener un texto:
    self.idioma.t("login.btn_ingresar")        # → "INGRESAR" o "LOG IN"

    # Cambiar idioma:
    self.idioma.toggle()   # alterna ES ↔ EN
    self.idioma.set("en")  # fuerza un idioma

    # Registrar callback para cuando cambie el idioma:
    self.idioma.registrar(mi_funcion)          # mi_funcion() sin argumentos
    self.idioma.desregistrar(mi_funcion)

Patrón idéntico a GestorTema:
    - registrar / desregistrar / _notificar
    - idioma persiste en data/idioma.cfg
    - t() acepta claves con punto: "seccion.clave"
"""

import json
from pathlib import Path

_RAIZ     = Path(__file__).resolve().parent.parent        # raíz del proyecto
_LANG_JSON = _RAIZ / "data" / "lang.json"
_CFG_FILE  = _RAIZ / "data" / "idioma.cfg"
_IDIOMAS   = ("es", "en")
_DEFAULT   = "es"


class GestorIdioma:

    def __init__(self):
        self._idioma    = self._cargar_preferencia()
        self._diccionario: dict = {}
        self._listeners: list   = []
        self._cargar_json()

    # ── Carga ──────────────────────────────────────────────────────────────────
    def _cargar_json(self):
        try:
            with open(_LANG_JSON, encoding="utf-8") as f:
                datos = json.load(f)
            self._diccionario = datos.get(self._idioma, datos.get(_DEFAULT, {}))
        except Exception as e:
            print(f"[GestorIdioma] No se pudo cargar {_LANG_JSON}: {e}")
            self._diccionario = {}

    def _cargar_preferencia(self) -> str:
        try:
            if _CFG_FILE.exists():
                idioma = _CFG_FILE.read_text(encoding="utf-8").strip()
                if idioma in _IDIOMAS:
                    return idioma
        except Exception:
            pass
        return _DEFAULT

    def _guardar_preferencia(self):
        try:
            _CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
            _CFG_FILE.write_text(self._idioma, encoding="utf-8")
        except Exception as e:
            print(f"[GestorIdioma] No se pudo guardar preferencia: {e}")

    # ── API pública ────────────────────────────────────────────────────────────
    def idioma_actual(self) -> str:
        """Retorna el código del idioma activo: 'es' o 'en'."""
        return self._idioma

    def es_ingles(self) -> bool:
        return self._idioma == "en"

    def set(self, codigo: str):
        """Fuerza un idioma por código ('es' o 'en')."""
        if codigo not in _IDIOMAS or codigo == self._idioma:
            return
        self._idioma = codigo
        self._cargar_json()
        self._guardar_preferencia()
        self._notificar()

    def toggle(self):
        """Alterna entre ES y EN."""
        nuevo = "en" if self._idioma == "es" else "es"
        self.set(nuevo)

    def t(self, clave: str, fallback: str = "") -> str:
        """
        Retorna el texto para la clave dada.
        Acepta notación con punto: "login.btn_ingresar"
        Si la clave no existe devuelve `fallback` (o la clave misma).
        """
        partes = clave.split(".")
        nodo   = self._diccionario
        for parte in partes:
            if isinstance(nodo, dict):
                nodo = nodo.get(parte)
            else:
                nodo = None
                break
        if nodo is None:
            return fallback if fallback else clave
        # Si es lista, devolver como está (útil para roles, meses, etc.)
        return nodo

    # ── Listeners (mismo patrón que GestorTema) ───────────────────────────────
    def registrar(self, callback):
        """Registra una función que se llama sin argumentos al cambiar idioma."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def desregistrar(self, callback):
        """Elimina un listener registrado previamente."""
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _notificar(self):
        """Llama a todos los listeners registrados."""
        for cb in list(self._listeners):
            try:
                cb()
            except Exception as e:
                print(f"[GestorIdioma] Error en listener: {e}")