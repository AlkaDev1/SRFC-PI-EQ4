"""
ui/screens/pantalla_principal.py
Pantalla principal — versión refinada profesional.
Proyecto: SRFC-PI-EQ4 | Universidad de Colima | 800x480
"""

import tkinter as tk
import math
from pathlib import Path
from datetime import datetime
from ui.components.barra_superior import crear_encabezado
from ui.styles import FUENTES, MEDIDAS
from ui.components.aviso_privacidad import mostrar_aviso

# ── Paleta ────────────────────────────────────────────────────────────────────
V_DARK   = "#1B5E20"   # header
V_MID    = "#2E7D32"   # fondo central
V_LIGHT  = "#43A047"   # círculo / botones
V_ACCENT = "#66BB6A"   # separadores / hover sutil
V_BANDA  = "#357A38"   # banda diagonal (tono intermedio)
BLANCO   = "#FFFFFF"
GRIS_BG  = "#EEF2EE"   # fondo barra botones
TEXTO_DIM= "#A5D6A7"   # subtítulo sobre verde

_RAIZ    = Path(__file__).resolve().parent.parent.parent
_LOGO    = _RAIZ / "assets" / "img" / "logoudc.png"
_PERICOS = _RAIZ / "assets" / "img" / "pericos.png"
_ICONO_ACCESO = _RAIZ / "assets" / "img" / "accederIcon.png"
_ICONO_AVISO_PRIVACIDAD = _RAIZ / "assets" / "img" / "avisoPrivacidadIcon.png"
_ICONO_GESTION = _RAIZ / "assets" / "img" / "gestionIcon.png"

# ─────────────────────────────────────────────────────────────────────────────
def crear_pantalla_principal(parent: tk.Frame, app) -> None:
    f = tk.Frame(parent, bg=V_DARK)
    f.pack(fill="both", expand=True)
    crear_encabezado(f, app.root)
    _Central(f)
    _Botones(f, app)

# ─────────────────────────────────────────────────────────────────────────────
#  ÁREA CENTRAL
# ─────────────────────────────────────────────────────────────────────────────
class _Central(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=V_MID)
        self.pack(fill="both", expand=True)
        self._cv   = tk.Canvas(self, bg=V_MID, highlightthickness=0)
        self._cv.pack(fill="both", expand=True)
        self._foto = None
        self._cv.bind("<Configure>", self._draw)

    def _draw(self, _=None):
        c = self._cv
        W = c.winfo_width();  H = c.winfo_height()
        if W < 2 or H < 2: return
        c.delete("all")

        # Fondo base
        c.create_rectangle(0, 0, W, H, fill=V_MID, outline="")

        # Banda diagonal decorativa
        self._banda(c, W, H)

        # Ola blanca — base al 86 % de la altura del área central
        self._ola(c, W, H, base_pct=0.86, amp_pct=0.08)

        # Círculo + mascota
        # radio = 36 % de H → siempre queda dentro del área verde
        radio = int(H * 0.36)
        cx    = int(W * 0.20)
        cy    = int(H * 0.44)   # levemente arriba del centro
        self._circulo(c, cx, cy, radio)

        # Texto
        self._texto(c, W, H, cx, radio)

    def _banda(self, c, W, H):
        pts = [int(W*0.32), 0, int(W*0.58), 0, int(W*0.86), H, int(W*0.60), H]
        c.create_polygon(pts, fill=V_BANDA, outline="")

    def _ola(self, c, W, H, base_pct, amp_pct):
        base  = int(H * base_pct)
        amp   = int(H * amp_pct)
        pts   = [0, H]
        steps = 120
        for i in range(steps + 1):
            x = W * i / steps
            y = base - int(amp * math.sin(math.pi * i / steps))
            pts += [x, y]
        pts += [W, H]
        c.create_polygon(pts, fill=BLANCO, outline="", smooth=True)

    def _circulo(self, c, cx, cy, radio):
        # Sombra
        c.create_oval(cx-radio+5, cy-radio+5,
                      cx+radio+5, cy+radio+5,
                      fill=V_DARK, outline="")
        # Anillo blanco externo
        c.create_oval(cx-radio, cy-radio,
                      cx+radio, cy+radio,
                      fill=BLANCO, outline="")
        # Relleno verde interior
        ri = radio - 6
        c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri,
                      fill=V_LIGHT, outline="")

        # Imagen pericos
        if _PERICOS.exists():
            try:
                from PIL import Image, ImageTk
                import numpy as np
                img  = Image.open(str(_PERICOS)).convert("RGBA")
                data = np.array(img)
                r_c, g_c, b_c = data[:,:,0], data[:,:,1], data[:,:,2]
                data[(r_c < 50) & (g_c < 50) & (b_c < 50), 3] = 0
                img  = Image.fromarray(data)
                tam  = int(ri * 1.85)
                img  = img.resize((tam, tam), Image.LANCZOS)
                foto = ImageTk.PhotoImage(img)
                self._foto = foto
                c.create_image(cx, cy, image=foto, anchor="center")
            except Exception as e:
                print(f"[PERICOS] {e}")
                c.create_text(cx, cy, text="🦜🦜",
                              font=("Segoe UI", int(ri * 0.5)),
                              fill=BLANCO, anchor="center")
        else:
            c.create_text(cx, cy, text="🦜🦜",
                          font=("Segoe UI", int(radio * 0.5)),
                          fill=BLANCO, anchor="center")

    def _texto(self, c, W, H, cx, radio):
        # Zona de texto: desde el borde derecho del círculo hasta el borde derecho
        zona_izq  = cx + radio + 20        # margen derecho del círculo
        zona_ancho = W - zona_izq - 20     # hasta margen derecho
        tx = zona_izq + zona_ancho // 2    # centro de esa zona
        ty = int(H * 0.35)

        # Tamaño dinámico — no superar el ancho disponible
        tam = max(26, int(H * 0.175))

        # Sombra
        c.create_text(tx+2, ty+3, text="BIENVENIDOS",
                      font=("Segoe UI", tam, "bold"),
                      fill=V_DARK, anchor="center")
        # Principal
        c.create_text(tx, ty, text="BIENVENIDOS",
                      font=("Segoe UI", tam, "bold"),
                      fill=BLANCO, anchor="center")

        # Subtítulo
        sub = max(10, int(H * 0.060))
        c.create_text(tx, ty + tam + 8,
                      text="Sistema de Control Biométrico",
                      font=("Segoe UI", sub),
                      fill=TEXTO_DIM, anchor="center")


