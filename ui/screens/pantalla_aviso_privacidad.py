"""
ui/screens/pantalla_aviso_privacidad.py
Pantalla de Aviso de Privacidad — versión táctil para Raspberry Pi 800x480.

CAMBIOS v2:
  - Scroll táctil corregido: usa event.y_root en lugar de event.y
    (evita el bug donde el dedo selecciona texto al bajar)
  - Umbral de 8px para distinguir tap vs arrastre
  - Bloqueo de selección más agresivo con "return break" en todos los eventos
  - Scrollbar oculta (funcional pero invisible)
  - Botón Aceptar siempre visible (side=bottom)
"""

import tkinter as tk
import platform
import time
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
from ui.styles import PALETA, FUENTES
from ui.components.barra_superior import crear_encabezado

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

TEXTO_AVISO = (
    "AVISO DE PRIVACIDAD\n\n"
    "La Universidad de Colima, a través de la Facultad de Ingeniería "
    "Electromecánica, es responsable del tratamiento de sus datos biométricos.\n\n"
    "DATOS QUE RECOPILAMOS\n"
    "  • Imagen facial para reconocimiento biométrico\n"
    "  • Registros de acceso (fecha, hora, laboratorio)\n"
    "  • Datos de identificación (nombre, matrícula o número de empleado)\n\n"
    "FINALIDAD\n"
    "Los datos recabados se utilizarán exclusivamente para:\n"
    "  • Control de acceso a laboratorios\n"
    "  • Trazabilidad de uso de instalaciones\n"
    "  • Seguridad institucional\n\n"
    "ALMACENAMIENTO\n"
    "Toda la información se procesa y almacena de forma local en el dispositivo. "
    "No se transmite ningún dato a servidores externos ni servicios en la nube.\n\n"
    "DERECHOS ARCO\n"
    "Usted tiene derecho a Acceder, Rectificar, Cancelar u Oponerse al tratamiento "
    "de sus datos personales, conforme a la Ley Federal de Protección de Datos "
    "Personales en Posesión de los Particulares.\n\n"
    "Al presionar 'Aceptar', usted otorga su consentimiento para el tratamiento "
    "de sus datos biométricos bajo los términos descritos."
)

