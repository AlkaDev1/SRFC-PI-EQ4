"""
ui/components/teclado_virtual.py
Teclado virtual Tkinter — Raspberry Pi 5 pantalla táctil 800x480

CARACTERÍSTICAS:
  - Auto-detecta si el Entry es numérico → muestra teclado de números
  - Auto-detecta si es texto → muestra QWERTY
  - Shift: 1 toque = una mayúscula, 2 toques = CAPS LOCK, 3 = desactiva
  - Teclas más grandes, diseño oscuro moderno
  - Se coloca en y=285 (parte inferior), altura 195px
  - Backspace, Espacio, Enter, cerrar
  - Dispara <KeyRelease> para activar validaciones de los Entry
"""

import tkinter as tk

# ── Paleta oscura moderna ─────────────────────────────────────────────────────
_P = {
    "bg":          "#141414",
    "fila_bg":     "#141414",
    "tecla_bg":    "#2a2a2a",
    "tecla_fg":    "#f0f0f0",
    "tecla_hover": "#3a3a3a",
    "tecla_borde": "#1a1a1a",
    "especial_bg": "#1e3a1e",
    "especial_fg": "#6fcf6f",
    "accion_bg":   "#1a1a2e",
    "accion_fg":   "#8888cc",
    "shift_on":    "#2e4a2e",
    "shift_fg":    "#6fcf6f",
    "caps_bg":     "#4a3000",
    "caps_fg":     "#ffb347",
    "danger_bg":   "#2e1a1a",
    "danger_fg":   "#e07070",
    "num_bg":      "#1a2a3a",
    "num_fg":      "#70c0ff",
    "separador":   "#222222",
}

# ── Layouts ───────────────────────────────────────────────────────────────────
_QWERTY_1 = ["q","w","e","r","t","y","u","i","o","p"]
_QWERTY_2 = ["a","s","d","f","g","h","j","k","l"]
_QWERTY_3 = ["⇧","z","x","c","v","b","n","m","⌫"]
_QWERTY_4 = ["123"," ","↵","✕"]

_NUM_ROWS = [
    ["7","8","9"],
    ["4","5","6"],
    ["1","2","3"],
    ["ABC","0","⌫"],
]


def _es_entry_numerico(entry: tk.Entry) -> bool:
    """Detecta si un Entry solo acepta números."""
    try:
        vcmd = entry.cget("validatecommand")
        if vcmd:
            return True
    except Exception:
        pass
    # Por nombre del widget o clase padre
    try:
        name = str(entry).lower()
        if "cod" in name or "num" in name:
            return True
    except Exception:
        pass
    return False


