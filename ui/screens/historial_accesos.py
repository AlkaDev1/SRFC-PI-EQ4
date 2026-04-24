"""
ui/screens/historial_accesos.py
Pantalla de Historial de Accesos con barra superior universal.
"""

# __________________________1__________________________#
# Imports y bootstrap de ruta

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA
from core.database import inicializar_bd, obtener_conexion

# ________________________FIN_1_______________________#


# __________________________2__________________________#
# Configuracion visual y utilidades

_BG_APP = "#f3f4f5"
_BG_CARD = "#ffffff"
_VERDE_HEADER_TABLA = "#58bd4a"
_VERDE_BOTON = "#22252a"
_VERDE_BOTON_HOVER = "#343841"
_TEXTO_OSCURO = "#1f2328"
_BORDE_SUAVE = "#d8dce1"

_MESES = [
    "Todos",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

_MESES_NUM = {
    "Enero": "01",
    "Febrero": "02",
    "Marzo": "03",
    "Abril": "04",
    "Mayo": "05",
    "Junio": "06",
    "Julio": "07",
    "Agosto": "08",
    "Septiembre": "09",
    "Octubre": "10",
    "Noviembre": "11",
    "Diciembre": "12",
}


def _formatear_fecha_hora(fecha: str, hora: str) -> str:
    if not fecha:
        return "-"
    try:
        d = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_txt = d.strftime("%d/%m/%y")
    except Exception:
        fecha_txt = fecha
    hora_txt = hora or "--:--"
    return f"{fecha_txt} {hora_txt}"


# ________________________FIN_2_______________________#


# __________________________3__________________________#
# Vista principal

class PantallaHistorialAccesos:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._filtro_rol = tk.StringVar(value="Todos los roles")
        self._filtro_mes = tk.StringVar(value="Mes")

        inicializar_bd()
        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=_BG_APP)
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())

        tk.Frame(
            self.pantalla,
            bg=PALETA["topbar_sistema_fg"],
            height=3,
        ).pack(fill="x")

        cont = tk.Frame(self.pantalla, bg=_BG_APP)
        cont.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(
            cont,
            text="HISTORIAL DE ACCESOS",
            font=("Segoe UI", 20, "bold"),
            fg=_TEXTO_OSCURO,
            bg=_BG_APP,
        ).pack(anchor="w", pady=(0, 8))

        barra = tk.Frame(cont, bg=_BG_APP)
        barra.pack(fill="x", pady=(0, 8))

        filtros = tk.Frame(barra, bg=_BG_APP)
        filtros.pack(side="right")

        self.cmb_rol = ttk.Combobox(
            filtros,
            textvariable=self._filtro_rol,
            state="readonly",
            values=["Todos los roles", "Alumno", "Admin", "Profesor", "SuperAdmin", "SuperUsuario"],
            width=18,
            font=("Segoe UI", 9),
        )
        self.cmb_rol.pack(side="left", padx=(0, 8))
        self.cmb_rol.bind("<<ComboboxSelected>>", lambda _e: self._cargar_datos())

        self.cmb_mes = ttk.Combobox(
            filtros,
            textvariable=self._filtro_mes,
            state="readonly",
            values=["Mes"] + _MESES,
            width=12,
            font=("Segoe UI", 9),
        )
        self.cmb_mes.pack(side="left")
        self.cmb_mes.bind("<<ComboboxSelected>>", lambda _e: self._cargar_datos())

        card = tk.Frame(cont, bg=_BG_CARD, highlightthickness=1, highlightbackground=_BORDE_SUAVE)
        card.pack(fill="both", expand=True)

        style = ttk.Style(self.pantalla)
        style.theme_use("clam")
        style.configure(
            "Historial.Treeview",
            background=_BG_CARD,
            foreground=_TEXTO_OSCURO,
            fieldbackground=_BG_CARD,
            rowheight=36,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Historial.Treeview.Heading",
            background=_VERDE_HEADER_TABLA,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Historial.Treeview", background=[("selected", "#d6eedd")])

        columnas = (
            "No. Institucional",
            "Nombre",
            "Apellido Paterno",
            "Apellido Materno",
            "Programa Academico",
            "Rol",
            "Fecha y Hora",
        )

        self.tree = ttk.Treeview(card, columns=columnas, show="headings", style="Historial.Treeview")

        for col in columnas:
            self.tree.heading(col, text=col)

        self.tree.column("No. Institucional", width=125, anchor="center")
        self.tree.column("Nombre", width=110, anchor="center")
        self.tree.column("Apellido Paterno", width=125, anchor="center")
        self.tree.column("Apellido Materno", width=125, anchor="center")
        self.tree.column("Programa Academico", width=170, anchor="center")
        self.tree.column("Rol", width=90, anchor="center")
        self.tree.column("Fecha y Hora", width=135, anchor="center")

        self.tree.tag_configure("par", background="#f7f7f7")
        self.tree.tag_configure("impar", background="#ececec")

        yscroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=(0, 0))
        yscroll.pack(side="right", fill="y")

        pie = tk.Frame(cont, bg=_BG_APP)
        pie.pack(fill="x", pady=(10, 0))

        btn_cerrar = tk.Button(
            pie,
            text="CERRAR",
            font=("Segoe UI", 10, "bold"),
            bg=_VERDE_BOTON,
            fg="#ffffff",
            activebackground=_VERDE_BOTON_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=10,
            command=self._cerrar,
        )
        btn_cerrar.pack(side="left")

    def _cerrar(self):
        if hasattr(self.app, "mostrar_pantalla"):
            self.app.mostrar_pantalla("gestion")
            return
        self.parent.winfo_toplevel().destroy()

    def _cargar_datos(self):
        self.tree.delete(*self.tree.get_children())

        rol = self._filtro_rol.get().strip()
        mes = self._filtro_mes.get().strip()

        sql = """
            SELECT
                a.cod_institucional,
                COALESCE(u.primer_nombre, '') AS nombre,
                COALESCE(u.apellido_paterno, '') AS apellido_paterno,
                COALESCE(u.apellido_materno, '') AS apellido_materno,
                COALESCE(ad.carrera, 'Sin programa') AS programa,
                COALESCE(r.nombre, 'Sin rol') AS rol,
                a.fecha,
                a.hora
            FROM Acceso a
            LEFT JOIN Usuarios u ON u.cod_institucional = a.cod_institucional
            LEFT JOIN Alumnos_Detalle ad ON ad.cod_institucional = a.cod_institucional
            LEFT JOIN Roles r ON r.id_rol = u.id_rol
            WHERE 1 = 1
        """

        params = []
        if rol and rol != "Todos los roles":
            sql += " AND COALESCE(r.nombre, 'Sin rol') = ?"
            params.append(rol)

        if mes and mes != "Mes" and mes != "Todos":
            mes_num = _MESES_NUM.get(mes)
            if mes_num:
                sql += " AND strftime('%m', a.fecha) = ?"
                params.append(mes_num)

        sql += " ORDER BY a.id_acceso DESC LIMIT 250"

        con = obtener_conexion()
        if not con:
            return

        try:
            rows = con.execute(sql, tuple(params)).fetchall()
            for i, row in enumerate(rows):
                tag = "par" if i % 2 == 0 else "impar"
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        row["cod_institucional"] or "-",
                        row["nombre"] or "-",
                        row["apellido_paterno"] or "-",
                        row["apellido_materno"] or "-",
                        row["programa"] or "-",
                        row["rol"] or "-",
                        _formatear_fecha_hora(row["fecha"], row["hora"]),
                    ),
                    tags=(tag,),
                )
        finally:
            con.close()


# ________________________FIN_3_______________________#


# __________________________4__________________________#
# Funciones de arranque


def crear_pantalla_historial_accesos(parent, app):
    PantallaHistorialAccesos(parent, app)


if __name__ == "__main__":
    class _AppDemo:
        def mostrar_pantalla(self, _nombre):
            pass

    root = tk.Tk()
    root.title("SRFC | Historial de Accesos")
    root.geometry("1024x600")
    PantallaHistorialAccesos(root, _AppDemo())
    root.mainloop()

# ________________________FIN_4_______________________#
