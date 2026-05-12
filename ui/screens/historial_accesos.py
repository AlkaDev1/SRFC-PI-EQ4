"""
ui/screens/historial_accesos.py
Pantalla de Historial de Accesos.

CAMBIOS:
  1. _pie se empaqueta con side="bottom" ANTES que el contenido,
     garantizando que ← CERRAR siempre sea visible sin importar el tamaño
  2. Botones Rol/Mes con highlightthickness=2 y borde verde:
       - Modo claro  → #4caf50 (verde_claro)
       - Modo oscuro → #2D531A (verde_oscuro)
  3. Resto del comportamiento idéntico a la versión anterior
"""

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA
from core.database import inicializar_bd, obtener_conexion

_MESES_NUM = {
    "Enero": "01",   "Febrero": "02",  "Marzo": "03",
    "Abril": "04",   "Mayo": "05",     "Junio": "06",
    "Julio": "07",   "Agosto": "08",   "Septiembre": "09",
    "Octubre": "10", "Noviembre": "11","Diciembre": "12",
}

# ── Paleta modo claro ─────────────────────────────────────────────────────────
_C = {
    "bg_app":       "#f3f4f5",
    "card_bg":      "#ffffff",
    "texto_titulo": "#1f2328",
    "texto_oscuro": "#1f2328",
    "texto_gris":   "#6b7280",
    "borde":        "#d8dce1",
    "header_tabla": "#43a047",
    "fila_par":     "#f7f7f7",
    "fila_impar":   "#ececec",
    "sel_tree":     "#d6eedd",
    "sel_tree_fg":  "#2e7d32",
    "btn_bg":       "#43a047",
    "btn_hover":    "#2e7d32",
    "btn_fg":       "#ffffff",
    "filtro_bg":    "#ffffff",   # blanco — contrasta claramente sobre fondo gris
    "filtro_borde": "#43a047",   # verde sólido, borde bien visible en modo claro
    "filtro_fg":    "#1f2328",
    "flecha_img":   "arrow_circle_black.png",
}

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
_O = {
    "bg_app":       "#071E07",
    "card_bg":      "#0d2a0d",
    "texto_titulo": "#d0f0d0",
    "texto_oscuro": "#d0f0d0",
    "texto_gris":   "#7aaa7a",
    "borde":        "#1a3a1a",
    "header_tabla": "#2D531A",
    "fila_par":     "#0d2a0d",
    "fila_impar":   "#071E07",
    "sel_tree":     "#1a3a1a",
    "sel_tree_fg":  "#4ade80",
    "btn_bg":       "#2D531A",
    "btn_hover":    "#477023",
    "btn_fg":       "#ffffff",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",   # verde medio — visible sobre fondo verde muy oscuro
    "filtro_fg":    "#d0f0d0",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaHistorialAccesos:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._p     = _paleta(app)
        self._filtro_rol = tk.StringVar(value="Todos los roles")
        self._filtro_mes = tk.StringVar(value="Mes")
        self._ico_flecha = None
        self._widgets_repintables = []

        inicializar_bd()
        self._construir_ui()
        self._cargar_datos()

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
            self.pantalla.configure(bg=p["bg_app"])
            self._cont.configure(bg=p["bg_app"])
            self._barra_filtros.configure(bg=p["bg_app"])
            self._filtros_frame.configure(bg=p["bg_app"])
            self._card.configure(bg=p["card_bg"], highlightbackground=p["borde"])
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

            # Botones filtro — borde verde según tema
            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_mes):
                try:
                    btn.configure(
                        bg=p["filtro_bg"],
                        fg=p["filtro_fg"],
                        highlightthickness=2,
                        highlightbackground=p["filtro_borde"],
                        activebackground=p["borde"],
                        image=self._ico_flecha,
                    )
                except tk.TclError:
                    pass

            try:
                self._btn_cerrar.configure(bg=p["btn_bg"], fg=p["btn_fg"],
                                            activebackground=p["btn_hover"])
            except tk.TclError:
                pass

            s = ttk.Style()
            s.configure("Historial.Treeview",
                        background=p["card_bg"], foreground=p["texto_oscuro"],
                        fieldbackground=p["card_bg"])
            s.configure("Historial.Treeview.Heading",
                        background=p["header_tabla"], foreground="#ffffff")
            s.map("Historial.Treeview",
                  background=[("selected", p["sel_tree"])],
                  foreground=[("selected", p["sel_tree_fg"])])
            self.tree.tag_configure("par",   background=p["fila_par"])
            self.tree.tag_configure("impar", background=p["fila_impar"])

        except tk.TclError:
            pass

    def _limpiar_tema(self, event=None):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._on_tema_cambio)

    def _reg(self, widget, bg_k, fg_k=None):
        self._widgets_repintables.append((widget, bg_k, fg_k))

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p

        # Marco raíz — ocupa todo el parent igual que PantallaGestion
        self.pantalla = tk.Frame(self.parent, bg=p["bg_app"])
        self.pantalla.pack(fill="both", expand=True)

        # Encabezado + separador
        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        # ── PIE con side="bottom" PRIMERO: tkinter lo reserva antes del contenido
        #    Así siempre queda visible aunque la tabla sea grande
        self._pie = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._pie.pack(side="bottom", fill="x", padx=20, pady=(8, 12))

        self._btn_cerrar = tk.Button(
            self._pie,
            text="← CERRAR",
            font=("Segoe UI", 10, "bold"),
            bg=p["btn_bg"], fg=p["btn_fg"],
            activebackground=p["btn_hover"], activeforeground="#ffffff",
            relief="flat", bd=0, cursor="hand2",
            padx=18, pady=10,
            command=self._cerrar,
        )
        self._btn_cerrar.pack(side="left")

        # ── Contenido principal — ocupa lo que sobra tras el pie
        self._cont = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._cont.pack(fill="both", expand=True, padx=20, pady=(14, 0))

        # Título
        lbl_titulo = tk.Label(self._cont, text="HISTORIAL DE ACCESOS",
                               font=("Segoe UI", 20, "bold"),
                               fg=p["texto_titulo"], bg=p["bg_app"])
        lbl_titulo.pack(anchor="w", pady=(0, 8))
        self._reg(lbl_titulo, "bg_app", "texto_titulo")

        # Barra de filtros
        self._barra_filtros = tk.Frame(self._cont, bg=p["bg_app"])
        self._barra_filtros.pack(fill="x", pady=(0, 8))

        self._filtros_frame = tk.Frame(self._barra_filtros, bg=p["bg_app"])
        self._filtros_frame.pack(side="right")

        self._recargar_ico_flecha()
        self._construir_botones_filtro()

        # Card con la tabla
        self._card = tk.Frame(self._cont, bg=p["card_bg"],
                               highlightthickness=1, highlightbackground=p["borde"])
        self._card.pack(fill="both", expand=True)

        self._construir_tabla()

    def _recargar_ico_flecha(self):
        if not _PIL_OK:
            self._ico_flecha = None
            return
        try:
            ruta = BASE_DIR / "assets" / "img" / self._p["flecha_img"]
            img  = Image.open(ruta).convert("RGBA").resize((16, 16), Image.LANCZOS)
            self._ico_flecha = ImageTk.PhotoImage(img)
        except Exception:
            self._ico_flecha = None

    def _construir_botones_filtro(self):
        p = self._p

        def _abrir_menu_rol(event, btn):
            cp = self._p
            menu = tk.Menu(self._filtros_frame, tearoff=0,
                           font=("Segoe UI", 9), bg=cp["card_bg"],
                           fg=cp["texto_oscuro"],
                           activebackground=cp["btn_bg"],
                           activeforeground="#ffffff")
            for op in ["Todos los roles", "Alumno", "Admin", "Profesor", "SuperAdmin", "SuperUsuario"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._filtro_rol.set(o),
                                          btn.config(text=f"  {o}"),
                                          self._cargar_datos()])
            menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

        self._btn_rol = tk.Button(
            self._filtros_frame,
            text="  Todos los roles",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=2,
            highlightbackground=p["filtro_borde"],   # ← borde verde
            cursor="hand2")
        self._btn_rol.bind("<Button-1>", lambda e: _abrir_menu_rol(e, self._btn_rol))
        self._btn_rol.pack(side="left", padx=(0, 8))

        def _abrir_menu_mes(event, btn):
            cp = self._p
            menu = tk.Menu(self._filtros_frame, tearoff=0,
                           font=("Segoe UI", 9), bg=cp["card_bg"],
                           fg=cp["texto_oscuro"],
                           activebackground=cp["btn_bg"],
                           activeforeground="#ffffff")
            for op in ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo",
                       "Junio", "Julio", "Agosto", "Septiembre",
                       "Octubre", "Noviembre", "Diciembre"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._filtro_mes.set(o),
                                          btn.config(text=f"  {o}"),
                                          self._cargar_datos()])
            menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())

        self._btn_mes = tk.Button(
            self._filtros_frame,
            text="  Mes",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=2,
            highlightbackground=p["filtro_borde"],   # ← borde verde
            cursor="hand2")
        self._btn_mes.bind("<Button-1>", lambda e: _abrir_menu_mes(e, self._btn_mes))
        self._btn_mes.pack(side="left")

    def _construir_tabla(self):
        p = self._p
        s = ttk.Style(self.pantalla)
        s.theme_use("clam")
        s.configure("Historial.Treeview",
                    background=p["card_bg"], foreground=p["texto_oscuro"],
                    fieldbackground=p["card_bg"],
                    rowheight=36, font=("Segoe UI", 9), borderwidth=0)
        s.configure("Historial.Treeview.Heading",
                    background=p["header_tabla"], foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Historial.Treeview",
              background=[("selected", p["sel_tree"])],
              foreground=[("selected", p["sel_tree_fg"])])

        columnas = ("No. Institucional", "Nombre", "Ap.Paterno",
                    "Ap.Materno", "Programa", "Rol", "Fecha y Hora")

        self.tree = ttk.Treeview(self._card, columns=columnas,
                                  show="headings", style="Historial.Treeview")

        anchos = {
            "No. Institucional":  90,
            "Nombre":             80,
            "Ap.Paterno":   90,
            "Ap.Materno":         90,
            "Programa":           130,
            "Rol":                60,
            "Fecha y Hora":       100,
        }
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=anchos.get(col, 80), minwidth=40,
                             stretch=True, anchor="center")

        self.tree.tag_configure("par",   background=p["fila_par"])
        self.tree.tag_configure("impar", background=p["fila_impar"])

        self.tree.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  DATOS
    # ══════════════════════════════════════════════════════════════════════════
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
        if mes and mes not in ("Mes", "Todos"):
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
                self.tree.insert("", "end", tags=(tag,),
                    values=(
                        row["cod_institucional"] or "-",
                        row["nombre"] or "-",
                        row["apellido_paterno"] or "-",
                        row["apellido_materno"] or "-",
                        row["programa"] or "-",
                        row["rol"] or "-",
                        self._fmt_fecha(row["fecha"], row["hora"]),
                    ))
        finally:
            con.close()

    @staticmethod
    def _fmt_fecha(fecha, hora):
        if not fecha:
            return "-"
        try:
            d = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_txt = d.strftime("%d/%m/%y")
        except Exception:
            fecha_txt = fecha
        return f"{fecha_txt} {hora or '--:--'}"

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _cerrar(self):
        if hasattr(self.app, "mostrar_pantalla"):
            self.app.mostrar_pantalla("gestion_real")
        else:
            self.parent.winfo_toplevel().destroy()


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