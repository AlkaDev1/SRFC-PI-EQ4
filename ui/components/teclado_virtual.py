"""
ui/components/teclado_virtual.py
Teclado virtual Tkinter — Raspberry Pi 5 pantalla táctil 800x480

CAMBIOS v3:
  - Detección numérica corregida: solo si tiene validatecommand Y NO es password
  - Layout numérico rediseñado: teclas grandes que llenan todo el espacio
  - QWERTY mejorado: teclas más grandes y uniformes
  - Shift: 1 toque = mayúscula, 2 toques = CAPS LOCK, 3 = off
"""

import tkinter as tk

# ── Paleta oscura ─────────────────────────────────────────────────────────────
_P = {
    "bg":          "#141414",
    "tecla_bg":    "#2a2a2a",
    "tecla_fg":    "#f0f0f0",
    "tecla_hover": "#3a3a3a",
    "tecla_borde": "#1a1a1a",
    "especial_bg": "#1e3a1e",
    "especial_fg": "#6fcf6f",
    "accion_bg":   "#252540",
    "accion_fg":   "#9090dd",
    "shift_bg":    "#2e4a2e",
    "shift_fg":    "#6fcf6f",
    "caps_bg":     "#4a3000",
    "caps_fg":     "#ffb347",
    "danger_bg":   "#3a1a1a",
    "danger_fg":   "#e07070",
    "num_bg":      "#1a2a4a",
    "num_fg":      "#70b8ff",
    "num_cero_bg": "#1a2a4a",
    "separador":   "#1a1a1a",
}

_QWERTY_F1 = ["q","w","e","r","t","y","u","i","o","p"]
_QWERTY_F2 = ["a","s","d","f","g","h","j","k","l"]
_QWERTY_F3 = ["z","x","c","v","b","n","m"]


def _es_entry_numerico(entry: tk.Entry) -> bool:
    """
    Detecta si un Entry solo acepta números.
    IMPORTANTE: campos de contraseña (show='●' o show='•') NUNCA son numéricos.
    """
    try:
        # Si tiene show configurado es un campo de contraseña → QWERTY siempre
        show = entry.cget("show")
        if show and show != "":
            return False
    except Exception:
        pass

    try:
        # Verificar si tiene validatecommand (solo los numéricos lo tienen)
        vcmd = entry.cget("validatecommand")
        if vcmd:
            return True
    except Exception:
        pass

    return False


