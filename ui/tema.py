"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ui/tema.py  —  Sistema de Temas SRFC-PI-EQ4                                ║
║  Universidad de Colima | Raspberry Pi 5 | 800x480                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ¿QUÉ HACE ESTE ARCHIVO?                                                    ║
║  Define dos diccionarios de colores (CLARO y OSCURO) y una clase            ║
║  GestorTema que:                                                             ║
║    1. Guarda qué tema está activo (claro u oscuro).                          ║
║    2. Permite que cualquier pantalla "se registre" para recibir un aviso     ║
║       cuando el tema cambie.                                                 ║
║    3. Al cambiar el tema, avisa a todos los registrados para que             ║
║       actualicen sus colores automáticamente (patrón Observer).             ║
║                                                                              ║
║  ¿CÓMO SE USA EN MAIN.PY?                                                   ║
║    from ui.tema import GestorTema                                            ║
║    self.tema = GestorTema()          # crear UNA SOLA instancia en App      ║
║                                                                              ║
║  ¿CÓMO LO USA UNA PANTALLA?                                                 ║
║    p = app.tema.paleta()             # obtener colores del tema activo      ║
║    app.tema.registrar(self._aplicar_tema)  # suscribirse a cambios          ║
║    # cuando se destruye la pantalla:                                         ║
║    app.tema.desregistrar(self._aplicar_tema)                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ──────────────────────────────────────────────────────────────────────────────
#  PALETA MODO CLARO
#  Son los colores originales del proyecto, tal como estaban en styles.py
#  y en los archivos de pantallas.
# ──────────────────────────────────────────────────────────────────────────────
TEMA_CLARO = {
    # ── Colores generales de ventana/página ───────────────────────────────
    "window_bg":            "#e6eaef",   # Fondo de la ventana raíz
    "page_bg":              "#ffffff",   # Fondo de las páginas/frames

    # ── Barra superior (header) ──────────────────────────────────────────
    "topbar_bg":            "#1B5E20",   # Fondo del header  (verde oscuro)
    "topbar_logo_bg":       "#1B5E20",   # Fondo detrás del logo
    "topbar_titulo_fg":     "#66BB6A",   # Texto "SISTEMA DE CONTROL"
    "topbar_sistema_fg":    "#ffffff",   # Texto "BIOMÉTRICO"
    "topbar_fecha_fg":      "#ffffff",   # Color de fecha/hora
    "topbar_dim_fg":        "#A5D6A7",   # Subtítulo tenue "Universidad..."
    "topbar_separador":     "#43A047",   # Línea vertical separadora
    "topbar_btn_bg":        "#43A047",   # Fondo botones header (idioma/tema)
    "topbar_btn_fg":        "#ffffff",   # Texto/icono botones header
    "topbar_btn_hover":     "#66BB6A",   # Hover sobre botones header

    # ── Área central de pantalla_principal ───────────────────────────────
    "central_bg":           "#2E7D32",   # Fondo verde medio
    "central_banda":        "#357A38",   # Banda diagonal decorativa
    "central_ola":          "#ffffff",   # Color de la ola inferior
    "central_circulo":      "#43A047",   # Relleno del círculo de mascota
    "central_circulo_aro":  "#ffffff",   # Aro externo del círculo
    "central_sombra":       "#1B5E20",   # Sombra del círculo
    "central_texto":        "#ffffff",   # "BIENVENIDOS"
    "central_subtitulo":    "#A5D6A7",   # "Sistema de Control Biométrico"

    # ── Barra de botones inferiores (ACCEDER / GESTIÓN / AVISO) ──────────
    "botones_barra_bg":     "#EEF2EE",   # Fondo de la barra de botones
    "botones_separador":    "#66BB6A",   # Línea superior de la barra
    "boton_bg":             "#43A047",   # Fondo normal del botón
    "boton_hover":          "#1B5E20",   # Fondo al pasar el mouse
    "boton_sombra":         "#b0bfb0",   # Sombra del rectángulo redondeado
    "boton_linea":          "#66BB6A",   # Línea divisora ícono | texto
    "boton_fg":             "#ffffff",   # Texto del botón

    # ── Pantalla acceso / validación (cámara) ────────────────────────────
    "acceso_fondo":         "#000000",   # Fondo negro detrás de la cámara
    "acceso_ok_bg":         "#1B5E20",   # Fondo verde de acceso concedido
    "acceso_deny_bg":       "#000000",   # Se mantiene cámara en denegado
    "acceso_ok_texto":      "#ffffff",   # Texto en pantalla verde
    "acceso_deny_texto":    "#f44336",   # Texto rojo de acceso denegado
    "acceso_hud_bg":        "#1a1a1a",   # Fondo del HUD inferior
    "acceso_hud_fg":        "#ffffff",   # Texto del HUD
    "acceso_hud_sub":       "#888888",   # Subtexto del HUD
    "acceso_barra_ok":      "#4CAF50",   # Barra confianza alta (verde)
    "acceso_barra_mid":     "#FFC107",   # Barra confianza media (amarillo)
    "acceso_barra_low":     "#546e7a",   # Barra confianza baja (gris)
    "acceso_barra_fondo":   "#333333",   # Fondo de la barra de confianza
    "acceso_bbox_ok":       "#00e676",   # Recuadro de cara reconocida
    "acceso_bbox_deny":     "#f44336",   # Recuadro de cara no reconocida
    "acceso_bbox_scan":     "#42a5f5",   # Recuadro escaneando

    # ── Tabla / gestión ──────────────────────────────────────────────────
    "tabla_header_bg":      "#6fa67a",   # Encabezado de la tabla
    "tabla_header_active":  "#5f956a",   # Hover en encabezado
    "tabla_row_a":          "#f9fbfc",   # Fila par
    "tabla_row_b":          "#f1f5f7",   # Fila impar
    "tabla_fg":             "#2f3c47",   # Texto de la tabla
    "tabla_titulo_fg":      "#1f2a33",   # Título de la sección
    "ghost_bg":             "#edf1f5",   # Fondo botones ghost
    "ghost_active":         "#dde4ec",   # Hover botones ghost
}


