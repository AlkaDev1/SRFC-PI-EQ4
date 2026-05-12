"""
ui/screens/pantalla_principal.py
Pantalla principal — versión refinada profesional.
Proyecto: SRFC-PI-EQ4 | Universidad de Colima | 800x480

ESTRUCTURA DE IMÁGENES (en assets/img/):
  fondo_claro.png   — olas + decorativos modo claro  (800x332px)
  fondo_oscuro.png  — olas + decorativos modo oscuro (800x332px)
  pericos.png       — mascota, se recorta circular con PIL

CAPAS DEL CANVAS (de atrás hacia adelante):
  1. fondo_claro.png / fondo_oscuro.png  — imagen de fondo completa
  2. Círculo dibujado en código (sombra + aro blanco + relleno verde)
  3. pericos.png recortado circular y centrado dentro del círculo
  4. Texto "BIENVENIDOS" + línea decorativa + badge subtítulo

SOPORTE DE TEMA:
  - Al construirse obtiene la paleta activa de app.tema
  - Registra _aplicar_tema() en GestorTema
  - Al cambiar el tema, _aplicar_tema() redibuja el canvas con la nueva imagen
    y actualiza los colores de la barra de botones
  - Al destruirse (bind <Destroy>) se desregistra del GestorTema
  - _Botones usa after(50) al construirse para forzar el color correcto
    incluso al navegar de vuelta desde otra pantalla
"""

import tkinter as tk
from pathlib import Path
from ui.components.barra_superior import crear_encabezado
from ui.styles import FUENTES, MEDIDAS
from ui.components.aviso_privacidad import mostrar_aviso
from PIL import Image, ImageTk, ImageDraw

# ── Paleta modo claro ─────────────────────────────────────────────────────────
V_DARK   = "#104213"
V_MID    = "#2E7D32"
V_LIGHT  = "#43A047"
V_ACCENT = "#60D366"
BLANCO   = "#FFFFFF"

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
O_DARK   = "#071E07"
O_MID    = "#2D531A"
O_ACCENT = "#4F8B15"

# ── Rutas de assets ───────────────────────────────────────────────────────────
_RAIZ                   = Path(__file__).resolve().parent.parent.parent
_PERICOS                = _RAIZ / "assets" / "img" / "pericos.png"
_ICONO_ACCESO           = _RAIZ / "assets" / "img" / "accederIcon.png"
_ICONO_AVISO_PRIVACIDAD = _RAIZ / "assets" / "img" / "avisoPrivacidadIcon.png"
_ICONO_GESTION          = _RAIZ / "assets" / "img" / "gestionIcon.png"
_FONDO_CLARO            = _RAIZ / "assets" / "img" / "fondo_claro.png"
_FONDO_OSCURO           = _RAIZ / "assets" / "img" / "fondo_oscuro.png"


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: recorte circular con PIL
#  Tkinter no soporta transparencia PNG en Canvas nativamente.
#  Esta función crea una máscara circular y la aplica como canal alpha,
#  haciendo que las esquinas sean transparentes sin importar el fondo original.
# ─────────────────────────────────────────────────────────────────────────────
def _recortar_circular(img: Image.Image) -> Image.Image:
    img     = img.convert("RGBA")
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, img.size[0]-1, img.size[1]-1), fill=255)
    img.putalpha(mascara)
    return img


# ─────────────────────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def crear_pantalla_principal(parent: tk.Frame, app) -> None:
    es_oscuro = hasattr(app, "tema") and app.tema.es_oscuro()

    f = tk.Frame(parent, bg=O_DARK if es_oscuro else V_DARK)
    f.pack(fill="both", expand=True)

    crear_encabezado(f, app)

    central = _Central(f, app)
    botones = _Botones(f, app)

    # ── Listener de tema ──────────────────────────────────────────────────────
    # Llamado automáticamente por GestorTema cuando el usuario presiona ☀️/🌙.
    def _aplicar_tema(p: dict):
        try:
            f.configure(bg=p["central_sombra"])
            central._aplicar_tema(p)
            botones._aplicar_tema(p)
        except tk.TclError:
            pass

    if hasattr(app, "tema"):
        app.tema.registrar(_aplicar_tema)

    # Desregistrar al destruirse el frame para no llamar widgets eliminados
    def _limpiar(evento=None):
        if hasattr(app, "tema"):
            app.tema.desregistrar(_aplicar_tema)

    f.bind("<Destroy>", _limpiar)


