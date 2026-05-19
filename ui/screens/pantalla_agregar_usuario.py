"""
ui/screens/pantalla_agregar_usuario.py
Pantalla de Agregar Usuario -- 800x480 táctil (Raspberry Pi 5)

CAMBIOS v11:
  - Columna izquierda reemplazada por panel de estado de captura
  - Botón CAPTURAR ROSTRO redirige a pantalla_captura_rostro
  - Al regresar de captura con encoding, muestra estado completado
  - Formulario completo en columna derecha
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
_PROGRAMAS          = ["Software", "Mecatrónica"]

_C = {
    "bg":           "#f3f4f5",
    "panel_bg":     "#1c1c2e",
    "panel_fg":     "#ffffff",
    "panel_fg2":    "#8888aa",
    "panel_ok":     "#43a047",
    "panel_ok_fg":  "#a5d6a7",
    "texto":        "#1a1a1a",
    "texto2":       "#757575",
    "borde":        "#e0e0e0",
    "campo_bg":     "#f5f5f5",
    "campo_dis":    "#ebebeb",
    "verde_m":      "#4caf50",
    "verde_btn":    "#43a047",
    "verde_hover":  "#388e3c",
    "rojo_btn":     "#e53935",
    "rojo_hover":   "#b71c1c",
    "aviso_fg":     "#e53935",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#43a047",
    "filtro_fg":    "#1a1a1a",
    "flecha_img":   "arrow_circle_black.png",
}

_O = {
    "bg":           "#071E07",
    "panel_bg":     "#0a0a1a",
    "panel_fg":     "#d0f0d0",
    "panel_fg2":    "#557755",
    "panel_ok":     "#2D531A",
    "panel_ok_fg":  "#6fcf6f",
    "texto":        "#d0f0d0",
    "texto2":       "#7aaa7a",
    "borde":        "#1a3a1a",
    "campo_bg":     "#1a3a1a",
    "campo_dis":    "#071E07",
    "verde_m":      "#477023",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "rojo_btn":     "#7f1d1d",
    "rojo_hover":   "#991b1b",
    "aviso_fg":     "#f87171",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",
    "filtro_fg":    "#d0f0d0",
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
        parent, text=f"  {var.get()}",
        image=ico_flecha, compound="right",
        font=font, anchor="w",
        fg=p["filtro_fg"], bg=p["filtro_bg"],
        activebackground=p["borde"],
        relief="flat", bd=0, padx=6, pady=4,
        highlightthickness=1, highlightbackground=p["filtro_borde"],
        cursor="hand2", command=_abrir)
    return btn


def _campo_password(parent, p, label_txt, img_on, img_off):
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
    return sub, ent, wrapper, ojo


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
        self._sub_password = None
        self._pwd_wrappers = []
        self._entradas    = {}

        # Encoding recibido de pantalla_captura_rostro
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
            self._panel.configure(bg=p["panel_bg"])
            self._col_form_frame.configure(bg=p["bg"])
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
                                      disabledforeground=p["texto2"])
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
                                  image=self._ico_flecha)
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

        self._construir_panel_captura(self._cuerpo)
        self._construir_formulario(self._cuerpo)

    # ══════════════════════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO — estado de captura
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_panel_captura(self, parent):
        p = self._p
        self._panel = tk.Frame(parent, bg=p["panel_bg"])
        self._panel.grid(row=0, column=0, sticky="nsew")

        # Ícono grande
        canvas = tk.Canvas(self._panel, width=90, height=90,
                           bg=p["panel_bg"], highlightthickness=0)
        canvas.pack(pady=(30, 8))
        # Círculo con silueta
        canvas.create_oval(5, 5, 85, 85, fill="#2a2a4a", outline="#3a3a6a", width=2)
        canvas.create_oval(30, 15, 60, 42, fill="#5a5a8a", outline="")
        canvas.create_arc(10, 45, 80, 90, start=0, extent=180,
                          fill="#5a5a8a", outline="", style="chord")

        tk.Label(self._panel,
                 text="ESCANEO FACIAL",
                 font=("Segoe UI", 11, "bold"),
                 fg=p["panel_fg"], bg=p["panel_bg"]).pack(pady=(0, 6))

        self._lbl_panel_estado = tk.Label(
            self._panel,
            text="Presiona el botón para\ncapturar tu rostro",
            font=("Segoe UI", 9),
            fg=p["panel_fg2"], bg=p["panel_bg"],
            justify="center")
        self._lbl_panel_estado.pack(pady=(0, 20))

        # Si ya hay encoding (regresó de captura), mostrar estado OK
        if self._encoding is not None:
            self._mostrar_captura_ok()
            return

        # Botón capturar
        self._btn_captura = tk.Button(
            self._panel,
            text="📷  CAPTURAR ROSTRO",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=16, pady=12, relief="flat", cursor="hand2",
            command=self._ir_a_captura)
        self._btn_captura.pack(padx=20, fill="x")

        tk.Label(self._panel,
                 text="La captura se realiza\nen pantalla completa",
                 font=("Segoe UI", 7),
                 fg=p["panel_fg2"], bg=p["panel_bg"],
                 justify="center").pack(pady=(10, 0))

    def _mostrar_captura_ok(self):
        """Muestra estado de captura completada en el panel."""
        p = self._p
        # Limpiar panel
        for w in self._panel.winfo_children():
            w.destroy()

        # Ícono check grande
        c = tk.Canvas(self._panel, width=80, height=80,
                      bg=p["panel_bg"], highlightthickness=0)
        c.pack(pady=(30, 8))
        c.create_oval(5, 5, 75, 75, fill="#1a3a1a", outline="#43a047", width=3)
        c.create_text(40, 40, text="✓", font=("Segoe UI", 32, "bold"),
                      fill="#43a047")

        tk.Label(self._panel,
                 text="ROSTRO CAPTURADO",
                 font=("Segoe UI", 11, "bold"),
                 fg="#81c784", bg=p["panel_bg"]).pack(pady=(0, 6))

        tk.Label(self._panel,
                 text="Encoding facial listo.\nPuedes confirmar el registro.",
                 font=("Segoe UI", 9),
                 fg=p["panel_fg2"], bg=p["panel_bg"],
                 justify="center").pack(pady=(0, 20))

        # Botón recapturar por si acaso
        tk.Button(
            self._panel,
            text="↺  RECAPTURAR",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg="#424242",
            activebackground="#212121", activeforeground="#ffffff",
            bd=0, padx=12, pady=8, relief="flat", cursor="hand2",
            command=self._ir_a_captura).pack(padx=20, fill="x")

        # Habilitar botón confirmar
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

        # Barra verde
        tk.Frame(self._col_form_frame, bg=p["verde_m"], height=4).pack(fill="x")

        # Encabezado
        encab = tk.Frame(self._col_form_frame, bg=p["bg"])
        encab.pack(fill="x", pady=(4, 0), padx=12)
        tk.Label(encab,
                 text="Ingrese los datos de la persona",
                 font=_F_INSTRUC, fg=p["texto2"], bg=p["bg"],
                 justify="left").pack(anchor="w")

        # Pie siempre visible (primero)
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

        tk.Button(
            self._pie_form, text="CANCELAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["rojo_btn"], activebackground=p["rojo_hover"],
            activeforeground="#ffffff",
            bd=0, padx=14, pady=7, relief="flat", cursor="hand2",
            command=self._cancelar).pack(side="left")

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

        self._campo(self._form, 0, 0, "Codigo Institucional", "cod_institucional")
        self._campo(self._form, 0, 1, "Nombre(s)",            "nombre")
        self._campo(self._form, 1, 0, "Apellido Paterno",     "apellido_paterno")
        self._campo(self._form, 1, 1, "Apellido Materno",     "apellido_materno")

        self._recargar_ico_flecha()

        # Programa
        self._carrera_var = tk.StringVar(
            value=self.datos.get("carrera", "Software"))
        sub_c = tk.Frame(self._form, bg=p["bg"])
        sub_c.grid(row=2, column=0, padx=(0,4), pady=2, sticky="ew")
        self._reg(sub_c, "bg")
        tk.Label(sub_c, text="Programa Académico", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_carrera = _hacer_dropdown(
            sub_c, self._carrera_var, _PROGRAMAS, p, self._ico_flecha)
        self._btn_carrera.pack(fill="x", ipady=2, pady=(1,0))

        # Rol
        self._rol_var = tk.StringVar(value=self.datos.get("rol", "Alumno"))
        sub_r = tk.Frame(self._form, bg=p["bg"])
        sub_r.grid(row=2, column=1, padx=(4,0), pady=2, sticky="ew")
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
            sub_r, text=f"  {self._rol_var.get()}",
            image=self._ico_flecha, compound="right",
            font=_F_ENTRY, anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=6, pady=4,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2", command=_abrir_rol)
        self._btn_rol.pack(fill="x", ipady=2, pady=(1,0))

        # Status
        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))
        sub_s = tk.Frame(self._form, bg=p["bg"])
        sub_s.grid(row=3, column=0, columnspan=2, pady=2, sticky="ew")
        self._reg(sub_s, "bg")
        tk.Label(sub_s, text="Status", font=_F_LABEL,
                 fg=p["texto2"], bg=p["bg"]).pack(anchor="w")
        self._btn_status = _hacer_dropdown(
            sub_s, self._status_var, ["Activo", "Inactivo"], p, self._ico_flecha)
        self._btn_status.pack(fill="x", ipady=2, pady=(1,0))

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

        # Mostrar contraseña si el rol inicial lo requiere
        if self._rol_var.get() in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=2, sticky="ew")

    def _on_rol_cambio(self, rol):
        if rol in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=2, sticky="ew")
        else:
            self._sub_password.grid_remove()
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

        # Valor inicial desde datos (para restaurar al regresar de captura)
        ent.insert(0, self.datos.get(key, ""))
        ent.pack(fill="x", ipady=4, pady=(1,0))

        if key == "cod_institucional":
            vcmd = (self.pantalla.winfo_toplevel().register(
                        lambda s: (s.isdigit() and len(s) <= 8) or s == ""), "%P")
            ent.configure(validate="key", validatecommand=vcmd)

        self._entradas[key] = ent

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _ir_a_captura(self):
        """Recolecta datos del formulario y va a pantalla de captura."""
        datos_actuales = {
            "cod_institucional": self._entradas["cod_institucional"].get().strip(),
            "nombre":            self._entradas["nombre"].get().strip(),
            "apellido_paterno":  self._entradas["apellido_paterno"].get().strip(),
            "apellido_materno":  self._entradas["apellido_materno"].get().strip(),
            "carrera":           self._carrera_var.get(),
            "rol":               self._rol_var.get(),
            "status":            self._status_var.get(),
        }
        # Guardar contraseñas si aplica
        if self._rol_var.get() in _ROLES_CON_PASSWORD:
            datos_actuales["_pwd1"] = self._ent_password.get()
            datos_actuales["_pwd2"] = self._ent_password2.get()

        self.app.mostrar_pantalla("captura_rostro", datos_actuales)

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        if self._encoding is None:
            self._lbl_aviso.config(text="Primero captura el rostro.")
            return

        cod       = self._entradas["cod_institucional"].get().strip()
        nombre    = self._entradas["nombre"].get().strip()
        apellidop = self._entradas["apellido_paterno"].get().strip()
        rol       = self._rol_var.get()
        carrera   = self._carrera_var.get()

        if not cod:
            self._lbl_aviso.config(text="El código es requerido.")
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
                return
            password_plain = pwd1

        self._btn_confirmar.config(state="disabled", text="GUARDANDO...")

        encoding_snap  = self._encoding
        password_snap  = password_plain

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
                "primer_nombre":     nombre,
                "segundo_nombre":    None,
                "apellido_paterno":  apellidop,
                "apellido_materno":  self._entradas["apellido_materno"].get().strip() or None,
                "carrera":           carrera,
                "grado":             None,
                "grupo":             None,
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