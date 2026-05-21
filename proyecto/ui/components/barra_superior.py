"""
ui/components/barra_superior.py

CAMBIOS vs versión anterior:
  - Botón 🌐 ahora llama a app.idioma.toggle() al hacer clic.
  - La barra se registra en GestorIdioma para actualizar los textos
    del topbar (línea1, línea2, universidad) y la fecha cuando cambia el idioma.
  - Al destruirse se desregistra de GestorIdioma y GestorTema (limpieza automática).
  - actualizar_fecha_hora() ahora usa los días/meses del idioma activo.
"""

import tkinter as tk
from datetime import datetime
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent.parent


def actualizar_fecha_hora(
    lbl_fecha: tk.Label,
    lbl_hora: tk.Label,
    root: tk.Tk,
    idioma=None,          # instancia GestorIdioma, opcional
) -> None:
    if not lbl_fecha.winfo_exists() or not lbl_hora.winfo_exists():
        return
    n = datetime.now()

    # Usar días/meses del idioma activo si está disponible
    if idioma:
        DIAS  = idioma.t("barra_superior.dias")
        MESES = idioma.t("barra_superior.meses")
    else:
        DIAS  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        MESES = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]

    # Fallback si t() devuelve string en lugar de lista (clave no encontrada)
    if not isinstance(DIAS,  list): DIAS  = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    if not isinstance(MESES, list): MESES = ["Jan","Feb","Mar","Apr","May","Jun",
                                              "Jul","Aug","Sep","Oct","Nov","Dec"]

    lbl_fecha.config(
        text=f"{DIAS[n.weekday()]} {n.day} de {MESES[n.month-1]} de {n.year}")
    hora = n.strftime("%I:%M:%S %p").lower().replace("am","a.m.").replace("pm","p.m.")
    lbl_hora.config(text=hora)
    root.after(1000, lambda: actualizar_fecha_hora(lbl_fecha, lbl_hora, root, idioma))


def crear_encabezado(parent: tk.Frame, app_o_root) -> "_BarraSuperior":
    """Construye el header y lo empaqueta en parent.

    Acepta como segundo argumento:
      - La instancia App (con .tema, .idioma y .root) → botones funcionales
      - Un tk.Tk directamente → funciona igual, botones decorativos sin acción
    """
    return _BarraSuperior(parent, app_o_root)


