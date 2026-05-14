"""
ui/screens/pantalla_editar_usuario.py
Pantalla de Edición de Usuario — 800x480

CAMBIOS v2:
  - Campo contraseña aparece dinámicamente cuando Rol = Admin o Super Admin
  - Si se deja vacío al guardar → NO se modifica la contraseña existente
  - Si se ingresa una nueva → se hashea con SHA-256 y se actualiza
  - _on_rol_cambio() maneja la visibilidad del campo
  - Campo contraseña se muestra automáticamente si el usuario ya es Admin/SuperAdmin
"""

import tkinter as tk
from tkinter import messagebox
from pathlib import Path

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA
from core.database import actualizar_usuario

_RAIZ = Path(__file__).resolve().parents[2]

_ROLES_CON_PASSWORD = {"Admin", "Super Admin"}

_C = {
    "bg_app":       "#f3f4f5",
    "card_bg":      "#ffffff",
    "texto_oscuro": "#1a1a1a",
    "texto_gris":   "#757575",
    "borde":        "#e0e0e0",
    "verde_btn":    "#43a047",
    "verde_hover":  "#388e3c",
    "campo_bg":     "#f5f5f5",
    "campo_dis":    "#ebebeb",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#43a047",
    "filtro_fg":    "#1a1a1a",
    "flecha_img":   "arrow_circle_black.png",
}