# ── Paleta modo claro ─────────────────────────────────────────────────────────
_C = {
    "bg_app":       "#f3f4f5",
    "card_bg":      "#ffffff",
    "texto_titulo": "#1f2328",
    "texto_gris":   "#6b7280",
    "borde":        "#d8dce1",
    "btn_bg":       "#43a047",
    "btn_hover":    "#2e7d32",
    "btn_fg":       "#ffffff",
}

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
_O = {
    "bg_app":       "#071E07",
    "card_bg":      "#0d2a0d",
    "texto_titulo": "#d0f0d0",
    "texto_gris":   "#7aaa7a",
    "borde":        "#1a3a1a",
    "btn_bg":       "#2D531A",
    "btn_hover":    "#477023",
    "btn_fg":       "#ffffff",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaAvisoPrivacidad:
    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._p     = _paleta(app)
        self._widgets_repintables = []
        self._raiz  = Path(__file__).resolve().parent.parent.parent
        self._iconos_btn = {}

        # ── Variables para scroll táctil (v2: usa y_root) ────────────────────
        self._touch_y_root   = 0    # coordenada absoluta de pantalla
        self._touch_time     = 0    # tiempo del último evento
        self._arrastrando    = False
        self._velocidad      = 0    # velocidad de scroll (unidades por ms)
        self._UMBRAL_ARRASTRE = 5   # px mínimos para considerar scroll
        self._momentum_id     = None # ID del after para momentum

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════════════════════════════════════
    #  SOPORTE DE TEMA
    # ══════════════════════════════════════════════════════════════════════════
    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg_app"])
            self._cont.configure(bg=p["bg_app"])
            self._card.configure(bg=p["card_bg"], highlightbackground=p["borde"])
            self._pie.configure(bg=p["card_bg"])
            self._frame_botones.configure(bg=p["card_bg"])
            self._titulo_frame.configure(bg=p["card_bg"])
            self._sep.configure(bg=p["borde"])
            self._frame_scroll.configure(bg=p["card_bg"])
            self._titulo.configure(bg=p["card_bg"], fg=p["texto_titulo"])
            self._texto.configure(bg=p["card_bg"], fg=p["texto_gris"])

            for key in list(self._iconos_btn.keys()):
                self._iconos_btn[key] = None

            ruta_check = self._raiz / "assets" / "img" / "check_icon.png"
            self._iconos_btn["normal"] = self._crear_boton_redondeado(
                160, 45, 8, p["btn_bg"], ruta_check)
            self._iconos_btn["hover"]  = self._crear_boton_redondeado(
                160, 45, 8, p["btn_hover"], ruta_check)

            self._btn_aceptar.configure(
                bg=p["card_bg"], fg=p["btn_fg"],
                activebackground=p["card_bg"], activeforeground=p["btn_fg"],
                image=self._iconos_btn["normal"])
        except tk.TclError:
            pass

    def _limpiar_tema(self, evento=None):
        # Cancelar momentum si existe
        if self._momentum_id:
            self.pantalla.after_cancel(self._momentum_id)
            self._momentum_id = None
        
        if hasattr(self.app, "tema"):
            try:
                self.app.tema.desregistrar(self._on_tema_cambio)
            except tk.TclError:
                pass

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPER — botón redondeado con icono
    # ══════════════════════════════════════════════════════════════════════════
    def _crear_boton_redondeado(self, ancho, alto, radio, color, ruta_icono=None):
        factor = 3
        img = Image.new("RGBA", (ancho * factor, alto * factor), (255, 255, 255, 0))
        ImageDraw.Draw(img).rounded_rectangle(
            (0, 0, ancho * factor, alto * factor),
            fill=color, radius=radio * factor)
        img = img.resize((ancho, alto), Image.Resampling.LANCZOS)

        if ruta_icono and Path(ruta_icono).exists():
            try:
                ico = Image.open(ruta_icono).convert("RGBA").resize(
                    (26, 26), Image.Resampling.LANCZOS)
                img.paste(ico, (18, (alto - 26) // 2), ico)
            except Exception:
                pass
        return ImageTk.PhotoImage(img)

    # ══════════════════════════════════════════════════════════════════════════
    #  SCROLL TÁCTIL v2 — usa y_root para coordenadas absolutas
    #
    #  Problema anterior: event.y es relativo al widget y en RPi con pantalla
    #  táctil el sistema puede reportar coordenadas inconsistentes durante
    #  B1-Motion, haciendo que el delta sea casi 0 o negativo aunque el dedo
    #  baje, lo que no activaba self._arrastrando y Tkinter interpretaba el
    #  gesto como selección de texto.
    #
    #  Fix: event.y_root es la coordenada absoluta de pantalla → siempre
    #  consistente independientemente del widget bajo el dedo.
    # ══════════════════════════════════════════════════════════════════════════
    def _on_touch_start(self, event):
        self._touch_y_root = event.y_root   # ancla para acumular/calcular unidades de scroll
        self._last_y       = event.y_root   # ancla temporal para calcular velocidad entre eventos
        self._start_y      = event.y_root   # ancla del toque original para el umbral
        self._touch_time   = time.time()    # guardar tiempo actual (en segundos)
        self._arrastrando  = False
        self._velocidad    = 0
        self._momentum_accum = 0            # acumulador para los píxeles de la inercia
        
        # Cancelar momentum anterior si existe
        if hasattr(self, "_momentum_id") and self._momentum_id:
            self.pantalla.after_cancel(self._momentum_id)
            self._momentum_id = None
        
        # Limpiar selección inmediatamente al tocar
        try:
            self._texto.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            pass
        return "break"

    def _on_touch_move(self, event):
        ahora = time.time()
        dt = ahora - self._touch_time  # delta de tiempo en segundos
        
        # Calcular velocidad usando el movimiento real entre eventos consecutivos
        dy_vel = self._last_y - event.y_root
        if dt > 0.001:
            # Convertimos a píxeles por frame (asumiendo 60 FPS -> 0.016s por frame)
            velocidad_inst = (dy_vel / dt) * 0.016
            # Filtro para suavizar picos en la velocidad
            self._velocidad = self._velocidad * 0.6 + velocidad_inst * 0.4
            
        self._touch_time = ahora
        self._last_y = event.y_root

        # Activar arrastre si la distancia desde el inicio supera el umbral
        if not self._arrastrando and abs(self._start_y - event.y_root) >= self._UMBRAL_ARRASTRE:
            self._arrastrando = True

        if self._arrastrando:
            # Calcular scroll acumulado respecto a la posición no consumida
            dy_scroll = self._touch_y_root - event.y_root
            unidades = int(dy_scroll / 18)
            
            if unidades != 0:
                self._texto.yview_scroll(unidades, "units")
                # Solo actualizar el ancla restando lo que ya hemos avanzado
                self._touch_y_root -= unidades * 18

        # Siempre cancelar selección durante el movimiento
        try:
            self._texto.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            pass
        return "break"

    def _on_touch_end(self, event):
        if self._arrastrando:
            self._arrastrando = False
            self._momentum_accum = 0
            # Iniciar momentum scroll si hay velocidad significativa (px/frame)
            if abs(self._velocidad) > 1.0:
                self._aplicar_momentum()
            return "break"
        # Si no hubo arrastre fue un tap → dejar que el evento siga (botón Aceptar)

    def _aplicar_momentum(self):
        """Aplica scroll con momentum (inercia) hasta que se detenga."""
        if abs(self._velocidad) > 0.5:  # umbral mínimo de velocidad residual
            # Acumulamos el desplazamiento (en píxeles) por cada frame animado
            if hasattr(self, '_momentum_accum'):
                self._momentum_accum += self._velocidad
            else:
                self._momentum_accum = self._velocidad
                
            unidades = int(self._momentum_accum / 18)
            if unidades != 0:
                self._texto.yview_scroll(unidades, "units")
                # Restar la parte entera consumida
                self._momentum_accum -= (unidades * 18)
            
            # Desacelerar: fricción ajustada para deslizar estilo smartphone
            self._velocidad *= 0.94  
            
            # Programar siguiente iteración en ~16ms (para ~60 fps)
            self._momentum_id = self.pantalla.after(16, self._aplicar_momentum)
        else:
            # Detener cuando la velocidad es insignificante
            self._velocidad = 0
            self._momentum_id = None
            self._momentum_accum = 0

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p

        self.pantalla = tk.Frame(self.parent, bg=p["bg_app"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)

        self._cont = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._cont.pack(fill="both", expand=True, padx=20, pady=(10, 10))

        self._card = tk.Frame(self._cont, bg=p["card_bg"],
                              relief="solid", bd=1,
                              highlightthickness=1,
                              highlightbackground=p["borde"])
        self._card.pack(fill="both", expand=True)

        # ── PIE con botón (side=bottom — siempre visible) ─────────────────────
        self._pie = tk.Frame(self._card, bg=p["card_bg"])
        self._pie.pack(side="bottom", fill="x", padx=16, pady=(8, 12))

        self._frame_botones = tk.Frame(self._pie, bg=p["card_bg"])
        self._frame_botones.pack(fill="x")

        ruta_check = self._raiz / "assets" / "img" / "check_icon.png"
        self._iconos_btn["normal"] = self._crear_boton_redondeado(
            160, 45, 8, p["btn_bg"], ruta_check)
        self._iconos_btn["hover"]  = self._crear_boton_redondeado(
            160, 45, 8, p["btn_hover"], ruta_check)

        self._btn_aceptar = tk.Button(
            self._frame_botones,
            text="     Aceptar",
            font=("Segoe UI", 11, "bold"),
            image=self._iconos_btn["normal"],
            compound="center",
            fg=p["btn_fg"], bd=0, padx=20,
            cursor="hand2",
            command=self._aceptar,
            activeforeground=p["btn_fg"],
            bg=p["card_bg"],
            activebackground=p["card_bg"],
            relief="flat")
        self._btn_aceptar.pack(expand=True)

        self._btn_aceptar.bind("<Enter>",
            lambda e: self._btn_aceptar.config(image=self._iconos_btn["hover"]))
        self._btn_aceptar.bind("<Leave>",
            lambda e: self._btn_aceptar.config(image=self._iconos_btn["normal"]))

        # ── Título ────────────────────────────────────────────────────────────
        self._titulo_frame = tk.Frame(self._card, bg=p["card_bg"])
        self._titulo_frame.pack(fill="x", padx=16, pady=(14, 10))

        self._icono_candado = None
        ruta_candado = self._raiz / "assets" / "img" / "lock_icon.png"
        if ruta_candado.exists():
            try:
                img_pil = Image.open(ruta_candado).resize(
                    (24, 24), Image.Resampling.LANCZOS)
                self._icono_candado = ImageTk.PhotoImage(img_pil)
                self._titulo = tk.Label(
                    self._titulo_frame,
                    text="Aviso de Privacidad",
                    font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                    bg=p["card_bg"], fg=p["texto_titulo"],
                    image=self._icono_candado, compound="left")
            except Exception:
                self._titulo = tk.Label(
                    self._titulo_frame,
                    text="🔒 Aviso de Privacidad",
                    font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                    bg=p["card_bg"], fg=p["texto_titulo"])
        else:
            self._titulo = tk.Label(
                self._titulo_frame,
                text="🔒 Aviso de Privacidad",
                font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                bg=p["card_bg"], fg=p["texto_titulo"])
        self._titulo.pack(side="left")

        # ── Separador ─────────────────────────────────────────────────────────
        self._sep = tk.Frame(self._card, bg=p["borde"], height=1)
        self._sep.pack(fill="x")

        # ── Texto con scroll táctil ───────────────────────────────────────────
        self._frame_scroll = tk.Frame(self._card, bg=p["card_bg"])
        self._frame_scroll.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        # Scrollbar invisible (existe para manejar yview, no se empaqueta)
        self._scrollbar = tk.Scrollbar(self._frame_scroll)

        self._texto = tk.Text(
            self._frame_scroll,
            font=("Segoe UI", 10),
            fg=p["texto_gris"],
            bg=p["card_bg"],
            wrap="word",
            yscrollcommand=self._scrollbar.set,
            bd=0, padx=12, pady=10,
            relief="flat",
            cursor="arrow",
            # Deshabilitar selección con el mouse a nivel de configuración
            selectbackground=p["card_bg"],   # selección invisible
            selectforeground=p["texto_gris"],
            inactiveselectbackground=p["card_bg"],
        )
        self._scrollbar.config(command=self._texto.yview)
        self._texto.pack(fill="both", expand=True)
        self._texto.insert("1.0", TEXTO_AVISO)
        self._texto.config(state="disabled")

        # ── Bindings táctiles v2 ──────────────────────────────────────────────
        # Usar <B1-Motion> para capturar movimiento con botón presionado
        self._texto.bind("<ButtonPress-1>",   self._on_touch_start, add="+")
        self._texto.bind("<B1-Motion>",       self._on_touch_move,  add="+")
        self._texto.bind("<ButtonRelease-1>", self._on_touch_end,   add="+")

        # Prevenir selección por doble/triple clic
        self._texto.bind("<Double-Button-1>", lambda e: "break")
        self._texto.bind("<Triple-Button-1>", lambda e: "break")

        # Scroll con rueda del ratón (escritorio / USB mouse en RPi)
        self._texto.bind("<MouseWheel>",
            lambda e: self._texto.yview_scroll(int(-1*(e.delta/120)), "units"))
        # Linux: botones 4 y 5
        self._texto.bind("<Button-4>",
            lambda e: self._texto.yview_scroll(-2, "units"))
        self._texto.bind("<Button-5>",
            lambda e: self._texto.yview_scroll(2, "units"))

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _aceptar(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_aviso_privacidad(parent: tk.Frame, app) -> None:
    PantallaAvisoPrivacidad(parent, app)