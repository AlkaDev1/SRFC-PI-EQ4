"""
ui/screens/pantalla_gestion.py
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from core.database import (listar_usuarios as obtener_usuarios,listar_accesos as obtener_accesos,inicializar_bd)

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
        self._todos_usuarios   = []
        self._datos_accesos    = []
        self._filtro_rol       = tk.StringVar(value="Todos los roles")
        self._filtro_anio      = tk.StringVar(value=str(datetime.now().year))
        inicializar_bd()
        self._construir_ui()
        self.pantalla.after(100, self._cargar_todo)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=_GRIS_BG)
        self.pantalla.pack(fill="both", expand=True)

        # Encabezado institucional
        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        # Área scrollable
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
        canvas_scroll.bind("<Configure>", lambda e: canvas_scroll.itemconfig(
            win_id, width=e.width))

        # Mousewheel
        def _wheel(e):
            canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas_scroll.bind_all("<MouseWheel>", _wheel)

        self._construir_contenido(self._inner)

    def _construir_contenido(self, parent):
        pad = tk.Frame(parent, bg=_GRIS_BG)
        pad.pack(fill="both", expand=True, padx=20, pady=16)

        # ── Fila de tarjetas superiores ────────────────────────────────────────
        self._construir_tarjetas(pad)

        # ── Cuerpo: columna izquierda + columna derecha ────────────────────────
        cuerpo = tk.Frame(pad, bg=_GRIS_BG)
        cuerpo.pack(fill="both", expand=True, pady=(14, 0))
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)

        col_izq = tk.Frame(cuerpo, bg=_GRIS_BG)
        col_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        col_der = tk.Frame(cuerpo, bg=_GRIS_BG)
        col_der.grid(row=0, column=1, sticky="nsew")

        self._construir_historial(col_izq)
        self._construir_grafica(col_izq)

        self._construir_distribucion(col_der)
        self._construir_usuarios_registrados(col_der)
        self._construir_acciones_rapidas(col_der)

    # ══════════════════════════════════════════════════════════════════════════
    #  TARJETAS SUPERIORES
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_tarjetas(self, parent):
        fila = tk.Frame(parent, bg=_GRIS_BG)
        fila.pack(fill="x")

        self._tarjetas = {}
        specs = [
            ("accesos_hoy",  "ACCESOS HOY",         _VERDE_CLARO, "accesos_hoy_sub"),
            ("total_alumnos","ALUMNOS",              _VERDE_CLARO, "alumnos_sub"),
            ("total_admins", "PROFESORES",           _VERDE_CLARO, "admins_sub"),
            ("acc_denegados","ACCESOS DENEGADOS",    _ROJO,        "deny_sub"),
        ]

        for i, (key, titulo, color_barra, key_sub) in enumerate(specs):
            card = tk.Frame(fila, bg=_CARD_BG,
                            highlightthickness=1,
                            highlightbackground=_BORDE)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 10, 0))

            # Barra de color superior
            tk.Frame(card, bg=color_barra, height=5).pack(fill="x")

            body = tk.Frame(card, bg=_CARD_BG, padx=16, pady=12)
            body.pack(fill="both")

            tk.Label(body, text=titulo,
                     font=("Segoe UI", 8, "bold"),
                     fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")

            lbl_num = tk.Label(body, text="—",
                               font=("Segoe UI", 32, "bold"),
                               fg=_TEXTO_OSCURO, bg=_CARD_BG)
            lbl_num.pack(anchor="w")

            lbl_sub = tk.Label(body, text="",
                               font=("Segoe UI", 8),
                               fg=_VERDE_CLARO, bg=_CARD_BG)
            lbl_sub.pack(anchor="w")

            self._tarjetas[key]     = lbl_num
            self._tarjetas[key_sub] = lbl_sub

    # ══════════════════════════════════════════════════════════════════════════
    #  HISTORIAL DE ACCESOS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_historial(self, parent):
        card = self._card(parent, pady_bottom=10)

        # Cabecera
        cab = tk.Frame(card, bg=_CARD_BG)
        cab.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(cab, text="HISTORIAL DE ACCESOS",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(side="left")

        # Filtros
        filtros = tk.Frame(cab, bg=_CARD_BG)
        filtros.pack(side="right")

        roles = ["Todos los roles", "Alumno", "Admin", "Profesor"]
        om_rol = tk.OptionMenu(filtros, self._filtro_rol, *roles,
                               command=lambda _: self._filtrar_historial())
        self._estilo_optionmenu(om_rol)
        om_rol.pack(side="left", padx=(0, 6))

        anios = [str(y) for y in range(2024, datetime.now().year + 1)]
        om_anio = tk.OptionMenu(filtros, self._filtro_anio, *anios,
                                command=lambda _: self._filtrar_historial())
        self._estilo_optionmenu(om_anio)
        om_anio.pack(side="left")

        # Tabla
        cols = ("No. Institucional", "Nombre", "Fecha", "Hora", "Rol")
        self.tree_hist = self._crear_tree(card, cols, height=6)
        self.tree_hist.pack(fill="x", padx=16)

        # Ver todos
        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=16, pady=(4, 12))
        lbl_ver = tk.Label(pie, text="Ver todos →",
                           font=("Segoe UI", 9),
                           fg=_VERDE, bg=_CARD_BG, cursor="hand2")
        lbl_ver.pack(side="right")
        lbl_ver.bind("<Button-1>", lambda e: self.app.mostrar_pantalla("historial")
                     if hasattr(self.app, "mostrar_pantalla") else None)

    def _estilo_optionmenu(self, om):
        om.config(font=("Segoe UI", 8), bg=_GRIS_BG, fg=_TEXTO_OSCURO,
                  relief="flat", bd=0, highlightthickness=1,
                  highlightbackground=_BORDE, activebackground=_BORDE,
                  cursor="hand2", pady=3)
        om["menu"].config(font=("Segoe UI", 9), bg=_CARD_BG,
                          activebackground=_VERDE_CLARO,
                          activeforeground="#ffffff")

    # ══════════════════════════════════════════════════════════════════════════
    #  GRÁFICA DE BARRAS — ACCESOS POR HORA
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_grafica(self, parent):
        card = self._card(parent)

        tk.Label(card, text="ACCESOS POR HORA — HOY",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(anchor="w", padx=16, pady=(14, 8))

        self.canvas_graf = tk.Canvas(card, bg=_CARD_BG,
                                     height=160, highlightthickness=0)
        self.canvas_graf.pack(fill="x", padx=16, pady=(0, 14))

        self._datos_grafica = [0] * 13   # 7am … 7pm
        self._hora_activa   = None
        self.canvas_graf.bind("<Configure>", lambda e: self._dibujar_grafica())

    def _dibujar_grafica(self, hora_hover=None):
        c  = self.canvas_graf
        c.delete("all")
        w  = c.winfo_width()
        h  = c.winfo_height()
        if w < 10:
            return

        datos  = self._datos_grafica
        maximo = max(datos) if max(datos) > 0 else 1
        horas  = [f"{7+i}am" if (7+i) < 12 else
                  ("12pm" if (7+i) == 12 else f"{7+i-12}pm")
                  for i in range(13)]

        n        = len(datos)
        margen_l = 10
        margen_r = 10
        margen_t = 16
        margen_b = 22
        espacio  = (w - margen_l - margen_r) / n
        ancho_b  = espacio * 0.55
        area_h   = h - margen_t - margen_b

        for i, (val, hora) in enumerate(zip(datos, horas)):
            x_centro = margen_l + i * espacio + espacio / 2
            alto_b   = max(4, (val / maximo) * area_h)
            x1 = x_centro - ancho_b / 2
            y1 = margen_t + area_h - alto_b
            x2 = x_centro + ancho_b / 2
            y2 = margen_t + area_h

            if i == hora_hover:
                color = "#ff9800"
                # Tooltip
                c.create_rectangle(x_centro - 28, y1 - 22,
                                   x_centro + 28, y1 - 4,
                                   fill="#333333", outline="")
                c.create_text(x_centro, y1 - 13,
                              text=f"{val} accesos",
                              font=("Segoe UI", 7), fill="#ffffff")
            elif val == max(datos) and max(datos) > 0:
                color = _VERDE_CLARO
            else:
                color = "#c8e6c9"

            # Barra redondeada (simulada con dos rect + oval)
            r_top = min(4, ancho_b / 2)
            c.create_rectangle(x1, y1 + r_top, x2, y2, fill=color, outline="")
            c.create_oval(x1, y1, x2, y1 + r_top * 2, fill=color, outline="")

            c.create_text(x_centro, h - margen_b + 6,
                          text=hora, font=("Segoe UI", 7), fill=_TEXTO_GRIS)

        def on_motion(e):
            idx = int((e.x - margen_l) / espacio)
            if 0 <= idx < n:
                self._dibujar_grafica(hora_hover=idx)
            else:
                self._dibujar_grafica()

        c.bind("<Motion>", on_motion)
        c.bind("<Leave>",  lambda e: self._dibujar_grafica())

    # ══════════════════════════════════════════════════════════════════════════
    #  DISTRIBUCIÓN POR ROL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_distribucion(self, parent):
        card = self._card(parent, pady_bottom=10)

        tk.Label(card, text="DISTRIBUCIÓN POR ROL",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(anchor="w", padx=16, pady=(14, 10))

        self._barras_dist = {}
        roles_cfg = [
            ("Alumnos",    _VERDE_CLARO),
            ("Profesores", _VERDE),
            ("Denegados",  _ROJO),
        ]
        for rol, color in roles_cfg:
            fila = tk.Frame(card, bg=_CARD_BG)
            fila.pack(fill="x", padx=16, pady=3)

            tk.Label(fila, text=rol, font=("Segoe UI", 9),
                     fg=_TEXTO_OSCURO, bg=_CARD_BG,
                     width=10, anchor="w").pack(side="left")

            barra_bg = tk.Frame(fila, bg=_BORDE, height=12)
            barra_bg.pack(side="left", fill="x", expand=True, padx=(4, 8))
            barra_bg.pack_propagate(False)

            barra_fill = tk.Frame(barra_bg, bg=color, height=12)
            barra_fill.place(x=0, y=0, relheight=1, relwidth=0.0)

            lbl_pct = tk.Label(fila, text="0%", font=("Segoe UI", 8, "bold"),
                               fg=_TEXTO_GRIS, bg=_CARD_BG, width=4)
            lbl_pct.pack(side="left")

            self._barras_dist[rol] = (barra_fill, lbl_pct)

        # Total del día
        sep = tk.Frame(card, bg=_BORDE, height=1)
        sep.pack(fill="x", padx=16, pady=(10, 6))

        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=16, pady=(0, 14))
        tk.Label(pie, text="Total del día:",
                 font=("Segoe UI", 9), fg=_TEXTO_GRIS, bg=_CARD_BG).pack(side="left")
        self.lbl_total_dia = tk.Label(pie, text="0 accesos",
                                      font=("Segoe UI", 10, "bold"),
                                      fg=_TEXTO_OSCURO, bg=_CARD_BG)
        self.lbl_total_dia.pack(side="left", padx=6)

    # ══════════════════════════════════════════════════════════════════════════
    #  USUARIOS REGISTRADOS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_usuarios_registrados(self, parent):
        card = self._card(parent, pady_bottom=10)

        tk.Label(card, text="USUARIOS REGISTRADOS",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(anchor="w", padx=16, pady=(14, 10))

        fila = tk.Frame(card, bg=_CARD_BG)
        fila.pack(fill="x", padx=16, pady=(0, 14))

        # Total
        bloque_total = tk.Frame(fila, bg=_CARD_BG)
        bloque_total.pack(side="left", expand=True)
        self.lbl_total_usr = tk.Label(bloque_total, text="—",
                                      font=("Segoe UI", 28, "bold"),
                                      fg=_VERDE, bg=_CARD_BG)
        self.lbl_total_usr.pack()
        tk.Label(bloque_total, text="Total usuarios",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack()

        tk.Frame(fila, bg=_BORDE, width=1).pack(side="left", fill="y", padx=8)

        # Activos hoy
        bloque_activos = tk.Frame(fila, bg=_CARD_BG)
        bloque_activos.pack(side="left", expand=True)
        self.lbl_activos_hoy = tk.Label(bloque_activos, text="—",
                                        font=("Segoe UI", 28, "bold"),
                                        fg="#1565C0", bg=_CARD_BG)
        self.lbl_activos_hoy.pack()
        tk.Label(bloque_activos, text="Activos hoy",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack()

    # ══════════════════════════════════════════════════════════════════════════
    #  ACCIONES RÁPIDAS
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_acciones_rapidas(self, parent):
        card = self._card(parent)

        tk.Label(card, text="ACCIONES RÁPIDAS",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(anchor="w", padx=16, pady=(14, 10))

        botones = [
            ("+ AGREGAR USUARIO", _VERDE_BTN,  _VERDE_HOVER, "#fff",
             lambda: self.app.mostrar_pantalla("registro")),
        ]
        for texto, bg, hover, fg, cmd in botones:
            b = tk.Button(card, text=texto,
                          font=("Segoe UI", 10, "bold"),
                          fg=fg, bg=bg, activebackground=hover,
                          activeforeground=fg,
                          bd=0, pady=10, cursor="hand2", relief="flat",
                          command=cmd)
            b.pack(fill="x", padx=16, pady=(0, 6))

        # Fila: Gestión | Historial
        fila2 = tk.Frame(card, bg=_CARD_BG)
        fila2.pack(fill="x", padx=16, pady=(0, 6))
        fila2.columnconfigure(0, weight=1)
        fila2.columnconfigure(1, weight=1)

        for i, (texto, cmd) in enumerate([
            ("GESTIÓN",   lambda: self.app.mostrar_pantalla("gestion_real")),
            ("HISTORIAL", lambda: self.app.mostrar_pantalla("historial")),
        ]):
            b = tk.Button(fila2, text=texto,
                          font=("Segoe UI", 10, "bold"),
                          fg="#fff", bg=_VERDE_BTN,
                          activebackground=_VERDE_HOVER,
                          activeforeground="#fff",
                          bd=0, pady=10, cursor="hand2", relief="flat",
                          command=cmd)
            b.grid(row=0, column=i, sticky="ew",
                   padx=(0 if i == 0 else 6, 0))

        # Cerrar sesión
        b_salir = tk.Button(card, text="← CERRAR SESIÓN",
                            font=("Segoe UI", 10, "bold"),
                            fg="#ffffff", bg="#212121",
                            activebackground="#000000",
                            activeforeground="#ffffff",
                            bd=0, pady=10, cursor="hand2", relief="flat",
                            command=self._volver)
        b_salir.pack(fill="x", padx=16, pady=(0, 16))

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS UI
    # ══════════════════════════════════════════════════════════════════════════
    def _card(self, parent, pady_bottom=0):
        """Frame con fondo blanco y borde sutil."""
        wrap = tk.Frame(parent, bg=_BORDE)
        wrap.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(wrap, bg=_CARD_BG)
        inner.pack(fill="both", padx=1, pady=1)
        return inner

    def _crear_tree(self, parent, cols, height=6):
        s = ttk.Style()
        s.configure("D.Treeview",
                    font=("Segoe UI", 9), rowheight=28,
                    background=_CARD_BG, foreground=_TEXTO_OSCURO,
                    fieldbackground=_CARD_BG, borderwidth=0)
        s.configure("D.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=_VERDE, foreground="#ffffff", relief="flat")
        s.map("D.Treeview",
              background=[("selected", "#e8f5e9")],
              foreground=[("selected", _VERDE)])

        frame = tk.Frame(parent, bg=_CARD_BG)
        sy = ttk.Scrollbar(frame, orient="vertical")

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            height=height, style="D.Treeview",
                            yscrollcommand=sy.set)
        sy.config(command=tree.yview)

        anchos = {
            "No. Institucional": 110, "Nombre": 160,
            "Fecha": 80,  "Hora": 70, "Rol": 80,
        }
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=anchos.get(col, 100), minwidth=60)

        tree.tag_configure("par",   background="#f9f9f9")
        tree.tag_configure("impar", background=_CARD_BG)

        sy.pack(side="right", fill="y")
        tree.pack(fill="x", expand=False)

        frame._tree = tree
        return frame

    # ══════════════════════════════════════════════════════════════════════════
    #  CARGA DE DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cargar_todo(self):
        self._cargar_estadisticas()
        self._cargar_historial()

    def _cargar_estadisticas(self):
        usuarios = obtener_usuarios()
        accesos  = obtener_accesos(limite=1000)
        hoy      = datetime.now().strftime("%Y-%m-%d")

        total    = len(usuarios)
        alumnos  = sum(1 for u in usuarios if u["rol"] == "Alumno")
        admins   = sum(1 for u in usuarios
                       if u["rol"] in ("Admin", "SuperAdmin",
                                       "SuperUsuario", "Profesor"))
        acc_hoy_lista = [a for a in accesos if a["fecha"] == hoy]
        acc_hoy  = len(acc_hoy_lista)

        # Tarjetas
        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))
        self._tarjetas["accesos_hoy_sub"].config(text="accesos registrados hoy")
        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        pct_alumnos = f"{round(alumnos/total*100)}% del total" if total else "0%"
        self._tarjetas["alumnos_sub"].config(text=pct_alumnos)
        self._tarjetas["total_admins"].config(text=str(admins))
        pct_admins = f"{round(admins/total*100)}% del total" if total else "0%"
        self._tarjetas["admins_sub"].config(text=pct_admins)
        self._tarjetas["acc_denegados"].config(text="0")
        self._tarjetas["deny_sub"].config(
            text="accesos rechazados", fg=_ROJO_CLARO)

        # Usuarios registrados
        self.lbl_total_usr.config(text=str(total))
        self.lbl_activos_hoy.config(text=str(acc_hoy))
        self._todos_usuarios = usuarios

        # Distribución
        total_acc = acc_hoy if acc_hoy > 0 else 1
        roles_data = {
            "Alumnos":    sum(1 for a in acc_hoy_lista),  # simplificado
            "Profesores": admins,
            "Denegados":  0,
        }
        # Recalcular con proporciones reales
        alumnos_acc = sum(1 for a in acc_hoy_lista
                          if "alumno" in (a.get("nombre") or "").lower()
                          or True)   # por ahora todos van a alumnos
        for rol, (barra, lbl_pct) in self._barras_dist.items():
            if rol == "Alumnos":
                pct = round(alumnos / total * 100) if total else 0
            elif rol == "Profesores":
                pct = round(admins / total * 100) if total else 0
            else:
                pct = 1
            barra.place(relwidth=pct / 100)
            lbl_pct.config(text=f"{pct}%")

        self.lbl_total_dia.config(text=f"{acc_hoy} accesos")

        # Gráfica de barras por hora
        conteo = [0] * 13
        for a in acc_hoy_lista:
            try:
                hora_str = a.get("hora", "")
                if hora_str:
                    h_num = int(hora_str.split(":")[0])
                    idx = h_num - 7
                    if 0 <= idx < 13:
                        conteo[idx] += 1
            except Exception:
                pass
        self._datos_grafica = conteo
        self.canvas_graf.after(100, self._dibujar_grafica)

    def _cargar_historial(self):
        self._datos_accesos = obtener_accesos(limite=100)
        self._filtrar_historial()

    def _filtrar_historial(self):
        rol_f  = self._filtro_rol.get()
        anio_f = self._filtro_anio.get()

        datos = self._datos_accesos
        if rol_f != "Todos los roles":
            datos = [a for a in datos
                     if rol_f.lower() in (a.get("nombre") or "").lower()
                     or True]   # sin campo rol en accesos, mostramos todos
        if anio_f:
            datos = [a for a in datos if (a.get("fecha") or "").startswith(anio_f)]

        t = self.tree_hist._tree
        t.delete(*t.get_children())
        for i, a in enumerate(datos[:6]):
            t.insert("", "end", tags=("par" if i % 2 == 0 else "impar",),
                     values=(a["cod_institucional"],
                             a["nombre"] or "—",
                             a["fecha"], a["hora"],
                             a.get("rol") or "Alumno"))

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _volver(self):
        self.app.mostrar_pantalla("principal")


def crear_pantalla_gestion_real(parent, app):
    PantallaGestion(parent, app)