class _BarraSuperior(tk.Frame):

    def __init__(self, parent, app_o_root):
        # Detectar GestorTema y GestorIdioma
        self._tema   = getattr(app_o_root, "tema",   None)
        self._idioma = getattr(app_o_root, "idioma", None)

        # Obtener root para el reloj
        if isinstance(app_o_root, tk.Tk):
            self._root = app_o_root
        else:
            self._root = getattr(app_o_root, "root", parent.winfo_toplevel())

        # Colores iniciales
        p = self._tema.paleta() if self._tema else _colores_claro()

        super().__init__(parent, bg=p["topbar_bg"], height=72)
        self.pack(fill="x", side="top")
        self.pack_propagate(False)

        self._repintables = []
        self._img_refs    = []
        self._btn_tema    = None
        self._btn_idioma  = None

        # Referencias a los labels de texto del topbar (para actualizar con idioma)
        self._lbl_sistema1   = None
        self._lbl_sistema2   = None
        self._lbl_universidad = None

        self._construir(p)

        # Registrar en GestorTema
        if self._tema:
            self._tema.registrar(self._aplicar_tema)

        # Registrar en GestorIdioma
        if self._idioma:
            self._idioma.registrar(self._aplicar_idioma)

    # ── Construcción ──────────────────────────────────────────────────────────
    def _construir(self, p):
        i = self._idioma  # shorthand

        # Logo
        logo_wrap = tk.Frame(self, bg=p["topbar_bg"])
        logo_wrap.pack(side="left", padx=(14, 0), fill="y")
        self._reg(logo_wrap, "topbar_bg")

        ruta_logo = _RAIZ / "assets" / "img" / "logoudc.png"
        if ruta_logo.exists():
            try:
                raw = tk.PhotoImage(file=str(ruta_logo))
                lbl_logo = tk.Label(logo_wrap, image=raw, bg=p["topbar_bg"])
                lbl_logo.image = raw
                lbl_logo.pack()
                self._reg(lbl_logo, "topbar_bg")
            except Exception:
                self._lbl_texto(logo_wrap, "UdC", p, "topbar_bg", "topbar_titulo_fg")
        else:
            self._lbl_texto(logo_wrap, "UdC", p, "topbar_bg", "topbar_titulo_fg")

        # Separador vertical
        sep = tk.Frame(self, bg=p["topbar_separador"], width=2)
        sep.pack(side="left", fill="y", pady=14, padx=10)
        self._reg(sep, "topbar_separador")

        # Nombre del sistema — textos desde GestorIdioma si está disponible
        txt1 = i.t("topbar.sistema_linea1") if i else "SISTEMA DE CONTROL"
        txt2 = i.t("topbar.sistema_linea2") if i else "BIOMÉTRICO"
        txt3 = i.t("topbar.universidad")    if i else "Universidad de Colima"

        col = tk.Frame(self, bg=p["topbar_bg"])
        col.pack(side="left")
        self._reg(col, "topbar_bg")

        self._lbl_sistema1 = tk.Label(col, text=txt1,
                      font=("Segoe UI", 9, "bold"),
                      fg=p["topbar_titulo_fg"], bg=p["topbar_bg"])
        self._lbl_sistema1.pack(anchor="w")
        self._reg(self._lbl_sistema1, "topbar_bg", "topbar_titulo_fg")

        self._lbl_sistema2 = tk.Label(col, text=txt2,
                      font=("Segoe UI", 10, "bold"),
                      fg=p["topbar_sistema_fg"], bg=p["topbar_bg"])
        self._lbl_sistema2.pack(anchor="w")
        self._reg(self._lbl_sistema2, "topbar_bg", "topbar_sistema_fg")

        self._lbl_universidad = tk.Label(col, text=txt3,
                      font=("Segoe UI", 8),
                      fg=p["topbar_dim_fg"], bg=p["topbar_bg"])
        self._lbl_universidad.pack(anchor="w")
        self._reg(self._lbl_universidad, "topbar_bg", "topbar_dim_fg")

        # Derecha: botones + fecha/hora
        der = tk.Frame(self, bg=p["topbar_bg"])
        der.pack(side="right", padx=14, fill="y")
        self._reg(der, "topbar_bg")

        btn_f = tk.Frame(der, bg=p["topbar_bg"])
        btn_f.pack(side="right", padx=(8, 0), pady=18)
        self._reg(btn_f, "topbar_bg")

        # ── Botón idioma ← CONECTADO AL GESTORIDIOMA ─────────────────────────
        ruta_idioma = _RAIZ / "assets" / "img" / "languageIcon.png"
        self._btn_idioma = tk.Label(
            btn_f, bg=p["topbar_btn_bg"], padx=7, pady=2, cursor="hand2")
        if ruta_idioma.exists():
            img = self._cargar_img(ruta_idioma)
            if img:
                self._btn_idioma.config(image=img)
        else:
            self._btn_idioma.config(
                text="🌐", font=("Segoe UI", 14), fg=p["topbar_btn_fg"])
            self._reg(self._btn_idioma, "topbar_btn_bg", "topbar_btn_fg")
        self._btn_idioma.pack(side="right", padx=3)
        self._reg(self._btn_idioma, "topbar_btn_bg")
        self._btn_idioma.bind("<Button-1>", lambda e: self._toggle_idioma())
        self._btn_idioma.bind("<Enter>",
            lambda e: self._btn_idioma.config(bg=p["topbar_btn_hover"]))
        self._btn_idioma.bind("<Leave>",
            lambda e: self._btn_idioma.config(bg=p["topbar_btn_bg"]))

        # ── Botón modo oscuro/claro ← CONECTADO AL GESTORTEMA ────────────────
        ruta_dia = _RAIZ / "assets" / "img" / "lightModeIcon.png"
        self._btn_tema = tk.Label(
            btn_f, bg=p["topbar_btn_bg"], padx=7, pady=2, cursor="hand2")
        if ruta_dia.exists():
            img = self._cargar_img(ruta_dia)
            if img:
                self._btn_tema.config(image=img)
        else:
            icono = "☀️" if (self._tema and self._tema.es_oscuro()) else "🌙"
            self._btn_tema.config(
                text=icono, font=("Segoe UI", 14), fg=p["topbar_btn_fg"])
        self._btn_tema.pack(side="right", padx=3)
        self._btn_tema.bind("<Button-1>", lambda e: self._toggle_tema())
        self._btn_tema.bind("<Enter>",
            lambda e: self._btn_tema.config(bg=p["topbar_btn_hover"]))
        self._btn_tema.bind("<Leave>",
            lambda e: self._btn_tema.config(bg=p["topbar_btn_bg"]))

        # Fecha y hora
        dt = tk.Frame(der, bg=p["topbar_bg"])
        dt.pack(side="right", pady=10)
        self._reg(dt, "topbar_bg")

        fila_fecha = tk.Frame(dt, bg=p["topbar_bg"])
        fila_fecha.pack(anchor="e")
        self._reg(fila_fecha, "topbar_bg")

        ruta_cal = _RAIZ / "assets" / "img" / "calendar_Icon.png"
        if ruta_cal.exists():
            raw = tk.PhotoImage(file=str(ruta_cal))
            factor = max(1, round(raw.height() / 18))
            img_cal = raw.subsample(factor, factor)
            self._img_refs.append(img_cal)
            lc = tk.Label(fila_fecha, image=img_cal, bg=p["topbar_bg"])
            lc.pack(side="left", padx=(0, 4), pady=(2, 0))
            self._reg(lc, "topbar_bg")

        self._lbl_fecha = tk.Label(fila_fecha, text="",
                                    font=("Segoe UI", 10, "bold"),
                                    fg=p["topbar_fecha_fg"], bg=p["topbar_bg"])
        self._lbl_fecha.pack(side="left")
        self._reg(self._lbl_fecha, "topbar_bg", "topbar_fecha_fg")

        fila_hora = tk.Frame(dt, bg=p["topbar_bg"])
        fila_hora.pack(anchor="e")
        self._reg(fila_hora, "topbar_bg")

        ruta_clk = _RAIZ / "assets" / "img" / "clockIcon.png"
        if ruta_clk.exists():
            raw = tk.PhotoImage(file=str(ruta_clk))
            factor = max(1, round(raw.height() / 18))
            img_clk = raw.subsample(factor, factor)
            self._img_refs.append(img_clk)
            lh = tk.Label(fila_hora, image=img_clk, bg=p["topbar_bg"])
            lh.pack(side="left", padx=(0, 4))
            self._reg(lh, "topbar_bg")

        self._lbl_hora = tk.Label(fila_hora, text="",
                                   font=("Segoe UI", 10),
                                   fg=p["topbar_dim_fg"], bg=p["topbar_bg"])
        self._lbl_hora.pack(side="left")
        self._reg(self._lbl_hora, "topbar_bg", "topbar_dim_fg")

        actualizar_fecha_hora(
            self._lbl_fecha, self._lbl_hora, self._root, self._idioma)

    # ── Toggles ───────────────────────────────────────────────────────────────
    def _toggle_tema(self):
        if self._tema:
            self._tema.toggle()

    def _toggle_idioma(self):
        if self._idioma:
            self._idioma.toggle()

    # ── Respuesta al cambio de tema ───────────────────────────────────────────
    def _aplicar_tema(self, p: dict):
        try:
            self.configure(bg=p["topbar_bg"])
            for widget, bg_k, fg_k in self._repintables:
                if not widget.winfo_exists():
                    continue
                try:
                    widget.configure(bg=p[bg_k])
                    if fg_k:
                        widget.configure(fg=p[fg_k])
                except tk.TclError:
                    pass
            # Actualizar botón de tema si usa emoji
            if self._btn_tema and self._btn_tema.winfo_exists():
                self._btn_tema.configure(bg=p["topbar_btn_bg"])
                if self._btn_tema.cget("text") in ("🌙", "☀️"):
                    self._btn_tema.configure(
                        text="☀️" if self._tema.es_oscuro() else "🌙",
                        fg=p["topbar_btn_fg"])
        except tk.TclError:
            pass

    # ── Respuesta al cambio de idioma ─────────────────────────────────────────
    def _aplicar_idioma(self):
        """Actualiza los textos del topbar cuando cambia el idioma."""
        i = self._idioma
        if not i:
            return
        try:
            if self._lbl_sistema1 and self._lbl_sistema1.winfo_exists():
                self._lbl_sistema1.config(text=i.t("topbar.sistema_linea1"))
            if self._lbl_sistema2 and self._lbl_sistema2.winfo_exists():
                self._lbl_sistema2.config(text=i.t("topbar.sistema_linea2"))
            if self._lbl_universidad and self._lbl_universidad.winfo_exists():
                self._lbl_universidad.config(text=i.t("topbar.universidad"))
            # La fecha se actualiza sola en el siguiente tick del reloj
            # (ya usa self._idioma en su loop)
        except tk.TclError:
            pass

    # ── Destrucción limpia ────────────────────────────────────────────────────
    def destroy(self):
        if self._tema:
            self._tema.desregistrar(self._aplicar_tema)
        if self._idioma:
            self._idioma.desregistrar(self._aplicar_idioma)
        super().destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _reg(self, widget, bg_key, fg_key=None):
        self._repintables.append((widget, bg_key, fg_key))

    def _lbl_texto(self, parent, texto, p, bg_k, fg_k):
        lbl = tk.Label(parent, text=texto, font=("Segoe UI", 12, "bold"),
                       fg=p[fg_k], bg=p[bg_k])
        lbl.pack(pady=12)
        self._reg(lbl, bg_k, fg_k)

    def _cargar_img(self, ruta: Path, max_h: int = 24):
        try:
            raw    = tk.PhotoImage(file=str(ruta))
            factor = max(1, round(raw.height() / max_h))
            img    = raw.subsample(factor, factor)
            self._img_refs.append(img)
            return img
        except Exception:
            return None


def _colores_claro() -> dict:
    """Colores por defecto si no hay GestorTema disponible."""
    return {
        "topbar_bg":        "#1B5E20",
        "topbar_titulo_fg": "#66BB6A",
        "topbar_sistema_fg":"#ffffff",
        "topbar_fecha_fg":  "#ffffff",
        "topbar_dim_fg":    "#A5D6A7",
        "topbar_separador": "#43A047",
        "topbar_btn_bg":    "#43A047",
        "topbar_btn_fg":    "#ffffff",
        "topbar_btn_hover": "#66BB6A",
    }