# ─────────────────────────────────────────────────────────────────────────────
#  BARRA BOTONES — altura fija 78 px
# ─────────────────────────────────────────────────────────────────────────────
class _Botones(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=GRIS_BG, height=78)
        self.pack(fill="x", side="bottom")
        self.pack_propagate(False)

        tk.Frame(self, bg=V_ACCENT, height=2).pack(fill="x")

        fila = tk.Frame(self, bg=GRIS_BG)
        fila.pack(expand=True)          # centrado vertical por expand

        _Btn(fila, _ICONO_ACCESO, "ACCEDER",
            lambda: app.mostrar_pantalla("acceso"))
        _Btn(fila, _ICONO_GESTION,  "GESTIÓN",
            lambda: app.mostrar_pantalla("gestion"))
        _Btn(fila, _ICONO_AVISO_PRIVACIDAD, "AVISO DE\nPRIVACIDAD",
            lambda: mostrar_aviso(
                parent.winfo_toplevel(), al_aceptar=lambda: None))


# ─────────────────────────────────────────────────────────────────────────────
#  BOTÓN con canvas redondeado
# ─────────────────────────────────────────────────────────────────────────────
class _Btn:
    W, H, R = 208, 58, 10

    def __init__(self, parent, img_path: Path, txt, cmd):
        self._txt = txt; self._cmd = cmd
        self._bg  = V_LIGHT; self._hov = V_DARK

        self._img_tk = None
        if img_path.exists():
            try:

                self._img_tk = tk.PhotoImage(file=str(img_path))
            except Exception as e:
                print(f"[ERROR ICONO] No se pudo cargar {img_path}: {e}")

        wrap = tk.Frame(parent, bg=GRIS_BG)
        wrap.pack(side="left", padx=10, pady=8)

        self._cv = tk.Canvas(wrap, width=self.W, height=self.H, bg=GRIS_BG, highlightthickness=0, cursor="hand2")
        self._cv.pack()
        self._draw(self._bg)

        self._cv.bind("<Button-1>", lambda e: cmd())
        self._cv.bind("<Enter>",    lambda e: self._draw(self._hov))
        self._cv.bind("<Leave>",    lambda e: self._draw(self._bg))

    def _draw(self, color):
        c = self._cv; c.delete("all")

        _rr(c, 2, 2, self.W+2, self.H+2, self.R, "#b0bfb0")

        _rr(c, 0, 0, self.W, self.H, self.R, color)
        

        if self._img_tk:

            c.create_image(30, self.H//2, image=self._img_tk, anchor="center")
        else:

            c.create_text(30, self.H//2, text="?", font=("Segoe UI", 17), fill=BLANCO)

        c.create_line(56, 10, 56, self.H-10, fill=V_ACCENT, width=1)

        c.create_text(132, self.H//2, text=self._txt,
                    font=("Segoe UI", 12, "bold"),
                    fill=BLANCO, anchor="center", justify="center")

# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIÓN AUXILIAR PARA DIBUJAR RECTÁNGULOS REDONDEADOS
# ─────────────────────────────────────────────────────────────────────────────
def _rr(c, x1, y1, x2, y2, r, col):
    kw = dict(fill=col, outline="")
    c.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90, **kw)
    c.create_arc(x2-2*r, y1,      x2,     y1+2*r, start=0,   extent=90, **kw)
    c.create_arc(x1,      y2-2*r, x1+2*r, y2,     start=180, extent=90, **kw)
    c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, **kw)
    c.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
    c.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)