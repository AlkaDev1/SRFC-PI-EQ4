"""
ui/screens/pantalla_editar_usuario.py

CAMBIOS:
  - Conectado a GestorIdioma: título, etiquetas de campos, botones
    y mensajes de validación leen del idioma activo.
  - _limpiar() desregistra también el listener de idioma.
"""

import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from ui.components.barra_superior import crear_encabezado
from ui.components.modal_dialogo import modal_info, modal_error, modal_warning
from ui.styles import PALETA
from core.database import actualizar_usuario

_RAIZ = Path(__file__).resolve().parents[2]

_ROLES_CON_PASSWORD = {"Admin", "Super Admin"}
_PROGRAMAS          = ["Ninguno", "Software", "Mecatrónica"]

_C = {
    "bg_app":"#f3f4f5","card_bg":"#ffffff","texto_oscuro":"#1a1a1a",
    "texto_gris":"#757575","borde":"#e0e0e0","verde_btn":"#43a047",
    "verde_hover":"#388e3c","campo_bg":"#f5f5f5","campo_dis":"#ebebeb",
    "filtro_bg":"#f5f5f5","filtro_borde":"#43a047","filtro_fg":"#1a1a1a",
    "flecha_img":"arrow_circle_black.png",
}
_O = {
    "bg_app":"#071E07","card_bg":"#0d2a0d","texto_oscuro":"#d0f0d0",
    "texto_gris":"#7aaa7a","borde":"#1a3a1a","verde_btn":"#2D531A",
    "verde_hover":"#477023","campo_bg":"#1a3a1a","campo_dis":"#071E07",
    "filtro_bg":"#1a3a1a","filtro_borde":"#477023","filtro_fg":"#d0f0d0",
    "flecha_img":"arrow_drop_down.png",
}


def _paleta(app) -> dict:
    return _O if (hasattr(app, "tema") and app.tema.es_oscuro()) else _C


def _validar_password(pwd: str):
    if len(pwd) < 6:                          return "error_pwd_min"
    if not any(c.isupper() for c in pwd):     return "error_pwd_mayus"
    if not any(c.islower() for c in pwd):     return "error_pwd_minus"
    if not any(c.isdigit() for c in pwd):     return "error_pwd_num"
    return None


def _hacer_dropdown(parent, var, opciones, p, ico_flecha, on_select=None, font=None):
    font = font or ("Segoe UI", 10)

    def _abrir():
        menu = tk.Menu(parent, tearoff=0, font=font,
                       bg=p["card_bg"], fg=p["texto_oscuro"],
                       activebackground=p["verde_btn"],
                       activeforeground="#ffffff")
        for op in opciones:
            def _sel(o=op):
                var.set(o)
                btn.config(text=f"  {o}")
                if on_select:
                    on_select(o)
            menu.add_command(label=op, command=_sel)
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        menu.post(x, y)

    btn = tk.Button(
        parent, text=f"  {var.get()}",
        image=ico_flecha, compound="right",
        font=font, anchor="w",
        fg=p["filtro_fg"], bg=p["filtro_bg"],
        activebackground=p["borde"],
        relief="flat", bd=0, padx=8, pady=6,
        highlightthickness=1, highlightbackground=p["filtro_borde"],
        cursor="hand2", command=_abrir)
    return btn


def _campo_password_editar(parent, p, label_txt, img_on, img_off):
    tk.Label(parent, text=label_txt, font=("Segoe UI", 8),
             fg=p["texto_gris"], bg=p["card_bg"]).pack(anchor="w", fill="x")
    wrapper = tk.Frame(parent, bg=p["campo_bg"],
                       highlightthickness=1, highlightbackground=p["borde"])
    wrapper.pack(fill="x", pady=(2, 6))
    ent = tk.Entry(wrapper, font=("Segoe UI", 10),
                   fg=p["texto_oscuro"], bg=p["campo_bg"],
                   relief="flat", bd=0,
                   insertbackground=p["texto_oscuro"], show="•")
    ent.pack(side="left", fill="both", expand=True, ipady=6, padx=(6, 0))

    _visible = [False]
    def _toggle():
        _visible[0] = not _visible[0]
        ent.config(show="" if _visible[0] else "•")
        if img_on and img_off:
            ojo.config(image=img_off if _visible[0] else img_on)
        else:
            ojo.config(text="🙈" if _visible[0] else "👁")

    if img_on:
        ojo = tk.Label(wrapper, image=img_on, bg=p["campo_bg"], cursor="hand2")
    else:
        ojo = tk.Label(wrapper, text="👁", font=("Segoe UI", 10),
                       bg=p["campo_bg"], fg=p["texto_gris"], cursor="hand2")
    ojo.pack(side="right", padx=(2, 6))
    ojo.bind("<Button-1>", lambda e: _toggle())
    return ent, wrapper, ojo