# ─────────────────────────────────────────────────────────────────────────────
#  ÁREA CENTRAL
# ─────────────────────────────────────────────────────────────────────────────
class _Central(tk.Frame):
    def __init__(self, parent, app):
        es_oscuro = hasattr(app, "tema") and app.tema.es_oscuro()
        super().__init__(parent, bg=O_MID if es_oscuro else V_MID)
        self.pack(fill="both", expand=True)

        self._app       = app
        self._foto_bg   = None
        self._foto_perc = None

        self._cv = tk.Canvas(self, bg=O_MID if es_oscuro else V_MID, highlightthickness=0)
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", self._draw)

    def _aplicar_tema(self, p: dict):
        """Recibe nueva paleta y redibuja el canvas con los nuevos colores e imagen."""
        try:
            bg = p.get("central_bg", V_MID)
            self.configure(bg=bg)
            self._cv.configure(bg=bg)
            self._draw()
        except tk.TclError:
            pass

    def _draw(self, _=None):
        c = self._cv
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 2 or H < 2:
            return
        c.delete("all")

        es_oscuro = hasattr(self._app, "tema") and self._app.tema.es_oscuro()

        # ── 1. Imagen de fondo ────────────────────────────────────────────────
        ruta_fondo = _FONDO_OSCURO if es_oscuro else _FONDO_CLARO
        if ruta_fondo.exists():
            try:
                img = Image.open(ruta_fondo).resize((W, H), Image.LANCZOS)
                self._foto_bg = ImageTk.PhotoImage(img)
                c.create_image(0, 0, image=self._foto_bg, anchor="nw")
            except Exception as e:
                print(f"[FONDO] {e}")
                c.create_rectangle(0, 0, W, H,
                                   fill=O_MID if es_oscuro else V_MID, outline="")
        else:
            c.create_rectangle(0, 0, W, H,
                               fill=O_MID if es_oscuro else V_MID, outline="")

        # ── 2. Círculo dibujado en código ─────────────────────────────────────
        radio = int(H * 0.36)
        cx    = int(W * 0.20)
        cy    = int(H * 0.44)
        ri    = radio - 6

        color_circulo = O_ACCENT if es_oscuro else V_LIGHT
        color_sombra  = O_DARK   if es_oscuro else V_DARK

        c.create_oval(cx-radio+5, cy-radio+5, cx+radio+5, cy+radio+5,
                      fill=color_sombra, outline="")
        c.create_oval(cx-radio, cy-radio, cx+radio, cy+radio,
                      fill=BLANCO, outline="")
        c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri,
                      fill=color_circulo, outline="")

        # ── 3. Pericos circular ────────────────────────────────────
        if _PERICOS.exists():
            try:
                target   = int(ri * 1.5)
                img_perc = Image.open(_PERICOS).resize((target, target), Image.LANCZOS)
                self._foto_perc = ImageTk.PhotoImage(img_perc)
                c.create_image(cx, cy, image=self._foto_perc, anchor="center")
            except Exception as e:
                print(f"[PERICOS] {e}")
                c.create_text(cx, cy, text="🦜🦜",
                              font=("Segoe UI", int(ri * 0.4)), fill=BLANCO)
        else:
            c.create_text(cx, cy, text="🦜🦜",
                          font=("Segoe UI", int(radio * 0.4)), fill=BLANCO)

        # ── 4. Texto "BIENVENIDOS" + línea + badge ────────────────────────────
        zona_izq   = cx + radio + 20
        zona_ancho = W - zona_izq - 20
        tx  = zona_izq + zona_ancho // 2
        ty  = int(H * 0.28)
        tam = max(20, int(H * 0.13))
        sub = max(10, int(H * 0.058))

        color_titulo = BLANCO if es_oscuro else "#1B5E20"

        c.create_text(tx+2, ty+3, text="BIENVENIDOS",
                      font=("Segoe UI", tam, "bold"),
                      fill=color_sombra, anchor="center")
        c.create_text(tx, ty, text="BIENVENIDOS",
                      font=("Segoe UI", tam, "bold"),
                      fill=color_titulo, anchor="center")

        linea_y  = ty + int(tam * 0.68)
        linea_x1 = zona_izq
        c.create_rectangle(linea_x1, linea_y,
                           linea_x1 + int(zona_ancho * 0.45), linea_y + 3,
                           fill=O_ACCENT if es_oscuro else V_LIGHT, outline="")
        c.create_rectangle(linea_x1 + int(zona_ancho * 0.47), linea_y,
                           linea_x1 + int(zona_ancho * 0.60), linea_y + 3,
                           fill="#2D531A" if es_oscuro else "#A5D6A7", outline="")

        badge_y  = linea_y + 8
        badge_h  = int(sub * 2.2)
        badge_w  = int(zona_ancho * 0.95)
        badge_x1 = zona_izq
        badge_x2 = badge_x1 + badge_w

        color_badge_bg    = "#1a3a0f" if es_oscuro else "#E8F5E9"
        color_badge_borde = O_ACCENT  if es_oscuro else V_LIGHT
        color_badge_texto = BLANCO    if es_oscuro else V_MID

        _badge(c, badge_x1, badge_y, badge_x2, badge_y + badge_h,
               badge_h // 2, color_badge_bg, color_badge_borde)
        c.create_text((badge_x1 + badge_x2) // 2, badge_y + badge_h // 2,
                      text="Sistema de Control Biométrico",
                      font=("Segoe UI", int(sub * 0.95), "bold"),
                      fill=color_badge_texto, anchor="center")


# ─────────────────────────────────────────────────────────────────────────────
#  BARRA BOTONES
# ─────────────────────────────────────────────────────────────────────────────
class _Botones(tk.Frame):
    def __init__(self, parent, app):
        self._app     = app
        es_oscuro     = hasattr(app, "tema") and app.tema.es_oscuro()
        bg            = O_MID    if es_oscuro else "#ffffff"
        sep_color     = O_ACCENT if es_oscuro else V_ACCENT

        super().__init__(parent, bg=bg, height=78)
        self.pack(fill="x", side="bottom")
        self.pack_propagate(False)

        self._sep = tk.Frame(self, bg=sep_color, height=2)
        self._sep.pack(fill="x")

        self._fila = tk.Frame(self, bg=bg)
        self._fila.pack(expand=True)

        self._btn_acceder = _Btn(self._fila, _ICONO_ACCESO, "ACCEDER",
                                  lambda: app.mostrar_pantalla("acceso"), es_oscuro, bg)
        self._btn_gestion = _Btn(self._fila, _ICONO_GESTION, "GESTIÓN",
                                  lambda: app.mostrar_pantalla("gestion"), es_oscuro, bg)
        self._btn_aviso   = _Btn(self._fila, _ICONO_AVISO_PRIVACIDAD, "AVISO DE\nPRIVACIDAD",
                                  lambda: mostrar_aviso(
                                      parent.winfo_toplevel(), al_aceptar=lambda: None),
                                  es_oscuro, bg)

        # Forzar repintado inicial después de que Tkinter termine de construir
        # los widgets. Esto corrige el color transparente al volver de otra pantalla.
        self.after(50, self._repintar_inicial)

    def _repintar_inicial(self):
        """Fuerza el color correcto al construirse, especialmente al volver de otra pantalla."""
        if hasattr(self._app, "tema"):
            try:
                self._aplicar_tema(self._app.tema.paleta())
            except tk.TclError:
                pass

    def _aplicar_tema(self, p: dict):
        """Repinta la barra y sus botones con la nueva paleta."""
        try:
            bg  = p["botones_barra_bg"]
            sep = p["botones_separador"]
            self.configure(bg=bg)
            self._sep.configure(bg=sep)
            self._fila.configure(bg=bg)
            self._btn_acceder._aplicar_tema(p, bg)
            self._btn_gestion._aplicar_tema(p, bg)
            self._btn_aviso._aplicar_tema(p, bg)
        except tk.TclError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  BOTÓN con canvas redondeado
# ─────────────────────────────────────────────────────────────────────────────
class _Btn:
    W, H, R = 208, 58, 10

    def __init__(self, parent, img_path: Path, txt, cmd, es_oscuro=False, wrap_bg="#ffffff"):
        self._txt    = txt
        self._bg     = O_MID    if es_oscuro else V_LIGHT
        self._hov    = O_DARK   if es_oscuro else V_DARK
        self._sombra = O_DARK   if es_oscuro else "#b0bfb0"
        self._linea  = O_ACCENT if es_oscuro else V_ACCENT
        self._img_tk = None

        if img_path.exists():
            try:
                self._img_tk = tk.PhotoImage(file=str(img_path))
            except Exception as e:
                print(f"[ERROR ICONO] {img_path}: {e}")

        self._wrap = tk.Frame(parent, bg=wrap_bg)
        self._wrap.pack(side="left", padx=10, pady=8)

        self._cv = tk.Canvas(self._wrap, width=self.W, height=self.H,
                              bg=wrap_bg, highlightthickness=0, cursor="hand2")
        self._cv.pack()
        self._draw(self._bg)

        self._cv.bind("<Button-1>", lambda e: cmd())
        self._cv.bind("<Enter>",    lambda e: self._draw(self._hov))
        self._cv.bind("<Leave>",    lambda e: self._draw(self._bg))

    def _aplicar_tema(self, p: dict, wrap_bg: str):
        """Actualiza colores del botón según nueva paleta."""
        self._bg     = p["boton_bg"]
        self._hov    = p["boton_hover"]
        self._sombra = p["boton_sombra"]
        self._linea  = p["boton_linea"]
        try:
            self._wrap.configure(bg=wrap_bg)
            self._cv.configure(bg=wrap_bg)
            self._draw(self._bg)
        except tk.TclError:
            pass

    def _draw(self, color):
        c = self._cv
        c.delete("all")
        _rr(c, 2, 2, self.W+2, self.H+2, self.R, self._sombra)
        _rr(c, 0, 0, self.W,   self.H,   self.R, color)
        if self._img_tk:
            c.create_image(30, self.H//2, image=self._img_tk, anchor="center")
        else:
            c.create_text(30, self.H//2, text="?",
                          font=("Segoe UI", 17), fill=BLANCO)
        c.create_line(56, 10, 56, self.H-10, fill=self._linea, width=1)
        c.create_text(132, self.H//2, text=self._txt,
                      font=("Segoe UI", 12, "bold"),
                      fill=BLANCO, anchor="center", justify="center")


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _badge(c, x1, y1, x2, y2, r, fill, border):
    kw = dict(fill=fill, outline="")
    c.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90, **kw)
    c.create_arc(x2-2*r, y1,      x2,     y1+2*r, start=0,   extent=90, **kw)
    c.create_arc(x1,      y2-2*r, x1+2*r, y2,     start=180, extent=90, **kw)
    c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, **kw)
    c.create_rectangle(x1+r, y1, x2-r, y2, **kw)
    c.create_rectangle(x1, y1+r, x2, y2-r, **kw)
    c.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90,
                 style="arc", outline=border, width=1.5)
    c.create_arc(x2-2*r, y1,      x2,     y1+2*r, start=0,   extent=90,
                 style="arc", outline=border, width=1.5)
    c.create_arc(x1,      y2-2*r, x1+2*r, y2,     start=180, extent=90,
                 style="arc", outline=border, width=1.5)
    c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,
                 style="arc", outline=border, width=1.5)
    c.create_line(x1+r, y1, x2-r, y1, fill=border, width=1.5)
    c.create_line(x1+r, y2, x2-r, y2, fill=border, width=1.5)
    c.create_line(x1, y1+r, x1, y2-r, fill=border, width=1.5)
    c.create_line(x2, y1+r, x2, y2-r, fill=border, width=1.5)


def _rr(c, x1, y1, x2, y2, r, col):
    kw = dict(fill=col, outline="")
    c.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90, **kw)
    c.create_arc(x2-2*r, y1,      x2,     y1+2*r, start=0,   extent=90, **kw)
    c.create_arc(x1,      y2-2*r, x1+2*r, y2,     start=180, extent=90, **kw)
    c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, **kw)
    c.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
    c.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)