class TecladoVirtual:

    def __init__(self, root: tk.Tk, app):
        self.root  = root
        self.app   = app
        self._entry_activo = None
        self._shift  = False
        self._caps   = False
        self._modo   = "qwerty"
        self._visible = False
        self._frame  = None
        self._shift_btn = None
        self._char_btns = []   # lista (btn, char_min)

    # ══════════════════════════════════════════════════════════════════════════
    #  CONEXIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def conectar(self, root: tk.Tk):
        root.bind_all("<FocusIn>",  self._on_focus_in)
        root.bind_all("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event):
        if not isinstance(event.widget, tk.Entry):
            return
        self._entry_activo = event.widget
        # Auto-detectar modo
        if _es_entry_numerico(event.widget):
            self._modo = "num"
        else:
            self._modo = "qwerty"
        self._mostrar()

    def _on_focus_out(self, event):
        if isinstance(event.widget, tk.Entry):
            self.root.after(150, self._verificar_ocultar)

    def _verificar_ocultar(self):
        foco = self.root.focus_get()
        if isinstance(foco, tk.Entry):
            return
        if self._frame and foco:
            try:
                if str(foco).startswith(str(self._frame)):
                    return
            except Exception:
                pass
        self._ocultar()

    # ══════════════════════════════════════════════════════════════════════════
    #  MOSTRAR / OCULTAR
    # ══════════════════════════════════════════════════════════════════════════
    def _mostrar(self):
        if self._visible and self._frame and self._frame.winfo_exists():
            # Solo reconstruir si cambió el modo
            self._construir()
            return
        self._visible = True
        self._construir()

    def _ocultar(self):
        if not self._visible:
            return
        self._visible = False
        self._entry_activo = None
        if self._frame and self._frame.winfo_exists():
            self._frame.destroy()
            self._frame = None
        self._shift_btn = None
        self._char_btns = []

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _construir(self):
        if self._frame and self._frame.winfo_exists():
            self._frame.destroy()

        self._shift_btn = None
        self._char_btns = []

        p = _P
        self._frame = tk.Frame(
            self.root, bg=p["bg"],
            highlightthickness=2,
            highlightbackground=p["especial_bg"])
        self._frame.place(x=0, y=285, width=800, height=195)

        # Línea decorativa superior
        tk.Frame(self._frame, bg=p["especial_fg"], height=2).pack(fill="x")

        contenido = tk.Frame(self._frame, bg=p["bg"])
        contenido.pack(fill="both", expand=True, padx=4, pady=4)

        if self._modo == "num":
            self._construir_num(contenido)
        else:
            self._construir_qwerty(contenido)

    def _tecla(self, parent, texto, comando, tipo="normal",
               ancho=None, alto=None, expand=False):
        """Crea una tecla con estilo."""
        p = _P
        estilos = {
            "normal":   (p["tecla_bg"],    p["tecla_fg"]),
            "especial": (p["especial_bg"], p["especial_fg"]),
            "accion":   (p["accion_bg"],   p["accion_fg"]),
            "danger":   (p["danger_bg"],   p["danger_fg"]),
            "num":      (p["num_bg"],      p["num_fg"]),
            "shift":    (p["shift_on"],    p["shift_fg"]),
            "caps":     (p["caps_bg"],     p["caps_fg"]),
        }
        bg, fg = estilos.get(tipo, estilos["normal"])

        kw = dict(
            text=texto,
            font=("Segoe UI", 13, "bold"),
            fg=fg, bg=bg,
            activebackground=p["tecla_hover"],
            activeforeground=fg,
            relief="flat", bd=0,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=p["tecla_borde"],
            command=comando,
        )
        if ancho:
            kw["width"] = ancho
        if alto:
            kw["height"] = alto

        btn = tk.Button(parent, **kw)
        return btn

    def _construir_qwerty(self, parent):
        p = _P

        # ── Fila 1: q w e r t y u i o p ─────────────────────────────────────
        f1 = tk.Frame(parent, bg=p["bg"])
        f1.pack(fill="x", pady=1)
        for c in _QWERTY_1:
            disp = c.upper() if (self._shift or self._caps) else c
            btn  = self._tecla(f1, disp, lambda ch=c: self._escribir(ch))
            btn.pack(side="left", padx=2, ipady=6, fill="x", expand=True)
            self._char_btns.append((btn, c))

        # ── Fila 2: a s d f g h j k l ────────────────────────────────────────
        f2 = tk.Frame(parent, bg=p["bg"])
        f2.pack(fill="x", pady=1)
        # pequeño spacer para centrar
        tk.Frame(f2, bg=p["bg"], width=20).pack(side="left")
        for c in _QWERTY_2:
            disp = c.upper() if (self._shift or self._caps) else c
            btn  = self._tecla(f2, disp, lambda ch=c: self._escribir(ch))
            btn.pack(side="left", padx=2, ipady=6, fill="x", expand=True)
            self._char_btns.append((btn, c))
        tk.Frame(f2, bg=p["bg"], width=20).pack(side="left")

        # ── Fila 3: ⇧ z x c v b n m ⌫ ────────────────────────────────────────
        f3 = tk.Frame(parent, bg=p["bg"])
        f3.pack(fill="x", pady=1)

        tipo_shift = "caps" if self._caps else ("shift" if self._shift else "accion")
        self._shift_btn = self._tecla(f3, "⇧", self._toggle_shift, tipo_shift)
        self._shift_btn.pack(side="left", padx=2, ipady=6, ipadx=8, fill="x", expand=True)

        for c in ["z","x","c","v","b","n","m"]:
            disp = c.upper() if (self._shift or self._caps) else c
            btn  = self._tecla(f3, disp, lambda ch=c: self._escribir(ch))
            btn.pack(side="left", padx=2, ipady=6, fill="x", expand=True)
            self._char_btns.append((btn, c))

        bsp = self._tecla(f3, "⌫", self._backspace, "danger")
        bsp.pack(side="left", padx=2, ipady=6, ipadx=8, fill="x", expand=True)

        # ── Fila 4: 123 | ESPACIO | ↵ | ✕ ───────────────────────────────────
        f4 = tk.Frame(parent, bg=p["bg"])
        f4.pack(fill="x", pady=1)

        self._tecla(f4, "123", self._modo_num, "accion").pack(
            side="left", padx=2, ipady=6, ipadx=10)

        self._tecla(f4, "ESPACIO", lambda: self._escribir(" "), "accion").pack(
            side="left", padx=2, ipady=6, fill="x", expand=True)

        self._tecla(f4, "↵  Enter", self._enter, "especial").pack(
            side="left", padx=2, ipady=6, ipadx=10)

        self._tecla(f4, "✕", self._ocultar, "danger").pack(
            side="left", padx=2, ipady=6, ipadx=10)

    def _construir_num(self, parent):
        p = _P
        contenedor = tk.Frame(parent, bg=p["bg"])
        contenedor.pack(expand=True)

        for fila in _NUM_ROWS:
            f = tk.Frame(contenedor, bg=p["bg"])
            f.pack(pady=2)
            for tecla in fila:
                if tecla == "⌫":
                    btn = self._tecla(f, "⌫", self._backspace, "danger",
                                      ancho=6, alto=2)
                elif tecla == "ABC":
                    btn = self._tecla(f, "ABC", self._modo_qwerty, "accion",
                                      ancho=6, alto=2)
                else:
                    btn = self._tecla(f, tecla,
                                      lambda c=tecla: self._escribir(c),
                                      "num", ancho=6, alto=2)
                btn.pack(side="left", padx=4, ipady=4)

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIONES
    # ══════════════════════════════════════════════════════════════════════════
    def _escribir(self, char):
        if not (self._entry_activo and self._entry_activo.winfo_exists()):
            return
        try:
            char_final = char.upper() if (self._shift or self._caps) else char
            pos = self._entry_activo.index(tk.INSERT)
            self._entry_activo.insert(pos, char_final)
            self._entry_activo.event_generate("<KeyRelease>")
        except Exception:
            pass
        # Desactivar shift una vez (no caps)
        if self._shift and not self._caps:
            self._shift = False
            self._actualizar_labels()

    def _backspace(self):
        if not (self._entry_activo and self._entry_activo.winfo_exists()):
            return
        try:
            pos = self._entry_activo.index(tk.INSERT)
            if pos > 0:
                self._entry_activo.delete(pos - 1, pos)
                self._entry_activo.event_generate("<KeyRelease>")
        except Exception:
            pass

    def _enter(self):
        if self._entry_activo and self._entry_activo.winfo_exists():
            try:
                self._entry_activo.event_generate("<Return>")
            except Exception:
                pass
        self._ocultar()

    def _toggle_shift(self):
        if self._caps:
            self._caps  = False
            self._shift = False
        elif self._shift:
            self._caps  = True
            self._shift = False
        else:
            self._shift = True
        self._actualizar_labels()

    def _actualizar_labels(self):
        for btn, char in self._char_btns:
            try:
                disp = char.upper() if (self._shift or self._caps) else char
                btn.config(text=disp)
            except tk.TclError:
                pass
        if self._shift_btn:
            try:
                tipo = "caps" if self._caps else ("shift" if self._shift else "accion")
                colores = {
                    "caps":   (_P["caps_bg"],  _P["caps_fg"]),
                    "shift":  (_P["shift_on"], _P["shift_fg"]),
                    "accion": (_P["accion_bg"],_P["accion_fg"]),
                }
                bg, fg = colores[tipo]
                self._shift_btn.config(bg=bg, fg=fg)
            except tk.TclError:
                pass

    def _modo_num(self):
        self._modo = "num"
        self._construir()

    def _modo_qwerty(self):
        self._modo = "qwerty"
        self._construir()