# ──────────────────────────────────────────────────────────────────────────────
#  PALETA MODO OSCURO
#  Basada en la paleta "Dark Moss / Dark Green":
#    #071E07  Dark Green   → fondos más profundos
#    #2D531A  Dark Moss    → fondos medios, topbar, botones
#    #477023  Fern Green   → acentos, separadores, hover
#    #ffffff               → todo el texto
#
#  Todos los claves son IDÉNTICOS a TEMA_CLARO para que las pantallas
#  puedan hacer paleta["clave"] sin preocuparse de qué tema está activo.
# ──────────────────────────────────────────────────────────────────────────────
TEMA_OSCURO = {
    # ── Colores generales ─────────────────────────────────────────────────
    "window_bg":            "#071E07",   # Dark Green — fondo de la ventana raíz
    "page_bg":              "#071E07",   # Dark Green — fondo de páginas/frames

    # ── Barra superior ────────────────────────────────────────────────────
    "topbar_bg":            "#2D531A",   # Dark Moss  — fondo del header
    "topbar_logo_bg":       "#2D531A",   # Dark Moss  — fondo detrás del logo
    "topbar_titulo_fg":     "#ffffff",   # Blanco     — "SISTEMA DE CONTROL"
    "topbar_sistema_fg":    "#ffffff",   # Blanco     — "BIOMÉTRICO"
    "topbar_fecha_fg":      "#ffffff",   # Blanco     — fecha y hora
    "topbar_dim_fg":        "#ffffff",   # Blanco     — "Universidad de Colima"
    "topbar_separador":     "#477023",   # Fern Green — línea vertical
    "topbar_btn_bg":        "#477023",   # Fern Green — fondo botones header
    "topbar_btn_fg":        "#ffffff",   # Blanco     — ícono botones header
    "topbar_btn_hover":     "#2D531A",   # Dark Moss  — hover botones header

    # ── Área central ──────────────────────────────────────────────────────
    "central_bg":           "#2D531A",   # Dark Moss  — fondo principal del área
    "central_banda":        "#477023",   # Fern Green — banda diagonal decorativa
    "central_ola":          "#071E07",   # Dark Green — ola inferior (contraste)
    "central_circulo":      "#477023",   # Fern Green — relleno del círculo
    "central_circulo_aro":  "#ffffff",   # Blanco     — aro externo del círculo
    "central_sombra":       "#071E07",   # Dark Green — sombra del círculo
    "central_texto":        "#ffffff",   # Blanco     — "BIENVENIDOS"
    "central_subtitulo":    "#ffffff",   # Blanco     — "Sistema de Control..."

    # ── Barra de botones inferiores ───────────────────────────────────────
    "botones_barra_bg":     "#071E07",   # Dark Green — fondo de la barra
    "botones_separador":    "#477023",   # Fern Green — línea superior
    "boton_bg":             "#2D531A",   # Dark Moss  — fondo normal del botón
    "boton_hover":          "#477023",   # Fern Green — hover del botón
    "boton_sombra":         "#071E07",   # Dark Green — sombra del botón
    "boton_linea":          "#477023",   # Fern Green — divisor ícono | texto
    "boton_fg":             "#ffffff",   # Blanco     — texto del botón

    # ── Pantalla acceso / validación (cámara) ────────────────────────────
    "acceso_fondo":         "#071E07",   # Dark Green — fondo detrás de la cámara
    "acceso_ok_bg":         "#2D531A",   # Dark Moss  — pantalla de acceso OK
    "acceso_deny_bg":       "#071E07",   # Dark Green — fondo en denegado
    "acceso_ok_texto":      "#ffffff",   # Blanco     — texto acceso concedido
    "acceso_deny_texto":    "#ff5252",   # Rojo       — texto acceso denegado
    "acceso_hud_bg":        "#2D531A",   # Dark Moss  — fondo del HUD inferior
    "acceso_hud_fg":        "#ffffff",   # Blanco     — texto del HUD
    "acceso_hud_sub":       "#ffffff",   # Blanco     — subtexto del HUD
    "acceso_barra_ok":      "#477023",   # Fern Green — barra confianza alta
    "acceso_barra_mid":     "#FFC107",   # Amarillo   — barra confianza media
    "acceso_barra_low":     "#2D531A",   # Dark Moss  — barra confianza baja
    "acceso_barra_fondo":   "#071E07",   # Dark Green — fondo barra confianza
    "acceso_bbox_ok":       "#ffffff",   # Blanco     — recuadro cara reconocida
    "acceso_bbox_deny":     "#ff5252",   # Rojo       — recuadro cara no reconocida
    "acceso_bbox_scan":     "#477023",   # Fern Green — recuadro escaneando

    # ── Tabla / gestión ───────────────────────────────────────────────────
    "tabla_header_bg":      "#2D531A",   # Dark Moss  — encabezado de tabla
    "tabla_header_active":  "#477023",   # Fern Green — hover encabezado
    "tabla_row_a":          "#071E07",   # Dark Green — fila par
    "tabla_row_b":          "#0d2a0d",   # Entre Dark Green y Dark Moss — fila impar
    "tabla_fg":             "#ffffff",   # Blanco     — texto de la tabla
    "tabla_titulo_fg":      "#ffffff",   # Blanco     — título de la sección
    "ghost_bg":             "#2D531A",   # Dark Moss  — fondo botones ghost
    "ghost_active":         "#477023",   # Fern Green — hover botones ghost
}


