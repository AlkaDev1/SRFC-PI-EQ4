"""
ui/screens/pantalla_gestion.py
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from core.database import (listar_usuarios as obtener_usuarios,
                            listar_accesos as obtener_accesos,
                            inicializar_bd)

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
        canvas_scroll.bind("<Configure>", lambda e: canvas_scroll.itemconfig(
            win_id, width=e.width))

        def _wheel(e):
            canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas_scroll.bind_all("<MouseWheel>", _wheel)

        self._construir_contenido(self._inner)

    def _construir_contenido(self, parent):
        pad = tk.Frame(parent, bg=_GRIS_BG)
        pad.pack(fill="both", expand=True, padx=20, pady=16)

        self._construir_tarjetas(pad)

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
                            highlightthickness=1, highlightbackground=_BORDE)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 10, 0))

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
    #  HISTORIAL DE ACCESOS (mini, en dashboard)
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_historial(self, parent):
        card = self._card(parent, pady_bottom=10)

        cab = tk.Frame(card, bg=_CARD_BG)
        cab.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(cab, text="HISTORIAL DE ACCESOS",
                 font=("Segoe UI", 10, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(side="left")

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

        cols = ("No. Institucional", "Nombre", "Fecha", "Hora", "Rol")
        self.tree_hist = self._crear_tree(card, cols, height=6)
        self.tree_hist.pack(fill="x", padx=16)

        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=16, pady=(4, 12))
        lbl_ver = tk.Label(pie, text="Ver todos →",
                           font=("Segoe UI", 9),
                           fg=_VERDE, bg=_CARD_BG, cursor="hand2")
        lbl_ver.pack(side="right")
        lbl_ver.bind("<Button-1>", lambda e: self._abrir_modal_historial())

    def _estilo_optionmenu(self, om):
        om.config(font=("Segoe UI", 8), bg=_GRIS_BG, fg=_TEXTO_OSCURO,
                  relief="flat", bd=0, highlightthickness=1,
                  highlightbackground=_BORDE, activebackground=_BORDE,
                  cursor="hand2", pady=3)
        om["menu"].config(font=("Segoe UI", 9), bg=_CARD_BG,
                          activebackground=_VERDE_CLARO, activeforeground="#ffffff")

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

        self._datos_grafica = [0] * 13
        self._hora_activa   = None
        self.canvas_graf.bind("<Configure>", lambda e: self._dibujar_grafica())

    def _dibujar_grafica(self, hora_hover=None):
        c = self.canvas_graf
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
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

        bloque_total = tk.Frame(fila, bg=_CARD_BG)
        bloque_total.pack(side="left", expand=True)
        self.lbl_total_usr = tk.Label(bloque_total, text="—",
                                      font=("Segoe UI", 28, "bold"),
                                      fg=_VERDE, bg=_CARD_BG)
        self.lbl_total_usr.pack()
        tk.Label(bloque_total, text="Total usuarios",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack()

        tk.Frame(fila, bg=_BORDE, width=1).pack(side="left", fill="y", padx=8)

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
            ("+ AGREGAR USUARIO", _VERDE_BTN, _VERDE_HOVER, "#fff",
             lambda: self._abrir_modal_agregar()),
        ]
        for texto, bg, hover, fg, cmd in botones:
            b = tk.Button(card, text=texto,
                          font=("Segoe UI", 10, "bold"),
                          fg=fg, bg=bg, activebackground=hover,
                          activeforeground=fg,
                          bd=0, pady=10, cursor="hand2", relief="flat",
                          command=cmd)
            b.pack(fill="x", padx=16, pady=(0, 6))

        fila2 = tk.Frame(card, bg=_CARD_BG)
        fila2.pack(fill="x", padx=16, pady=(0, 6))
        fila2.columnconfigure(0, weight=1)
        fila2.columnconfigure(1, weight=1)

        for i, (texto, cmd) in enumerate([
            ("GESTIÓN",   lambda: self._abrir_modal_gestion()),
            ("HISTORIAL", lambda: self._abrir_modal_historial()),
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

        b_salir = tk.Button(card, text="← CERRAR SESIÓN",
                            font=("Segoe UI", 10, "bold"),
                            fg="#ffffff", bg="#212121",
                            activebackground="#000000",
                            activeforeground="#ffffff",
                            bd=0, pady=10, cursor="hand2", relief="flat",
                            command=self._volver)
        b_salir.pack(fill="x", padx=16, pady=(0, 16))

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPER — ventana flotante Toplevel centrada, sin barra de título
    # ══════════════════════════════════════════════════════════════════════════
    def _crear_modal_toplevel(self, width, height):
        """
        Crea un Toplevel sin decoración, centrado sobre la ventana principal.
        El dashboard sigue visible detrás — el modal flota encima.
        Devuelve (toplevel, card_frame).
        """
        root = self.pantalla.winfo_toplevel()
        root.update_idletasks()

        rx = root.winfo_x()
        ry = root.winfo_y()
        rw = root.winfo_width()
        rh = root.winfo_height()
        x  = rx + (rw - width)  // 2
        y  = ry + (rh - height) // 2

        top = tk.Toplevel(root)
        top.overrideredirect(True)   # sin barra de título de Windows
        top.geometry(f"{width}x{height}+{x}+{y}")
        top.grab_set()               # bloquea clics en la ventana principal
        top.lift()
        top.focus_force()
        top.configure(bg=_BORDE)

        # Sombra simulada con un frame exterior ligeramente más grande
        shadow = tk.Frame(top, bg="#00000033" if False else "#cccccc")
        shadow.place(x=4, y=4, width=width - 4, height=height - 4)

        card = tk.Frame(top, bg=_CARD_BG,
                        highlightthickness=1, highlightbackground="#bbbbbb")
        card.place(x=0, y=0, width=width - 4, height=height - 4)

        return top, card

    # ══════════════════════════════════════════════════════════════════════════
    #  MODAL — HISTORIAL DE ACCESOS COMPLETO
    # ══════════════════════════════════════════════════════════════════════════
    def _abrir_modal_historial(self):
        top, card = self._crear_modal_toplevel(740, 500)

        # ── Cabecera ──────────────────────────────────────────────────────
        cab = tk.Frame(card, bg=_CARD_BG)
        cab.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(cab, text="HISTORIAL DE ACCESOS",
                 font=("Segoe UI", 13, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(side="left")

        filtros = tk.Frame(cab, bg=_CARD_BG)
        filtros.pack(side="right")

        _filtro_rol_m  = tk.StringVar(value="Todos los roles")
        _filtro_anio_m = tk.StringVar(value=str(datetime.now().year))

        roles = ["Todos los roles", "Alumno", "Admin", "Profesor"]
        om_rol = tk.OptionMenu(filtros, _filtro_rol_m, *roles)
        self._estilo_optionmenu(om_rol)
        om_rol.pack(side="left", padx=(0, 6))

        anios = [str(y) for y in range(2024, datetime.now().year + 1)]
        om_anio = tk.OptionMenu(filtros, _filtro_anio_m, *anios)
        self._estilo_optionmenu(om_anio)
        om_anio.pack(side="left")

        # ── Tabla ─────────────────────────────────────────────────────────
        cols = ("No. Institucional", "Nombre", "Fecha", "Hora", "Rol")
        tree_frame = self._crear_tree(card, cols, height=11)
        tree_frame.pack(fill="x", padx=20)
        tree = tree_frame._tree

        accesos = obtener_accesos(limite=500)

        def _poblar(datos):
            tree.delete(*tree.get_children())
            for i, a in enumerate(datos):
                tree.insert("", "end",
                            tags=("par" if i % 2 == 0 else "impar",),
                            values=(a["cod_institucional"],
                                    a["nombre"] or "—",
                                    a["fecha"], a["hora"],
                                    a.get("rol") or "Alumno"))

        def _filtrar(*_):
            anio_f = _filtro_anio_m.get()
            datos  = accesos
            if anio_f:
                datos = [a for a in datos
                         if (a.get("fecha") or "").startswith(anio_f)]
            _poblar(datos)

        _filtro_rol_m.trace_add("write",  _filtrar)
        _filtro_anio_m.trace_add("write", _filtrar)
        _poblar(accesos)

        # ── Pie ───────────────────────────────────────────────────────────
        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=20, pady=(8, 14))

        tk.Label(pie, text=f"Mostrando {len(accesos)} registros",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack(side="left")

        tk.Button(pie, text="← CERRAR",
                  font=("Segoe UI", 9, "bold"),
                  fg="#ffffff", bg="#424242",
                  activebackground="#212121", activeforeground="#ffffff",
                  bd=0, padx=14, pady=6, relief="flat", cursor="hand2",
                  command=top.destroy).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    #  MODAL — GESTIÓN DE USUARIOS
    # ══════════════════════════════════════════════════════════════════════════
    def _abrir_modal_gestion(self):
        top, card = self._crear_modal_toplevel(760, 520)

        # ── Cabecera ──────────────────────────────────────────────────────
        cab = tk.Frame(card, bg=_CARD_BG)
        cab.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(cab, text="GESTIÓN DE USUARIOS",
                 font=("Segoe UI", 13, "bold"),
                 fg=_TEXTO_OSCURO, bg=_CARD_BG).pack(side="left")

        controles = tk.Frame(cab, bg=_CARD_BG)
        controles.pack(side="right")

        _filtro_rol_g  = tk.StringVar(value="Todos los roles")
        _filtro_anio_g = tk.StringVar(value=str(datetime.now().year))

        roles = ["Todos los roles", "Alumno", "Admin", "Profesor"]
        om_rol = tk.OptionMenu(controles, _filtro_rol_g, *roles)
        self._estilo_optionmenu(om_rol)
        om_rol.pack(side="left", padx=(0, 6))

        anios = [str(y) for y in range(2024, datetime.now().year + 1)]
        om_anio = tk.OptionMenu(controles, _filtro_anio_g, *anios)
        self._estilo_optionmenu(om_anio)
        om_anio.pack(side="left", padx=(0, 10))

        tk.Button(controles, text="+ Agregar usuario",
                  font=("Segoe UI", 9, "bold"),
                  fg="#ffffff", bg=_VERDE_BTN,
                  activebackground=_VERDE_HOVER, activeforeground="#ffffff",
                  bd=0, padx=12, pady=5, relief="flat", cursor="hand2",
                  command=lambda: self._abrir_modal_agregar(top)).pack(side="left")

        # ── Tabla ─────────────────────────────────────────────────────────
        s = ttk.Style()
        s.configure("G.Treeview",
                    font=("Segoe UI", 9), rowheight=30,
                    background=_CARD_BG, foreground=_TEXTO_OSCURO,
                    fieldbackground=_CARD_BG, borderwidth=0)
        s.configure("G.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=_VERDE, foreground="#ffffff", relief="flat")
        s.map("G.Treeview",
              background=[("selected", "#e8f5e9")],
              foreground=[("selected", _VERDE)])

        frame_t = tk.Frame(card, bg=_CARD_BG)
        frame_t.pack(fill="x", padx=20)

        sy = ttk.Scrollbar(frame_t, orient="vertical")
        cols_g = ("No. Institucional", "Nombre",
                  "Fecha de registro", "Hora de registro",
                  "Rol", "Acciones")
        tree_g = ttk.Treeview(frame_t, columns=cols_g, show="headings",
                               height=10, style="G.Treeview",
                               yscrollcommand=sy.set)
        sy.config(command=tree_g.yview)

        anchos_g = {
            "No. Institucional":  110,
            "Nombre":             155,
            "Fecha de registro":  105,
            "Hora de registro":   105,
            "Rol":                 80,
            "Acciones":            70,
        }
        for col in cols_g:
            tree_g.heading(col, text=col)
            tree_g.column(col, width=anchos_g.get(col, 90), minwidth=60)

        tree_g.tag_configure("par",   background="#f9f9f9")
        tree_g.tag_configure("impar", background=_CARD_BG)

        sy.pack(side="right", fill="y")
        tree_g.pack(fill="x")

        usuarios = obtener_usuarios()

        def _poblar_g(datos):
            tree_g.delete(*tree_g.get_children())
            for i, u in enumerate(datos):
                tree_g.insert("", "end",
                               tags=("par" if i % 2 == 0 else "impar",),
                               values=(u.get("cod_institucional", ""),
                                       u.get("nombre", "—"),
                                       u.get("fecha_registro", ""),
                                       u.get("hora_registro", ""),
                                       u.get("rol", "Alumno"),
                                       "✏️ Editar"))

        _poblar_g(usuarios)

        # ── Pie ───────────────────────────────────────────────────────────
        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=20, pady=(8, 14))

        tk.Label(pie,
                 text=f"Mostrando {len(usuarios)} usuarios registrados",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack(side="left")

        tk.Button(pie, text="← CERRAR",
                  font=("Segoe UI", 9, "bold"),
                  fg="#ffffff", bg="#424242",
                  activebackground="#212121", activeforeground="#ffffff",
                  bd=0, padx=14, pady=6, relief="flat", cursor="hand2",
                  command=top.destroy).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    #  MODAL — AGREGAR USUARIO
    # ══════════════════════════════════════════════════════════════════════════
    def _abrir_modal_agregar(self, parent_top=None):
        """
        Abre el modal de Agregar Usuario.
        Si viene del modal de Gestión (parent_top), maneja el grab correctamente.
        """
        if parent_top:
            parent_top.grab_release()

        top, card = self._crear_modal_toplevel(520, 500)

        def _cerrar():
            top.destroy()
            if parent_top and parent_top.winfo_exists():
                parent_top.grab_set()
                parent_top.lift()
                parent_top.focus_force()

        # ── Cabecera verde ────────────────────────────────────────────────
        header = tk.Frame(card, bg=_VERDE_BTN, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="AGREGAR USUARIO",
                 font=("Segoe UI", 13, "bold"),
                 fg="#ffffff", bg=_VERDE_BTN).place(relx=0.5, rely=0.5, anchor="center")

        # ── Cuerpo ────────────────────────────────────────────────────────
        body = tk.Frame(card, bg=_CARD_BG)
        body.pack(fill="both", expand=True, padx=24, pady=(14, 0))

        campos = [
            ("Nombre de Usuario", "nombre",  ""),
            ("No. Institucional", "cod",     ""),
            ("Fecha de registro", "fecha",   "DD/MM/AAAA"),
            ("Hora de registro",  "hora",    "00:00 a.m."),
        ]
        entradas = {}

        for i, (label, key, placeholder) in enumerate(campos):
            col = i % 2
            row = i // 2
            sub = tk.Frame(body, bg=_CARD_BG)
            sub.grid(row=row, column=col,
                     padx=(0, 14 if col == 0 else 0),
                     pady=6, sticky="ew")
            body.columnconfigure(col, weight=1)

            tk.Label(sub, text=label, font=("Segoe UI", 8),
                     fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")

            e = tk.Entry(sub, font=("Segoe UI", 10),
                         fg=_TEXTO_GRIS if placeholder else _TEXTO_OSCURO,
                         bg="#f5f5f5", relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=_BORDE)
            if placeholder:
                e.insert(0, placeholder)

                def _focus_in(ev, entry=e, ph=placeholder):
                    if entry.get() == ph:
                        entry.delete(0, "end")
                        entry.config(fg=_TEXTO_OSCURO)

                def _focus_out(ev, entry=e, ph=placeholder):
                    if not entry.get().strip():
                        entry.insert(0, ph)
                        entry.config(fg=_TEXTO_GRIS)

                e.bind("<FocusIn>",  _focus_in)
                e.bind("<FocusOut>", _focus_out)

            e.pack(fill="x", ipady=6, pady=(2, 0))
            entradas[key] = e

        # ── Fila: Rol + Registro facial ────────────────────────────────────
        fila_extra = tk.Frame(body, bg=_CARD_BG)
        fila_extra.grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        fila_extra.columnconfigure(0, weight=1)
        fila_extra.columnconfigure(1, weight=1)

        sub_rol = tk.Frame(fila_extra, bg=_CARD_BG)
        sub_rol.grid(row=0, column=0, padx=(0, 14), sticky="ew")
        tk.Label(sub_rol, text="Rol", font=("Segoe UI", 8),
                 fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")
        _rol_var = tk.StringVar(value="Selecciones Rol")
        om_rol_ag = tk.OptionMenu(sub_rol, _rol_var, "Alumno", "Profesor", "Admin")
        om_rol_ag.config(font=("Segoe UI", 10), bg="#f5f5f5", fg=_TEXTO_OSCURO,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=_BORDE,
                         activebackground=_BORDE, width=18)
        om_rol_ag["menu"].config(font=("Segoe UI", 9), bg=_CARD_BG,
                                 activebackground=_VERDE_CLARO,
                                 activeforeground="#ffffff")
        om_rol_ag.pack(fill="x", ipady=4, pady=(2, 0))

        sub_facial = tk.Frame(fila_extra, bg=_CARD_BG)
        sub_facial.grid(row=0, column=1, sticky="ew")
        tk.Label(sub_facial, text="Registro facial",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")
        e_facial = tk.Entry(sub_facial, font=("Segoe UI", 10),
                            fg=_TEXTO_OSCURO, bg="#f5f5f5",
                            relief="flat", bd=0,
                            highlightthickness=1, highlightbackground=_BORDE)
        e_facial.pack(fill="x", ipady=6, pady=(2, 0))
        entradas["registro_facial"] = e_facial

        # ── Selección de carrera ───────────────────────────────────────────
        fila_carrera = tk.Frame(body, bg=_CARD_BG)
        fila_carrera.grid(row=3, column=0, columnspan=2, sticky="ew", pady=6)
        tk.Label(fila_carrera, text="Selección de carrera",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_CARD_BG).pack(anchor="w")
        e_car = tk.Entry(fila_carrera, font=("Segoe UI", 10),
                         fg=_TEXTO_OSCURO, bg="#f5f5f5",
                         relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=_BORDE)
        e_car.pack(fill="x", ipady=6, pady=(2, 0))
        entradas["carrera"] = e_car

        # ── Botones ───────────────────────────────────────────────────────
        pie = tk.Frame(card, bg=_CARD_BG)
        pie.pack(fill="x", padx=24, pady=16)

        def _confirmar():
            datos = {k: v.get() for k, v in entradas.items()}
            datos["rol"] = _rol_var.get()
            print("[AGREGAR USUARIO]", datos)
            # TODO: llamar aquí a tu función de BD para insertar el usuario
            _cerrar()

        tk.Button(pie, text="CONFIRMAR",
                  font=("Segoe UI", 10, "bold"),
                  fg="#ffffff", bg=_VERDE_BTN,
                  activebackground=_VERDE_HOVER, activeforeground="#ffffff",
                  bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
                  command=_confirmar).pack(side="left", padx=(0, 10))

        tk.Button(pie, text="CANCELAR",
                  font=("Segoe UI", 10, "bold"),
                  fg="#ffffff", bg=_ROJO,
                  activebackground=_ROJO_CLARO, activeforeground="#ffffff",
                  bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
                  command=_cerrar).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS UI
    # ══════════════════════════════════════════════════════════════════════════
    def _card(self, parent, pady_bottom=0):
        wrap  = tk.Frame(parent, bg=_BORDE)
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
        sy    = ttk.Scrollbar(frame, orient="vertical")

        tree  = ttk.Treeview(frame, columns=cols, show="headings",
                             height=height, style="D.Treeview",
                             yscrollcommand=sy.set)
        sy.config(command=tree.yview)

        anchos = {
            "No. Institucional": 110, "Nombre": 160,
            "Fecha": 80, "Hora": 70, "Rol": 80,
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

        total   = len(usuarios)
        alumnos = sum(1 for u in usuarios if u["rol"] == "Alumno")
        admins  = sum(1 for u in usuarios
                      if u["rol"] in ("Admin", "SuperAdmin",
                                      "SuperUsuario", "Profesor"))
        acc_hoy_lista = [a for a in accesos if a["fecha"] == hoy]
        acc_hoy = len(acc_hoy_lista)

        self._tarjetas["accesos_hoy"].config(text=str(acc_hoy))
        self._tarjetas["accesos_hoy_sub"].config(text="accesos registrados hoy")
        self._tarjetas["total_alumnos"].config(text=str(alumnos))
        pct_alumnos = f"{round(alumnos/total*100)}% del total" if total else "0%"
        self._tarjetas["alumnos_sub"].config(text=pct_alumnos)
        self._tarjetas["total_admins"].config(text=str(admins))
        pct_admins = f"{round(admins/total*100)}% del total" if total else "0%"
        self._tarjetas["admins_sub"].config(text=pct_admins)
        self._tarjetas["acc_denegados"].config(text="0")
        self._tarjetas["deny_sub"].config(text="accesos rechazados", fg=_ROJO_CLARO)

        self.lbl_total_usr.config(text=str(total))
        self.lbl_activos_hoy.config(text=str(acc_hoy))
        self._todos_usuarios = usuarios

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

        conteo = [0] * 13
        for a in acc_hoy_lista:
            try:
                hora_str = a.get("hora", "")
                if hora_str:
                    h_num = int(hora_str.split(":")[0])
                    idx   = h_num - 7
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
        anio_f = self._filtro_anio.get()
        datos  = self._datos_accesos
        if anio_f:
            datos = [a for a in datos
                     if (a.get("fecha") or "").startswith(anio_f)]

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