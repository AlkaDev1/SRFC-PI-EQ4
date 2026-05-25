"""
ui/screens/historial_accesos.py

FIXES:
  - Un solo menú abierto a la vez (cerrar el anterior antes de abrir otro)
  - Al cambiar idioma se destruyen los menús abiertos antes de reconstruir
  - Menús usan unpost() + destroy() para limpieza completa
  - FIX: filas de accesos denegados se pintan en rojo
  - FIX: historial muestra TODOS los accesos (concedidos y denegados)
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
    "Enero":"01","Febrero":"02","Marzo":"03","Abril":"04",
    "Mayo":"05","Junio":"06","Julio":"07","Agosto":"08",
    "Septiembre":"09","Octubre":"10","Noviembre":"11","Diciembre":"12",
    "January":"01","February":"02","March":"03","April":"04",
    "May":"05","June":"06","July":"07","August":"08",
    "September":"09","October":"10","November":"11","December":"12",
}

_C = {
    "bg_app":"#f3f4f5","card_bg":"#ffffff","texto_titulo":"#1f2328",
    "texto_oscuro":"#1f2328","texto_gris":"#6b7280","borde":"#d8dce1",
    "header_tabla":"#43a047","fila_par":"#f7f7f7","fila_impar":"#ececec",
    "sel_tree":"#d6eedd","sel_tree_fg":"#2e7d32","btn_bg":"#43a047",
    "btn_hover":"#2e7d32","btn_fg":"#ffffff","filtro_bg":"#ffffff",
    "filtro_borde":"#43a047","filtro_fg":"#1f2328",
    "flecha_img":"arrow_circle_black.png",
    # Colores para filas denegadas
    "fila_denegada_bg":"#ffebee","fila_denegada_fg":"#c62828",
}
_O = {
    "bg_app":"#071E07","card_bg":"#0d2a0d","texto_titulo":"#d0f0d0",
    "texto_oscuro":"#d0f0d0","texto_gris":"#7aaa7a","borde":"#1a3a1a",
    "header_tabla":"#2D531A","fila_par":"#0d2a0d","fila_impar":"#071E07",
    "sel_tree":"#1a3a1a","sel_tree_fg":"#4ade80","btn_bg":"#2D531A",
    "btn_hover":"#477023","btn_fg":"#ffffff","filtro_bg":"#1a3a1a",
    "filtro_borde":"#477023","filtro_fg":"#d0f0d0",
    "flecha_img":"arrow_drop_down.png",
    # Colores para filas denegadas (tema oscuro)
    "fila_denegada_bg":"#3b0f0f","fila_denegada_fg":"#f87171",
}


def _paleta(app):
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


class PantallaHistorialAccesos:

    def __init__(self, parent, app, datos=None):
        self.parent  = parent
        self.app     = app
        self._p      = _paleta(app)
        self._id_rol = (datos or {}).get("id_rol")

        self._filtro_rol = tk.StringVar(value="")
        self._filtro_mes = tk.StringVar(value="")
        self._ico_flecha = None
        self._widgets_repintables = []
        self._menu_abierto = None

        inicializar_bd()
        self._construir_ui()
        self._cargar_datos()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        if hasattr(app, "idioma"):
            app.idioma.registrar(self._aplicar_idioma)

        self.pantalla.bind("<Destroy>", self._limpiar)

    # ── Helpers de idioma ─────────────────────────────────────────────────────
    def _t(self, clave, fallback=""):
        if hasattr(self.app, "idioma"):
            return self.app.idioma.t(clave, fallback)
        return fallback or clave

    def _opciones_rol(self):
        v = self._t("historial.roles")
        return v if isinstance(v, list) else \
            ["Todos los roles", "Alumno", "Admin", "Profesor", "SuperAdmin", "SuperUsuario"]

    def _opciones_mes(self):
        v = self._t("historial.meses")
        return v if isinstance(v, list) else \
            ["Mes", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def _columnas(self):
        v = self._t("historial.columnas")
        return v if isinstance(v, list) else \
            ["No. Institucional", "Nombre", "Ap.Paterno",
             "Ap.Materno", "Programa", "Rol", "Fecha y Hora"]

    # ── Cerrar menú abierto ───────────────────────────────────────────────────
    def _cerrar_menu(self):
        if self._menu_abierto:
            try:
                self._menu_abierto.unpost()
                self._menu_abierto.destroy()
            except Exception:
                pass
            self._menu_abierto = None

    # ── Aplicar idioma ────────────────────────────────────────────────────────
    def _aplicar_idioma(self):
        self._cerrar_menu()
        try:
            self._lbl_titulo.config(
                text=self._t("historial.titulo", "HISTORIAL DE ACCESOS"))
            self._btn_cerrar.config(
                text=self._t("historial.btn_cerrar", "← CERRAR"))

            primera_rol = self._opciones_rol()[0]
            self._filtro_rol.set(primera_rol)
            self._btn_rol.config(text=f"  {primera_rol}")

            primera_mes = self._opciones_mes()[0]
            self._filtro_mes.set(primera_mes)
            self._btn_mes.config(text=f"  {primera_mes}")

            for i, col in enumerate(self._columnas()):
                col_id = self.tree["columns"][i]
                self.tree.heading(col_id, text=col)

            self._cargar_datos()
        except tk.TclError:
            pass

    # ── Tema ──────────────────────────────────────────────────────────────────
    def _on_tema_cambio(self, _):
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

            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_mes):
                try:
                    btn.configure(bg=p["filtro_bg"], fg=p["filtro_fg"],
                                  highlightthickness=2,
                                  highlightbackground=p["filtro_borde"],
                                  activebackground=p["borde"],
                                  image=self._ico_flecha)
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
            self.tree.tag_configure("par",      background=p["fila_par"])
            self.tree.tag_configure("impar",    background=p["fila_impar"])
            # FIX: reconfigurar tag denegado con colores del tema
            self.tree.tag_configure("denegado",
                                    background=p["fila_denegada_bg"],
                                    foreground=p["fila_denegada_fg"])
        except tk.TclError:
            pass

    def _limpiar(self, event=None):
        self._cerrar_menu()
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._on_tema_cambio)
        if hasattr(self.app, "idioma"):
            self.app.idioma.desregistrar(self._aplicar_idioma)

    def _reg(self, widget, bg_k, fg_k=None):
        self._widgets_repintables.append((widget, bg_k, fg_k))

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg_app"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        self._pie = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._pie.pack(side="bottom", fill="x", padx=20, pady=(8, 12))

        self._btn_cerrar = tk.Button(
            self._pie,
            text=self._t("historial.btn_cerrar", "← CERRAR"),
            font=("Segoe UI", 10, "bold"),
            bg=p["btn_bg"], fg=p["btn_fg"],
            activebackground=p["btn_hover"], activeforeground="#ffffff",
            relief="flat", bd=0, cursor="hand2", padx=18, pady=10,
            command=self._cerrar)
        self._btn_cerrar.pack(side="left")

        self._cont = tk.Frame(self.pantalla, bg=p["bg_app"])
        self._cont.pack(fill="both", expand=True, padx=20, pady=(14, 0))

        self._lbl_titulo = tk.Label(
            self._cont,
            text=self._t("historial.titulo", "HISTORIAL DE ACCESOS"),
            font=("Segoe UI", 20, "bold"),
            fg=p["texto_titulo"], bg=p["bg_app"])
        self._lbl_titulo.pack(anchor="w", pady=(0, 8))
        self._reg(self._lbl_titulo, "bg_app", "texto_titulo")

        self._barra_filtros = tk.Frame(self._cont, bg=p["bg_app"])
        self._barra_filtros.pack(fill="x", pady=(0, 8))

        self._filtros_frame = tk.Frame(self._barra_filtros, bg=p["bg_app"])
        self._filtros_frame.pack(side="right")

        self._recargar_ico_flecha()
        self._construir_botones_filtro()

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

    def _abrir_menu(self, btn, opciones, var, callback):
        """Abre un menú, cerrando primero cualquier otro que esté abierto."""
        self._cerrar_menu()
        cp = self._p
        menu = tk.Menu(self.pantalla, tearoff=0, font=("Segoe UI", 9),
                       bg=cp["card_bg"], fg=cp["texto_oscuro"],
                       activebackground=cp["btn_bg"], activeforeground="#ffffff")

        def _seleccionar(op):
            self._cerrar_menu()
            var.set(op)
            btn.config(text=f"  {op}")
            callback()

        for op in opciones:
            menu.add_command(label=op, command=lambda o=op: _seleccionar(o))

        self._menu_abierto = menu
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        menu.post(x, y)

    def _construir_botones_filtro(self):
        p = self._p
        primera_rol = self._opciones_rol()[0]
        self._filtro_rol.set(primera_rol)

        self._btn_rol = tk.Button(
            self._filtros_frame, text=f"  {primera_rol}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"], activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=2, highlightbackground=p["filtro_borde"],
            cursor="hand2",
            command=lambda: self._abrir_menu(
                self._btn_rol, self._opciones_rol(),
                self._filtro_rol, self._cargar_datos))
        self._btn_rol.pack(side="left", padx=(0, 8))

        primera_mes = self._opciones_mes()[0]
        self._filtro_mes.set(primera_mes)

        self._btn_mes = tk.Button(
            self._filtros_frame, text=f"  {primera_mes}",
            image=self._ico_flecha, compound="right",
            font=("Segoe UI", 9, "bold"),
            fg=p["filtro_fg"], bg=p["filtro_bg"], activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=5,
            highlightthickness=2, highlightbackground=p["filtro_borde"],
            cursor="hand2",
            command=lambda: self._abrir_menu(
                self._btn_mes, self._opciones_mes(),
                self._filtro_mes, self._cargar_datos))
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

        col_ids  = [f"col{i}" for i in range(7)]
        col_txts = self._columnas()
        anchos   = [90, 80, 90, 90, 130, 60, 100]

        self.tree = ttk.Treeview(self._card, columns=col_ids,
                                  show="headings", style="Historial.Treeview")
        for i, cid in enumerate(col_ids):
            self.tree.heading(cid, text=col_txts[i] if i < len(col_txts) else cid)
            self.tree.column(cid, width=anchos[i], minwidth=40,
                             stretch=True, anchor="center")

        self.tree.tag_configure("par",   background=p["fila_par"])
        self.tree.tag_configure("impar", background=p["fila_impar"])
        # FIX: tag para filas denegadas (fondo rojo claro, texto rojo)
        self.tree.tag_configure("denegado",
                                background=p["fila_denegada_bg"],
                                foreground=p["fila_denegada_fg"])
        self.tree.pack(fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cargar_datos(self):
        self.tree.delete(*self.tree.get_children())
        rol = self._filtro_rol.get().strip()
        mes = self._filtro_mes.get().strip()

        # FIX: traer TODOS los accesos (concedidos y denegados) con campo denegado
        sql = """
            SELECT a.cod_institucional,
                   a.denegado,
                   COALESCE(u.primer_nombre,'') AS nombre,
                   COALESCE(u.apellido_paterno,'') AS apellido_paterno,
                   COALESCE(u.apellido_materno,'') AS apellido_materno,
                   COALESCE(ad.carrera,'Sin programa') AS programa,
                   COALESCE(r.nombre,'Sin rol') AS rol,
                   a.fecha, a.hora
            FROM Acceso a
            LEFT JOIN Usuarios u ON u.cod_institucional = a.cod_institucional
            LEFT JOIN Alumnos_Detalle ad ON ad.cod_institucional = a.cod_institucional
            LEFT JOIN Roles r ON r.id_rol = u.id_rol
            WHERE 1=1
        """
        params = []

        # Primera opción de roles = sin filtro
        sin_filtro_rol = [self._opciones_rol()[0],
                          "Ninguno", "Todos los roles", "All roles"]
        if rol and rol not in sin_filtro_rol:
            sql += " AND COALESCE(r.nombre,'Sin rol') = ?"
            params.append(rol)

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
                # FIX: filas denegadas usan el tag "denegado" (rojo)
                if row["denegado"]:
                    tag = "denegado"
                else:
                    tag = "par" if i % 2 == 0 else "impar"

                self.tree.insert("", "end", tags=(tag,), values=(
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
            fecha_txt = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%y")
        except Exception:
            fecha_txt = fecha
        return f"{fecha_txt} {hora or '--:--'}"

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _cerrar(self):
        if not hasattr(self.app, "mostrar_pantalla"):
            self.parent.winfo_toplevel().destroy()
            return
        if self._id_rol in (1, 2):
            self.app.mostrar_pantalla("gestion_real")
        else:
            self.app.mostrar_pantalla("principal")


def crear_pantalla_historial_accesos(parent, app, datos=None):
    PantallaHistorialAccesos(parent, app, datos)


if __name__ == "__main__":
    class _AppDemo:
        def mostrar_pantalla(self, _n, _d=None):
            pass
    root = tk.Tk()
    root.title("SRFC | Historial de Accesos")
    root.geometry("1024x600")
    PantallaHistorialAccesos(root, _AppDemo())
    root.mainloop()