class TecladoVirtual:

    def __init__(self, root: tk.Tk, app):
        self.root  = root
        self.app   = app
        self._entry_activo = None
        self._shift   = False
        self._caps    = False
        self._modo    = "qwerty"
        self._visible = False
        self._frame   = None
        self._shift_btn  = None
        self._char_btns  = []

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
        nuevo_modo = "num" if _es_entry_numerico(event.widget) else "qwerty"
        if nuevo_modo != self._modo or not self._visible:
            self._modo = nuevo_modo
            self._mostrar()
        elif not self._visible:
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

        # Línea verde superior
        tk.Frame(self._frame, bg=p["especial_fg"], height=2).pack(fill="x")

        contenido = tk.Frame(self._frame, bg=p["bg"])
        contenido.pack(fill="both", expand=True, padx=3, pady=3)

        if self._modo == "num":
            self._construir_num(contenido)
        else:
            self._construir_qwerty(contenido)

    # ══════════════════════════════════════════════════════════════════════════
    #  QWERTY
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_qwerty(self, parent):
        p = _P

        def tecla(frame, char, tipo="normal", ipadx=4, expand=True):
            estilos = {
                "normal":   (p["tecla_bg"],    p["tecla_fg"]),
                "especial": (p["especial_bg"], p["especial_fg"]),
                "accion":   (p["accion_bg"],   p["accion_fg"]),
                "danger":   (p["danger_bg"],   p["danger_fg"]),
                "shift":    (p["shift_bg"],    p["shift_fg"]),
                "caps":     (p["caps_bg"],     p["caps_fg"]),
            }
            bg, fg = estilos.get(tipo, estilos["normal"])
            disp = char.upper() if (self._shift or self._caps) else char
            btn = tk.Button(
                frame, text=disp,
                font=("Segoe UI", 12, "bold"),
                fg=fg, bg=bg,
                activebackground=p["tecla_hover"],
                activeforeground=fg,
                relief="flat", bd=0, cursor="hand2",
                highlightthickness=1,
                highlightbackground=p["separador"],
                command=lambda c=char: self._escribir(c))
            btn.pack(side="left", padx=2, ipady=7,
                     ipadx=ipadx, fill="x",
                     expand=expand)
            return btn

        # Fila 1
        f1 = tk.Frame(parent, bg=p["bg"])
        f1.pack(fill="x", pady=1)
        for c in _QWERTY_F1:
            b = tecla(f1, c)
            self._char_btns.append((b, c))

        # Fila 2
        f2 = tk.Frame(parent, bg=p["bg"])
        f2.pack(fill="x", pady=1)
        tk.Frame(f2, bg=p["bg"], width=24).pack(side="left")
        for c in _QWERTY_F2:
            b = tecla(f2, c)
            self._char_btns.append((b, c))
        tk.Frame(f2, bg=p["bg"], width=24).pack(side="left")

        # Fila 3: shift + letras + backspace
        f3 = tk.Frame(parent, bg=p["bg"])
        f3.pack(fill="x", pady=1)

        tipo_shift = "caps" if self._caps else ("shift" if self._shift else "accion")
        self._shift_btn = tk.Button(
            f3, text="⇧",
            font=("Segoe UI", 12, "bold"),
            fg=_P[f"{tipo_shift}_fg"] if tipo_shift in ("shift","caps") else p["accion_fg"],
            bg=_P[f"{tipo_shift}_bg"] if tipo_shift in ("shift","caps") else p["accion_bg"],
            activebackground=p["tecla_hover"],
            relief="flat", bd=0, cursor="hand2",
            highlightthickness=1,
            highlightbackground=p["separador"],
            command=self._toggle_shift)
        self._shift_btn.pack(side="left", padx=2, ipady=7, ipadx=10, fill="x")

        for c in _QWERTY_F3:
            b = tecla(f3, c)
            self._char_btns.append((b, c))

        bsp = tk.Button(
            f3, text="⌫",
            font=("Segoe UI", 12, "bold"),
            fg=p["danger_fg"], bg=p["danger_bg"],
            activebackground=p["tecla_hover"],
            relief="flat", bd=0, cursor="hand2",
            highlightthickness=1,
            highlightbackground=p["separador"],
            command=self._backspace)
        bsp.pack(side="left", padx=2, ipady=7, ipadx=10, fill="x")

        # Fila 4: 123 | espacio | enter | cerrar
        f4 = tk.Frame(parent, bg=p["bg"])
        f4.pack(fill="x", pady=1)

        tk.Button(f4, text="123",
                  font=("Segoe UI", 11, "bold"),
                  fg=p["accion_fg"], bg=p["accion_bg"],
                  activebackground=p["tecla_hover"],
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=p["separador"],
                  command=self._modo_num
                  ).pack(side="left", padx=2, ipady=7, ipadx=14)

        tk.Button(f4, text="ESPACIO",
                  font=("Segoe UI", 11, "bold"),
                  fg=p["accion_fg"], bg=p["accion_bg"],
                  activebackground=p["tecla_hover"],
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=p["separador"],
                  command=lambda: self._escribir(" ")
                  ).pack(side="left", padx=2, ipady=7, fill="x", expand=True)

        tk.Button(f4, text="↵ Enter",
                  font=("Segoe UI", 11, "bold"),
                  fg=p["especial_fg"], bg=p["especial_bg"],
                  activebackground=p["tecla_hover"],
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=p["separador"],
                  command=self._enter
                  ).pack(side="left", padx=2, ipady=7, ipadx=14)

        tk.Button(f4, text="✕",
                  font=("Segoe UI", 11, "bold"),
                  fg=p["danger_fg"], bg=p["danger_bg"],
                  activebackground=p["tecla_hover"],
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=p["separador"],
                  command=self._ocultar
                  ).pack(side="left", padx=2, ipady=7, ipadx=14)

    # ══════════════════════════════════════════════════════════════════════════
    #  NUMÉRICO — teclas grandes que llenan el espacio
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_num(self, parent):
        p = _P

        # Contenedor que ocupa todo el ancho
        grid = tk.Frame(parent, bg=p["bg"])
        grid.pack(fill="both", expand=True)

        # 4 columnas: 3 números + 1 columna de acciones
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)
        grid.columnconfigure(3, weight=1)
        for i in range(4):
            grid.rowconfigure(i, weight=1)

        def _num_btn(texto, row, col, comando=None, tipo="num",
                     rowspan=1, colspan=1):
            estilos = {
                "num":    (p["num_bg"],    p["num_fg"]),
                "accion": (p["accion_bg"], p["accion_fg"]),
                "danger": (p["danger_bg"], p["danger_fg"]),
                "cero":   (p["num_cero_bg"], p["num_fg"]),
            }
            bg, fg = estilos.get(tipo, estilos["num"])
            if comando is None:
                comando = lambda t=texto: self._escribir(t)
            btn = tk.Button(
                grid, text=texto,
                font=("Segoe UI", 18, "bold"),
                fg=fg, bg=bg,
                activebackground=p["tecla_hover"],
                activeforeground=fg,
                relief="flat", bd=0, cursor="hand2",
                highlightthickness=1,
                highlightbackground=p["separador"],
                command=comando)
            btn.grid(row=row, column=col,
                     rowspan=rowspan, columnspan=colspan,
                     padx=3, pady=3, sticky="nsew")
            return btn

        # Números 7-8-9 / 4-5-6 / 1-2-3
        _num_btn("7", 0, 0)
        _num_btn("8", 0, 1)
        _num_btn("9", 0, 2)
        _num_btn("4", 1, 0)
        _num_btn("5", 1, 1)
        _num_btn("6", 1, 2)
        _num_btn("1", 2, 0)
        _num_btn("2", 2, 1)
        _num_btn("3", 2, 2)
        _num_btn("0", 3, 0, colspan=2, tipo="cero")  # 0 ocupa 2 cols
        _num_btn(".", 3, 2)

        # Columna de acciones (col 3)
        _num_btn("⌫", 0, 3, comando=self._backspace, tipo="danger")
        _num_btn("ABC", 1, 3, comando=self._modo_qwerty, tipo="accion")
        _num_btn("↵", 2, 3, comando=self._enter, tipo="accion")
        _num_btn("✕", 3, 3, comando=self._ocultar, tipo="danger")

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
                btn.config(text=char.upper() if (self._shift or self._caps) else char)
            except tk.TclError:
                pass
        if self._shift_btn:
            try:
                if self._caps:
                    self._shift_btn.config(bg=_P["caps_bg"], fg=_P["caps_fg"])
                elif self._shift:
                    self._shift_btn.config(bg=_P["shift_bg"], fg=_P["shift_fg"])
                else:
                    self._shift_btn.config(bg=_P["accion_bg"], fg=_P["accion_fg"])
            except tk.TclError:
                pass

    def _modo_num(self):
        self._modo = "num"
        self._construir()

    def _modo_qwerty(self):
        self._modo = "qwerty"
        self._construir()