_O = {
    "bg_app":       "#071E07",
    "card_bg":      "#0d2a0d",
    "texto_oscuro": "#d0f0d0",
    "texto_gris":   "#7aaa7a",
    "borde":        "#1a3a1a",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "campo_bg":     "#1a3a1a",
    "campo_dis":    "#071E07",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",
    "filtro_fg":    "#d0f0d0",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaEditarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent = parent
        self.app    = app
        self.datos  = datos or {}
        self._p     = _paleta(app)
        self._ico_flecha          = None
        self._widgets_repintables = []
        self._entradas            = {}
        self._btn_rol             = None
        self._btn_status          = None
        self._btn_guardar         = None
        self._sub_password        = None   # frame contraseña (dinámico)

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════════════════════════════════════
    #  TEMA
    # ══════════════════════════════════════════════════════════════════════════
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
            self._pie.configure(bg=p["bg_app"])

            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists():
                        continue
                    widget.configure(bg=p[bg_k])
                    if fg_k:
                        widget.configure(fg=p[fg_k])
                except tk.TclError:
                    pass

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
                except tk.TclError:
                    pass

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_status):
                if btn is None:
                    continue
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
                except tk.TclError:
                    pass

            if self._btn_guardar:
                try:
                    self._btn_guardar.configure(bg=p["verde_btn"],
                                                activebackground=p["verde_hover"])
                except tk.TclError:
                    pass
                self._cuerpo.configure(bg=p["bg_app"])
                self._card.update_idletasks()

            # Repintar campo contraseña si está visible
            if self._sub_password and self._sub_password.winfo_exists():
                try:
                    self._sub_password.configure(bg=p["card_bg"])
                    for child in self._sub_password.winfo_children():
                        if isinstance(child, tk.Label):
                            child.configure(bg=p["card_bg"], fg=p["texto_gris"])
                        elif isinstance(child, tk.Entry):
                            child.configure(bg=p["campo_bg"], fg=p["texto_oscuro"],
                                            insertbackground=p["texto_oscuro"],
                                            highlightbackground=p["borde"])
                except tk.TclError:
                    pass

        except tk.TclError:
            pass

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
            img  = Image.open(ruta).convert("RGBA").resize((16, 16), Image.LANCZOS)
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
        cuerpo = self._cuerpo
        cuerpo.pack(fill="both", expand=True, padx=20, pady=6)
        cuerpo.rowconfigure(1, weight=1)
        cuerpo.columnconfigure(0, weight=1)

        self._encab_frame = tk.Frame(cuerpo, bg=p["bg_app"])
        self._encab_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        lbl_titulo = tk.Label(self._encab_frame, text="EDITAR USUARIO",
                              font=("Segoe UI", 16, "bold"),
                              fg=p["texto_oscuro"], bg=p["bg_app"])
        lbl_titulo.pack(side="left")
        self._reg(lbl_titulo, "bg_app", "texto_oscuro")

        cod = self.datos.get("cod_institucional", "")
        if cod:
            lbl_cod = tk.Label(self._encab_frame, text=f"  #{cod}",
                               font=("Segoe UI", 12),
                               fg=p["texto_gris"], bg=p["bg_app"])
            lbl_cod.pack(side="left", pady=(4, 0))
            self._reg(lbl_cod, "bg_app", "texto_gris")

        self._card = tk.Frame(cuerpo, bg=p["card_bg"])
        self._card.grid(row=1, column=0, sticky="nsew")

        self._card_barra = tk.Frame(self._card, bg=p["verde_btn"], height=4)
        self._card_barra.pack(fill="x")

        self._form = tk.Frame(self._card, bg=p["card_bg"])
        self._form.pack(fill="both", expand=True, padx=20, pady=8)

        self._recargar_ico_flecha()
        self._construir_campos()

        self._pie = tk.Frame(cuerpo, bg=p["bg_app"])
        self._pie.grid(row=2, column=0, sticky="ew", pady=(8, 4))

        self._btn_guardar = tk.Button(
            self._pie, text="GUARDAR CAMBIOS",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
            command=self._guardar)
        self._btn_guardar.pack(side="left", padx=(0, 10))

        tk.Button(
            self._pie, text="CANCELAR",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg="#424242",
            activebackground="#212121", activeforeground="#ffffff",
            bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
            command=self._cancelar).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAMPOS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_campos(self):
        p    = self._p
        form = self._form

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        campos = [
            (0, 0, "No. Institucional", "cod_institucional", False),
            (0, 1, "Nombre",            "nombre",            True),
            (1, 0, "Apellido Paterno",  "apellido_paterno",  True),
            (1, 1, "Apellido Materno",  "apellido_materno",  True),
            (2, 0, "Programa / Carrera","carrera",            True),
            (2, 1, "Fecha y Hora",      "fecha_hora",         False),
        ]

        for row, col, label, key, editable in campos:
            padx = (0, 12) if col == 0 else (12, 0)
            sub = tk.Frame(form, bg=p["card_bg"])
            sub.grid(row=row, column=col, padx=padx, pady=3, sticky="ew")
            self._reg(sub, "card_bg")

            lbl = tk.Label(sub, text=label, font=("Segoe UI", 8),
                           fg=p["texto_gris"], bg=p["card_bg"])
            lbl.pack(anchor="w")
            self._reg(lbl, "card_bg", "texto_gris")

            valor = self.datos.get(key, "")
            bg_e  = p["campo_bg"] if editable else p["campo_dis"]
            fg_e  = p["texto_oscuro"] if editable else p["texto_gris"]

            e = tk.Entry(sub, font=("Segoe UI", 10),
                         fg=fg_e, bg=bg_e,
                         relief="flat", bd=0,
                         highlightthickness=1,
                         highlightbackground=p["borde"],
                         insertbackground=p["texto_oscuro"])
            e.insert(0, valor)
            if not editable:
                e.config(state="disabled",
                         disabledforeground=p["texto_gris"],
                         disabledbackground=p["campo_dis"])
            e.pack(fill="x", ipady=6, pady=(2, 0))
            self._entradas[key] = e

        # ── Fila 3: Rol + Status ──────────────────────────────────────────────
        fila_extra = tk.Frame(form, bg=p["card_bg"])
        fila_extra.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        fila_extra.columnconfigure(0, weight=1)
        fila_extra.columnconfigure(1, weight=1)
        self._reg(fila_extra, "card_bg")

        # Rol
        sub_rol = tk.Frame(fila_extra, bg=p["card_bg"])
        sub_rol.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        self._reg(sub_rol, "card_bg")

        lbl_rol = tk.Label(sub_rol, text="Rol", font=("Segoe UI", 8),
                           fg=p["texto_gris"], bg=p["card_bg"])
        lbl_rol.pack(anchor="w")
        self._reg(lbl_rol, "card_bg", "texto_gris")

        rol_inicial = self._normalizar_rol(self.datos.get("rol", "Alumno"))
        self._rol_var = tk.StringVar(value=rol_inicial)

        def _abrir_rol(event, btn):
            cp = self._p
            menu = tk.Menu(sub_rol, tearoff=0, font=("Segoe UI", 9),
                           bg=cp["card_bg"], fg=cp["texto_oscuro"],
                           activebackground=cp["verde_btn"],
                           activeforeground="#ffffff")
            for op in ["Alumno", "Maestro", "Admin", "Super Admin"]:
                menu.add_command(label=op,
                    command=lambda o=op: [
                        self._rol_var.set(o),
                        btn.config(text=f"  {o}"),
                        self._on_rol_cambio(o),  # ← mostrar/ocultar contraseña
                    ])
            menu.tk_popup(btn.winfo_rootx(),
                          btn.winfo_rooty() + btn.winfo_height())

        self._btn_rol = tk.Button(
            sub_rol, text=f"  {self._rol_var.get()}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 10), anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=6,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2")
        self._btn_rol.bind("<Button-1>", lambda e: _abrir_rol(e, self._btn_rol))
        self._btn_rol.pack(fill="x", pady=(2, 0))

        # Status
        sub_status = tk.Frame(fila_extra, bg=p["card_bg"])
        sub_status.grid(row=0, column=1, padx=(12, 0), sticky="ew")
        self._reg(sub_status, "card_bg")

        lbl_status = tk.Label(sub_status, text="Status", font=("Segoe UI", 8),
                              fg=p["texto_gris"], bg=p["card_bg"])
        lbl_status.pack(anchor="w")
        self._reg(lbl_status, "card_bg", "texto_gris")

        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))

        def _abrir_status(event, btn):
            cp = self._p
            menu = tk.Menu(sub_status, tearoff=0, font=("Segoe UI", 9),
                           bg=cp["card_bg"], fg=cp["texto_oscuro"],
                           activebackground=cp["verde_btn"],
                           activeforeground="#ffffff")
            for op in ["Activo", "Inactivo"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._status_var.set(o),
                                          btn.config(text=f"  {o}")])
            menu.tk_popup(btn.winfo_rootx(),
                          btn.winfo_rooty() + btn.winfo_height())

        self._btn_status = tk.Button(
            sub_status, text=f"  {self._status_var.get()}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 10), anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=6,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2")
        self._btn_status.bind("<Button-1>",
                              lambda e: _abrir_status(e, self._btn_status))
        self._btn_status.pack(fill="x", pady=(2, 0))

        # ── Fila 4: Contraseña (oculta por defecto, aparece para Admin) ───────
        self._sub_password = tk.Frame(form, bg=p["card_bg"])
        # NO se hace grid aquí — se maneja en _on_rol_cambio()

        lbl_pwd = tk.Label(self._sub_password,
                           text="Nueva Contraseña  (dejar vacío = no cambiar)",
                           font=("Segoe UI", 8),
                           fg=p["texto_gris"], bg=p["card_bg"])
        lbl_pwd.pack(anchor="w")

        self._ent_password = tk.Entry(
            self._sub_password, font=("Segoe UI", 10),
            fg=p["texto_oscuro"], bg=p["campo_bg"],
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=p["borde"],
            insertbackground=p["texto_oscuro"],
            show="•")
        self._ent_password.pack(fill="x", ipady=6, pady=(2, 0))

        # Mostrar automáticamente si el usuario ya es Admin/SuperAdmin
        if rol_inicial in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=3, sticky="ew")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAMPO CONTRASEÑA DINÁMICO
    # ══════════════════════════════════════════════════════════════════════════
    def _on_rol_cambio(self, rol: str):
        """Muestra u oculta el campo contraseña según el rol seleccionado."""
        if rol in _ROLES_CON_PASSWORD:
            self._sub_password.grid(
                row=4, column=0, columnspan=2,
                padx=0, pady=3, sticky="ew")
        else:
            self._sub_password.grid_remove()
            self._ent_password.delete(0, tk.END)

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def _normalizar_rol(rol: str) -> str:
        mapa = {
            "superadmin":   "Super Admin",
            "super admin":  "Super Admin",
            "superusuario": "Super Admin",
            "admin":        "Admin",
            "alumno":       "Alumno",
            "maestro":      "Maestro",
            "profesor":     "Maestro",
        }
        return mapa.get((rol or "Alumno").lower().strip(), rol or "Alumno")

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        rol = self._rol_var.get()

        datos_actualizados = {
            "cod_institucional": self.datos.get("cod_institucional", ""),
            "nombre":            self._entradas["nombre"].get().strip(),
            "apellido_paterno":  self._entradas["apellido_paterno"].get().strip(),
            "apellido_materno":  self._entradas["apellido_materno"].get().strip(),
            "carrera":           self._entradas["carrera"].get().strip(),
            "rol":               rol,
            "status":            self._status_var.get(),
        }

        if not datos_actualizados["nombre"]:
            messagebox.showwarning("Campo requerido", "El nombre no puede estar vacío.")
            return
        if not datos_actualizados["apellido_paterno"]:
            messagebox.showwarning("Campo requerido",
                                   "El apellido paterno no puede estar vacío.")
            return

        # ── Contraseña: solo actualizar si se ingresó algo ────────────────────
        if rol in _ROLES_CON_PASSWORD:
            nueva_pwd = self._ent_password.get().strip()
            if nueva_pwd:
                # Validar longitud mínima
                if len(nueva_pwd) < 6:
                    messagebox.showwarning(
                        "Contraseña inválida",
                        "La contraseña debe tener al menos 6 caracteres.")
                    return
                # Hashear y agregar a los datos
                import hashlib
                datos_actualizados["password_hash"] = hashlib.sha256(
                    nueva_pwd.encode("utf-8")).hexdigest()
            # Si está vacío → no se incluye password_hash → BD no lo cambia

        ok, msg = actualizar_usuario(datos_actualizados)
        if ok:
            messagebox.showinfo("Guardado", msg)
            self.app.mostrar_pantalla("gestion_real")
        else:
            messagebox.showerror("Error al guardar", msg)

    def _cancelar(self):
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_editar_usuario(parent, app, datos=None):
    PantallaEditarUsuario(parent, app, datos)