# ──────────────────────────────────────────────────────────────────────────────
#  GESTOR DE TEMA  —  patrón Observer simplificado
# ──────────────────────────────────────────────────────────────────────────────
class GestorTema:
    """
    Clase central que controla el tema activo y notifica cambios.

    CÓMO FUNCIONA INTERNAMENTE:
    ┌─────────────────────────────────────────────────────────────────┐
    │  GestorTema mantiene una lista de "listeners" (funciones).      │
    │  Cuando se llama toggle(), cambia _oscuro y llama a cada        │
    │  listener pasándole la nueva paleta como argumento.             │
    │                                                                 │
    │  Cada pantalla registra su método _aplicar_tema como listener.  │
    │  Ese método recibe la paleta y repinta sus widgets.             │
    └─────────────────────────────────────────────────────────────────┘

    CICLO COMPLETO:
      Botón 🌙 presionado
        → barra_superior llama tema.toggle()
          → GestorTema._oscuro = True
          → GestorTema notifica a todos los listeners
            → pantalla_principal._aplicar_tema(TEMA_OSCURO)   ← repinta
            → pantalla_acceso._aplicar_tema(TEMA_OSCURO)      ← repinta
            → barra_superior._aplicar_tema(TEMA_OSCURO)       ← repinta
      Botón ☀️ presionado → mismo ciclo con TEMA_CLARO
    """

    def __init__(self):
        # Estado actual: False = claro, True = oscuro
        self._oscuro: bool = False

        # Lista de funciones a llamar cuando cambia el tema.
        # Cada elemento es un callable: fn(paleta: dict) -> None
        self._listeners: list = []

    # ── Acceso a la paleta ────────────────────────────────────────────────────
    def paleta(self) -> dict:
        """Devuelve el diccionario de colores del tema ACTIVO.

        Uso en una pantalla al construirse:
            p = app.tema.paleta()
            self.frame.configure(bg=p["page_bg"])
        """
        return TEMA_OSCURO if self._oscuro else TEMA_CLARO

    def es_oscuro(self) -> bool:
        """True si el modo oscuro está activo."""
        return self._oscuro

    # ── Toggle (accionado por el botón en barra_superior) ────────────────────
    def toggle(self):
        """Alterna entre modo claro y oscuro y notifica a todos los registrados.

        Este método es el que se asigna al botón 🌙/☀️ en barra_superior:
            btn_tema.config(command=app.tema.toggle)
        """
        self._oscuro = not self._oscuro
        self._notificar()

    # ── Registro / desregistro de listeners ──────────────────────────────────
    def registrar(self, callback):
        """Registra una función para ser avisada cuando cambie el tema.

        La función debe aceptar UN argumento: la nueva paleta (dict).

        Ejemplo de uso en una pantalla:
            # Al inicializar la pantalla:
            app.tema.registrar(self._aplicar_tema)

            # El método que recibe el aviso:
            def _aplicar_tema(self, p: dict):
                self.frame.configure(bg=p["page_bg"])
                self.lbl.configure(fg=p["topbar_titulo_fg"])
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def desregistrar(self, callback):
        """Quita una función de la lista de avisos.

        MUY IMPORTANTE: llamar esto cuando la pantalla se destruye,
        para evitar que el gestor intente llamar a widgets ya eliminados.

        Ejemplo:
            def destruir(self):
                app.tema.desregistrar(self._aplicar_tema)
                self.pantalla.destroy()
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ── Notificación interna ──────────────────────────────────────────────────
    def _notificar(self):
        """Llama a todos los listeners registrados con la paleta activa.

        Se usa una copia de la lista para que si un listener se desregistra
        durante la notificación no cause errores de iteración.
        """
        paleta_actual = self.paleta()
        for fn in list(self._listeners):
            try:
                fn(paleta_actual)
            except Exception as e:
                # Si un widget ya fue destruido puede lanzar TclError.
                # Lo capturamos para que los otros listeners sigan recibiendo
                # la notificación sin interrumpirse.
                print(f"[GestorTema] Error en listener {fn}: {e}")