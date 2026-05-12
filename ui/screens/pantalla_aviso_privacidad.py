"""
ui/screens/pantalla_aviso_privacidad.py
Pantalla de Aviso de Privacidad — versión completa.

Esta pantalla reemplaza el modal anterior con una pantalla de navegación
completa que se integra con el sistema de cambio de temas.
Incluye iconos personalizados y botones con fondos redondeados.
"""

import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
from ui.styles import PALETA, FUENTES
from ui.components.barra_superior import crear_encabezado

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
    "bg_app": "#f3f4f5",
    "card_bg": "#ffffff",
    "texto_titulo": "#1f2328",
    "texto_gris": "#6b7280",
    "borde": "#d8dce1",
    "btn_bg": "#43a047",
    "btn_hover": "#2e7d32",
    "btn_fg": "#ffffff",
}

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
_O = {
    "bg_app": "#071E07",
    "card_bg": "#0d2a0d",
    "texto_titulo": "#d0f0d0",
    "texto_gris": "#7aaa7a",
    "borde": "#1a3a1a",
    "btn_bg": "#2D531A",
    "btn_hover": "#477023",
    "btn_fg": "#ffffff",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaAvisoPrivacidad:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._p = _paleta(app)
        self._widgets_repintables = []
        self._raiz = Path(__file__).resolve().parent.parent.parent
        self._iconos_btn = {}  # Almacenar referencias a ImageTk

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════════════════════════════════════
    #  SOPORTE DE TEMA
    # ══════════════════════════════════════════════════════════════════════════
    def _on_tema_cambio(self, paleta_nueva: dict):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg_app"])
            self._cont.configure(bg=p["bg_app"])
            self._card.configure(bg=p["card_bg"], highlightbackground=p["borde"])
            self._pie.configure(bg=p["bg_app"])
            self._frame_botones.configure(bg=p["bg_app"])
            self._titulo.configure(bg=p["card_bg"], fg=p["texto_titulo"])
            self._texto.configure(bg=p["card_bg"], fg=p["texto_gris"])
            
            # Limpiar referencias antiguas de imágenes
            for key in list(self._iconos_btn.keys()):
                self._iconos_btn[key] = None
            
            # Recrear fondos redondeados con nuevos colores
            ruta_check_icon = self._raiz / "assets" / "img" / "check_icon.png"
            
            self._iconos_btn["aceptar_normal"] = self._crear_boton_redondeado_con_icono(
                160, 45, 8, p["btn_bg"], ruta_check_icon
            )
            self._iconos_btn["aceptar_hover"] = self._crear_boton_redondeado_con_icono(
                160, 45, 8, p["btn_hover"], ruta_check_icon
            )
            
            # Actualizar botón con nueva imagen
            self._btn_aceptar.configure(
                bg=p["bg_app"],
                fg=p["btn_fg"],
                activebackground=p["bg_app"],
                activeforeground=p["btn_fg"],
                image=self._iconos_btn["aceptar_normal"]
            )
            # Forzar actualización
            self._btn_aceptar.update_idletasks()

            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists():
                        continue
                    widget.configure(bg=p[bg_k], fg=p[fg_k])
                except tk.TclError:
                    pass
        except tk.TclError:
            pass

    def _limpiar_tema(self, evento=None):
        if hasattr(self.app, "tema"):
            try:
                self.app.tema.desregistrar(self._on_tema_cambio)
            except tk.TclError:
                pass

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _crear_boton_redondeado_con_icono(self, ancho, alto, radio, color, ruta_icono=None):
        """Crea un fondo redondeado con un icono centrado."""
        factor = 3
        img = Image.new("RGBA", (ancho * factor, alto * factor), (255, 255, 255, 0))
        dibujo = ImageDraw.Draw(img)
        dibujo.rounded_rectangle(
            (0, 0, ancho * factor, alto * factor),
            fill=color,
            radius=radio * factor
        )

        img_suave = img.resize((ancho, alto), Image.Resampling.LANCZOS)

        if ruta_icono and Path(ruta_icono).exists():
            try:
                icono = Image.open(ruta_icono).convert("RGBA")
                tam_icono = 26
                icono = icono.resize((tam_icono, tam_icono), Image.Resampling.LANCZOS)
                pos_x = 18
                pos_y = (alto - tam_icono) // 2
                img_suave.paste(icono, (pos_x, pos_y), icono)
            except Exception:
                pass

        return ImageTk.PhotoImage(img_suave)

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DE UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p

        self.pantalla = tk.Frame(self.parent, bg=p["bg_app"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)

        # ── Contenedor principal ──
        self._cont = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._cont.pack(fill="both", expand=True, padx=20, pady=20)

        # ── Tarjeta con contenido ──
        self._card = tk.Frame(
            self._cont,
            bg=p["card_bg"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=p["borde"],
        )
        self._card.pack(fill="both", expand=True)

        # ── Título con icono ──
        titulo_frame = tk.Frame(self._card, bg=p["card_bg"])
        titulo_frame.pack(fill="x", padx=16, pady=(16, 12))

        self._icono_candado = None
        ruta_candado = self._raiz / "assets" / "img" / "lock_icon.png"
        if ruta_candado.exists():
            try:
                img_pil = Image.open(ruta_candado).resize((24, 24), Image.Resampling.LANCZOS)
                self._icono_candado = ImageTk.PhotoImage(img_pil)
                self._titulo = tk.Label(
                    titulo_frame,
                    text="Aviso de Privacidad",
                    font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                    bg=p["card_bg"],
                    fg=p["texto_titulo"],
                    image=self._icono_candado,
                    compound="left"
                )
            except Exception:
                self._titulo = tk.Label(
                    titulo_frame,
                    text="🔒 Aviso de Privacidad",
                    font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                    bg=p["card_bg"],
                    fg=p["texto_titulo"],
                )
        else:
            self._titulo = tk.Label(
                titulo_frame,
                text="🔒 Aviso de Privacidad",
                font=FUENTES.get("modal_titulo", ("Segoe UI", 16, "bold")),
                bg=p["card_bg"],
                fg=p["texto_titulo"],
            )
        self._titulo.pack(side="left")

        # ── Separador ──
        sep = tk.Frame(self._card, bg=p["borde"], height=1)
        sep.pack(fill="x", padx=0, pady=0)

        # ── Frame con scrollbar ──
        frame_scroll = tk.Frame(self._card, bg=p["card_bg"])
        frame_scroll.pack(fill="both", expand=True, padx=16, pady=12)

        scrollbar = tk.Scrollbar(frame_scroll)
        scrollbar.pack(side="right", fill="y")

        # ── Texto del aviso ──
        self._texto = tk.Text(
            frame_scroll,
            font=("Segoe UI", 10),
            fg=p["texto_gris"],
            bg=p["card_bg"],
            wrap="word",
            yscrollcommand=scrollbar.set,
            bd=0,
            padx=12,
            pady=10,
            relief="flat",
        )
        self._texto.pack(fill="both", expand=True)
        scrollbar.config(command=self._texto.yview)
        self._texto.insert("1.0", TEXTO_AVISO)
        self._texto.config(state="disabled")

        # ── Pie con botón ──
        self._pie = tk.Frame(self._card, bg=p["bg_app"])
        self._pie.pack(fill="x", side="bottom", padx=16, pady=16)

        self._frame_botones = tk.Frame(self._pie, bg=p["bg_app"])
        self._frame_botones.pack(fill="x")

        # Cargar iconos para botones
        ruta_check_icon = self._raiz / "assets" / "img" / "check_icon.png"
        
        # Crear fondos redondeados para botón
        self._iconos_btn["aceptar_normal"] = self._crear_boton_redondeado_con_icono(
            160, 45, 8, p["btn_bg"], ruta_check_icon
        )
        self._iconos_btn["aceptar_hover"] = self._crear_boton_redondeado_con_icono(
            160, 45, 8, p["btn_hover"], ruta_check_icon
        )

        # Botón Aceptar (centrado)
        self._btn_aceptar = tk.Button(
            self._frame_botones,
            text="     Aceptar",
            font=("Segoe UI", 11, "bold"),
            image=self._iconos_btn["aceptar_normal"],
            compound="center",
            fg=p["btn_fg"],
            bd=0,
            padx=20,
            cursor="hand2",
            command=self._aceptar,
            activeforeground=p["btn_fg"],
            bg=p["bg_app"],
            activebackground=p["bg_app"],
            relief="flat"
        )
        self._btn_aceptar.pack(expand=True)

        # Efectos Hover para botón Aceptar
        self._btn_aceptar.bind(
            "<Enter>",
            lambda e: self._btn_aceptar.config(image=self._iconos_btn["aceptar_hover"])
        )
        self._btn_aceptar.bind(
            "<Leave>",
            lambda e: self._btn_aceptar.config(image=self._iconos_btn["aceptar_normal"])
        )

    def _aceptar(self):
        """Acepta el aviso y vuelve a la pantalla anterior"""
        self.app.mostrar_pantalla("principal")


# ─────────────────────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def crear_pantalla_aviso_privacidad(parent: tk.Frame, app) -> None:
    """Función de entrada para crear la pantalla de aviso de privacidad."""
    PantallaAvisoPrivacidad(parent, app)