def _nombre_completo_para_editar(datos: dict) -> str:
    primer  = datos.get("primer_nombre", "").strip()
    segundo = datos.get("segundo_nombre", "").strip()
    if primer and segundo:
        return f"{primer} {segundo}".strip()
    if primer:
        return primer
    return datos.get("nombre", "").strip()


class PantallaEditarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent = parent
        self.app    = app
        self.datos  = datos or {}
        self._p     = _paleta(app)
        self._ico_flecha          = None
        self._img_ojo_on          = None
        self._img_ojo_off         = None
        self._widgets_repintables = []
        self._entradas            = {}
        self._btn_rol             = None
        self._btn_status          = None
        self._btn_carrera         = None
        self._btn_guardar         = None
        self._sub_password        = None
        self._pwd_wrappers        = []
        self._labels_campos       = {}   # lang_key → Label

        self._cargar_iconos_ojo()
        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        if hasattr(app, "idioma"):
            app.idioma.registrar(self._aplicar_idioma)
        self.pantalla.bind("<Destroy>", self._limpiar)

    # ── Idioma ────────────────────────────────────────────────────────────────
    def _t(self, clave, fallback=""):
        if hasattr(self.app, "idioma"):
            return self.app.idioma.t(clave, fallback)
        return fallback or clave

    def _roles(self):
        v = self._t("editar_usuario.roles")
        return v if isinstance(v, list) else ["Alumno", "Maestro", "Admin", "Super Admin"]

    def _status_opts(self):
        v = self._t("editar_usuario.status")
        return v if isinstance(v, list) else ["Activo", "Inactivo"]

    def _programas(self):
        v = self._t("editar_usuario.programas")
        if isinstance(v, list):
            return ["Ninguno"] + v
        return ["Ninguno", "Software", "Mecatrónica"]

    def _aplicar_idioma(self):
        try:
            # Título
            self._lbl_titulo.config(
                text=self._t("editar_usuario.titulo", "EDITAR USUARIO"))
            # Botones pie
            self._btn_guardar.config(
                text=self._t("editar_usuario.btn_guardar", "GUARDAR CAMBIOS"))
            self._btn_cancelar_widget.config(
                text=self._t("editar_usuario.btn_cancelar", "CANCELAR"))
            # Etiquetas de campos
            for key, lbl in self._labels_campos.items():
                try:
                    lbl.config(text=self._t(f"editar_usuario.{key}",
                                            lbl.cget("text")))
                except tk.TclError:
                    pass
        except tk.TclError:
            pass

    # ── Tema ──────────────────────────────────────────────────────────────────
    def _cargar_iconos_ojo(self):
        try:
            on  = Image.open(_RAIZ/"assets"/"img"/"visibility_icon.png"
                             ).resize((16,16), Image.LANCZOS)
            off = Image.open(_RAIZ/"assets"/"img"/"visibility_off_icon.png"
                             ).resize((16,16), Image.LANCZOS)
            self._img_ojo_on  = ImageTk.PhotoImage(on)
            self._img_ojo_off = ImageTk.PhotoImage(off)
        except Exception:
            self._img_ojo_on  = None
            self._img_ojo_off = None

    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg_app"])
            self._encab_frame.configure(bg=p["bg_app"])
            self._card.configure(bg=p["card_bg"])
            self._card_barra.configure(bg=p["verde_btn"])
            self._form.configure(bg=p["card_bg"])
            try: self._canvas_scroll.configure(bg=p["card_bg"])
            except Exception: pass
            self._pie.configure(bg=p["bg_app"])

            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists(): continue
                    widget.configure(bg=p[bg_k])
                    if fg_k: widget.configure(fg=p[fg_k])
                except tk.TclError: pass

            for key, entry in self._entradas.items():
                try:
                    editable = entry.cget("state") != "disabled"
                    if editable:
                        entry.configure(bg=p["campo_bg"], fg=p["texto_oscuro"],
                                        highlightbackground=p["borde"],
                                        insertbackground=p["texto_oscuro"])
                    else:
                        entry.configure(disabledbackground=p["campo_dis"],
                                        disabledforeground=p["texto_gris"],
                                        highlightbackground=p["borde"])
                except tk.TclError: pass

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_status, self._btn_carrera):
                if btn is None: continue
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
                except tk.TclError: pass

            if self._btn_guardar:
                try:
                    self._btn_guardar.configure(bg=p["verde_btn"],
                                                activebackground=p["verde_hover"])
                except tk.TclError: pass
            self._cuerpo.configure(bg=p["bg_app"])

            for wrapper, ojo in self._pwd_wrappers:
                try:
                    wrapper.configure(bg=p["campo_bg"],
                                      highlightbackground=p["borde"])
                    ojo.configure(bg=p["campo_bg"])
                except tk.TclError: pass

            if self._sub_password and self._sub_password.winfo_exists():
                self._sub_password.configure(bg=p["card_bg"])
        except tk.TclError: pass

    def _limpiar(self, event=None):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._on_tema_cambio)
        if hasattr(self.app, "idioma"):
            self.app.idioma.desregistrar(self._aplicar_idioma)

    def _reg(self, widget, bg_k, fg_k=None):
        self._widgets_repintables.append((widget, bg_k, fg_k))

    def _recargar_ico_flecha(self):
        if not _PIL_OK:
            self._ico_flecha = None
            return
        try:
            ruta = _RAIZ/"assets"/"img"/self._p["flecha_img"]
            img  = Image.open(ruta).convert("RGBA").resize((16,16), Image.LANCZOS)
            self._ico_flecha = ImageTk.PhotoImage(img)
        except Exception:
            self._ico_flecha = None

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg_app"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        self._cuerpo = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._cuerpo.pack(fill="both", expand=True, padx=20, pady=6)
        self._cuerpo.rowconfigure(1, weight=1)
        self._cuerpo.columnconfigure(0, weight=1)

        self._encab_frame = tk.Frame(self._cuerpo, bg=p["bg_app"])
        self._encab_frame.grid(row=0, column=0, sticky="ew", pady=(0,6))

        self._lbl_titulo = tk.Label(
            self._encab_frame,
            text=self._t("editar_usuario.titulo", "EDITAR USUARIO"),
            font=("Segoe UI", 16, "bold"),
            fg=p["texto_oscuro"], bg=p["bg_app"])
        self._lbl_titulo.pack(side="left")
        self._reg(self._lbl_titulo, "bg_app", "texto_oscuro")

        cod = self.datos.get("cod_institucional", "")
        if cod:
            lbl_cod = tk.Label(self._encab_frame, text=f"  #{cod}",
                               font=("Segoe UI", 12),
                               fg=p["texto_gris"], bg=p["bg_app"])
            lbl_cod.pack(side="left", pady=(4,0))
            self._reg(lbl_cod, "bg_app", "texto_gris")

        self._card = tk.Frame(self._cuerpo, bg=p["card_bg"])
        self._card.grid(row=1, column=0, sticky="nsew")

        self._card_barra = tk.Frame(self._card, bg=p["verde_btn"], height=4)
        self._card_barra.pack(fill="x")

        scroll_container = tk.Frame(self._card, bg=p["card_bg"])
        scroll_container.pack(fill="both", expand=True)
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        self._canvas_scroll = tk.Canvas(
            scroll_container, bg=p["card_bg"],
            highlightthickness=0, bd=0)
        self._canvas_scroll.grid(row=0, column=0, sticky="nsew")

        self._scrollbar = tk.Scrollbar(
            scroll_container, orient="vertical",
            command=self._canvas_scroll.yview)
        self._scrollbar.grid(row=0, column=1, sticky="ns")
        self._canvas_scroll.configure(yscrollcommand=self._scrollbar.set)

        self._form = tk.Frame(self._canvas_scroll, bg=p["card_bg"])
        self._form_window = self._canvas_scroll.create_window(
            (0,0), window=self._form, anchor="nw")

        def _on_canvas_resize(event):
            self._canvas_scroll.itemconfig(self._form_window, width=event.width)
        self._canvas_scroll.bind("<Configure>", _on_canvas_resize)

        def _on_form_resize(event):
            self._canvas_scroll.configure(
                scrollregion=self._canvas_scroll.bbox("all"))
        self._form.bind("<Configure>", _on_form_resize)

        self._canvas_scroll.bind("<MouseWheel>",
            lambda e: self._canvas_scroll.yview_scroll(
                int(-1*(e.delta/120)), "units"))
        self._form.bind_all("<Button-4>",
            lambda e: self._canvas_scroll.yview_scroll(-1, "units"))
        self._form.bind_all("<Button-5>",
            lambda e: self._canvas_scroll.yview_scroll(1, "units"))

        self._recargar_ico_flecha()
        self._construir_campos()
        self._canvas_scroll.yview_moveto(0)

        self._pie = tk.Frame(self._cuerpo, bg=p["bg_app"])
        self._pie.grid(row=2, column=0, sticky="ew", pady=(8,4))

        self._btn_guardar = tk.Button(
            self._pie,
            text=self._t("editar_usuario.btn_guardar", "GUARDAR CAMBIOS"),
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
            command=self._guardar)
        self._btn_guardar.pack(side="left", padx=(0,10))

        self._btn_cancelar_widget = tk.Button(
            self._pie,
            text=self._t("editar_usuario.btn_cancelar", "CANCELAR"),
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg="#424242",
            activebackground="#212121", activeforeground="#ffffff",
            bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
            command=self._cancelar)
        self._btn_cancelar_widget.pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAMPOS
    # ══════════════════════════════════════════════════════════════════════════
    def _campo(self, parent, row, col, lang_key, fallback_label,
               data_key, editable=True, valor_override=None):
        p    = self._p
        padx = (0,12) if col == 0 else (12,0)
        sub  = tk.Frame(parent, bg=p["card_bg"])
        sub.grid(row=row, column=col, padx=padx, pady=3, sticky="ew")
        self._reg(sub, "card_bg")

        lbl = tk.Label(sub,
                       text=self._t(f"editar_usuario.{lang_key}", fallback_label),
                       font=("Segoe UI", 8),
                       fg=p["texto_gris"], bg=p["card_bg"])
        lbl.pack(anchor="w")
        self._reg(lbl, "card_bg", "texto_gris")
        self._labels_campos[lang_key] = lbl

        valor = valor_override if valor_override is not None else self.datos.get(data_key, "")
        bg_e  = p["campo_bg"] if editable else p["campo_dis"]
        fg_e  = p["texto_oscuro"] if editable else p["texto_gris"]

        e = tk.Entry(sub, font=("Segoe UI", 10),
                     fg=fg_e, bg=bg_e,
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=p["borde"],
                     insertbackground=p["texto_oscuro"])
        e.insert(0, valor)
        if not editable:
            e.config(state="disabled",
                     disabledforeground=p["texto_gris"],
                     disabledbackground=p["campo_dis"])
        e.pack(fill="x", ipady=6, pady=(2,0))
        self._entradas[data_key] = e

    def _construir_campos(self):
        p    = self._p
        form = self._form
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        nombre_valor = _nombre_completo_para_editar(self.datos)

        self._campo(form, 0, 0, "campo_cod",
                    "No. Institucional", "cod_institucional", editable=False)
        self._campo(form, 0, 1, "campo_nombre",
                    "Nombre", "nombre", editable=True,
                    valor_override=nombre_valor)
        self._campo(form, 1, 0, "campo_ap_paterno",
                    "Apellido Paterno", "apellido_paterno")
        self._campo(form, 1, 1, "campo_ap_materno",
                    "Apellido Materno", "apellido_materno")
        self._campo(form, 2, 1, "campo_fecha_hora",
                    "Fecha y Hora", "fecha_hora", editable=False)

        # Carrera
        carrera_actual = self.datos.get("carrera", "Ninguno") or "Ninguno"
        if carrera_actual not in self._programas():
            carrera_actual = "Ninguno"
        self._carrera_var = tk.StringVar(value=carrera_actual)

        sub_carrera = tk.Frame(form, bg=p["card_bg"])
        sub_carrera.grid(row=2, column=0, padx=(0,12), pady=3, sticky="ew")
        self._reg(sub_carrera, "card_bg")
        lbl_prog = tk.Label(sub_carrera,
                            text=self._t("editar_usuario.campo_programa",
                                         "Programa / Carrera"),
                            font=("Segoe UI", 8),
                            fg=p["texto_gris"], bg=p["card_bg"])
        lbl_prog.pack(anchor="w")
        self._reg(lbl_prog, "card_bg", "texto_gris")
        self._labels_campos["campo_programa"] = lbl_prog
        self._btn_carrera = _hacer_dropdown(
            sub_carrera, self._carrera_var, self._programas(), p, self._ico_flecha)
        self._btn_carrera.pack(fill="x", pady=(2,0))

        # Rol + Status
        fila_extra = tk.Frame(form, bg=p["card_bg"])
        fila_extra.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        fila_extra.columnconfigure(0, weight=1)
        fila_extra.columnconfigure(1, weight=1)
        self._reg(fila_extra, "card_bg")

        sub_rol = tk.Frame(fila_extra, bg=p["card_bg"])
        sub_rol.grid(row=0, column=0, padx=(0,12), sticky="ew")
        self._reg(sub_rol, "card_bg")
        lbl_rol = tk.Label(sub_rol,
                           text=self._t("editar_usuario.campo_rol", "Rol"),
                           font=("Segoe UI", 8),
                           fg=p["texto_gris"], bg=p["card_bg"])
        lbl_rol.pack(anchor="w")
        self._reg(lbl_rol, "card_bg", "texto_gris")
        self._labels_campos["campo_rol"] = lbl_rol

        rol_inicial = self._normalizar_rol(self.datos.get("rol", "Alumno"))
        self._rol_var = tk.StringVar(value=rol_inicial)

        def _abrir_rol():
            cp = self._p
            menu = tk.Menu(sub_rol, tearoff=0, font=("Segoe UI", 9),
                           bg=cp["card_bg"], fg=cp["texto_oscuro"],
                           activebackground=cp["verde_btn"],
                           activeforeground="#ffffff")
            for op in self._roles():
                menu.add_command(label=op, command=lambda o=op: [
                    self._rol_var.set(o),
                    self._btn_rol.config(text=f"  {o}"),
                    self._on_rol_cambio(o),
                ])
            x = self._btn_rol.winfo_rootx()
            y = self._btn_rol.winfo_rooty() + self._btn_rol.winfo_height()
            menu.post(x, y)

        self._btn_rol = tk.Button(
            sub_rol, text=f"  {rol_inicial}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 10), anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=6,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2", command=_abrir_rol)
        self._btn_rol.pack(fill="x", pady=(2,0))

        sub_status = tk.Frame(fila_extra, bg=p["card_bg"])
        sub_status.grid(row=0, column=1, padx=(12,0), sticky="ew")
        self._reg(sub_status, "card_bg")
        lbl_status = tk.Label(sub_status,
                              text=self._t("editar_usuario.campo_status", "Status"),
                              font=("Segoe UI", 8),
                              fg=p["texto_gris"], bg=p["card_bg"])
        lbl_status.pack(anchor="w")
        self._reg(lbl_status, "card_bg", "texto_gris")
        self._labels_campos["campo_status"] = lbl_status

        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))
        self._btn_status = _hacer_dropdown(
            sub_status, self._status_var, self._status_opts(), p, self._ico_flecha)
        self._btn_status.pack(fill="x", pady=(2,0))

        # Contraseña
        self._sub_password = tk.Frame(form, bg=p["card_bg"])

        ent1, w1, o1 = _campo_password_editar(
            self._sub_password, p,
            self._t("editar_usuario.campo_password",
                    "Nueva Contraseña  (mayúscula, minúscula y número — vacío = no cambiar)"),
            self._img_ojo_on, self._img_ojo_off)
        self._ent_password = ent1
        self._pwd_wrappers.append((w1, o1))

        ent2, w2, o2 = _campo_password_editar(
            self._sub_password, p,
            self._t("editar_usuario.campo_confirmar_password",
                    "Confirmar nueva contraseña"),
            self._img_ojo_on, self._img_ojo_off)
        self._ent_password2 = ent2
        self._pwd_wrappers.append((w2, o2))

        if rol_inicial in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=3, sticky="ew")

    # ══════════════════════════════════════════════════════════════════════════
    #  ROL DINÁMICO
    # ══════════════════════════════════════════════════════════════════════════
    def _on_rol_cambio(self, rol: str):
        if rol in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=3, sticky="ew")
        else:
            self._sub_password.grid_remove()
            self._ent_password.delete(0, tk.END)
            self._ent_password2.delete(0, tk.END)

    @staticmethod
    def _normalizar_rol(rol: str) -> str:
        mapa = {
            "superadmin":"Super Admin","super admin":"Super Admin",
            "superusuario":"Super Admin","admin":"Admin",
            "alumno":"Alumno","maestro":"Maestro","profesor":"Maestro",
        }
        return mapa.get((rol or "Alumno").lower().strip(), rol or "Alumno")

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        rol        = self._rol_var.get()
        nombre_raw = self._entradas["nombre"].get().strip()
        partes     = nombre_raw.split(None, 1)
        primer     = partes[0] if partes else ""
        segundo    = partes[1].strip() if len(partes) > 1 else None

        carrera = self._carrera_var.get()
        if carrera == "Ninguno":
            carrera = None

        datos_actualizados = {
            "cod_institucional": self.datos.get("cod_institucional", ""),
            "nombre":            primer,
            "segundo_nombre":    segundo,
            "apellido_paterno":  self._entradas["apellido_paterno"].get().strip(),
            "apellido_materno":  self._entradas["apellido_materno"].get().strip(),
            "carrera":           carrera,
            "rol":               rol,
            "status":            self._status_var.get(),
        }

        if not datos_actualizados["nombre"]:
            modal_warning(self.pantalla,
                          self._t("editar_usuario.error_nombre",
                                  "El nombre no puede estar vacío."))
            return
        if not datos_actualizados["apellido_paterno"]:
            modal_warning(self.pantalla,
                          self._t("editar_usuario.error_apellido",
                                  "El apellido paterno no puede estar vacío."))
            return

        if rol in _ROLES_CON_PASSWORD:
            pwd1 = self._ent_password.get().strip()
            pwd2 = self._ent_password2.get().strip()
            if pwd1:
                err_key = _validar_password(pwd1)
                if err_key:
                    modal_warning(
                        self.pantalla,
                        self._t(f"editar_usuario.{err_key}", err_key),
                        titulo=self._t("editar_usuario.modal_pwd_invalida",
                                       "Contraseña inválida"))
                    return
                if pwd1 != pwd2:
                    modal_warning(
                        self.pantalla,
                        self._t("editar_usuario.error_pwd_no_coinciden",
                                 "Las contraseñas no coinciden."))
                    self._pwd_wrappers[1][0].configure(
                        highlightbackground="#e53935", highlightthickness=2)
                    return
                self._pwd_wrappers[1][0].configure(
                    highlightbackground=self._p["borde"], highlightthickness=1)
                import hashlib
                datos_actualizados["password_hash"] = hashlib.sha256(
                    pwd1.encode("utf-8")).hexdigest()

        ok, msg = actualizar_usuario(datos_actualizados)
        if ok:
            modal_info(self.pantalla, msg,
                       titulo=self._t("editar_usuario.modal_guardado", "Guardado"),
                       on_ok=lambda: self.app.mostrar_pantalla("gestion_real"))
        else:
            modal_error(self.pantalla, msg,
                        titulo=self._t("editar_usuario.modal_error_guardar",
                                       "Error al guardar"))

    def _cancelar(self):
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_editar_usuario(parent, app, datos=None):
    PantallaEditarUsuario(parent, app, datos)