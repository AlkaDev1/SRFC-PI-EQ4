"""
ui/screens/pantalla_agregar_usuario.py
Pantalla de Agregar Usuario -- 800x480 táctil (Raspberry Pi 5)

CAMBIOS v10:
  - Fix cámara RPi 5 + Wayland: usa cv2.CAP_V4L2 backend explícito
  - Fallback automático entre índices 0, 1, 2
  - Solo números en código institucional (máx 8 dígitos)
  - Ojito en contraseña
  - Validaciones: mayúscula + minúscula + número + mín 6 chars
  - Umbral duplicado facial: 0.38
"""

import tkinter as tk
import threading
import os
import platform
from pathlib import Path

from ui.components.barra_superior import crear_encabezado
from ui.components.modal_dialogo import modal_info, modal_error
from ui.styles import PALETA

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RAIZ = Path(__file__).resolve().parents[2]

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

_F_LABEL   = ("Segoe UI", 7)
_F_ENTRY   = ("Segoe UI", 9)
_F_BTN     = ("Segoe UI", 9, "bold")
_F_INSTRUC = ("Segoe UI", 8)
_F_CAM_MSG = ("Segoe UI", 10, "bold")
_F_CAM_SUB = ("Segoe UI", 8, "bold")

CAPTURAS_REQUERIDAS  = 30
_ROLES_CON_PASSWORD  = {"Admin", "Super Admin"}
_PROGRAMAS           = ["Software", "Mecatrónica"]
_UMBRAL_DUPLICADO    = 0.38

_C = {
    "bg":           "#f3f4f5",
    "cam_bg":       "#1c1c1c",
    "texto":        "#1a1a1a",
    "texto2":       "#757575",
    "borde":        "#e0e0e0",
    "campo_bg":     "#f5f5f5",
    "campo_dis":    "#ebebeb",
    "verde":        "#2e7d32",
    "verde_m":      "#4caf50",
    "verde_btn":    "#43a047",
    "verde_hover":  "#388e3c",
    "rojo_btn":     "#e53935",
    "rojo_hover":   "#b71c1c",
    "cam_fg":       "#ffffff",
    "cam_sub_fg":   "#aaaaaa",
    "icono_circulo":"#e0e0e0",
    "icono_fill":   "#9e9e9e",
    "icono_borde":  "#bdbdbd",
    "aviso_fg":     "#e53935",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#43a047",
    "filtro_fg":    "#1a1a1a",
    "flecha_img":   "arrow_circle_black.png",
}

