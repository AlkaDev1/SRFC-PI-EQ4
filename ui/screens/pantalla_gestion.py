"""
ui/screens/pantalla_gestion.py
Pantalla de Gestión — tabs: Estadísticas | Usuarios | Historial
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from core.database import obtener_usuarios, obtener_accesos, inicializar_bd


class PantallaGestion:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._todos_usuarios = []
        inicializar_bd()
        self._construir_ui()
        # Cargar datos después de que tkinter procese el layout
        self.pantalla.after(100, self._cargar_todo)

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=PALETA["page_bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        # Barra superior
        barra = tk.Frame(self.pantalla, bg=PALETA["page_bg"], pady=8)
        barra.pack(fill="x", padx=20)

        tk.Button(barra, text="← VOLVER",
                  font=("Segoe UI", 11, "bold"),
                  fg=PALETA["topbar_btn_fg"], bg=PALETA["topbar_btn_bg"],
                  activebackground=PALETA["topbar_btn_hover"],
                  bd=0, padx=15, pady=8, cursor="hand2", relief="flat",
                  command=self._volver).pack(side="left")

        tk.Label(barra, text="GESTIÓN DEL SISTEMA",
                 font=("Segoe UI", 14, "bold"),
                 fg=PALETA["topbar_sistema_fg"],
                 bg=PALETA["page_bg"]).pack(side="left", padx=20)

        tk.Button(barra, text="+ REGISTRAR USUARIO",
                  font=("Segoe UI", 11, "bold"),
                  fg=PALETA["boton_fg"], bg=PALETA["boton_bg"],
                  activebackground=PALETA["boton_hover"],
                  bd=0, padx=15, pady=8, cursor="hand2", relief="flat",
                  command=lambda: self.app.mostrar_pantalla("registro")
                  ).pack(side="right")

        tk.Button(barra, text="↺ ACTUALIZAR",
                  font=("Segoe UI", 10),
                  fg=PALETA["topbar_btn_fg"], bg=PALETA["topbar_btn_bg"],
                  activebackground=PALETA["topbar_btn_hover"],
                  bd=0, padx=12, pady=8, cursor="hand2", relief="flat",
                  command=self._cargar_todo).pack(side="right", padx=(0, 8))

        # Tabs
        s = ttk.Style()
        s.configure("G.TNotebook", background=PALETA["page_bg"], borderwidth=0)
        s.configure("G.TNotebook.Tab",
                    font=("Segoe UI", 10, "bold"), padding=(16, 8),
                    background=PALETA["ghost_bg"], foreground="#666666")
        s.map("G.TNotebook.Tab",
              background=[("selected", PALETA["page_bg"])],
              foreground=[("selected", PALETA["topbar_sistema_fg"])])

        self.nb = ttk.Notebook(self.pantalla, style="G.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.tab_stats    = tk.Frame(self.nb, bg=PALETA["page_bg"])
        self.tab_usuarios = tk.Frame(self.nb, bg=PALETA["page_bg"])
        self.tab_accesos  = tk.Frame(self.nb, bg=PALETA["page_bg"])

        self.nb.add(self.tab_stats,    text="  📊  Estadísticas  ")
        self.nb.add(self.tab_usuarios, text="  👥  Usuarios  ")
        self.nb.add(self.tab_accesos,  text="  🕐  Historial  ")

        self._construir_tab_stats()
        self._construir_tab_usuarios()
        self._construir_tab_accesos()

    # ══════════════════════════════════════════
    #  Tab Estadísticas
    # ══════════════════════════════════════════
    def _construir_tab_stats(self):
        pad = tk.Frame(self.tab_stats, bg=PALETA["page_bg"])
        pad.pack(fill="both", expand=True, padx=24, pady=20)

        # Tarjetas
        fila = tk.Frame(pad, bg=PALETA["page_bg"])
        fila.pack(fill="x", pady=(0, 20))

        self._tarjetas = {}
        tarjetas = [
            ("total_usuarios", "Total usuarios",    "#333333"),
            ("total_alumnos",  "Alumnos",           PALETA["topbar_sistema_fg"]),
            ("total_admins",   "Administradores",   "#1565C0"),
            ("con_biometria",  "Con biometría",     "#2e7d32"),
            ("sin_biometria",  "Sin biometría",     "#c62828"),
            ("accesos_hoy",    "Accesos hoy",       "#6A1B9A"),
        ]

        for key, titulo, color in tarjetas:
            card = tk.Frame(fila, bg=PALETA["ghost_bg"], padx=18, pady=14)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(card, text=titulo, font=("Segoe UI", 9),
                     fg="#888888", bg=PALETA["ghost_bg"]).pack(anchor="w")
            lbl = tk.Label(card, text="—", font=("Segoe UI", 26, "bold"),
                           fg=color, bg=PALETA["ghost_bg"])
            lbl.pack(anchor="w")
            self._tarjetas[key] = lbl

        tk.Frame(pad, bg=PALETA["topbar_separador"], height=1).pack(fill="x", pady=(0, 12))

        tk.Label(pad, text="Últimos accesos",
                 font=("Segoe UI", 11, "bold"),
                 fg=PALETA["topbar_sistema_fg"],
                 bg=PALETA["page_bg"]).pack(anchor="w", pady=(0, 6))

        self.tree_stats = self._crear_tree(pad,
            ("Código", "Nombre", "Fecha", "Hora"), height=7)
        self.tree_stats.pack(fill="both", expand=True)

    # ══════════════════════════════════════════
    #  Tab Usuarios
    # ══════════════════════════════════════════
    def _construir_tab_usuarios(self):
        pad = tk.Frame(self.tab_usuarios, bg=PALETA["page_bg"])
        pad.pack(fill="both", expand=True, padx=24, pady=16)

        # Buscador
        bb = tk.Frame(pad, bg=PALETA["page_bg"])
        bb.pack(fill="x", pady=(0, 10))

        tk.Label(bb, text="Buscar:", font=("Segoe UI", 10),
                 fg="#444", bg=PALETA["page_bg"]).pack(side="left", padx=(0, 8))

        self.var_busq = tk.StringVar()
        self.var_busq.trace("w", lambda *_: self._filtrar())

        tk.Entry(bb, textvariable=self.var_busq,
                 font=("Segoe UI", 10), bg=PALETA["ghost_bg"],
                 relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=PALETA["topbar_separador"],
                 highlightcolor=PALETA["topbar_sistema_fg"],
                 width=28).pack(side="left", ipady=5, padx=(0, 8))

        tk.Button(bb, text="✕", font=("Segoe UI", 9),
                  fg=PALETA["topbar_btn_fg"], bg=PALETA["topbar_btn_bg"],
                  bd=0, padx=8, pady=5, cursor="hand2", relief="flat",
                  command=lambda: self.var_busq.set("")).pack(side="left")

        self.lbl_count_usr = tk.Label(bb, text="", font=("Segoe UI", 9),
                                      fg="#888", bg=PALETA["page_bg"])
        self.lbl_count_usr.pack(side="right")

        self.tree_usuarios = self._crear_tree(pad,
            ("Código", "Nombre", "Rol", "Carrera",
             "Grado", "Grupo", "Biometría", "Estado"))
        self.tree_usuarios.pack(fill="both", expand=True)

    # ══════════════════════════════════════════
    #  Tab Historial
    # ══════════════════════════════════════════
    def _construir_tab_accesos(self):
        pad = tk.Frame(self.tab_accesos, bg=PALETA["page_bg"])
        pad.pack(fill="both", expand=True, padx=24, pady=16)

        cab = tk.Frame(pad, bg=PALETA["page_bg"])
        cab.pack(fill="x", pady=(0, 10))

        tk.Label(cab, text="Últimos 100 accesos",
                 font=("Segoe UI", 11, "bold"),
                 fg=PALETA["topbar_sistema_fg"],
                 bg=PALETA["page_bg"]).pack(side="left")

        self.lbl_count_acc = tk.Label(cab, text="", font=("Segoe UI", 9),
                                      fg="#888", bg=PALETA["page_bg"])
        self.lbl_count_acc.pack(side="right")

        self.tree_accesos = self._crear_tree(pad,
            ("ID", "Código", "Nombre", "Fecha", "Hora"))
        self.tree_accesos.pack(fill="both", expand=True)

    # ══════════════════════════════════════════
    #  Tabla reutilizable
    # ══════════════════════════════════════════
    def _crear_tree(self, parent, cols, height=12):
        s = ttk.Style()
        s.configure("G.Treeview",
                    font=("Segoe UI", 10), rowheight=30,
                    background=PALETA["page_bg"], foreground="#333",
                    fieldbackground=PALETA["page_bg"], borderwidth=0)
        s.configure("G.Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background=PALETA["header_bg"],
                    foreground="#ffffff", relief="flat")
        s.map("G.Treeview",
              background=[("selected", PALETA["topbar_btn_bg"])],
              foreground=[("selected", PALETA["topbar_sistema_fg"])])

        frame = tk.Frame(parent, bg=PALETA["page_bg"])
        sy = ttk.Scrollbar(frame, orient="vertical")
        sx = ttk.Scrollbar(frame, orient="horizontal")

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            height=height, style="G.Treeview",
                            yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.config(command=tree.yview)
        sx.config(command=tree.xview)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=max(90, len(col)*12), minwidth=60)

        sy.pack(side="right",  fill="y")
        sx.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.tag_configure("par",   background=PALETA["row_a"])
        tree.tag_configure("impar", background=PALETA["row_b"])

        # Guardar referencia al tree en el frame para acceder desde fuera
        frame._tree = tree
        return frame

    # ══════════════════════════════════════════
    #  Carga de datos
    # ══════════════════════════════════════════
    def _cargar_todo(self):
        self._cargar_estadisticas()
        self._cargar_usuarios()
        self._cargar_accesos()

    def _cargar_estadisticas(self):
        usuarios = obtener_usuarios()
        accesos  = obtener_accesos(limite=7)

        total   = len(usuarios)
        alumnos = sum(1 for u in usuarios if u["rol"] == "Alumno")
        admins  = sum(1 for u in usuarios
                      if u["rol"] in ("Admin", "SuperAdmin", "SuperUsuario"))
        con_bio = sum(1 for u in usuarios if u["tiene_encoding"])
        sin_bio = total - con_bio
        hoy     = datetime.now().strftime("%Y-%m-%d")
        acc_hoy = sum(1 for a in obtener_accesos(limite=1000) if a["fecha"] == hoy)

        self._tarjetas["total_usuarios"].config(text=str(total))
        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        self._tarjetas["total_admins"].config(text=str(admins))
        self._tarjetas["con_biometria"].config(text=str(con_bio))
        self._tarjetas["sin_biometria"].config(text=str(sin_bio))
        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))

        t = self.tree_stats._tree
        t.delete(*t.get_children())
        for i, a in enumerate(accesos):
            t.insert("", "end", tags=("par" if i%2==0 else "impar",),
                     values=(a["cod_institucional"], a["nombre"] or "—",
                             a["fecha"], a["hora"]))

    def _cargar_usuarios(self):
        self._todos_usuarios = obtener_usuarios()
        self._filtrar()

    def _filtrar(self):
        busq = self.var_busq.get().lower().strip()
        t = self.tree_usuarios._tree
        t.delete(*t.get_children())

        data = [u for u in self._todos_usuarios
                if not busq or
                busq in u["cod_institucional"].lower() or
                busq in (u["primer_nombre"] or "").lower() or
                busq in (u["apellido_paterno"] or "").lower() or
                busq in (u["rol"] or "").lower() or
                busq in (u["carrera"] or "").lower()]

        for i, u in enumerate(data):
            nombre = " ".join(filter(None, [
                u["primer_nombre"], u.get("segundo_nombre"),
                u["apellido_paterno"], u.get("apellido_materno")]))
            bio    = "✓ Sí" if u["tiene_encoding"] else "✗ No"
            estado = "Activo" if u["estado"] else "Inactivo"
            tag    = "par" if i % 2 == 0 else "impar"
            t.insert("", "end", tags=(tag,), values=(
                u["cod_institucional"], nombre,
                u["rol"] or "—", u["carrera"] or "—",
                u["grado"] or "—", u["grupo"] or "—",
                bio, estado))

        self.lbl_count_usr.config(text=f"{len(data)} usuario(s)")

    def _cargar_accesos(self):
        accesos = obtener_accesos(limite=100)
        t = self.tree_accesos._tree
        t.delete(*t.get_children())
        for i, a in enumerate(accesos):
            t.insert("", "end", tags=("par" if i%2==0 else "impar",),
                     values=(a["id_acceso"], a["cod_institucional"],
                             a["nombre"] or "—", a["fecha"], a["hora"]))
        self.lbl_count_acc.config(text=f"{len(accesos)} registro(s)")

    # ══════════════════════════════════════════
    #  Navegación
    # ══════════════════════════════════════════
    def _volver(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_gestion_real(parent, app):
    PantallaGestion(parent, app)