"""
ui/screens/pantalla_editar_usuario.py
Pantalla de Edición de Usuario — pantalla completa 800x480
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA

# ── Colores ────────────────────────────────────────────────────────────────────
_BG_APP       = "#f3f4f5"
_BG_CARD      = "#ffffff"
_VERDE        = "#2e7d32"
_VERDE_BTN    = "#43a047"
_VERDE_HOVER  = "#388e3c"
_ROJO         = "#c62828"
_ROJO_CLARO   = "#ef5350"
_TEXTO_OSCURO = "#1a1a1a"
_TEXTO_GRIS   = "#757575"
_BORDE        = "#e0e0e0"


class PantallaEditarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent = parent
        self.app    = app
        self.datos  = datos or {}
        self._construir_ui()

    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=_BG_APP)
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        # ── Contenedor central ─────────────────────────────────────────────
        cont = tk.Frame(self.pantalla, bg=_BG_APP)
        cont.pack(fill="both", expand=True, padx=20, pady=6)

        # Título
        encab = tk.Frame(cont, bg=_BG_APP)
        encab.pack(fill="x", pady=(0, 6))

        tk.Label(encab, text="EDITAR USUARIO",
                 font=("Segoe UI", 16, "bold"),
                 fg=_TEXTO_OSCURO, bg=_BG_APP).pack(side="left")

        # No. Institucional como subtítulo
        cod = self.datos.get("cod_institucional", "")
        if cod:
            tk.Label(encab, text=f"  #{cod}",
                     font=("Segoe UI", 12),
                     fg=_TEXTO_GRIS, bg=_BG_APP).pack(side="left", pady=(4, 0))

        # ── Card de formulario ─────────────────────────────────────────────
        card = tk.Frame(cont, bg=_BG_CARD,
                        highlightthickness=1, highlightbackground=_BORDE)
        card.pack(fill="both", expand=True)

        # Barra verde superior del card
        tk.Frame(card, bg=_VERDE_BTN, height=4).pack(fill="x")

        form = tk.Frame(card, bg=_BG_CARD)
        form.pack(fill="both", expand=True, padx=20, pady=8)

        # ── Campos del formulario en grid 2 columnas ───────────────────────
        campos = [
            ("No. Institucional", "cod_institucional", False),  # False = no editable
            ("Nombre",            "nombre",            True),
            ("Apellido Paterno",  "apellido_paterno",  True),
            ("Apellido Materno",  "apellido_materno",  True),
            ("Programa / Carrera","carrera",            True),
            ("Fecha y Hora",      "fecha_hora",         False),
        ]

        self._entradas = {}

        for i, (label, key, editable) in enumerate(campos):
            col = i % 2
            row = i // 2
            form.columnconfigure(col, weight=1)

            sub = tk.Frame(form, bg=_BG_CARD)
            sub.grid(row=row, column=col,
                     padx=(0, 20 if col == 0 else 0),
                     pady=4, sticky="ew")

            tk.Label(sub, text=label,
                     font=("Segoe UI", 8),
                     fg=_TEXTO_GRIS, bg=_BG_CARD).pack(anchor="w")

            valor = self.datos.get(key, "")
            e = tk.Entry(sub,
                         font=("Segoe UI", 10),
                         fg=_TEXTO_OSCURO if editable else _TEXTO_GRIS,
                         bg="#f5f5f5" if editable else "#ebebeb",
                         relief="flat", bd=0,
                         highlightthickness=1,
                         highlightbackground=_BORDE)
            e.insert(0, valor)
            if not editable:
                e.config(state="disabled",
                         disabledforeground=_TEXTO_GRIS,
                         disabledbackground="#ebebeb")
            e.pack(fill="x", ipady=6, pady=(2, 0))
            self._entradas[key] = e

        # ── Fila: Rol + Status ─────────────────────────────────────────────
        fila_extra = tk.Frame(form, bg=_BG_CARD)
        fila_extra.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        fila_extra.columnconfigure(0, weight=1)
        fila_extra.columnconfigure(1, weight=1)

        # Rol
        sub_rol = tk.Frame(fila_extra, bg=_BG_CARD)
        sub_rol.grid(row=0, column=0, padx=(0, 20), sticky="ew")
        tk.Label(sub_rol, text="Rol",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_BG_CARD).pack(anchor="w")

        self._rol_var = tk.StringVar(value=self.datos.get("rol", "Alumno"))
        roles = ["Alumno", "Maestro", "Admin", "Super Admin"]
        om_rol = tk.OptionMenu(sub_rol, self._rol_var, *roles)
        om_rol.config(font=("Segoe UI", 10), bg="#f5f5f5", fg=_TEXTO_OSCURO,
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=_BORDE, activebackground=_BORDE,
                      cursor="hand2")
        om_rol["menu"].config(font=("Segoe UI", 9), bg=_BG_CARD,
                              activebackground=_VERDE_BTN,
                              activeforeground="#ffffff")
        om_rol.pack(fill="x", ipady=4, pady=(2, 0))

        # Status
        sub_status = tk.Frame(fila_extra, bg=_BG_CARD)
        sub_status.grid(row=0, column=1, sticky="ew")
        tk.Label(sub_status, text="Status",
                 font=("Segoe UI", 8), fg=_TEXTO_GRIS, bg=_BG_CARD).pack(anchor="w")

        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))
        om_status = tk.OptionMenu(sub_status, self._status_var, "Activo", "Inactivo")
        om_status.config(font=("Segoe UI", 10), bg="#f5f5f5", fg=_TEXTO_OSCURO,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=_BORDE, activebackground=_BORDE,
                         cursor="hand2")
        om_status["menu"].config(font=("Segoe UI", 9), bg=_BG_CARD,
                                 activebackground=_VERDE_BTN,
                                 activeforeground="#ffffff")
        om_status.pack(fill="x", ipady=4, pady=(2, 0))

        # ── Botones ────────────────────────────────────────────────────────
        pie = tk.Frame(cont, bg=_BG_APP)
        pie.pack(fill="x", pady=(6, 0))

        tk.Button(pie, text="GUARDAR CAMBIOS",
                  font=("Segoe UI", 10, "bold"),
                  fg="#ffffff", bg=_VERDE_BTN,
                  activebackground=_VERDE_HOVER, activeforeground="#ffffff",
                  bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
                  command=self._guardar).pack(side="left", padx=(0, 10))

        tk.Button(pie, text="CANCELAR",
                  font=("Segoe UI", 10, "bold"),
                  fg="#ffffff", bg="#424242",
                  activebackground="#212121", activeforeground="#ffffff",
                  bd=0, padx=20, pady=8, relief="flat", cursor="hand2",
                  command=self._cancelar).pack(side="left")

    def _guardar(self):
        datos_actualizados = {
            "cod_institucional": self.datos.get("cod_institucional", ""),
            "nombre":            self._entradas["nombre"].get(),
            "apellido_paterno":  self._entradas["apellido_paterno"].get(),
            "apellido_materno":  self._entradas["apellido_materno"].get(),
            "carrera":           self._entradas["carrera"].get(),
            "rol":               self._rol_var.get(),
            "status":            self._status_var.get(),
        }
        print("[EDITAR USUARIO] Guardando:", datos_actualizados)
        # TODO: llamar función de BD para actualizar el usuario
        # from core.database import actualizar_usuario
        # actualizar_usuario(datos_actualizados)
        self.app.mostrar_pantalla("gestion_real")

    def _cancelar(self):
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_editar_usuario(parent, app, datos=None):
    PantallaEditarUsuario(parent, app, datos)