_O = {
    "bg":           "#071E07",
    "cam_bg":       "#0a1a0a",
    "texto":        "#d0f0d0",
    "texto2":       "#7aaa7a",
    "borde":        "#1a3a1a",
    "campo_bg":     "#1a3a1a",
    "campo_dis":    "#071E07",
    "verde":        "#2D531A",
    "verde_m":      "#477023",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "rojo_btn":     "#7f1d1d",
    "rojo_hover":   "#991b1b",
    "cam_fg":       "#d0f0d0",
    "cam_sub_fg":   "#7aaa7a",
    "icono_circulo":"#1a3a1a",
    "icono_fill":   "#2d5a2d",
    "icono_borde":  "#1a3a1a",
    "aviso_fg":     "#f87171",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",
    "filtro_fg":    "#d0f0d0",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


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


def _abrir_camara_rpi():
    """
    Abre la cámara en RPi 5 con Wayland usando V4L2 backend.
    Prueba índices 0, 1, 2 automáticamente.
    """
    import cv2
    backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
    indices  = [0, 1, 2]

    for backend in backends:
        for idx in indices:
            try:
                cam = cv2.VideoCapture(idx, backend)
                if cam.isOpened():
                    # Verificar que realmente da frames
                    ok, frame = cam.read()
                    if ok and frame is not None:
                        print(f"[CAM] Abierta: índice={idx} backend={backend}")
                        return cam
                    cam.release()
            except Exception:
                pass
    return None


def _hacer_dropdown(parent, var, opciones, p, ico_flecha, on_select=None, font=None):
    font = font or _F_ENTRY

    def _abrir():
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

    btn = tk.Button(
        parent,
        text=f"  {var.get()}",
        image=ico_flecha, compound="right",
        font=font, anchor="w",
        fg=p["filtro_fg"], bg=p["filtro_bg"],
        activebackground=p["borde"],
        relief="flat", bd=0, padx=6, pady=4,
        highlightthickness=1, highlightbackground=p["filtro_borde"],
        cursor="hand2",
        command=_abrir)
    return btn


def _campo_password(parent, p, label_txt, img_vis_on, img_vis_off):
    sub = tk.Frame(parent, bg=p["bg"])
    sub.pack(fill="x")

    tk.Label(sub, text=label_txt, font=_F_LABEL,
             fg=p["texto2"], bg=p["bg"]).pack(anchor="w")

    wrapper = tk.Frame(sub, bg=p["campo_bg"],
                       highlightthickness=1, highlightbackground=p["borde"])
    wrapper.pack(fill="x", pady=(1, 0))

    ent = tk.Entry(wrapper, font=_F_ENTRY,
                   fg=p["texto"], bg=p["campo_bg"],
                   relief="flat", bd=0,
                   insertbackground=p["texto"],
                   show="•")
    ent.pack(side="left", fill="both", expand=True, ipady=4, padx=(6, 0))

    _visible = [False]

    def _toggle():
        _visible[0] = not _visible[0]
        ent.config(show="" if _visible[0] else "•")
        if img_vis_on and img_vis_off:
            ojo_btn.config(image=img_vis_off if _visible[0] else img_vis_on)
        else:
            ojo_btn.config(text="🙈" if _visible[0] else "👁")

    if img_vis_on:
        ojo_btn = tk.Label(wrapper, image=img_vis_on,
                           bg=p["campo_bg"], cursor="hand2")
    else:
        ojo_btn = tk.Label(wrapper, text="👁", font=("Segoe UI", 10),
                           bg=p["campo_bg"], fg=p["texto2"], cursor="hand2")
    ojo_btn.pack(side="right", padx=(2, 6))
    ojo_btn.bind("<Button-1>", lambda e: _toggle())

    return sub, ent, wrapper, ojo_btn


class PantallaAgregarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent       = parent
        self.app          = app
        self.datos        = datos or {}
        self._p           = _paleta(app)
        self._capturas_ok = 0
        self._capturando  = False
        self._hilo_camara = None
        self._last_photo  = None
        self._ico_flecha  = None
        self._widgets_repintables = []
        self._btn_rol     = None
        self._btn_status  = None
        self._btn_carrera = None
        self._sub_password = None
        self._pwd_wrappers = []
        self._img_ojo_on  = None
        self._img_ojo_off = None

        self._encodings_acumulados = []
        self._encoding_final       = None

        self._cargar_iconos_ojo()
        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    def _cargar_iconos_ojo(self):
        try:
            on  = Image.open(_RAIZ / "assets" / "img" / "visibility_icon.png"
                             ).resize((16, 16), Image.LANCZOS)
            off = Image.open(_RAIZ / "assets" / "img" / "visibility_off_icon.png"
                             ).resize((16, 16), Image.LANCZOS)
            self._img_ojo_on  = ImageTk.PhotoImage(on)
            self._img_ojo_off = ImageTk.PhotoImage(off)
        except Exception:
            self._img_ojo_on  = None
            self._img_ojo_off = None

    # ══════════════════════════════════════════════════════════════════════════
    #  TEMA
    # ══════════════════════════════════════════════════════════════════════════
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
            ruta = _RAIZ / "assets" / "img" / self._p["flecha_img"]
            img  = Image.open(ruta).convert("RGBA").resize((14, 14), Image.LANCZOS)
            self._ico_flecha = ImageTk.PhotoImage(img)
        except Exception:
            self._ico_flecha = None

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg"])
            self._cuerpo.configure(bg=p["bg"])
            self._col_cam_frame.configure(bg=p["cam_bg"])
            self._feed_wrap.configure(bg=p["cam_bg"])
            self._lbl_feed.configure(bg=p["cam_bg"])
            self._icono_cam.configure(bg=p["cam_bg"])
            self._pie_cam.configure(bg=p["cam_bg"])
            self._lbl_cam_msg.configure(bg=p["cam_bg"], fg=p["cam_fg"])
            self._lbl_cam_sub.configure(bg=p["cam_bg"], fg=p["cam_sub_fg"])

            if not self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
                self._btn_captura.configure(bg=p["verde_btn"],
                                            activebackground=p["verde_hover"])
            elif self._capturando:
                self._btn_captura.configure(bg=p["rojo_btn"],
                                            activebackground=p["rojo_hover"])
            else:
                self._btn_captura.configure(bg=p["verde"])

            self._col_form_frame.configure(bg=p["bg"],
                                           highlightbackground=p["borde"])
            self._barra_verde.configure(bg=p["verde_m"])
            self._encab.configure(bg=p["bg"])
            self._lbl_instruc.configure(bg=p["bg"], fg=p["texto2"])
            self._canvas_icono.configure(bg=p["bg"])
            self._redibujar_icono_usuario()
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

            for key, ent in self._entradas.items():
                try:
                    if ent.cget("state") == "disabled":
                        ent.configure(disabledbackground=p["campo_dis"],
                                      disabledforeground=p["texto2"],
                                      highlightbackground=p["borde"])
                    else:
                        ent.configure(bg=p["campo_bg"], fg=p["texto"],
                                      highlightbackground=p["borde"],
                                      insertbackground=p["texto"])
                except tk.TclError:
                    pass

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_status, self._btn_carrera):
                if btn is None:
                    continue
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
                except tk.TclError:
                    pass

            for wrapper, ojo_btn in self._pwd_wrappers:
                try:
                    wrapper.configure(bg=p["campo_bg"],
                                      highlightbackground=p["borde"])
                    ojo_btn.configure(bg=p["campo_bg"])
                except tk.TclError:
                    pass

            if self._sub_password and self._sub_password.winfo_exists():
                self._sub_password.configure(bg=p["bg"])
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
        self._cuerpo.columnconfigure(0, weight=46)
        self._cuerpo.columnconfigure(1, weight=54)
        self._cuerpo.rowconfigure(0, weight=1)

        self._construir_col_camara(self._cuerpo)
        self._construir_col_formulario(self._cuerpo)

    # ══════════════════════════════════════════════════════════════════════════
    #  COLUMNA IZQUIERDA — cámara
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_col_camara(self, parent):
        p = self._p
        self._col_cam_frame = tk.Frame(parent, bg=p["cam_bg"])
        self._col_cam_frame.grid(row=0, column=0, sticky="nsew")

        self._feed_wrap = tk.Frame(self._col_cam_frame, bg=p["cam_bg"])
        self._feed_wrap.pack(fill="both", expand=True)
        self._feed_wrap.pack_propagate(False)

        self._lbl_feed = tk.Label(self._feed_wrap, bg=p["cam_bg"], relief="flat")
        self._lbl_feed.place(x=0, y=0, relwidth=1, relheight=1)

        self._icono_cam = tk.Label(
            self._feed_wrap, text="", font=("Segoe UI", 30),
            fg="#444466", bg=p["cam_bg"])
        self._icono_cam.place(relx=0.5, rely=0.42, anchor="center")

        self._pie_cam = tk.Frame(self._col_cam_frame, bg=p["cam_bg"])
        self._pie_cam.pack(fill="x", padx=10, pady=(4, 6))

        self._lbl_cam_msg = tk.Label(
            self._pie_cam, text="INGRESE EL CÓDIGO PRIMERO",
            font=_F_CAM_MSG, fg=p["cam_fg"], bg=p["cam_bg"], justify="center")
        self._lbl_cam_msg.pack()

        self._lbl_cam_sub = tk.Label(
            self._pie_cam, text="luego presione Capturar Rostro",
            font=_F_CAM_SUB, fg=p["cam_sub_fg"], bg=p["cam_bg"], justify="center")
        self._lbl_cam_sub.pack(pady=(0, 4))

        self._btn_captura = tk.Button(
            self._pie_cam, text="CAPTURAR ROSTRO",
            font=_F_BTN, fg="#ffffff",
            bg=p["verde_btn"], activebackground=p["verde_hover"],
            activeforeground="#ffffff",
            bd=0, padx=14, pady=7, relief="flat", cursor="hand2",
            command=self._toggle_captura, state="disabled")
        self._btn_captura.pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  COLUMNA DERECHA — formulario
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_col_formulario(self, parent):
        p = self._p
        self._col_form_frame = tk.Frame(
            parent, bg=p["bg"],
            highlightthickness=1, highlightbackground=p["borde"])
        self._col_form_frame.grid(row=0, column=1, sticky="nsew")

        self._barra_verde = tk.Frame(self._col_form_frame, bg=p["verde_m"], height=4)
        self._barra_verde.pack(fill="x")

        self._encab = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._encab.pack(fill="x", pady=(4, 0), padx=12)

        fila_encab = tk.Frame(self._encab, bg=p["bg"])
        fila_encab.pack(fill="x")

        self._canvas_icono = tk.Canvas(
            fila_encab, width=36, height=36,
            bg=p["bg"], highlightthickness=0)
        self._canvas_icono.pack(side="left", padx=(0, 8))
        self._redibujar_icono_usuario()

        self._lbl_instruc = tk.Label(
            fila_encab,
            text="Ingrese el rostro y los datos de la persona",
            font=_F_INSTRUC, fg=p["texto2"], bg=p["bg"],
            justify="left", wraplength=280, anchor="w")
        self._lbl_instruc.pack(side="left", fill="x", expand=True)

        # Pie siempre visible
        self._pie_form = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._pie_form.pack(side="bottom", fill="x", padx=12, pady=(4, 6))

        self._btn_confirmar = tk.Button(
            self._pie_form, text="CONFIRMAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["verde_btn"], activebackground=p["verde_hover"],
            activeforeground="#ffffff",
            bd=0, padx=14, pady=7, relief="flat", cursor="hand2",
            command=self._guardar, state="disabled")
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

        self._entradas = {}

        self._campo(self._form, 0, 0, "Codigo Institucional", "cod_institucional")
        self._campo(self._form, 0, 1, "Nombre(s)",            "nombre")
        self._campo(self._form, 1, 0, "Apellido Paterno",     "apellido_paterno")
        self._campo(self._form, 1, 1, "Apellido Materno",     "apellido_materno")

        self._entradas["cod_institucional"].bind("<KeyRelease>", self._validar_cod)

        self._recargar_ico_flecha()

        # Programa Académico
        self._carrera_var = tk.StringVar(value="Software")
        sub_carrera = tk.Frame(self._form, bg=p["bg"])
        sub_carrera.grid(row=2, column=0, padx=(0, 4), pady=2, sticky="ew")
        self._reg(sub_carrera, "bg")
        tk.Label(sub_carrera, text="Programa Académico", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_carrera = _hacer_dropdown(
            sub_carrera, self._carrera_var, _PROGRAMAS, p, self._ico_flecha)
        self._btn_carrera.pack(fill="x", ipady=2, pady=(1, 0))

        # Rol
        self._rol_var = tk.StringVar(value="Alumno")
        sub_rol = tk.Frame(self._form, bg=p["bg"])
        sub_rol.grid(row=2, column=1, padx=(4, 0), pady=2, sticky="ew")
        self._reg(sub_rol, "bg")
        tk.Label(sub_rol, text="Rol", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")

        def _abrir_rol():
            cp = self._p
            menu = tk.Menu(sub_rol, tearoff=0, font=_F_ENTRY,
                           bg=cp["bg"], fg=cp["texto"],
                           activebackground=cp["verde_m"],
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
            sub_rol, text="  Alumno",
            image=self._ico_flecha, compound="right",
            font=_F_ENTRY, anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=6, pady=4,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2", command=_abrir_rol)
        self._btn_rol.pack(fill="x", ipady=2, pady=(1, 0))

        # Status
        self._status_var = tk.StringVar(value="Activo")
        sub_st = tk.Frame(self._form, bg=p["bg"])
        sub_st.grid(row=3, column=0, columnspan=2, pady=2, sticky="ew")
        self._reg(sub_st, "bg")
        tk.Label(sub_st, text="Status", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_status = _hacer_dropdown(
            sub_st, self._status_var, ["Activo", "Inactivo"], p, self._ico_flecha)
        self._btn_status.pack(fill="x", ipady=2, pady=(1, 0))

        # Contraseña dinámica
        self._sub_password = tk.Frame(self._form, bg=p["bg"])

        _, self._ent_password, w1, o1 = _campo_password(
            self._sub_password, p,
            "Contraseña  (mayúscula, minúscula y número)",
            self._img_ojo_on, self._img_ojo_off)
        self._pwd_wrappers.append((w1, o1))

        tk.Frame(self._sub_password, bg=p["bg"], height=3).pack()

        _, self._ent_password2, w2, o2 = _campo_password(
            self._sub_password, p,
            "Confirmar contraseña",
            self._img_ojo_on, self._img_ojo_off)
        self._pwd_wrappers.append((w2, o2))

        self._entradas["password"]  = self._ent_password
        self._entradas["password2"] = self._ent_password2

    def _on_rol_cambio(self, rol: str):
        if rol in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=2, sticky="ew")
        else:
            self._sub_password.grid_remove()
            self._ent_password.delete(0, tk.END)
            self._ent_password2.delete(0, tk.END)

    def _redibujar_icono_usuario(self):
        p = self._p
        c = self._canvas_icono
        c.delete("all")
        c.create_oval(2, 2, 34, 34, fill=p["icono_circulo"],
                      outline=p["icono_borde"], width=1)
        c.create_oval(11, 5, 25, 17, fill=p["icono_fill"], outline="")
        c.create_arc(5, 17, 31, 42, start=0, extent=180,
                     fill=p["icono_fill"], outline="", style="chord")

    def _campo(self, parent, row, col_i, etiqueta, key):
        p    = self._p
        padx = (0, 4) if col_i == 0 else (4, 0)
        sub  = tk.Frame(parent, bg=p["bg"])
        sub.grid(row=row, column=col_i, padx=padx, pady=2, sticky="ew")
        self._reg(sub, "bg")

        lbl = tk.Label(sub, text=etiqueta, font=_F_LABEL,
                       fg=p["texto2"], bg=p["bg"])
        lbl.pack(anchor="w")
        self._reg(lbl, "bg", "texto2")

        ent = tk.Entry(sub, font=_F_ENTRY,
                       fg=p["texto"], bg=p["campo_bg"],
                       relief="flat", bd=0,
                       highlightthickness=1, highlightbackground=p["borde"],
                       insertbackground=p["texto"])
        ent.insert(0, self.datos.get(key, ""))
        ent.pack(fill="x", ipady=4, pady=(1, 0))

        # Solo números + máx 8 dígitos para código institucional
        if key == "cod_institucional":
            vcmd = (self.pantalla.winfo_toplevel().register(
                        lambda s: (s.isdigit() and len(s) <= 8) or s == ""), "%P")
            ent.configure(validate="key", validatecommand=vcmd)

        self._entradas[key] = ent

    def _validar_cod(self, event=None):
        cod = self._entradas["cod_institucional"].get().strip()
        if cod and not self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            self._btn_captura.config(state="normal")
            self._lbl_cam_msg.config(text="PRESIONE CAPTURAR ROSTRO")
            self._lbl_cam_sub.config(text="para iniciar el escaneo biometrico")
        elif not cod:
            self._btn_captura.config(state="disabled")
            self._lbl_cam_msg.config(text="INGRESE EL CÓDIGO PRIMERO")
            self._lbl_cam_sub.config(text="luego presione Capturar Rostro")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAPTURA
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_captura(self):
        if self._capturando:
            self._detener_captura()
        else:
            self._iniciar_captura()

    def _iniciar_captura(self):
        p = self._p
        self._encodings_acumulados = []
        self._capturas_ok = 0
        self._encoding_final = None
        self._capturando = True
        self._btn_captura.config(text="DETENER CAPTURA",
                                  bg=p["rojo_btn"], activebackground=p["rojo_hover"])
        self._lbl_cam_msg.config(text="INICIANDO CÁMARA...")
        self._lbl_cam_sub.config(text="por favor espere", fg=p["cam_sub_fg"])
        threading.Thread(target=self._hilo_captura, daemon=True).start()

    def _detener_captura(self):
        p = self._p
        self._capturando = False
        self._btn_captura.config(text="CAPTURAR ROSTRO",
                                  bg=p["verde_btn"], activebackground=p["verde_hover"])
        self._lbl_cam_msg.config(text="CAPTURA PAUSADA")
        self._lbl_cam_sub.config(
            text=f"{self._capturas_ok} / {CAPTURAS_REQUERIDAS} capturas",
            fg=p["cam_sub_fg"])

    def _hilo_captura(self):
        try:
            import cv2
            import face_recognition
        except ImportError as e:
            self.pantalla.after(0, lambda: modal_error(
                self.pantalla, str(e), titulo="Dependencia faltante"))
            self._capturando = False
            return

        # ── FIX cámara RPi 5 + Wayland ────────────────────────────────────────
        if _ES_RASPBERRY:
            cam = _abrir_camara_rpi()
        else:
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                cam = cv2.VideoCapture(1)

        if cam is None or not cam.isOpened():
            self.pantalla.after(0, lambda: modal_error(
                self.pantalla,
                "No se pudo abrir la cámara.\n"
                "Verifica que la webcam USB esté conectada\n"
                "y que tengas permisos: sudo usermod -aG video $USER",
                titulo="Error de cámara"))
            self._capturando = False
            return

        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Confirmar que la cámara está lista
        self.pantalla.after(0, lambda: self._lbl_cam_msg.config(
            text="POR FAVOR NO SE MUEVA"))
        self.pantalla.after(0, lambda: self._lbl_cam_sub.config(
            text="ESCANEANDO ROSTRO..."))

        try:
            from PIL import Image as PILImage, ImageTk as ITk
            pil_ok = True
        except ImportError:
            pil_ok = False

        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        rostro_objetivo = None

        def iou(a, b):
            ax1,ay1,ax2,ay2 = a[0],a[1],a[0]+a[2],a[1]+a[3]
            bx1,by1,bx2,by2 = b[0],b[1],b[0]+b[2],b[1]+b[3]
            ix1,iy1 = max(ax1,bx1), max(ay1,by1)
            ix2,iy2 = min(ax2,bx2), min(ay2,by2)
            inter   = max(0,ix2-ix1)*max(0,iy2-iy1)
            union   = a[2]*a[3]+b[2]*b[3]-inter
            return inter/union if union > 0 else 0.0

        while self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            ok, frame = cam.read()
            if not ok or frame is None:
                continue

            frame = cv2.flip(frame, 1)
            gris  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

            if len(rostros) > 0:
                bbox = tuple(rostros[0])
                if rostro_objetivo is None:
                    rostro_objetivo = bbox
                if iou(rostro_objetivo, bbox) >= 0.40:
                    rostro_objetivo = bbox
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 200, 0), 2)
                    margen = 10
                    x1 = max(0, x - margen)
                    y1 = max(0, y - margen)
                    x2 = min(frame.shape[1], x + w + margen)
                    y2 = min(frame.shape[0], y + h + margen)
                    roi_bgr = frame[y1:y2, x1:x2]
                    h_roi, w_roi = roi_bgr.shape[:2]
                    if w_roi > 160:
                        escala = 160 / w_roi
                        roi_small = cv2.resize(roi_bgr, (160, int(h_roi * escala)),
                                               interpolation=cv2.INTER_LINEAR)
                    else:
                        roi_small = roi_bgr
                    roi_rgb = cv2.cvtColor(roi_small, cv2.COLOR_BGR2RGB)
                    encs = face_recognition.face_encodings(
                        roi_rgb, num_jitters=1, model="small")
                    if encs:
                        self._encodings_acumulados.append(encs[0])
                        self._capturas_ok += 1
                else:
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 2)

            n = self._capturas_ok
            if pil_ok:
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f = img_rgb.shape[:2]
                nw = 340
                nh = int(h_f * nw / w_f)
                img_pil = PILImage.fromarray(img_rgb).resize(
                    (nw, nh), PILImage.LANCZOS)
                photo = ITk.PhotoImage(img_pil)
                self.pantalla.after(0, self._actualizar_feed, n, photo)
            else:
                self.pantalla.after(0, self._actualizar_feed, n, None)
            cv2.waitKey(30)

        cam.release()
        cv2.destroyAllWindows()
        self.pantalla.after(0, self._captura_finalizada, self._capturas_ok)

    def _actualizar_feed(self, n, photo=None):
        if photo:
            self._last_photo = photo
            self._lbl_feed.config(image=photo)
            self._icono_cam.place_forget()
        prop = min(n / CAPTURAS_REQUERIDAS, 1.0)
        self._lbl_cam_sub.config(
            text=f"ESCANEANDO... {n}/{CAPTURAS_REQUERIDAS}  ({int(prop*100)} %)")

    def _captura_finalizada(self, n):
        p = self._p
        self._capturando = False
        if n >= CAPTURAS_REQUERIDAS:
            self._btn_captura.config(text="CAPTURA COMPLETA",
                                      bg=p["verde"], activebackground=p["verde"],
                                      state="disabled")
            self._lbl_cam_msg.config(text="ESCANEO COMPLETADO")
            self._lbl_cam_sub.config(
                text=f"{n} capturas registradas correctamente", fg="#81c784")
            self._btn_confirmar.config(state="normal")
            self._lbl_aviso.config(text="")
        else:
            self._capturas_ok = 0
            self._encodings_acumulados = []
            self._encoding_final = None
            self._btn_captura.config(text="REINTENTAR CAPTURA",
                                      bg=p["verde_btn"], activebackground=p["verde_hover"],
                                      state="normal")
            self._lbl_cam_msg.config(text="CAPTURA INCOMPLETA")
            self._lbl_cam_sub.config(
                text=f"Solo {n}/{CAPTURAS_REQUERIDAS}. Presione Reintentar.",
                fg="#ef9a9a")

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        cod       = self._entradas["cod_institucional"].get().strip()
        nombre    = self._entradas["nombre"].get().strip()
        apellidop = self._entradas["apellido_paterno"].get().strip()
        rol       = self._rol_var.get()
        carrera   = self._carrera_var.get()

        if not cod:
            self._lbl_aviso.config(text="El código institucional es requerido.")
            return
        if not nombre:
            self._lbl_aviso.config(text="El nombre es requerido.")
            return
        if not apellidop:
            self._lbl_aviso.config(text="El apellido paterno es requerido.")
            return

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
                self._pwd_wrappers[1][0].configure(
                    highlightbackground="#e53935", highlightthickness=2)
                return
            self._pwd_wrappers[1][0].configure(
                highlightbackground=self._p["borde"], highlightthickness=1)
            password_plain = pwd1

        if len(self._encodings_acumulados) < CAPTURAS_REQUERIDAS:
            self._lbl_aviso.config(
                text=f"Se requieren {CAPTURAS_REQUERIDAS} capturas faciales.")
            return

        self._btn_confirmar.config(state="disabled", text="GUARDANDO...")
        self._lbl_aviso.config(text="Calculando encoding final...")

        encodings_snap = list(self._encodings_acumulados)
        password_snap  = password_plain

        def _en_hilo():
            import face_recognition
            import numpy as np

            encoding_promedio = np.mean(encodings_snap, axis=0)
            self.pantalla.after(0, lambda: self._lbl_aviso.config(
                text="Verificando duplicados..."))

            from core.database import cargar_todos_encodings
            registrados = cargar_todos_encodings()
            if registrados:
                enc_existentes = [r["encoding"] for r in registrados]
                distancias = face_recognition.face_distance(
                    enc_existentes, encoding_promedio)
                idx_min = int(np.argmin(distancias))
                if distancias[idx_min] < _UMBRAL_DUPLICADO:
                    nombre_dup = registrados[idx_min].get("nombre", "—")
                    cod_dup    = registrados[idx_min].get("cod",    "—")

                    def _rostro_duplicado():
                        self._lbl_aviso.config(
                            text=f"Rostro ya registrado: {nombre_dup} ({cod_dup})")
                        self._btn_confirmar.config(state="normal", text="CONFIRMAR")
                        self._capturas_ok = 0
                        self._encodings_acumulados = []
                        self._encoding_final = None
                        self._btn_captura.config(
                            text="REINTENTAR CAPTURA",
                            bg=self._p["verde_btn"],
                            activebackground=self._p["verde_hover"],
                            state="normal")
                        self._lbl_cam_msg.config(text="ROSTRO YA REGISTRADO")
                        self._lbl_cam_sub.config(
                            text="Este rostro ya existe en el sistema",
                            fg="#ef9a9a")
                    self.pantalla.after(0, _rostro_duplicado)
                    return

            password_hash = None
            if password_snap:
                import hashlib
                password_hash = hashlib.sha256(
                    password_snap.encode("utf-8")).hexdigest()

            rol_map = {"Alumno": 4, "Maestro": 3, "Admin": 2, "Super Admin": 1}
            datos_bd = {
                "cod_institucional": cod,
                "id_rol":            rol_map.get(rol, 4),
                "primer_nombre":     nombre,
                "segundo_nombre":    None,
                "apellido_paterno":  apellidop,
                "apellido_materno":  self._entradas["apellido_materno"].get().strip() or None,
                "carrera":           carrera,
                "grado":             None,
                "grupo":             None,
                "face_encoding":     encoding_promedio,
                "password_hash":     password_hash,
            }

            from core.database import registrar_usuario, inicializar_bd
            inicializar_bd()
            ok, msg = registrar_usuario(datos_bd)

            def _resultado():
                if ok:
                    modal_info(self.pantalla, msg, titulo="Registro exitoso",
                               on_ok=lambda: self.app.mostrar_pantalla("gestion_real"))
                else:
                    self._lbl_aviso.config(text=msg)
                    self._btn_confirmar.config(state="normal", text="CONFIRMAR")
            self.pantalla.after(0, _resultado)

        threading.Thread(target=_en_hilo, daemon=True).start()

    def _cancelar(self):
        self._capturando = False
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_agregar_usuario(parent, app, datos=None):
    PantallaAgregarUsuario(parent, app, datos)