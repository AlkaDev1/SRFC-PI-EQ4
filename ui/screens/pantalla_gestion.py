"""
ui/screens/pantalla_gestion.py

CAMBIOS:
  - Recibe datos={"id_rol": ...} desde validacionUsrs para saber quién entró.
  - Admin  (id_rol=2): solo ve Alumnos y Maestros en tabla y dropdown.
  - Super Admin (id_rol=1): ve Alumnos, Maestros y Admins.
  - Super Admin tiene un 4to cuadro "INGRESOS ADMINS" en lugar de "ACCESOS DENEGADOS".
  - Admin mantiene el cuadro rojo "ACCESOS DENEGADOS".
  - Conectado a GestorIdioma.
  - _limpiar() desregistra tema e idioma.
  - Menús usan _abrir_menu() centralizado.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from core.database import (listar_usuarios as obtener_usuarios,
                            listar_accesos as obtener_accesos,
                            conteo_accesos_hoy,
                            inicializar_bd)

_RAIZ = Path(__file__).resolve().parents[2]

_C = {
    "gris_bg":"#f5f5f5","card_bg":"#ffffff","texto_oscuro":"#1a1a1a",
    "texto_gris":"#757575","borde":"#e0e0e0","verde":"#2e7d32",
    "verde_claro":"#4caf50","verde_btn":"#43a047","verde_hover":"#388e3c",
    "rojo":"#c62828","rojo_claro":"#ef5350","fila_par":"#f9f9f9",
    "fila_impar":"#ffffff","sel_tree":"#e8f5e9","sel_tree_fg":"#2e7d32",
    "filtro_bg":"#f5f5f5","filtro_borde":"#e0e0e0","filtro_fg":"#1a1a1a",
    "azul":"#1565c0","azul_claro":"#42a5f5",
    "flecha_img":"arrow_circle_black.png",
}
_O = {
    "gris_bg":"#071E07","card_bg":"#0d2a0d","texto_oscuro":"#d0f0d0",
    "texto_gris":"#7aaa7a","borde":"#1a3a1a","verde":"#2D531A",
    "verde_claro":"#477023","verde_btn":"#2D531A","verde_hover":"#477023",
    "rojo":"#7f1d1d","rojo_claro":"#f87171","fila_par":"#0d2a0d",
    "fila_impar":"#071E07","sel_tree":"#1a3a1a","sel_tree_fg":"#4ade80",
    "filtro_bg":"#1a3a1a","filtro_borde":"#1a3a1a","filtro_fg":"#d0f0d0",
    "azul":"#1e3a5f","azul_claro":"#90caf9",
    "flecha_img":"arrow_drop_down.png",
}

_MESES_NUM = {
    "Enero":"01","Febrero":"02","Marzo":"03","Abril":"04",
    "Mayo":"05","Junio":"06","Julio":"07","Agosto":"08",
    "Septiembre":"09","Octubre":"10","Noviembre":"11","Diciembre":"12",
    "January":"01","February":"02","March":"03","April":"04",
    "May":"05","June":"06","July":"07","August":"08",
    "September":"09","October":"10","November":"11","December":"12",
}


def _paleta(app) -> dict:
    return _O if (hasattr(app, "tema") and app.tema.es_oscuro()) else _C


class PantallaGestion:

    def __init__(self, parent, app, datos=None):
        self.parent  = parent
        self.app     = app
        self._p      = _paleta(app)
        # ── id_rol del usuario que inició sesión ─────────────────────────────
        # 1 = Super Admin  →  ve Alumnos + Maestros + Admins
        # 2 = Admin        →  ve Alumnos + Maestros
        self._id_rol = (datos or {}).get("id_rol", 2)

        self._todos_usuarios      = []
        self._filtro_rol          = tk.StringVar(value="")
        self._filtro_mes          = tk.StringVar(value="")
        self._ico_flecha          = None
        self._widgets_repintables = []
        self._btns_accion         = []
        self._menu_abierto        = None

        inicializar_bd()
        self._construir_ui()
        self.pantalla.after(100, self._cargar_todo)

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        if hasattr(app, "idioma"):
            app.idioma.registrar(self._aplicar_idioma)
        self.pantalla.bind("<Destroy>", self._limpiar)

    # ══════════════════════════════════════════════════════════════════════════
    #  PERMISOS POR ROL
    # ══════════════════════════════════════════════════════════════════════════
    def _roles_visibles(self) -> set:
        """Roles de usuario que puede ver en la tabla según quién inició sesión."""
        if self._id_rol == 1:          # Super Admin
            return {"Alumno", "Maestro", "Admin"}
        return {"Alumno", "Maestro"}   # Admin normal

    def _es_super_admin(self) -> bool:
        return self._id_rol == 1

    # ══════════════════════════════════════════════════════════════════════════
    #  IDIOMA
    # ══════════════════════════════════════════════════════════════════════════
    def _t(self, clave, fallback=""):
        if hasattr(self.app, "idioma"):
            return self.app.idioma.t(clave, fallback)
        return fallback or clave

    def _opciones_rol(self):
        v = self._t("gestion.roles")
        todos = v if isinstance(v, list) else \
            ["Rol", "Alumno", "Maestro", "Admin", "Super Admin"]
        # Admin no puede ver ni filtrar por Admin/Super Admin
        if not self._es_super_admin():
            todos = [r for r in todos
                     if r.lower() not in ("admin", "super admin")]
        return todos

    def _opciones_mes(self):
        v = self._t("gestion.meses")
        return v if isinstance(v, list) else \
            ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def _columnas(self):
        v = self._t("gestion.columnas")
        return v if isinstance(v, list) else \
            ["No. Inst.", "Nombre", "Ap. Paterno", "Ap. Materno",
             "Programa", "Rol", "Fecha/Hora", "Status", "Editar"]

    def _aplicar_idioma(self):
        self._cerrar_menu()
        try:
            self._lbl_titulo_tabla.config(
                text=self._t("gestion.titulo_tabla", " USUARIOS "))

            specs_t = [
                ("accesos_hoy_titulo",  "gestion.tarjeta_accesos_hoy",  "ACCESOS HOY"),
                ("alumnos_titulo",      "gestion.tarjeta_alumnos",      "ALUMNOS"),
                ("profesores_titulo",   "gestion.tarjeta_profesores",   "PROFESORES"),
            ]
            if self._es_super_admin():
                specs_t.append(
                    ("admins_titulo", "gestion.tarjeta_admins", "INGRESOS ADMINS"))
            else:
                specs_t.append(
                    ("denegados_titulo", "gestion.tarjeta_denegados", "ACCESOS DENEGADOS"))

            for key, clave, fb in specs_t:
                if key in self._tarjetas:
                    try:
                        self._tarjetas[key].config(text=self._t(clave, fb))
                    except tk.TclError:
                        pass

            if hasattr(self, "_btn_agregar"):
                self._btn_agregar.config(
                    text=self._t("gestion.btn_agregar", "  AGREGAR USUARIO"))
            if hasattr(self, "_btn_historial"):
                self._btn_historial.config(
                    text=self._t("gestion.btn_historial", "  HISTORIAL"))
            if hasattr(self, "_btn_cerrar_sesion"):
                self._btn_cerrar_sesion.config(
                    text=self._t("gestion.btn_cerrar_sesion", "  CERRAR SESIÓN"))

            primera_rol = self._opciones_rol()[0]
            self._filtro_rol.set(primera_rol)
            self._btn_rol.config(text=f"  {primera_rol}")

            primera_mes = self._opciones_mes()[0]
            self._filtro_mes.set(primera_mes)
            self._btn_mes.config(text=f"  {primera_mes}")

            for i, col in enumerate(self._columnas()):
                col_id = self.tree_usuarios["columns"][i]
                self.tree_usuarios.heading(col_id, text=col)

            self._filtrar_tabla()
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  MENÚ ÚNICO
    # ══════════════════════════════════════════════════════════════════════════
    def _cerrar_menu(self):
        if self._menu_abierto:
            try:
                self._menu_abierto.unpost()
                self._menu_abierto.destroy()
            except Exception:
                pass
            self._menu_abierto = None

    def _abrir_menu(self, btn, opciones, var, callback):
        self._cerrar_menu()
        cp = self._p
        menu = tk.Menu(self.pantalla, tearoff=0, font=("Segoe UI", 9),
                       bg=cp["card_bg"], fg=cp["texto_oscuro"],
                       activebackground=cp["verde_claro"],
                       activeforeground="#ffffff")

        def _sel(op):
            self._cerrar_menu()
            var.set(op)
            btn.config(text=f"  {op}")
            callback()

        for op in opciones:
            menu.add_command(label=op, command=lambda o=op: _sel(o))

        self._menu_abierto = menu
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        menu.post(x, y)

    # ══════════════════════════════════════════════════════════════════════════
    #  TEMA
    # ══════════════════════════════════════════════════════════════════════════
    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["gris_bg"])
            self._wrap.configure(bg=p["gris_bg"])
            self._canvas_scroll.configure(bg=p["gris_bg"])
            self._inner.configure(bg=p["gris_bg"])

            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists(): continue
                    widget.configure(bg=p[bg_k])
                    if fg_k: widget.configure(fg=p[fg_k])
                except tk.TclError: pass

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_mes):
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
                except tk.TclError: pass

            for btn, tipo in self._btns_accion:
                try:
                    if not btn.winfo_exists(): continue
                    if tipo == "verde":
                        btn.configure(bg=p["verde_btn"],
                                      activebackground=p["verde_hover"])
                except tk.TclError: pass

            s = ttk.Style()
            s.configure("U.Treeview",
                        background=p["card_bg"], foreground=p["texto_oscuro"],
                        fieldbackground=p["card_bg"])
            s.configure("U.Treeview.Heading",
                        background=p["verde"], foreground="#ffffff")
            s.map("U.Treeview",
                  background=[("selected", p["sel_tree"])],
                  foreground=[("selected", p["sel_tree_fg"])])
            self.tree_usuarios.tag_configure("par",   background=p["fila_par"])
            self.tree_usuarios.tag_configure("impar", background=p["fila_impar"])
        except tk.TclError: pass

    def _limpiar(self, event=None):
        self._cerrar_menu()
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
    #  UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["gris_bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        self._crear_scroll()

    def _crear_scroll(self):
        p = self._p
        self._wrap = tk.Frame(self.pantalla, bg=p["gris_bg"])
        self._wrap.pack(fill="both", expand=True)

        self._canvas_scroll = tk.Canvas(self._wrap, bg=p["gris_bg"],
                                        highlightthickness=0)
        sb = ttk.Scrollbar(self._wrap, orient="vertical",
                            command=self._canvas_scroll.yview)
        self._canvas_scroll.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas_scroll.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas_scroll, bg=p["gris_bg"])
        win_id = self._canvas_scroll.create_window(
            (0,0), window=self._inner, anchor="nw")

        def _resize(e):
            self._canvas_scroll.configure(
                scrollregion=self._canvas_scroll.bbox("all"))
            self._canvas_scroll.itemconfig(
                win_id, width=self._canvas_scroll.winfo_width())

        self._inner.bind("<Configure>", _resize)
        self._canvas_scroll.bind(
            "<Configure>",
            lambda e: self._canvas_scroll.itemconfig(win_id, width=e.width))
        self._canvas_scroll.bind("<MouseWheel>",
            lambda e: self._canvas_scroll.yview_scroll(
                int(-1*(e.delta/120)), "units"))
        self._canvas_scroll.bind("<Button-4>",
            lambda e: self._canvas_scroll.yview_scroll(-1, "units"))
        self._canvas_scroll.bind("<Button-5>",
            lambda e: self._canvas_scroll.yview_scroll(1, "units"))

        self._construir_contenido(self._inner)

    def _construir_contenido(self, parent):
        p = self._p
        pad = tk.Frame(parent, bg=p["gris_bg"])
        pad.pack(fill="both", expand=True, padx=10, pady=4)
        self._reg(pad, "gris_bg")

        self._construir_tarjetas(pad)

        cuerpo = tk.Frame(pad, bg=p["gris_bg"])
        cuerpo.pack(fill="both", expand=True, pady=(6,0))
        self._reg(cuerpo, "gris_bg")

        col_izq = tk.Frame(cuerpo, bg=p["gris_bg"])
        col_izq.pack(fill="both", expand=True)
        self._reg(col_izq, "gris_bg")

        self._construir_tabla_usuarios(col_izq)
        self._construir_acciones_rapidas(pad)

    # ══════════════════════════════════════════════════════════════════════════
    #  TARJETAS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_tarjetas(self, parent):
        p = self._p
        fila = tk.Frame(parent, bg=p["gris_bg"])
        fila.pack(fill="x", pady=(0,4))
        self._reg(fila, "gris_bg")

        self._tarjetas = {}

        # ── Primeras 3 tarjetas: iguales para todos ──────────────────────────
        specs_comunes = [
            ("accesos_hoy",   "accesos_hoy_titulo",
             self._t("gestion.tarjeta_accesos_hoy", "ACCESOS HOY"),
             p["verde_claro"], "accesos_hoy_sub",
             self._t("gestion.tarjeta_accesos_sub", "accesos registrados hoy")),

            ("total_alumnos", "alumnos_titulo",
             self._t("gestion.tarjeta_alumnos", "ALUMNOS"),
             p["verde_claro"], "alumnos_sub", ""),

            ("total_admins",  "profesores_titulo",
             self._t("gestion.tarjeta_profesores", "PROFESORES"),
             p["verde_claro"], "admins_sub", ""),
        ]

        # ── 4ta tarjeta: distinta según rol ──────────────────────────────────
        if self._es_super_admin():
            # Cuadro azul: ingresos de admins hoy
            spec_4ta = (
                "acc_admins_hoy", "admins_titulo",
                self._t("gestion.tarjeta_admins", "INGRESOS ADMINS"),
                p["azul"], "admins_hoy_sub",
                self._t("gestion.tarjeta_admins_sub", "accesos de admins hoy"),
            )
        else:
            # Cuadro rojo: accesos denegados
            spec_4ta = (
                "acc_denegados", "denegados_titulo",
                self._t("gestion.tarjeta_denegados", "ACCESOS DENEGADOS"),
                p["rojo"], "deny_sub",
                self._t("gestion.tarjeta_denegados_sub", "accesos denegados hoy"),
            )

        todas = specs_comunes + [spec_4ta]

        for i, (key_num, key_titulo, titulo, color_barra,
                key_sub, sub_txt) in enumerate(todas):
            card = tk.Frame(fila, bg=p["card_bg"],
                            highlightthickness=1, highlightbackground=p["borde"])
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 8, 0))
            self._reg(card, "card_bg")

            tk.Frame(card, bg=color_barra, height=3).pack(fill="x")

            body = tk.Frame(card, bg=p["card_bg"], padx=10, pady=3)
            body.pack(fill="both")
            self._reg(body, "card_bg")

            lbl_t = tk.Label(body, text=titulo,
                             font=("Segoe UI", 7, "bold"),
                             fg=p["texto_gris"], bg=p["card_bg"])
            lbl_t.pack(anchor="w")
            self._reg(lbl_t, "card_bg", "texto_gris")
            self._tarjetas[key_titulo] = lbl_t

            lbl_num = tk.Label(body, text="0",
                               font=("Segoe UI", 14, "bold"),
                               fg=p["texto_oscuro"], bg=p["card_bg"])
            lbl_num.pack(anchor="w")
            self._reg(lbl_num, "card_bg", "texto_oscuro")

            # Sub-texto con color según tipo de tarjeta
            sub_color = p["rojo_claro"] if key_num in ("acc_denegados",) else \
                        p["azul_claro"] if key_num == "acc_admins_hoy" else \
                        p["verde_claro"]
            lbl_sub = tk.Label(body, text=sub_txt,
                               font=("Segoe UI", 6),
                               fg=sub_color, bg=p["card_bg"])
            lbl_sub.pack(anchor="w")
            self._reg(lbl_sub, "card_bg")

            self._tarjetas[key_num] = lbl_num
            self._tarjetas[key_sub] = lbl_sub

    # ══════════════════════════════════════════════════════════════════════════
    #  TABLA USUARIOS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_tabla_usuarios(self, parent):
        p = self._p
        card = tk.Frame(parent, bg=p["card_bg"],
                        highlightthickness=1, highlightbackground=p["borde"])
        card.pack(fill="both", expand=True)
        self._reg(card, "card_bg")

        self._recargar_ico_flecha()

        cab = tk.Frame(card, bg=p["card_bg"])
        cab.pack(fill="x", padx=16, pady=(10,6))
        self._reg(cab, "card_bg")

        self._lbl_titulo_tabla = tk.Label(
            cab,
            text=self._t("gestion.titulo_tabla", " USUARIOS "),
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde_btn"], padx=8, pady=3)
        self._lbl_titulo_tabla.pack(side="left")
        self._reg(self._lbl_titulo_tabla, "verde_btn")

        filtros = tk.Frame(cab, bg=p["card_bg"])
        filtros.pack(side="right")
        self._reg(filtros, "card_bg")

        primera_rol = self._opciones_rol()[0]
        self._filtro_rol.set(primera_rol)
        self._btn_rol = tk.Button(
            filtros, text=f"  {primera_rol}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2",
            command=lambda: self._abrir_menu(
                self._btn_rol, self._opciones_rol(),
                self._filtro_rol, self._filtrar_tabla))
        self._btn_rol.pack(side="left", padx=(0,8))

        primera_mes = self._opciones_mes()[0]
        self._filtro_mes.set(primera_mes)
        self._btn_mes = tk.Button(
            filtros, text=f"  {primera_mes}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2",
            command=lambda: self._abrir_menu(
                self._btn_mes, self._opciones_mes(),
                self._filtro_mes, self._filtrar_tabla))
        self._btn_mes.pack(side="left")

        s = ttk.Style()
        s.configure("U.Treeview",
                    font=("Segoe UI", 8), rowheight=24,
                    background=p["card_bg"], foreground=p["texto_oscuro"],
                    fieldbackground=p["card_bg"], borderwidth=0)
        s.configure("U.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=p["verde"], foreground="#ffffff", relief="flat")
        s.map("U.Treeview",
              background=[("selected", p["sel_tree"])],
              foreground=[("selected", p["sel_tree_fg"])])

        frame_t = tk.Frame(card, bg=p["card_bg"])
        frame_t.pack(fill="both", expand=True, padx=14, pady=(0,12))
        self._reg(frame_t, "card_bg")

        col_ids   = [f"col{i}" for i in range(9)]
        col_txts  = self._columnas()
        anchos    = [80, 80, 90, 90, 110, 70, 95, 60, 50]
        centradas = {6, 7, 8}

        self.tree_usuarios = ttk.Treeview(
            frame_t, columns=col_ids, show="headings",
            height=6, style="U.Treeview")
        for i, cid in enumerate(col_ids):
            txt = col_txts[i] if i < len(col_txts) else cid
            self.tree_usuarios.heading(cid, text=txt)
            self.tree_usuarios.column(
                cid, width=anchos[i], minwidth=40, stretch=True,
                anchor="center" if i in centradas else "w")

        self.tree_usuarios.tag_configure("par",   background=p["fila_par"])
        self.tree_usuarios.tag_configure("impar", background=p["fila_impar"])
        self.tree_usuarios.tag_configure("vacio", background=p["card_bg"])
        self.tree_usuarios.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree_usuarios.pack(fill="both", expand=True)

    def _on_tree_click(self, event):
        region = self.tree_usuarios.identify("region", event.x, event.y)
        col    = self.tree_usuarios.identify_column(event.x)
        if region == "cell" and col == "#9":
            item = self.tree_usuarios.identify_row(event.y)
            if item:
                vals = self.tree_usuarios.item(item, "values")
                if vals[0] == "":
                    return
                self.app.mostrar_pantalla("editar_usuario", datos={
                    "cod_institucional": vals[0],
                    "nombre":            vals[1],
                    "apellido_paterno":  vals[2],
                    "apellido_materno":  vals[3],
                    "carrera":           vals[4],
                    "rol":               vals[5],
                    "fecha_hora":        vals[6],
                    "status":            vals[7],
                })

    def _cargar_icono(self, nombre, size=18):
        if not _PIL_OK:
            return None
        try:
            ruta = _RAIZ/"assets"/"img"/nombre
            img  = Image.open(ruta).convert("RGBA").resize((size,size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIONES RÁPIDAS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_acciones_rapidas(self, parent):
        p = self._p
        pie = tk.Frame(parent, bg=p["gris_bg"])
        pie.pack(fill="x", padx=24, pady=(6,8))
        self._reg(pie, "gris_bg")

        self._ico_agregar   = self._cargar_icono("person_add.png")
        self._ico_historial = self._cargar_icono("history.png")
        self._ico_cerrar    = self._cargar_icono("exit_to_app.png")

        self._btn_cerrar_sesion = tk.Button(
            pie,
            text=self._t("gestion.btn_cerrar_sesion", "  CERRAR SESIÓN"),
            image=self._ico_cerrar, compound="left",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg="#212121",
            activebackground="#000000", activeforeground="#ffffff",
            bd=0, padx=14, pady=10, cursor="hand2", relief="flat",
            command=self._volver)
        self._btn_cerrar_sesion.pack(side="right")

        self._btn_agregar = tk.Button(
            pie,
            text=self._t("gestion.btn_agregar", "  AGREGAR USUARIO"),
            image=self._ico_agregar, compound="left",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=14, pady=10, cursor="hand2", relief="flat",
            command=lambda: self.app.mostrar_pantalla("agregar_usuario"))
        self._btn_agregar.pack(side="left", padx=(0,8))
        self._btns_accion.append((self._btn_agregar, "verde"))

        self._btn_historial = tk.Button(
            pie,
            text=self._t("gestion.btn_historial", "  HISTORIAL"),
            image=self._ico_historial, compound="left",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg=p["verde_btn"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, padx=14, pady=10, cursor="hand2", relief="flat",
            command=lambda: self.app.mostrar_pantalla(
                "historial", {"id_rol": self._id_rol}))
        self._btn_historial.pack(side="left", padx=(0,8))
        self._btns_accion.append((self._btn_historial, "verde"))

    # ══════════════════════════════════════════════════════════════════════════
    #  DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cargar_todo(self):
        self._cargar_estadisticas()
        self._cargar_tabla_usuarios()

    def _cargar_estadisticas(self):
        p        = self._p
        usuarios = obtener_usuarios() or []
        total    = len(usuarios)
        alumnos  = sum(1 for u in usuarios if u.get("rol","") == "Alumno")
        profes   = sum(1 for u in usuarios
                       if u.get("rol","") in
                       ("Maestro", "Profesor"))

        conteos       = conteo_accesos_hoy()
        acc_hoy       = conteos.get("total", 0)
        denegados_hoy = conteos.get("denegados", 0)

        sin_reg = self._t("gestion.tarjeta_sin_registros", "Sin registros")

        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))
        self._tarjetas["accesos_hoy_sub"].config(
            text=self._t("gestion.tarjeta_accesos_sub", "accesos registrados hoy"))

        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        self._tarjetas["alumnos_sub"].config(
            text=f"{round(alumnos/total*100)}% del total" if total else sin_reg)

        self._tarjetas["total_admins"].config(text=str(profes))
        self._tarjetas["admins_sub"].config(
            text=f"{round(profes/total*100)}% del total" if total else sin_reg)

        if self._es_super_admin():
            # Contar accesos de admins hoy usando conteo_accesos_hoy
            # Si tu BD ya tiene conteos por rol, usa: conteos.get("admins", 0)
            # Si no, filtra de la lista de accesos:
            try:
                accesos = obtener_accesos() or []
                hoy = datetime.now().strftime("%Y-%m-%d")
                admins_ids = {
                    u.get("cod_institucional")
                    for u in usuarios
                    if u.get("rol","") in ("Admin", "Super Admin")
                }
                acc_admins = sum(
                    1 for a in accesos
                    if a.get("fecha","").startswith(hoy)
                    and a.get("cod_institucional") in admins_ids
                )
            except Exception:
                acc_admins = 0
            self._tarjetas["acc_admins_hoy"].config(text=str(acc_admins))
            self._tarjetas["admins_hoy_sub"].config(
                text=self._t("gestion.tarjeta_admins_sub", "accesos de admins hoy"))
        else:
            self._tarjetas["acc_denegados"].config(text=str(denegados_hoy))
            self._tarjetas["deny_sub"].config(
                text=self._t("gestion.tarjeta_denegados_sub", "accesos denegados hoy"),
                fg=p["rojo_claro"])

        self._todos_usuarios = usuarios

    def _cargar_tabla_usuarios(self):
        self._todos_usuarios = obtener_usuarios() or []
        self._filtrar_tabla()

    def _filtrar_tabla(self):
        rol_f = self._filtro_rol.get()
        mes_f = self._filtro_mes.get()
        datos = self._todos_usuarios

        # ── Filtrar por roles permitidos según quién inició sesión ───────────
        visibles = self._roles_visibles()
        datos = [u for u in datos
                 if (u.get("rol") or "").strip() in visibles]

        # ── Filtro de dropdown de rol ─────────────────────────────────────────
        sin_filtro_rol = [self._opciones_rol()[0], "Ninguno", "Rol", "All roles"]
        if rol_f and rol_f not in sin_filtro_rol:
            datos = [u for u in datos
                     if (u.get("rol") or "").lower() == rol_f.lower()]

        # ── Filtro de mes ─────────────────────────────────────────────────────
        mes_num = _MESES_NUM.get(mes_f)
        if mes_num:
            datos = [u for u in datos
                     if f"-{mes_num}-" in (u.get("fecha_registro") or "")]

        t = self.tree_usuarios
        t.delete(*t.get_children())

        sin_usuarios = self._t("gestion.sin_usuarios", "Sin usuarios registrados")
        if not datos:
            t.insert("", "end", tags=("vacio",),
                     values=("", sin_usuarios, "", "", "", "", "", "", ""))
            return

        icono_editar = self._t("gestion.icono_editar", "✏")
        for i, u in enumerate(datos):
            fecha_hora = f"{u.get('fecha_registro','')} {u.get('hora_registro','')}".strip()
            t.insert("", "end",
                tags=("par" if i % 2 == 0 else "impar",),
                values=(
                    u.get("cod_institucional", ""),
                    u.get("nombre", "—"),
                    u.get("apellido_paterno", ""),
                    u.get("apellido_materno", ""),
                    u.get("carrera", ""),
                    u.get("rol", "Alumno"),
                    fecha_hora,
                    u.get("status", "Activo"),
                    icono_editar,
                ))

    def _volver(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_gestion_real(parent, app, datos=None):
    PantallaGestion(parent, app, datos)