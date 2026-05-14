"""
ui/screens/pantalla_gestion.py
Rediseño según mockup — Hernández Vázquez Melany Guadalupe

CAMBIOS v2:
  - Botón HISTORIAL pasa {"id_rol": 2} a mostrar_pantalla()
    para que historial_accesos sepa regresar a "gestion_real" al cerrar
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
                            inicializar_bd)

_RAIZ = Path(__file__).resolve().parents[2]

_USUARIOS_DEMO = [
    {"cod_institucional": "20203455", "nombre": "Melany",
     "apellido_paterno": "Suarez",    "apellido_materno": "Hernandez",
     "carrera": "Ing. Software",      "rol": "Alumno",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.", "status": "Activo"},
    {"cod_institucional": "20203456", "nombre": "Carlos",
     "apellido_paterno": "Cabrera",   "apellido_materno": "Alcaraz",
     "carrera": "Ing. Mecanicánico y Electricista", "rol": "Alumno",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.", "status": "Inactivo"},
    {"cod_institucional": "10198822", "nombre": "José",
     "apellido_paterno": "Rodriguez", "apellido_materno": "Jacobo",
     "carrera": "Ing. Mecatrónica",   "rol": "Maestro",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.", "status": "Activo"},
    {"cod_institucional": "20181992", "nombre": "Jesus",
     "apellido_paterno": "Salazar",   "apellido_materno": "Lopez",
     "carrera": "Ing. Tecnología Electrónicas", "rol": "Admin",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.", "status": "Activo"},
    {"cod_institucional": "20181992", "nombre": "Miguel",
     "apellido_paterno": "Mendoza",   "apellido_materno": "Garcia",
     "carrera": "Ing. Software",      "rol": "Super Admin",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.", "status": "Activo"},
]

_C = {
    "gris_bg":      "#f5f5f5",
    "card_bg":      "#ffffff",
    "texto_oscuro": "#1a1a1a",
    "texto_gris":   "#757575",
    "borde":        "#e0e0e0",
    "verde":        "#2e7d32",
    "verde_claro":  "#4caf50",
    "verde_btn":    "#43a047",
    "verde_hover":  "#388e3c",
    "rojo":         "#c62828",
    "rojo_claro":   "#ef5350",
    "fila_par":     "#f9f9f9",
    "fila_impar":   "#ffffff",
    "sel_tree":     "#e8f5e9",
    "sel_tree_fg":  "#2e7d32",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#e0e0e0",
    "filtro_fg":    "#1a1a1a",
    "flecha_img":   "arrow_circle_black.png",
}

_O = {
    "gris_bg":      "#071E07",
    "card_bg":      "#0d2a0d",
    "texto_oscuro": "#d0f0d0",
    "texto_gris":   "#7aaa7a",
    "borde":        "#1a3a1a",
    "verde":        "#2D531A",
    "verde_claro":  "#477023",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "rojo":         "#7f1d1d",
    "rojo_claro":   "#f87171",
    "fila_par":     "#0d2a0d",
    "fila_impar":   "#071E07",
    "sel_tree":     "#1a3a1a",
    "sel_tree_fg":  "#4ade80",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#1a3a1a",
    "filtro_fg":    "#d0f0d0",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaGestion:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._p     = _paleta(app)
        self._todos_usuarios      = []
        self._filtro_rol          = tk.StringVar(value="Rol")
        self._filtro_mes          = tk.StringVar(value="Mes")
        self._ico_flecha          = None
        self._widgets_repintables = []
        self._btns_accion         = []
        inicializar_bd()
        self._construir_ui()
        self.pantalla.after(100, self._cargar_todo)

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════════════════════════════════════
    #  SOPORTE DE TEMA
    # ══════════════════════════════════════════════════════════════════════════
    def _on_tema_cambio(self, paleta_nueva: dict):
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
                    if not widget.winfo_exists():
                        continue
                    widget.configure(bg=p[bg_k])
                    if fg_k:
                        widget.configure(fg=p[fg_k])
                except tk.TclError:
                    pass

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_mes):
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
                except tk.TclError:
                    pass

            for btn, tipo in self._btns_accion:
                try:
                    if not btn.winfo_exists():
                        continue
                    if tipo == "verde":
                        btn.configure(bg=p["verde_btn"],
                                      activebackground=p["verde_hover"])
                except tk.TclError:
                    pass

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

        self._canvas_scroll = tk.Canvas(self._wrap, bg=p["gris_bg"], highlightthickness=0)
        sb = ttk.Scrollbar(self._wrap, orient="vertical", command=self._canvas_scroll.yview)
        self._canvas_scroll.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        self._canvas_scroll.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas_scroll, bg=p["gris_bg"])
        win_id = self._canvas_scroll.create_window((0, 0), window=self._inner, anchor="nw")

        def _resize(e):
            self._canvas_scroll.configure(scrollregion=self._canvas_scroll.bbox("all"))
            self._canvas_scroll.itemconfig(win_id, width=self._canvas_scroll.winfo_width())

        self._inner.bind("<Configure>", _resize)
        self._canvas_scroll.bind("<Configure>",
                           lambda e: self._canvas_scroll.itemconfig(win_id, width=e.width))
        self._canvas_scroll.bind_all("<MouseWheel>",
                           lambda e: self._canvas_scroll.yview_scroll(
                               int(-1 * (e.delta / 120)), "units"))

        self._construir_contenido(self._inner)

    def _construir_contenido(self, parent):
        p = self._p
        pad = tk.Frame(parent, bg=p["gris_bg"])
        pad.pack(fill="both", expand=True, padx=10, pady=4)
        self._reg(pad, "gris_bg")

        self._construir_tarjetas(pad)

        cuerpo = tk.Frame(pad, bg=p["gris_bg"])
        cuerpo.pack(fill="both", expand=True, pady=(6, 0))
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
        fila.pack(fill="x", pady=(0, 4))
        self._reg(fila, "gris_bg")

        self._tarjetas = {}
        specs = [
            ("accesos_hoy",   "ACCESOS HOY",      p["verde_claro"], "accesos_hoy_sub"),
            ("total_alumnos", "ALUMNOS",           p["verde_claro"], "alumnos_sub"),
            ("total_admins",  "PROFESORES",        p["verde_claro"], "admins_sub"),
            ("acc_denegados", "ACCESOS DENEGADOS", p["rojo"],        "deny_sub"),
        ]

        for i, (key, titulo, color_barra, key_sub) in enumerate(specs):
            card = tk.Frame(fila, bg=p["card_bg"],
                            highlightthickness=1, highlightbackground=p["borde"])
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 8, 0))
            self._reg(card, "card_bg")

            tk.Frame(card, bg=color_barra, height=3).pack(fill="x")

            body = tk.Frame(card, bg=p["card_bg"], padx=10, pady=3)
            body.pack(fill="both")
            self._reg(body, "card_bg")

            lbl_t = tk.Label(body, text=titulo, font=("Segoe UI", 7, "bold"),
                             fg=p["texto_gris"], bg=p["card_bg"])
            lbl_t.pack(anchor="w")
            self._reg(lbl_t, "card_bg", "texto_gris")

            lbl_num = tk.Label(body, text="—", font=("Segoe UI", 14, "bold"),
                               fg=p["texto_oscuro"], bg=p["card_bg"])
            lbl_num.pack(anchor="w")
            self._reg(lbl_num, "card_bg", "texto_oscuro")

            lbl_sub = tk.Label(body, text="", font=("Segoe UI", 6),
                               fg=p["verde_claro"], bg=p["card_bg"])
            lbl_sub.pack(anchor="w")
            self._reg(lbl_sub, "card_bg", "verde_claro")

            self._tarjetas[key]     = lbl_num
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
        cab.pack(fill="x", padx=16, pady=(10, 6))
        self._reg(cab, "card_bg")

        lbl_u = tk.Label(cab, text=" USUARIOS ", font=("Segoe UI", 10, "bold"),
                         fg="#ffffff", bg=p["verde_btn"], padx=8, pady=3)
        lbl_u.pack(side="left")
        self._reg(lbl_u, "verde_btn")

        filtros = tk.Frame(cab, bg=p["card_bg"])
        filtros.pack(side="right")
        self._reg(filtros, "card_bg")

        def _abrir_menu_rol(event, btn):
            cp = self._p
            menu = tk.Menu(filtros, tearoff=0, font=("Segoe UI", 9),
                           bg=cp["card_bg"], fg=cp["texto_oscuro"],
                           activebackground=cp["verde_claro"],
                           activeforeground="#ffffff")
            for op in ["Rol", "Alumno", "Maestro", "Admin", "Super Admin"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._filtro_rol.set(o),
                                          btn.config(text=f"  {o}"),
                                          self._filtrar_tabla()])
            menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

        self._btn_rol = tk.Button(filtros, text="  Rol",
                            image=self._ico_flecha, compound="right",
                            font=("Segoe UI", 9, "bold"),
                            fg=p["filtro_fg"], bg=p["filtro_bg"],
                            activebackground=p["borde"],
                            relief="flat", bd=0, padx=8, pady=5,
                            highlightthickness=1, highlightbackground=p["filtro_borde"],
                            cursor="hand2")
        self._btn_rol.bind("<Button-1>", lambda e: _abrir_menu_rol(e, self._btn_rol))
        self._btn_rol.pack(side="left", padx=(0, 8))
        self._reg(self._btn_rol, "filtro_bg", "filtro_fg")

        def _abrir_menu_mes(event, btn):
            cp = self._p
            menu = tk.Menu(filtros, tearoff=0, font=("Segoe UI", 9),
                           bg=cp["card_bg"], fg=cp["texto_oscuro"],
                           activebackground=cp["verde_claro"],
                           activeforeground="#ffffff")
            for op in ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo",
                       "Junio", "Julio", "Agosto", "Septiembre",
                       "Octubre", "Noviembre", "Diciembre"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._filtro_mes.set(o),
                                          btn.config(text=f"  {o}"),
                                          self._filtrar_tabla()])
            menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

        self._btn_mes = tk.Button(filtros, text="  Mes",
                            image=self._ico_flecha, compound="right",
                            font=("Segoe UI", 9, "bold"),
                            fg=p["filtro_fg"], bg=p["filtro_bg"],
                            activebackground=p["borde"],
                            relief="flat", bd=0, padx=8, pady=5,
                            highlightthickness=1, highlightbackground=p["filtro_borde"],
                            cursor="hand2")
        self._btn_mes.bind("<Button-1>", lambda e: _abrir_menu_mes(e, self._btn_mes))
        self._btn_mes.pack(side="left")
        self._reg(self._btn_mes, "filtro_bg", "filtro_fg")

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
        frame_t.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self._reg(frame_t, "card_bg")

        cols = ("No. Inst.", "Nombre", "Ap. Paterno", "Ap. Materno",
                "Programa", "Rol", "Fecha/Hora", "Status", "Editar")

        self.tree_usuarios = ttk.Treeview(frame_t, columns=cols, show="headings",
                                          height=6, style="U.Treeview")
        anchos = {
            "No. Inst.":   80, "Nombre":      80, "Ap. Paterno": 90,
            "Ap. Materno": 90, "Programa":   110, "Rol":         70,
            "Fecha/Hora":  95, "Status":      60, "Editar":      50,
        }
        centradas = {"Status", "Editar", "Rol"}
        for col in cols:
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(
                col,
                width=anchos.get(col, 80), minwidth=40, stretch=True,
                anchor="center" if col in centradas else "w")

        self.tree_usuarios.tag_configure("par",   background=p["fila_par"])
        self.tree_usuarios.tag_configure("impar", background=p["fila_impar"])
        self.tree_usuarios.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree_usuarios.pack(fill="both", expand=True)

    def _on_tree_click(self, event):
        region = self.tree_usuarios.identify("region", event.x, event.y)
        col    = self.tree_usuarios.identify_column(event.x)
        if region == "cell" and col == "#9":
            item = self.tree_usuarios.identify_row(event.y)
            if item:
                vals = self.tree_usuarios.item(item, "values")
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
            ruta = _RAIZ / "assets" / "img" / nombre
            img  = Image.open(ruta).convert("RGBA").resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIONES RÁPIDAS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_acciones_rapidas(self, parent):
        p = self._p
        pie = tk.Frame(parent, bg=p["gris_bg"])
        pie.pack(fill="x", padx=24, pady=(6, 8))
        self._reg(pie, "gris_bg")

        self._ico_agregar   = self._cargar_icono("person_add.png")
        self._ico_historial = self._cargar_icono("history.png")
        self._ico_cerrar    = self._cargar_icono("exit_to_app.png")

        tk.Button(pie, text="  CERRAR SESIÓN",
                  image=self._ico_cerrar, compound="left",
                  font=("Segoe UI", 9, "bold"),
                  fg="#ffffff", bg="#212121",
                  activebackground="#000000", activeforeground="#ffffff",
                  bd=0, padx=14, pady=10, cursor="hand2", relief="flat",
                  command=self._volver).pack(side="right")

        for texto, icono, cmd in [
            ("  AGREGAR USUARIO", self._ico_agregar,
             lambda: self.app.mostrar_pantalla("agregar_usuario")),
            # ── FIX: pasar id_rol=2 para que historial regrese a gestion_real ──
            ("  HISTORIAL", self._ico_historial,
             lambda: self.app.mostrar_pantalla("historial", {"id_rol": 2})),
        ]:
            btn = tk.Button(pie, text=texto,
                            image=icono, compound="left",
                            font=("Segoe UI", 9, "bold"),
                            fg="#ffffff", bg=p["verde_btn"],
                            activebackground=p["verde_hover"],
                            activeforeground="#ffffff",
                            bd=0, padx=14, pady=10,
                            cursor="hand2", relief="flat",
                            command=cmd)
            btn.pack(side="left", padx=(0, 8))
            self._btns_accion.append((btn, "verde"))

    # ══════════════════════════════════════════════════════════════════════════
    #  DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cargar_todo(self):
        self._cargar_estadisticas()
        self._cargar_tabla_usuarios()

    def _cargar_estadisticas(self):
        p = self._p
        bd_usuarios = obtener_usuarios()
        usuarios    = bd_usuarios if bd_usuarios else _USUARIOS_DEMO
        accesos     = obtener_accesos(limite=1000)
        hoy         = datetime.now().strftime("%Y-%m-%d")

        total   = len(usuarios)
        alumnos = sum(1 for u in usuarios if u.get("rol", "") == "Alumno")
        admins  = sum(1 for u in usuarios
                      if u.get("rol", "") in ("Admin", "SuperAdmin", "SuperUsuario",
                                              "Profesor", "Maestro"))
        acc_hoy = len([a for a in accesos if a.get("fecha") == hoy])

        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))
        self._tarjetas["accesos_hoy_sub"].config(text="↑ +18% vs ayer")
        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        self._tarjetas["alumnos_sub"].config(
            text=f"{round(alumnos/total*100)}% del total" if total else "0%")
        self._tarjetas["total_admins"].config(text=str(admins))
        self._tarjetas["admins_sub"].config(
            text=f"{round(admins/total*100)}% del total" if total else "0%")
        self._tarjetas["acc_denegados"].config(text="0")
        self._tarjetas["deny_sub"].config(text="↑ 3 más que ayer", fg=p["rojo_claro"])
        self._todos_usuarios = usuarios

    def _cargar_tabla_usuarios(self):
        bd = obtener_usuarios()
        self._todos_usuarios = bd if bd else _USUARIOS_DEMO
        self._filtrar_tabla()

    def _filtrar_tabla(self):
        rol_f = self._filtro_rol.get()
        mes_f = self._filtro_mes.get()
        datos = self._todos_usuarios

        if rol_f and rol_f != "Rol":
            datos = [u for u in datos if (u.get("rol") or "").lower() == rol_f.lower()]

        meses_num = {
            "Enero":"01","Febrero":"02","Marzo":"03","Abril":"04",
            "Mayo":"05","Junio":"06","Julio":"07","Agosto":"08",
            "Septiembre":"09","Octubre":"10","Noviembre":"11","Diciembre":"12",
        }
        if mes_f and mes_f != "Mes" and mes_f in meses_num:
            m = meses_num[mes_f]
            datos = [u for u in datos if f"-{m}-" in (u.get("fecha_registro") or "")]

        t = self.tree_usuarios
        t.delete(*t.get_children())
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
                    "✏",
                ))

    def _volver(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_gestion_real(parent, app):
    PantallaGestion(parent, app)