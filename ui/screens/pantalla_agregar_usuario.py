"""
ui/screens/pantalla_agregar_usuario.py
Pantalla de Agregar Usuario -- 800x480 táctil (Raspberry Pi 5)

CAMBIOS v15:
  - BUG 1 FIX: _campo_password ya no crea sub-Frame interno con pack().
    Ahora trabaja directo sobre el parent para evitar conflicto con grid().
    El campo "Confirmar contraseña" ahora es visible correctamente.
  - BUG 2 FIX: _PROGRAMAS incluye "Ninguno" como primera opción.
    Al guardar, "Ninguno" se convierte a None en la BD.
"""

import tkinter as tk
import threading
from pathlib import Path

from ui.components.barra_superior import crear_encabezado
from ui.components.modal_dialogo import modal_info, modal_error
from ui.styles import PALETA

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_RAIZ = Path(__file__).resolve().parents[2]

_F_LABEL   = ("Segoe UI", 7)
_F_ENTRY   = ("Segoe UI", 9)
_F_BTN     = ("Segoe UI", 9, "bold")
_F_INSTRUC = ("Segoe UI", 8)

_ROLES_CON_PASSWORD = {"Admin", "Super Admin"}
_ROLES_CON_DETALLE  = {"Alumno"}
# BUG 2 FIX: "Ninguno" agregado como primera opción
_PROGRAMAS          = ["Ninguno", "Software", "Mecatrónica"]
_GRADOS             = ["1°", "2°", "3°", "4°", "5°", "6°", "7°", "8°", "9°"]
_GRUPOS             = ["A", "B", "C", "D", "E"]

_C = {
    "bg":           "#f3f4f5",
    "panel_bg":     "#ffffff",
    "panel_fg":     "#1a1a1a",
    "panel_fg2":    "#757575",
    "texto":        "#1a1a1a",
    "texto2":       "#757575",
    "borde":        "#e0e0e0",
    "campo_bg":     "#f5f5f5",
    "campo_dis":    "#ebebeb",
    "texto_dis":    "#aaaaaa",
    "verde_m":      "#4caf50",
    "verde_btn":    "#43a047",
    "verde_hover":  "#388e3c",
    "rojo_btn":     "#e53935",
    "rojo_hover":   "#b71c1c",
    "aviso_fg":     "#e53935",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#43a047",
    "filtro_fg":    "#1a1a1a",
    "filtro_dis_bg":"#ebebeb",
    "filtro_dis_fg":"#aaaaaa",
    "flecha_img":   "arrow_circle_black.png",
}

