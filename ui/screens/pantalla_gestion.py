"""
ui/screens/pantalla_gestion.py
Rediseño según mockup — Hernández Vázquez Melany Guadalupe
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

# ── Datos de prueba (se muestran si la BD está vacía) ─────────────────────────
_USUARIOS_DEMO = [
    {"cod_institucional": "20203455", "nombre": "Melany",
     "apellido_paterno": "Suarez",    "apellido_materno": "Hernandez",
     "carrera": "Ing. Software",      "rol": "Alumno",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.",
     "status": "Activo"},
    {"cod_institucional": "20203456", "nombre": "Carlos",
     "apellido_paterno": "Cabrera",   "apellido_materno": "Alcaraz",
     "carrera": "Ing. Mecanicánico y Electricista", "rol": "Alumno",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.",
     "status": "Inactivo"},
    {"cod_institucional": "10198822", "nombre": "José",
     "apellido_paterno": "Rodriguez", "apellido_materno": "Jacobo",
     "carrera": "Ing. Mecatrónica",   "rol": "Maestro",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.",
     "status": "Activo"},
    {"cod_institucional": "20181992", "nombre": "Jesus",
     "apellido_paterno": "Salazar",   "apellido_materno": "Lopez",
     "carrera": "Ing. Tecnología Electrónicas", "rol": "Admin",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.",
     "status": "Activo"},
    {"cod_institucional": "20181992", "nombre": "Miguel",
     "apellido_paterno": "Mendoza",   "apellido_materno": "Garcia",
     "carrera": "Ing. Software",      "rol": "Super Admin",
     "fecha_registro": "2026-03-24",  "hora_registro": "8:41 p.m.",
     "status": "Activo"},
]

# ── Colores locales ────────────────────────────────────────────────────────────
_VERDE        = "#2e7d32"
_VERDE_CLARO  = "#4caf50"
_VERDE_BTN    = "#43a047"
_VERDE_HOVER  = "#388e3c"
_ROJO         = "#c62828"
_ROJO_CLARO   = "#ef5350"
_GRIS_BG      = "#f5f5f5"
_CARD_BG      = "#ffffff"
_TEXTO_OSCURO = "#1a1a1a"
_TEXTO_GRIS   = "#757575"
_BORDE        = "#e0e0e0"


class PantallaGestion:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._todos_usuarios = []
        self._filtro_rol     = tk.StringVar(value="Todos los roles")
        self._filtro_mes     = tk.StringVar(value="Mes")
        inicializar_bd()
        self._construir_ui()
        self.pantalla.after(100, self._cargar_todo)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=_GRIS_BG)
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        self._crear_scroll()

    def _crear_scroll(self):
        wrap = tk.Frame(self.pantalla, bg=_GRIS_BG)
        wrap.pack(fill="both", expand=True)

        canvas_scroll = tk.Canvas(wrap, bg=_GRIS_BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        canvas_scroll.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas_scroll, bg=_GRIS_BG)
        win_id = canvas_scroll.create_window((0, 0), window=self._inner, anchor="nw")

        def _resize(e):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
            canvas_scroll.itemconfig(win_id, width=canvas_scroll.winfo_width())

        self._inner.bind("<Configure>", _resize)
        canvas_scroll.bind("<Configure>",
                           lambda e: canvas_scroll.itemconfig(win_id, width=e.width))

        def _wheel(e):
            canvas_scroll.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas_scroll.bind_all("<MouseWheel>", _wheel)

        self._construir_contenido(self._inner)

    def _construir_contenido(self, parent):
        pad = tk.Frame(parent, bg=_GRIS_BG)
        pad.pack(fill="both", expand=True, padx=10, pady=4)

        self._construir_tarjetas(pad)

        cuerpo = tk.Frame(pad, bg=_GRIS_BG)
        cuerpo.pack(fill="both", expand=True, pady=(6, 0))

        col_izq = tk.Frame(cuerpo, bg=_GRIS_BG)
        col_izq.pack(fill="both", expand=True)

        self._construir_tabla_usuarios(col_izq)
        self._construir_acciones_rapidas(pad)

    # ══════════════════════════════════════════════════════════════════════════
    #  TARJETAS SUPERIORES
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_tarjetas(self, parent):
        fila = tk.Frame(parent, bg=_GRIS_BG)
        fila.pack(fill="x", pady=(0, 4))

        self._tarjetas = {}
        specs = [
            ("accesos_hoy",   "ACCESOS HOY",      _VERDE_CLARO, "accesos_hoy_sub"),
            ("total_alumnos", "ALUMNOS",           _VERDE_CLARO, "alumnos_sub"),
            ("total_admins",  "PROFESORES",        _VERDE_CLARO, "admins_sub"),
            ("acc_denegados", "ACCESOS DENEGADOS", _ROJO,        "deny_sub"),
        ]

        for i, (key, titulo, color_barra, key_sub) in enumerate(specs):
            card = tk.Frame(fila, bg=_CARD_BG,
                            highlightthickness=1, highlightbackground=_BORDE)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 8, 0))

            tk.Frame(card, bg=color_barra, height=3).pack(fill="x")

            body = tk.Frame(card, bg=_CARD_BG, padx=10, pady=3)
            body.pack(fill="both")

            tk.Label(body, text=titulo,
                     font=("Segoe UI", 7, "bold"),
                     fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")

            lbl_num = tk.Label(body, text="—",
                               font=("Segoe UI", 14, "bold"),
                               fg=_TEXTO_OSCURO, bg=_CARD_BG)
            lbl_num.pack(anchor="w")

            lbl_sub = tk.Label(body, text="",
                               font=("Segoe UI", 6),
                               fg=_VERDE_CLARO, bg=_CARD_BG)
            lbl_sub.pack(anchor="w")

            self._tarjetas[key]     = lbl_num
            self._tarjetas[key_sub] = lbl_sub

    # ══════════════════════════════════════════════════════════════════════════
    #  TABLA USUARIOS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_tabla_usuarios(self, parent):
        card = tk.Frame(parent, bg=_CARD_BG,
                        highlightthickness=1, highlightbackground=_BORDE)
        card.pack(fill="both", expand=True)

        cab = tk.Frame(card, bg=_CARD_BG)
        cab.pack(fill="x", padx=14, pady=(10, 6))

        tk.Label(cab, text=" USUARIOS ",
                 font=("Segoe UI", 10, "bold"),
                 fg="#ffffff", bg=_VERDE_BTN,
                 padx=8, pady=3).pack(side="left")

        filtros = tk.Frame(cab, bg=_CARD_BG)
        filtros.pack(side="right")

        roles = ["Todos los roles", "Alumno", "Maestro", "Admin", "Super Admin"]
        om_rol = tk.OptionMenu(filtros, self._filtro_rol, *roles,
                               command=lambda _: self._filtrar_tabla())
        self._estilo_optionmenu(om_rol)
        om_rol.pack(side="left", padx=(0, 6))

        meses = ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo",
                 "Junio", "Julio", "Agosto", "Septiembre",
                 "Octubre", "Noviembre", "Diciembre"]
        om_mes = tk.OptionMenu(filtros, self._filtro_mes, *meses,
                               command=lambda _: self._filtrar_tabla())
        self._estilo_optionmenu(om_mes)
        om_mes.pack(side="left")

        s = ttk.Style()
        s.configure("U.Treeview",
                    font=("Segoe UI", 8), rowheight=24,
                    background=_CARD_BG, foreground=_TEXTO_OSCURO,
                    fieldbackground=_CARD_BG, borderwidth=0)
        s.configure("U.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=_VERDE, foreground="#ffffff", relief="flat")
        s.map("U.Treeview",
              background=[("selected", "#e8f5e9")],
              foreground=[("selected", _VERDE)])

        frame_t = tk.Frame(card, bg=_CARD_BG)
        frame_t.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        sy = ttk.Scrollbar(frame_t, orient="vertical")

        cols = ("No. Inst.", "Nombre", "Ap. Paterno", "Ap. Materno",
                "Programa", "Rol", "Fecha/Hora", "Status", "Editar")

        self.tree_usuarios = ttk.Treeview(frame_t, columns=cols,
                                          show="headings", height=6,
                                          style="U.Treeview",
                                          yscrollcommand=sy.set)
        sy.config(command=self.tree_usuarios.yview)

        anchos = {
            "No. Inst.":   75,
            "Nombre":      70,
            "Ap. Paterno": 75,
            "Ap. Materno": 75,
            "Programa":    95,
            "Rol":         65,
            "Fecha/Hora":  90,
            "Status":      55,
            "Editar":      55,
        }
        for col in cols:
            self.tree_usuarios.heading(col, text=col)
            self.tree_usuarios.column(col,
                                      width=anchos.get(col, 70),
                                      minwidth=40,
                                      stretch=(col == "Programa"),
                                      anchor="center" if col in ("Status", "Editar", "Rol") else "w")

        self.tree_usuarios.tag_configure("par",   background="#f9f9f9")
        self.tree_usuarios.tag_configure("impar", background=_CARD_BG)
        self.tree_usuarios.bind("<ButtonRelease-1>", self._on_tree_click)

        sy.pack(side="right", fill="y")
        self.tree_usuarios.pack(fill="both", expand=True)

    def _on_tree_click(self, event):
        region = self.tree_usuarios.identify("region", event.x, event.y)
        col    = self.tree_usuarios.identify_column(event.x)
        if region == "cell" and col == "#9":
            item = self.tree_usuarios.identify_row(event.y)
            if item:
                vals = self.tree_usuarios.item(item, "values")
                datos_usuario = {
                    "cod_institucional": vals[0],
                    "nombre":            vals[1],
                    "apellido_paterno":  vals[2],
                    "apellido_materno":  vals[3],
                    "carrera":           vals[4],
                    "rol":               vals[5],
                    "fecha_hora":        vals[6],
                    "status":            vals[7],
                }
                self.app.mostrar_pantalla("editar_usuario", datos=datos_usuario)

    def _cargar_icono(self, nombre, size=18):
        """Carga un PNG de assets/img/ y lo redimensiona."""
        if not _PIL_OK:
            return None
        try:
            ruta = Path(__file__).resolve().parents[2] / "assets" / "img" / nombre
            img  = Image.open(ruta).convert("RGBA").resize((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIONES RÁPIDAS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_acciones_rapidas(self, parent):
        pie = tk.Frame(parent, bg=_GRIS_BG)
        pie.pack(fill="x", padx=24, pady=(6, 8))

        # Cargar iconos (guardamos referencias para evitar GC)
        self._ico_agregar  = self._cargar_icono("person_add.png")
        self._ico_historial = self._cargar_icono("history.png")
        self._ico_cerrar   = self._cargar_icono("exit_to_app.png")

        # CERRAR SESIÓN alineado a la derecha
        tk.Button(pie, text="  CERRAR SESIÓN",
                  image=self._ico_cerrar, compound="left",
                  font=("Segoe UI", 9, "bold"),
                  fg="#ffffff", bg="#212121",
                  activebackground="#000000", activeforeground="#ffffff",
                  bd=0, padx=14, pady=10,
                  cursor="hand2", relief="flat",
                  command=self._volver).pack(side="right")

        # AGREGAR USUARIO y HISTORIAL alineados a la izquierda
        for texto, icono, bg, hover, cmd in [
            ("  AGREGAR USUARIO", self._ico_agregar,  _VERDE_BTN, _VERDE_HOVER,
             lambda: self.app.mostrar_pantalla("agregar_usuario")),
            ("  HISTORIAL",         self._ico_historial, _VERDE_BTN, _VERDE_HOVER,
             lambda: self.app.mostrar_pantalla("historial")),
        ]:
            tk.Button(pie, text=texto,
                      image=icono, compound="left",
                      font=("Segoe UI", 9, "bold"),
                      fg="#ffffff", bg=bg,
                      activebackground=hover, activeforeground="#ffffff",
                      bd=0, padx=14, pady=10,
                      cursor="hand2", relief="flat",
                      command=cmd).pack(side="left", padx=(0, 8))

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPER — OptionMenu estilizado
    # ══════════════════════════════════════════════════════════════════════════
    def _estilo_optionmenu(self, om):
        om.config(font=("Segoe UI", 8), bg=_GRIS_BG, fg=_TEXTO_OSCURO,
                  relief="flat", bd=0, highlightthickness=1,
                  highlightbackground=_BORDE, activebackground=_BORDE,
                  cursor="hand2", pady=3, indicatoron=True)
        om["menu"].config(font=("Segoe UI", 9), bg=_CARD_BG,
                          activebackground=_VERDE_CLARO,
                          activeforeground="#ffffff")

    # ══════════════════════════════════════════════════════════════════════════
    #  CARGA Y FILTRADO DE DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cargar_todo(self):
        self._cargar_estadisticas()
        self._cargar_tabla_usuarios()

    def _cargar_estadisticas(self):
        bd_usuarios = obtener_usuarios()
        usuarios    = bd_usuarios if bd_usuarios else _USUARIOS_DEMO
        accesos     = obtener_accesos(limite=1000)
        hoy         = datetime.now().strftime("%Y-%m-%d")

        total   = len(usuarios)
        alumnos = sum(1 for u in usuarios if u["rol"] == "Alumno")
        admins  = sum(1 for u in usuarios
                      if u["rol"] in ("Admin", "SuperAdmin",
                                      "SuperUsuario", "Profesor", "Maestro"))
        acc_hoy_lista = [a for a in accesos if a["fecha"] == hoy]
        acc_hoy       = len(acc_hoy_lista)

        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))
        self._tarjetas["accesos_hoy_sub"].config(text="↑ +18% vs ayer")
        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        pct_alumnos = f"{round(alumnos/total*100)}% del total" if total else "0%"
        self._tarjetas["alumnos_sub"].config(text=pct_alumnos)
        self._tarjetas["total_admins"].config(text=str(admins))
        pct_admins = f"{round(admins/total*100)}% del total" if total else "0%"
        self._tarjetas["admins_sub"].config(text=pct_admins)
        self._tarjetas["acc_denegados"].config(text="0")
        self._tarjetas["deny_sub"].config(text="↑ 3 más que ayer", fg=_ROJO_CLARO)

        self._todos_usuarios = usuarios

    def _cargar_tabla_usuarios(self):
        bd = obtener_usuarios()
        self._todos_usuarios = bd if bd else _USUARIOS_DEMO
        self._filtrar_tabla()

    def _filtrar_tabla(self):
        rol_f = self._filtro_rol.get()
        mes_f = self._filtro_mes.get()
        datos = self._todos_usuarios

        if rol_f and rol_f != "Todos los roles":
            datos = [u for u in datos
                     if (u.get("rol") or "").lower() == rol_f.lower()]

        meses_num = {
            "Enero": "01", "Febrero": "02", "Marzo": "03",
            "Abril": "04", "Mayo": "05", "Junio": "06",
            "Julio": "07", "Agosto": "08", "Septiembre": "09",
            "Octubre": "10", "Noviembre": "11", "Diciembre": "12",
        }
        if mes_f and mes_f != "Mes" and mes_f in meses_num:
            m = meses_num[mes_f]
            datos = [u for u in datos
                     if f"-{m}-" in (u.get("fecha_registro") or "")]

        t = self.tree_usuarios
        t.delete(*t.get_children())
        for i, u in enumerate(datos):
            fecha_hora = (f"{u.get('fecha_registro', '')} "
                          f"{u.get('hora_registro', '')}").strip()
            tags = ("par" if i % 2 == 0 else "impar",)
            t.insert("", "end", tags=tags,
                     values=(u.get("cod_institucional", ""),
                             u.get("nombre", "—"),
                             u.get("apellido_paterno", ""),
                             u.get("apellido_materno", ""),
                             u.get("carrera", ""),
                             u.get("rol", "Alumno"),
                             fecha_hora,
                             u.get("status", "Activo"),
                             "✏"))

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _volver(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_gestion_real(parent, app):
    PantallaGestion(parent, app)