_O = {
    "bg":           "#071E07",
    "panel_bg":     "#0d2a0d",
    "panel_fg":     "#d0f0d0",
    "panel_fg2":    "#7aaa7a",
    "texto":        "#d0f0d0",
    "texto2":       "#7aaa7a",
    "borde":        "#1a3a1a",
    "campo_bg":     "#1a3a1a",
    "campo_dis":    "#071E07",
    "texto_dis":    "#557755",
    "verde_m":      "#477023",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "rojo_btn":     "#7f1d1d",
    "rojo_hover":   "#991b1b",
    "aviso_fg":     "#f87171",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",
    "filtro_fg":    "#d0f0d0",
    "filtro_dis_bg":"#071E07",
    "filtro_dis_fg":"#557755",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    return _O if (hasattr(app, "tema") and app.tema.es_oscuro()) else _C


def _validar_password(pwd: str):
    if len(pwd) < 6:
        return "Mínimo 6 caracteres."
    if not any(c.isupper() for c in pwd):
        return "Debe incluir al menos una mayúscula."
    if not any(c.islower() for c in pwd):
        return "Debe incluir al menos una minúscula."
    if not any(c.isdigit() for c in pwd):
        return "Debe incluir al menos un número."
    return None


def _separar_nombres(nombre_completo: str) -> tuple:
    partes  = nombre_completo.strip().split(None, 1)
    primer  = partes[0] if partes else ""
    segundo = partes[1].strip() if len(partes) > 1 else None
    return primer, segundo


def _hacer_dropdown(parent, var, opciones, p, ico_flecha,
                    on_select=None, font=None, habilitado=True):
    font = font or _F_ENTRY

    def _abrir():
        if not habilitado:
            return
        menu = tk.Menu(parent, tearoff=0, font=font,
                       bg=p["bg"], fg=p["texto"],
                       activebackground=p["verde_m"],
                       activeforeground="#ffffff")
        for op in opciones:
            def _sel(o=op):
                var.set(o)
                btn.config(text=f"  {o}")
                if on_select:
                    on_select(o)
            menu.add_command(label=op, command=_sel)
        menu.tk_popup(btn.winfo_rootx(),
                      btn.winfo_rooty() + btn.winfo_height())

    bg = p["filtro_bg"]    if habilitado else p["filtro_dis_bg"]
    fg = p["filtro_fg"]    if habilitado else p["filtro_dis_fg"]
    bd = p["filtro_borde"] if habilitado else p["borde"]

    btn = tk.Button(
        parent, text=f"  {var.get()}",
        image=ico_flecha, compound="right",
        font=font, anchor="w",
        fg=fg, bg=bg,
        activebackground=p["borde"],
        relief="flat", bd=0, padx=6, pady=4,
        highlightthickness=1, highlightbackground=bd,
        cursor="hand2" if habilitado else "arrow",
        command=_abrir)
    return btn


# ── BUG 1 FIX ────────────────────────────────────────────────────────────────
# _campo_password ya NO crea un sub-Frame interno con pack().
# Trabaja directo sobre `parent` (que es self._sub_password, un Frame con pack).
# Antes retornaba (sub, ent, wrapper, ojo); ahora retorna (ent, wrapper, ojo).
# Esto elimina el conflicto entre pack() interno y grid() externo que hacía
# que el formulario quedara pequeño y el campo "confirmar" no se mostrara.
# ─────────────────────────────────────────────────────────────────────────────
def _campo_password(parent, p, label_txt, img_on, img_off):
    tk.Label(parent, text=label_txt, font=_F_LABEL,
             fg=p["texto2"], bg=p["bg"]).pack(anchor="w", fill="x")
    wrapper = tk.Frame(parent, bg=p["campo_bg"],
                       highlightthickness=1, highlightbackground=p["borde"])
    wrapper.pack(fill="x", pady=(1, 4))
    ent = tk.Entry(wrapper, font=_F_ENTRY,
                   fg=p["texto"], bg=p["campo_bg"],
                   relief="flat", bd=0,
                   insertbackground=p["texto"], show="•")
    ent.pack(side="left", fill="both", expand=True, ipady=4, padx=(6, 0))

    _vis = [False]
    def _toggle():
        _vis[0] = not _vis[0]
        ent.config(show="" if _vis[0] else "•")
        if img_on and img_off:
            ojo.config(image=img_off if _vis[0] else img_on)
        else:
            ojo.config(text="🙈" if _vis[0] else "👁")

    if img_on:
        ojo = tk.Label(wrapper, image=img_on, bg=p["campo_bg"], cursor="hand2")
    else:
        ojo = tk.Label(wrapper, text="👁", font=("Segoe UI", 10),
                       bg=p["campo_bg"], fg=p["texto2"], cursor="hand2")
    ojo.pack(side="right", padx=(2, 6))
    ojo.bind("<Button-1>", lambda e: _toggle())
    # Retorna (ent, wrapper, ojo) — sin sub-Frame
    return ent, wrapper, ojo


class PantallaAgregarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent  = parent
        self.app     = app
        self.datos   = datos or {}
        self._p      = _paleta(app)
        self._ico_flecha  = None
        self._img_ojo_on  = None
        self._img_ojo_off = None
        self._widgets_repintables = []
        self._btn_rol     = None
        self._btn_status  = None
        self._btn_carrera = None
        self._btn_grado   = None
        self._btn_grupo   = None
        self._sub_password    = None
        self._sub_detalle_alu = None
        self._pwd_wrappers = []
        self._entradas    = {}

        self._encoding = self.datos.get("face_encoding", None)

        self._cargar_iconos()
        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    def _cargar_iconos(self):
        if not _PIL_OK:
            return
        try:
            on  = Image.open(_RAIZ/"assets"/"img"/"visibility_icon.png"
                             ).resize((16,16), Image.LANCZOS)
            off = Image.open(_RAIZ/"assets"/"img"/"visibility_off_icon.png"
                             ).resize((16,16), Image.LANCZOS)
            self._img_ojo_on  = ImageTk.PhotoImage(on)
            self._img_ojo_off = ImageTk.PhotoImage(off)
        except Exception:
            pass

    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _limpiar_tema(self, event=None):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._on_tema_cambio)

    def _reg(self, widget, bg_k, fg_k=None):
        self._widgets_repintables.append((widget, bg_k, fg_k))

    def _recargar_ico_flecha(self):
        if not _PIL_OK:
            self._ico_flecha = None
            return
        try:
            ruta = _RAIZ/"assets"/"img"/self._p["flecha_img"]
            img  = Image.open(ruta).convert("RGBA").resize((14,14), Image.LANCZOS)
            self._ico_flecha = ImageTk.PhotoImage(img)
        except Exception:
            self._ico_flecha = None

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg"])
            self._cuerpo.configure(bg=p["bg"])
            self._panel.configure(bg=p["panel_bg"],
                                  highlightbackground=p["borde"])
            self._col_form_frame.configure(bg=p["bg"],
                                           highlightbackground=p["borde"])
            self._form.configure(bg=p["bg"])
            self._pie_form.configure(bg=p["bg"])
            self._lbl_aviso.configure(bg=p["bg"], fg=p["aviso_fg"])
            self._btn_confirmar.configure(bg=p["verde_btn"],
                                          activebackground=p["verde_hover"])
            self._btn_cancelar.configure(bg=p["rojo_btn"],
                                         activebackground=p["rojo_hover"])

            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists():
                        continue
                    widget.configure(bg=p[bg_k])
                    if fg_k:
                        widget.configure(fg=p[fg_k])
                except tk.TclError:
                    pass

            def _repintar_widget(w):
                try:
                    if not w.winfo_exists():
                        return
                    cls = w.winfo_class()
                    if cls == "Entry":
                        show = ""
                        try:
                            show = w.cget("show")
                        except Exception:
                            pass
                        if show in ("•", "●"):
                            w.configure(bg=p["campo_bg"], fg=p["texto"],
                                        highlightbackground=p["borde"],
                                        insertbackground=p["texto"])
                        elif w.cget("state") == "disabled":
                            w.configure(disabledbackground=p["campo_dis"],
                                        disabledforeground=p["texto2"],
                                        highlightbackground=p["borde"])
                        else:
                            w.configure(bg=p["campo_bg"], fg=p["texto"],
                                        highlightbackground=p["borde"],
                                        insertbackground=p["texto"])
                    elif cls == "Frame":
                        w.configure(bg=p["bg"])
                        for child in w.winfo_children():
                            _repintar_widget(child)
                    elif cls == "Label":
                        w.configure(bg=p["bg"], fg=p["texto2"])
                except tk.TclError:
                    pass

            _repintar_widget(self._form)
            _repintar_widget(self._pie_form)

            self._recargar_ico_flecha()
            todos_dd = [self._btn_rol, self._btn_status,
                        self._btn_carrera, self._btn_grado, self._btn_grupo]
            for btn in todos_dd:
                if btn is None:
                    continue
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  image=self._ico_flecha)
                except tk.TclError:
                    pass

            for child in self._panel.winfo_children():
                try:
                    cls = child.winfo_class()
                    if cls == "Frame":
                        child.configure(bg=p["panel_bg"])
                    elif cls == "Label":
                        child.configure(bg=p["panel_bg"], fg=p["panel_fg2"])
                    elif cls == "Canvas":
                        child.configure(bg=p["panel_bg"])
                        child.delete("all")
                        child.create_oval(4, 4, 76, 76,
                                          fill=p["campo_bg"],
                                          outline=p["borde"], width=2)
                        child.create_oval(26, 12, 54, 36,
                                          fill=p["texto2"], outline="")
                        child.create_arc(10, 38, 70, 80,
                                         start=0, extent=180,
                                         fill=p["texto2"], outline="",
                                         style="chord")
                except tk.TclError:
                    pass

            try:
                for child in self._col_form_frame.winfo_children():
                    if isinstance(child, tk.Frame) and child != self._form and child != self._pie_form:
                        child.configure(bg=p["bg"])
                        for sub in child.winfo_children():
                            try:
                                sub.configure(bg=p["bg"], fg=p["texto2"])
                            except tk.TclError:
                                pass
            except tk.TclError:
                pass

        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        self._cuerpo = tk.Frame(self.pantalla, bg=p["bg"])
        self._cuerpo.pack(fill="both", expand=True)
        self._cuerpo.columnconfigure(0, weight=42)
        self._cuerpo.columnconfigure(1, weight=58)
        self._cuerpo.rowconfigure(0, weight=1)

        self._construir_panel(self._cuerpo)
        self._construir_formulario(self._cuerpo)

    # ══════════════════════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_panel(self, parent):
        p = self._p
        self._panel = tk.Frame(parent, bg=p["panel_bg"],
                               highlightthickness=1,
                               highlightbackground=p["borde"])
        self._panel.grid(row=0, column=0, sticky="nsew")

        tk.Frame(self._panel, bg=p["verde_m"], height=4).pack(fill="x")

        canvas = tk.Canvas(self._panel, width=80, height=80,
                           bg=p["panel_bg"], highlightthickness=0)
        canvas.pack(pady=(24, 8))
        canvas.create_oval(4, 4, 76, 76, fill=p["campo_bg"],
                           outline=p["borde"], width=2)
        canvas.create_oval(26, 12, 54, 36, fill=p["texto2"], outline="")
        canvas.create_arc(10, 38, 70, 80, start=0, extent=180,
                          fill=p["texto2"], outline="", style="chord")

        tk.Label(self._panel, text="ESCANEO FACIAL",
                 font=("Segoe UI", 11, "bold"),
                 fg=p["panel_fg"], bg=p["panel_bg"]).pack(pady=(0, 4))

        tk.Label(self._panel,
                 text="Presiona el botón para\ncapturar tu rostro",
                 font=("Segoe UI", 9),
                 fg=p["panel_fg2"], bg=p["panel_bg"],
                 justify="center").pack(pady=(0, 16))

        if self._encoding is not None:
            self._mostrar_captura_ok()
            return

        tk.Button(
            self._panel, text="📷  CAPTURAR ROSTRO",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=16, pady=12, relief="flat", cursor="hand2",
            command=self._ir_a_captura).pack(padx=20, fill="x")

        tk.Label(self._panel,
                 text="La captura se realiza\nen pantalla completa",
                 font=("Segoe UI", 7),
                 fg=p["panel_fg2"], bg=p["panel_bg"],
                 justify="center").pack(pady=(8, 0))

    def _mostrar_captura_ok(self):
        p = self._p
        for w in self._panel.winfo_children():
            w.destroy()

        tk.Frame(self._panel, bg=p["verde_m"], height=4).pack(fill="x")

        c = tk.Canvas(self._panel, width=70, height=70,
                      bg=p["panel_bg"], highlightthickness=0)
        c.pack(pady=(24, 8))
        c.create_oval(4, 4, 66, 66, fill="#e8f5e9", outline="#43a047", width=3)
        c.create_text(35, 35, text="✓", font=("Segoe UI", 28, "bold"),
                      fill="#43a047")

        tk.Label(self._panel, text="ROSTRO CAPTURADO",
                 font=("Segoe UI", 11, "bold"),
                 fg="#2e7d32", bg=p["panel_bg"]).pack(pady=(0, 4))

        tk.Label(self._panel,
                 text="Encoding facial listo.\nPuedes confirmar el registro.",
                 font=("Segoe UI", 9),
                 fg=p["panel_fg2"], bg=p["panel_bg"],
                 justify="center").pack(pady=(0, 16))

        tk.Button(
            self._panel, text="↺  RECAPTURAR",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg="#757575",
            activebackground="#424242", activeforeground="#ffffff",
            bd=0, padx=12, pady=8, relief="flat", cursor="hand2",
            command=self._ir_a_captura).pack(padx=20, fill="x")

        if hasattr(self, "_btn_confirmar"):
            self._btn_confirmar.config(state="normal")

    # ══════════════════════════════════════════════════════════════════════════
    #  FORMULARIO DERECHO
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_formulario(self, parent):
        p = self._p
        self._col_form_frame = tk.Frame(
            parent, bg=p["bg"],
            highlightthickness=1, highlightbackground=p["borde"])
        self._col_form_frame.grid(row=0, column=1, sticky="nsew")

        tk.Frame(self._col_form_frame, bg=p["verde_m"], height=4).pack(fill="x")

        encab = tk.Frame(self._col_form_frame, bg=p["bg"])
        encab.pack(fill="x", pady=(4, 0), padx=12)
        tk.Label(encab, text="Ingrese los datos de la persona",
                 font=_F_INSTRUC, fg=p["texto2"], bg=p["bg"]).pack(anchor="w")

        # Pie siempre visible
        self._pie_form = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._pie_form.pack(side="bottom", fill="x", padx=12, pady=(4, 6))

        estado_btn = "normal" if self._encoding is not None else "disabled"
        self._btn_confirmar = tk.Button(
            self._pie_form, text="CONFIRMAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["verde_btn"], activebackground=p["verde_hover"],
            activeforeground="#ffffff",
            bd=0, padx=14, pady=7, relief="flat", cursor="hand2",
            command=self._guardar, state=estado_btn)
        self._btn_confirmar.pack(side="left", padx=(0, 6))

        self._btn_cancelar = tk.Button(
            self._pie_form, text="CANCELAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["rojo_btn"], activebackground=p["rojo_hover"],
            activeforeground="#ffffff",
            bd=0, padx=14, pady=7, relief="flat", cursor="hand2",
            command=self._cancelar)
        self._btn_cancelar.pack(side="left")

        self._lbl_aviso = tk.Label(
            self._pie_form, text="", font=("Segoe UI", 7),
            fg=p["aviso_fg"], bg=p["bg"],
            wraplength=150, justify="left")
        self._lbl_aviso.pack(side="left", padx=6)

        # Formulario
        self._form = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._form.pack(fill="both", expand=True, padx=12, pady=(2, 0))
        self._form.columnconfigure(0, weight=1)
        self._form.columnconfigure(1, weight=1)

        # Fila 0: Código y Nombre(s)
        self._campo(self._form, 0, 0, "Codigo Institucional", "cod_institucional")
        self._campo(self._form, 0, 1,
                    "Nombre(s)  [si tiene 2 nombres sepáralos con espacio]",
                    "nombre")

        # Fila 1: Apellidos
        self._campo(self._form, 1, 0, "Apellido Paterno",  "apellido_paterno")
        self._campo(self._form, 1, 1, "Apellido Materno",  "apellido_materno")

        self._recargar_ico_flecha()

        # ── Fila 2: Rol ───────────────────────────────────────────────────────
        rol_inicial = self.datos.get("rol", "Alumno")
        self._rol_var = tk.StringVar(value=rol_inicial)

        sub_r = tk.Frame(self._form, bg=p["bg"])
        sub_r.grid(row=2, column=0, padx=(0, 4), pady=2, sticky="ew")
        self._reg(sub_r, "bg")
        tk.Label(sub_r, text="Rol", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")

        def _abrir_rol():
            menu = tk.Menu(sub_r, tearoff=0, font=_F_ENTRY,
                           bg=p["bg"], fg=p["texto"],
                           activebackground=p["verde_m"],
                           activeforeground="#ffffff")
            for op in ["Alumno", "Maestro", "Admin", "Super Admin"]:
                menu.add_command(label=op,
                    command=lambda o=op: [
                        self._rol_var.set(o),
                        self._btn_rol.config(text=f"  {o}"),
                        self._on_rol_cambio(o),
                    ])
            menu.tk_popup(self._btn_rol.winfo_rootx(),
                          self._btn_rol.winfo_rooty() + self._btn_rol.winfo_height())

        self._btn_rol = tk.Button(
            sub_r, text=f"  {rol_inicial}",
            image=self._ico_flecha, compound="right",
            font=_F_ENTRY, anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=6, pady=4,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2", command=_abrir_rol)
        self._btn_rol.pack(fill="x", ipady=2, pady=(1, 0))

        # ── Fila 2 col 1: Status ──────────────────────────────────────────────
        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))
        sub_s = tk.Frame(self._form, bg=p["bg"])
        sub_s.grid(row=2, column=1, padx=(4, 0), pady=2, sticky="ew")
        self._reg(sub_s, "bg")
        tk.Label(sub_s, text="Status", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_status = _hacer_dropdown(
            sub_s, self._status_var, ["Activo", "Inactivo"], p, self._ico_flecha)
        self._btn_status.pack(fill="x", ipady=2, pady=(1, 0))

        # ── Fila 3: Detalle Alumno (Carrera + Grado + Grupo) — oculto por defecto
        self._carrera_var = tk.StringVar(value=self.datos.get("carrera", "Software"))
        self._grado_var   = tk.StringVar(value=self.datos.get("grado",   "1°"))
        self._grupo_var   = tk.StringVar(value=self.datos.get("grupo",   "A"))

        self._sub_detalle_alu = tk.Frame(self._form, bg=p["bg"])
        self._sub_detalle_alu.columnconfigure(0, weight=2)
        self._sub_detalle_alu.columnconfigure(1, weight=1)
        self._sub_detalle_alu.columnconfigure(2, weight=1)

        # Carrera — ahora incluye "Ninguno" como primera opción (BUG 2 FIX)
        sub_ca = tk.Frame(self._sub_detalle_alu, bg=p["bg"])
        sub_ca.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self._reg(sub_ca, "bg")
        self._lbl_carrera = tk.Label(sub_ca, text="Programa Académico",
                                     font=_F_LABEL, fg=p["texto2"], bg=p["bg"])
        self._lbl_carrera.pack(anchor="w")
        self._btn_carrera = _hacer_dropdown(
            sub_ca, self._carrera_var, _PROGRAMAS, p, self._ico_flecha)
        self._btn_carrera.pack(fill="x", ipady=2, pady=(1, 0))

        # Grado
        sub_gr = tk.Frame(self._sub_detalle_alu, bg=p["bg"])
        sub_gr.grid(row=0, column=1, padx=(4, 4), sticky="ew")
        self._reg(sub_gr, "bg")
        tk.Label(sub_gr, text="Grado", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_grado = _hacer_dropdown(
            sub_gr, self._grado_var, _GRADOS, p, self._ico_flecha)
        self._btn_grado.pack(fill="x", ipady=2, pady=(1, 0))

        # Grupo
        sub_gp = tk.Frame(self._sub_detalle_alu, bg=p["bg"])
        sub_gp.grid(row=0, column=2, padx=(4, 0), sticky="ew")
        self._reg(sub_gp, "bg")
        tk.Label(sub_gp, text="Grupo", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_grupo = _hacer_dropdown(
            sub_gp, self._grupo_var, _GRUPOS, p, self._ico_flecha)
        self._btn_grupo.pack(fill="x", ipady=2, pady=(1, 0))

        # ── Contraseña (Admin / Super Admin) ──────────────────────────────────
        # BUG 1 FIX: _campo_password ya no crea sub-Frame interno.
        # self._sub_password usa pack() y _campo_password trabaja sobre él directamente.
        self._sub_password = tk.Frame(self._form, bg=p["bg"])

        self._ent_password, w1, o1 = _campo_password(
            self._sub_password, p,
            "Contraseña  (mayúscula, minúscula y número)",
            self._img_ojo_on, self._img_ojo_off)
        self._pwd_wrappers.append((w1, o1))

        tk.Frame(self._sub_password, bg=p["bg"], height=3).pack()

        self._ent_password2, w2, o2 = _campo_password(
            self._sub_password, p, "Confirmar contraseña",
            self._img_ojo_on, self._img_ojo_off)
        self._pwd_wrappers.append((w2, o2))

        self._entradas["password"]  = self._ent_password
        self._entradas["password2"] = self._ent_password2

        # Aplicar estado visual inicial
        self._on_rol_cambio(rol_inicial, init=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  CAMBIO DE ROL
    # ══════════════════════════════════════════════════════════════════════════
    def _on_rol_cambio(self, rol, init=False):
        es_alumno    = rol in _ROLES_CON_DETALLE
        es_admin_pwd = rol in _ROLES_CON_PASSWORD

        if es_alumno:
            self._sub_detalle_alu.grid(
                row=3, column=0, columnspan=2,
                padx=0, pady=2, sticky="ew")
        else:
            self._sub_detalle_alu.grid_remove()

        if es_admin_pwd:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=2, sticky="ew")
        else:
            self._sub_password.grid_remove()
            if not init:
                self._ent_password.delete(0, tk.END)
                self._ent_password2.delete(0, tk.END)

    def _campo(self, parent, row, col_i, etiqueta, key):
        p    = self._p
        padx = (0, 4) if col_i == 0 else (4, 0)
        sub  = tk.Frame(parent, bg=p["bg"])
        sub.grid(row=row, column=col_i, padx=padx, pady=2, sticky="ew")
        self._reg(sub, "bg")
        tk.Label(sub, text=etiqueta, font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        ent = tk.Entry(sub, font=_F_ENTRY,
                       fg=p["texto"], bg=p["campo_bg"],
                       relief="flat", bd=0,
                       highlightthickness=1, highlightbackground=p["borde"],
                       insertbackground=p["texto"])
        ent.insert(0, self.datos.get(key, ""))
        ent.pack(fill="x", ipady=4, pady=(1, 0))
        if key == "cod_institucional":
            vcmd = (self.pantalla.winfo_toplevel().register(
                        lambda s: (s.isdigit() and len(s) <= 8) or s == ""), "%P")
            ent.configure(validate="key", validatecommand=vcmd)
        self._entradas[key] = ent

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _ir_a_captura(self):
        datos = {
            "cod_institucional": self._entradas["cod_institucional"].get().strip(),
            "nombre":            self._entradas["nombre"].get().strip(),
            "apellido_paterno":  self._entradas["apellido_paterno"].get().strip(),
            "apellido_materno":  self._entradas["apellido_materno"].get().strip(),
            "carrera":           self._carrera_var.get(),
            "grado":             self._grado_var.get(),
            "grupo":             self._grupo_var.get(),
            "rol":               self._rol_var.get(),
            "status":            self._status_var.get(),
        }
        if self._rol_var.get() in _ROLES_CON_PASSWORD:
            datos["_pwd1"] = self._ent_password.get()
            datos["_pwd2"] = self._ent_password2.get()
        self.app.mostrar_pantalla("captura_rostro", datos)

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        if self._encoding is None:
            self._lbl_aviso.config(text="Primero captura el rostro.")
            return

        cod        = self._entradas["cod_institucional"].get().strip()
        nombre_raw = self._entradas["nombre"].get().strip()
        apellidop  = self._entradas["apellido_paterno"].get().strip()
        rol        = self._rol_var.get()

        if not cod:
            self._lbl_aviso.config(text="El código es requerido.")
            return
        if not nombre_raw:
            self._lbl_aviso.config(text="El nombre es requerido.")
            return
        if not apellidop:
            self._lbl_aviso.config(text="El apellido paterno es requerido.")
            return

        primer_nombre, segundo_nombre = _separar_nombres(nombre_raw)

        # BUG 2 FIX + BUG 5 FIX: solo se guarda carrera/grado/grupo si es Alumno
        es_alumno = rol in _ROLES_CON_DETALLE
        carrera   = self._carrera_var.get() if es_alumno else None
        grado     = self._grado_var.get()   if es_alumno else None
        grupo     = self._grupo_var.get()   if es_alumno else None
        # "Ninguno" se guarda como None en la BD
        if carrera == "Ninguno":
            carrera = None

        password_plain = None
        if rol in _ROLES_CON_PASSWORD:
            pwd1 = self._ent_password.get()
            pwd2 = self._ent_password2.get()
            err  = _validar_password(pwd1)
            if err:
                self._lbl_aviso.config(text=err)
                return
            if pwd1 != pwd2:
                self._lbl_aviso.config(text="Las contraseñas no coinciden.")
                return
            password_plain = pwd1

        self._btn_confirmar.config(state="disabled", text="GUARDANDO...")
        encoding_snap = self._encoding
        password_snap = password_plain

        def _en_hilo():
            password_hash = None
            if password_snap:
                import hashlib
                password_hash = hashlib.sha256(
                    password_snap.encode("utf-8")).hexdigest()

            rol_map = {"Alumno": 4, "Maestro": 3, "Admin": 2, "Super Admin": 1}
            datos_bd = {
                "cod_institucional": cod,
                "id_rol":            rol_map.get(rol, 4),
                "primer_nombre":     primer_nombre,
                "segundo_nombre":    segundo_nombre,
                "apellido_paterno":  apellidop,
                "apellido_materno":  self._entradas["apellido_materno"].get().strip() or None,
                "carrera":           carrera,
                "grado":             grado,
                "grupo":             grupo,
                "face_encoding":     encoding_snap,
                "password_hash":     password_hash,
            }

            from core.database import registrar_usuario, inicializar_bd
            inicializar_bd()
            ok, msg = registrar_usuario(datos_bd)

            def _result():
                if ok:
                    modal_info(self.pantalla, msg, titulo="Registro exitoso",
                               on_ok=lambda: self.app.mostrar_pantalla("gestion_real"))
                else:
                    self._lbl_aviso.config(text=msg)
                    self._btn_confirmar.config(state="normal", text="CONFIRMAR")
            self.pantalla.after(0, _result)

        threading.Thread(target=_en_hilo, daemon=True).start()

    def _cancelar(self):
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_agregar_usuario(parent, app, datos=None):
    PantallaAgregarUsuario(parent, app, datos)