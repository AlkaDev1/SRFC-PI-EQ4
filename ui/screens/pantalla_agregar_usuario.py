"""
ui/screens/pantalla_agregar_usuario.py
Pantalla de Agregar Usuario -- 800x480 tactil (Raspberry Pi 5)

CAMBIOS:
  - Soporte completo de tema oscuro/claro via GestorTema
  - Dropdowns Rol/Status usan tk.Button + tk.Menu con icono flecha
    (arrow_circle_black.png claro / arrow_drop_down.png oscuro)
    igual que pantalla_editar_usuario.py y pantalla_gestion.py
"""

import tkinter as tk
from tkinter import messagebox
import threading
import shutil
import os
from pathlib import Path

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RAIZ = Path(__file__).resolve().parents[2]

# ── Fuentes ───────────────────────────────────────────────────────────────────
_F_LABEL   = ("Segoe UI", 8)
_F_ENTRY   = ("Segoe UI", 10)
_F_BTN     = ("Segoe UI", 10, "bold")
_F_INSTRUC = ("Segoe UI", 9)
_F_CAM_MSG = ("Segoe UI", 12, "bold")
_F_CAM_SUB = ("Segoe UI", 9, "bold")

CAPTURAS_REQUERIDAS = 30

# ── Paleta modo claro ─────────────────────────────────────────────────────────
_C = {
    "bg":           "#ffffff",
    "cam_bg":       "#1c1c1c",
    "texto":        "#1c1c1c",
    "texto2":       "#757575",
    "borde":        "#e0e0e0",
    "campo_bg":     "#ffffff",
    "campo_dis":    "#f5f5f5",
    "verde":        "#2e7d32",
    "verde_m":      "#4caf50",
    "verde_btn":    "#4caf50",
    "verde_hover":  "#388e3c",
    "rojo_btn":     "#e53935",
    "rojo_hover":   "#b71c1c",
    "cam_fg":       "#ffffff",
    "cam_sub_fg":   "#aaaaaa",
    "icono_circulo":"#e0e0e0",
    "icono_fill":   "#9e9e9e",
    "icono_borde":  "#bdbdbd",
    "aviso_fg":     "#e53935",
    "filtro_bg":    "#f5f5f5",
    "filtro_borde": "#43a047",
    "filtro_fg":    "#1a1a1a",
    "flecha_img":   "arrow_circle_black.png",
}

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
_O = {
    "bg":           "#071E07",
    "cam_bg":       "#0a1a0a",
    "texto":        "#d0f0d0",
    "texto2":       "#7aaa7a",
    "borde":        "#1a3a1a",
    "campo_bg":     "#1a3a1a",
    "campo_dis":    "#0d2a0d",
    "verde":        "#2D531A",
    "verde_m":      "#477023",
    "verde_btn":    "#2D531A",
    "verde_hover":  "#477023",
    "rojo_btn":     "#7f1d1d",
    "rojo_hover":   "#991b1b",
    "cam_fg":       "#d0f0d0",
    "cam_sub_fg":   "#7aaa7a",
    "icono_circulo":"#1a3a1a",
    "icono_fill":   "#2d5a2d",
    "icono_borde":  "#1a3a1a",
    "aviso_fg":     "#f87171",
    "filtro_bg":    "#1a3a1a",
    "filtro_borde": "#477023",
    "filtro_fg":    "#d0f0d0",
    "flecha_img":   "arrow_drop_down.png",
}


def _paleta(app) -> dict:
    if hasattr(app, "tema") and app.tema.es_oscuro():
        return _O
    return _C


# ═══════════════════════════════════════════════════════════════════════════════
class PantallaAgregarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent       = parent
        self.app          = app
        self.datos        = datos or {}
        self._p           = _paleta(app)
        self._capturas_ok = 0
        self._capturando  = False
        self._hilo_camara = None
        self._last_photo  = None
        self._ico_flecha  = None
        self._widgets_repintables = []
        self._btn_rol    = None
        self._btn_status = None

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════════════════════════════════════
    #  SOPORTE DE TEMA
    # ══════════════════════════════════════════════════════════════════════════
    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

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

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg"])
            self._cuerpo.configure(bg=p["bg"])

            # Columna cámara
            self._col_cam_frame.configure(bg=p["cam_bg"])
            self._feed_wrap.configure(bg=p["cam_bg"])
            self._lbl_feed.configure(bg=p["cam_bg"])
            self._icono_cam.configure(bg=p["cam_bg"])
            self._pie_cam.configure(bg=p["cam_bg"])
            self._lbl_cam_msg.configure(bg=p["cam_bg"], fg=p["cam_fg"])
            self._lbl_cam_sub.configure(bg=p["cam_bg"], fg=p["cam_sub_fg"])

            if not self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
                self._btn_captura.configure(bg=p["verde_btn"],
                                            activebackground=p["verde_hover"])
            elif self._capturando:
                self._btn_captura.configure(bg=p["rojo_btn"],
                                            activebackground=p["rojo_hover"])
            else:
                self._btn_captura.configure(bg=p["verde"])

            # Columna formulario
            self._col_form_frame.configure(bg=p["bg"],
                                           highlightbackground=p["borde"])
            self._barra_verde.configure(bg=p["verde_m"])
            self._encab.configure(bg=p["bg"])
            self._lbl_instruc.configure(bg=p["bg"], fg=p["texto2"])
            self._canvas_icono.configure(bg=p["bg"])
            self._redibujar_icono_usuario()
            self._form.configure(bg=p["bg"])
            self._pie_form.configure(bg=p["bg"])
            self._lbl_aviso.configure(bg=p["bg"], fg=p["aviso_fg"])
            self._btn_confirmar.configure(bg=p["verde_btn"],
                                          activebackground=p["verde_hover"])
            self._btn_cancelar.configure(bg=p["rojo_btn"],
                                         activebackground=p["rojo_hover"])

            # Widgets genéricos
            for widget, bg_k, fg_k in self._widgets_repintables:
                try:
                    if not widget.winfo_exists():
                        continue
                    widget.configure(bg=p[bg_k])
                    if fg_k:
                        widget.configure(fg=p[fg_k])
                except tk.TclError:
                    pass

            # Entries
            for key, ent in self._entradas.items():
                try:
                    if ent.cget("state") == "disabled":
                        ent.configure(disabledbackground=p["campo_dis"],
                                      disabledforeground=p["texto2"],
                                      highlightbackground=p["borde"])
                    else:
                        ent.configure(bg=p["campo_bg"], fg=p["texto"],
                                      highlightbackground=p["borde"],
                                      insertbackground=p["texto"])
                except tk.TclError:
                    pass

            # Botones dropdown
            self._recargar_ico_flecha()
            for btn in (self._btn_rol, self._btn_status):
                if btn is None:
                    continue
                try:
                    btn.configure(
                        bg=p["filtro_bg"], fg=p["filtro_fg"],
                        highlightbackground=p["filtro_borde"],
                        activebackground=p["borde"],
                        image=self._ico_flecha)
                except tk.TclError:
                    pass

        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  UI PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        self._cuerpo = tk.Frame(self.pantalla, bg=p["bg"])
        self._cuerpo.pack(fill="both", expand=True)
        self._cuerpo.columnconfigure(0, weight=47)
        self._cuerpo.columnconfigure(1, weight=53)
        self._cuerpo.rowconfigure(0, weight=1)

        self._construir_col_camara(self._cuerpo)
        self._construir_col_formulario(self._cuerpo)

    # ══════════════════════════════════════════════════════════════════════════
    #  COLUMNA IZQUIERDA — cámara
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_col_camara(self, parent):
        p = self._p
        self._col_cam_frame = tk.Frame(parent, bg=p["cam_bg"])
        self._col_cam_frame.grid(row=0, column=0, sticky="nsew")

        self._feed_wrap = tk.Frame(self._col_cam_frame, bg=p["cam_bg"])
        self._feed_wrap.pack(fill="both", expand=True)
        self._feed_wrap.pack_propagate(False)

        self._lbl_feed = tk.Label(self._feed_wrap, bg=p["cam_bg"], relief="flat")
        self._lbl_feed.place(x=0, y=0, relwidth=1, relheight=1)

        self._icono_cam = tk.Label(
            self._feed_wrap, text="", font=("Segoe UI", 40),
            fg="#444466", bg=p["cam_bg"])
        self._icono_cam.place(relx=0.5, rely=0.42, anchor="center")

        self._pie_cam = tk.Frame(self._col_cam_frame, bg=p["cam_bg"])
        self._pie_cam.pack(fill="x", padx=14, pady=(6, 10))

        self._lbl_cam_msg = tk.Label(
            self._pie_cam, text="INGRESE EL CÓDIGO PRIMERO",
            font=_F_CAM_MSG, fg=p["cam_fg"], bg=p["cam_bg"], justify="center")
        self._lbl_cam_msg.pack()

        self._lbl_cam_sub = tk.Label(
            self._pie_cam, text="luego presione Capturar Rostro",
            font=_F_CAM_SUB, fg=p["cam_sub_fg"], bg=p["cam_bg"], justify="center")
        self._lbl_cam_sub.pack(pady=(0, 8))

        self._btn_captura = tk.Button(
            self._pie_cam, text="CAPTURAR ROSTRO",
            font=_F_BTN, fg="#ffffff",
            bg=p["verde_btn"], activebackground=p["verde_hover"],
            activeforeground="#ffffff",
            bd=0, padx=20, pady=10, relief="flat", cursor="hand2",
            command=self._toggle_captura, state="disabled")
        self._btn_captura.pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  COLUMNA DERECHA — formulario
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_col_formulario(self, parent):
        p = self._p
        self._col_form_frame = tk.Frame(
            parent, bg=p["bg"],
            highlightthickness=1, highlightbackground=p["borde"])
        self._col_form_frame.grid(row=0, column=1, sticky="nsew")

        self._barra_verde = tk.Frame(self._col_form_frame, bg=p["verde_m"], height=8)
        self._barra_verde.pack(fill="x")

        self._encab = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._encab.pack(fill="x", pady=(8, 2), padx=16)

        self._canvas_icono = tk.Canvas(
            self._encab, width=60, height=60,
            bg=p["bg"], highlightthickness=0)
        self._canvas_icono.pack()
        self._redibujar_icono_usuario()

        self._lbl_instruc = tk.Label(
            self._encab,
            text="Ingrese el rostro y los datos de la persona para ingresarla al sistema",
            font=_F_INSTRUC, fg=p["texto2"], bg=p["bg"],
            justify="center", wraplength=340)
        self._lbl_instruc.pack(pady=(4, 0))

        self._form = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._form.pack(fill="both", expand=True, padx=16, pady=(4, 2))
        self._form.columnconfigure(0, weight=1)
        self._form.columnconfigure(1, weight=1)

        campos = [
            (0, 0, "Codigo Institucional", "cod_institucional", True),
            (0, 1, "Nombre(s)",            "nombre",            True),
            (1, 0, "Apellido Paterno",     "apellido_paterno",  True),
            (1, 1, "Apellido Materno",     "apellido_materno",  True),
            (2, 0, "Programa Academico",   "carrera",           True),
        ]
        self._entradas = {}
        for row, col_i, lbl, key, edit in campos:
            self._campo(self._form, row, col_i, lbl, key, edit)

        self._entradas["cod_institucional"].bind("<KeyRelease>", self._validar_cod)

        # ── Rol (fila 2, col 1) ───────────────────────────────────────────────
        self._rol_var = tk.StringVar(value=self.datos.get("rol", "Alumno"))
        sub_rol = tk.Frame(self._form, bg=p["bg"])
        sub_rol.grid(row=2, column=1, padx=(6, 0), pady=3, sticky="ew")
        self._reg(sub_rol, "bg")

        lbl_rol = tk.Label(sub_rol, text="Rol", font=_F_LABEL,
                           fg=p["texto2"], bg=p["bg"])
        lbl_rol.pack(anchor="w")
        self._reg(lbl_rol, "bg", "texto2")

        self._recargar_ico_flecha()

        def _abrir_rol(event, btn):
            cp = self._p
            menu = tk.Menu(sub_rol, tearoff=0, font=_F_ENTRY,
                           bg=cp["bg"], fg=cp["texto"],
                           activebackground=cp["verde_m"],
                           activeforeground="#ffffff")
            for op in ["Alumno", "Maestro", "Admin", "Super Admin"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._rol_var.set(o),
                                          btn.config(text=f"  {o}")])
            menu.tk_popup(btn.winfo_rootx(),
                          btn.winfo_rooty() + btn.winfo_height())

        self._btn_rol = tk.Button(
            sub_rol,
            text=f"  {self._rol_var.get()}",
            image=self._ico_flecha, compound="right",
            font=_F_ENTRY, anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=6,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2")
        self._btn_rol.bind("<Button-1>", lambda e: _abrir_rol(e, self._btn_rol))
        self._btn_rol.pack(fill="x", ipady=2, pady=(2, 0))

        # ── Status (fila 3, col 0+1) ──────────────────────────────────────────
        self._status_var = tk.StringVar(value=self.datos.get("status", "Activo"))
        sub_st = tk.Frame(self._form, bg=p["bg"])
        sub_st.grid(row=3, column=0, columnspan=2, pady=3, sticky="ew")
        self._reg(sub_st, "bg")

        lbl_st = tk.Label(sub_st, text="Status", font=_F_LABEL,
                          fg=p["texto2"], bg=p["bg"])
        lbl_st.pack(anchor="w")
        self._reg(lbl_st, "bg", "texto2")

        def _abrir_status(event, btn):
            cp = self._p
            menu = tk.Menu(sub_st, tearoff=0, font=_F_ENTRY,
                           bg=cp["bg"], fg=cp["texto"],
                           activebackground=cp["verde_m"],
                           activeforeground="#ffffff")
            for op in ["Activo", "Inactivo"]:
                menu.add_command(label=op,
                    command=lambda o=op: [self._status_var.set(o),
                                          btn.config(text=f"  {o}")])
            menu.tk_popup(btn.winfo_rootx(),
                          btn.winfo_rooty() + btn.winfo_height())

        self._btn_status = tk.Button(
            sub_st,
            text=f"  {self._status_var.get()}",
            image=self._ico_flecha, compound="right",
            font=_F_ENTRY, anchor="w",
            fg=p["filtro_fg"], bg=p["filtro_bg"],
            activebackground=p["borde"],
            relief="flat", bd=0, padx=8, pady=6,
            highlightthickness=1, highlightbackground=p["filtro_borde"],
            cursor="hand2")
        self._btn_status.bind("<Button-1>",
                              lambda e: _abrir_status(e, self._btn_status))
        self._btn_status.pack(fill="x", ipady=2, pady=(2, 0))

        # ── Pie con botones ───────────────────────────────────────────────────
        self._pie_form = tk.Frame(self._col_form_frame, bg=p["bg"])
        self._pie_form.pack(fill="x", padx=16, pady=(4, 10))

        self._btn_confirmar = tk.Button(
            self._pie_form, text="CONFIRMAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["verde_btn"], activebackground=p["verde_hover"],
            activeforeground="#ffffff",
            bd=0, padx=18, pady=9, relief="flat", cursor="hand2",
            command=self._guardar, state="disabled")
        self._btn_confirmar.pack(side="left", padx=(0, 8))

        self._btn_cancelar = tk.Button(
            self._pie_form, text="CANCELAR",
            font=_F_BTN, fg="#ffffff",
            bg=p["rojo_btn"], activebackground=p["rojo_hover"],
            activeforeground="#ffffff",
            bd=0, padx=18, pady=9, relief="flat", cursor="hand2",
            command=self._cancelar)
        self._btn_cancelar.pack(side="left")

        self._lbl_aviso = tk.Label(
            self._pie_form, text="", font=("Segoe UI", 8),
            fg=p["aviso_fg"], bg=p["bg"],
            wraplength=170, justify="left")
        self._lbl_aviso.pack(side="left", padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS UI
    # ══════════════════════════════════════════════════════════════════════════
    def _redibujar_icono_usuario(self):
        p = self._p
        c = self._canvas_icono
        c.delete("all")
        c.create_oval(2, 2, 58, 58,
                      fill=p["icono_circulo"],
                      outline=p["icono_borde"], width=1)
        c.create_oval(20, 8, 40, 28, fill=p["icono_fill"], outline="")
        c.create_arc(8, 28, 52, 66, start=0, extent=180,
                     fill=p["icono_fill"], outline="", style="chord")

    def _campo(self, parent, row, col_i, etiqueta, key, editable):
        p    = self._p
        padx = (0, 6) if col_i == 0 else (6, 0)
        sub  = tk.Frame(parent, bg=p["bg"])
        sub.grid(row=row, column=col_i, padx=padx, pady=3, sticky="ew")
        self._reg(sub, "bg")

        lbl = tk.Label(sub, text=etiqueta, font=_F_LABEL,
                       fg=p["texto2"], bg=p["bg"])
        lbl.pack(anchor="w")
        self._reg(lbl, "bg", "texto2")

        ent = tk.Entry(
            sub, font=_F_ENTRY,
            fg=p["texto"] if editable else p["texto2"],
            bg=p["campo_bg"] if editable else p["campo_dis"],
            relief="solid", bd=1, highlightthickness=0,
            insertbackground=p["verde"])
        ent.insert(0, self.datos.get(key, ""))
        if not editable:
            ent.config(state="disabled",
                       disabledforeground=p["texto2"],
                       disabledbackground=p["campo_dis"])
        ent.pack(fill="x", ipady=5, pady=(2, 0))
        self._entradas[key] = ent

    def _validar_cod(self, event=None):
        cod = self._entradas["cod_institucional"].get().strip()
        if cod and not self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            self._btn_captura.config(state="normal")
            self._lbl_cam_msg.config(text="PRESIONE CAPTURAR ROSTRO")
            self._lbl_cam_sub.config(text="para iniciar el escaneo biometrico")
        elif not cod:
            self._btn_captura.config(state="disabled")
            self._lbl_cam_msg.config(text="INGRESE EL CÓDIGO PRIMERO")
            self._lbl_cam_sub.config(text="luego presione Capturar Rostro")

    # ══════════════════════════════════════════════════════════════════════════
    #  LÓGICA DE CAPTURA
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_captura(self):
        if self._capturando:
            self._detener_captura()
        else:
            self._iniciar_captura()

    def _iniciar_captura(self):
        p = self._p
        self._capturando = True
        self._btn_captura.config(
            text="DETENER CAPTURA",
            bg=p["rojo_btn"], activebackground=p["rojo_hover"])
        self._lbl_cam_msg.config(text="POR FAVOR NO SE MUEVA")
        self._lbl_cam_sub.config(text="ESCANEANDO ROSTRO...", fg=p["cam_sub_fg"])
        self._hilo_camara = threading.Thread(
            target=self._hilo_captura, daemon=True)
        self._hilo_camara.start()

    def _detener_captura(self):
        p = self._p
        self._capturando = False
        self._btn_captura.config(
            text="CAPTURAR ROSTRO",
            bg=p["verde_btn"], activebackground=p["verde_hover"])
        self._lbl_cam_msg.config(text="CAPTURA PAUSADA")
        self._lbl_cam_sub.config(
            text=f"{self._capturas_ok} / {CAPTURAS_REQUERIDAS} capturas guardadas",
            fg=p["cam_sub_fg"])

    def _hilo_captura(self):
        try:
            import cv2
        except ImportError:
            self.pantalla.after(0, lambda: messagebox.showerror(
                "Dependencia faltante",
                "OpenCV no instalado.\n\npip install opencv-python"))
            self._capturando = False
            return

        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        import platform
        _idx = 1 if platform.machine() in ("aarch64", "armv7l") else 0
        cam  = cv2.VideoCapture(_idx)
        if not cam.isOpened():
            self.pantalla.after(0, lambda: messagebox.showerror(
                "Error de camara", "No se pudo abrir la camara."))
            self._capturando = False
            return

        cod     = self._entradas["cod_institucional"].get().strip()
        carpeta = os.path.join(_BASE, "data", "rostros", cod)
        os.makedirs(carpeta, exist_ok=True)

        try:
            from PIL import Image as PILImage, ImageTk as ITk
            pil_ok = True
        except ImportError:
            pil_ok = False

        rostro_objetivo = None

        def iou(a, b):
            ax1,ay1,ax2,ay2 = a[0],a[1],a[0]+a[2],a[1]+a[3]
            bx1,by1,bx2,by2 = b[0],b[1],b[0]+b[2],b[1]+b[3]
            ix1,iy1 = max(ax1,bx1), max(ay1,by1)
            ix2,iy2 = min(ax2,bx2), min(ay2,by2)
            inter   = max(0,ix2-ix1)*max(0,iy2-iy1)
            union   = a[2]*a[3]+b[2]*b[3]-inter
            return inter/union if union > 0 else 0.0

        while self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            ok, frame = cam.read()
            if not ok:
                break
            frame   = cv2.flip(frame, 1)
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

            if len(rostros) > 0:
                bbox = tuple(rostros[0])
                if rostro_objetivo is None:
                    rostro_objetivo = bbox
                if iou(rostro_objetivo, bbox) >= 0.40:
                    rostro_objetivo = bbox
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,200,0), 2)
                    roi  = frame[y:y+h, x:x+w]
                    ruta = os.path.join(carpeta, f"{self._capturas_ok:03d}.jpg")
                    cv2.imwrite(ruta, roi)
                    self._capturas_ok += 1
                else:
                    x,y,w,h = bbox
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,200),2)

            n = self._capturas_ok
            if pil_ok:
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f = img_rgb.shape[:2]
                nw = 370
                nh = int(h_f * nw / w_f)
                img_pil = PILImage.fromarray(img_rgb).resize((nw, nh), PILImage.LANCZOS)
                photo   = ITk.PhotoImage(img_pil)
                self.pantalla.after(0, self._actualizar_feed, n, photo)
            else:
                self.pantalla.after(0, self._actualizar_feed, n, None)

            cv2.waitKey(80)

        cam.release()
        cv2.destroyAllWindows()
        self.pantalla.after(0, self._captura_finalizada, self._capturas_ok)

    def _actualizar_feed(self, n, photo=None):
        if photo:
            self._last_photo = photo
            self._lbl_feed.config(image=photo)
            self._icono_cam.place_forget()
        prop = min(n / CAPTURAS_REQUERIDAS, 1.0)
        self._lbl_cam_sub.config(
            text=f"ESCANEANDO... {n}/{CAPTURAS_REQUERIDAS}  ({int(prop*100)} %)")

    def _captura_finalizada(self, n):
        p = self._p
        self._capturando = False
        if n >= CAPTURAS_REQUERIDAS:
            self._btn_captura.config(
                text="CAPTURA COMPLETA",
                bg=p["verde"], activebackground=p["verde"], state="disabled")
            self._lbl_cam_msg.config(text="ESCANEO COMPLETADO")
            self._lbl_cam_sub.config(
                text=f"{n} capturas registradas correctamente", fg="#81c784")
            self._btn_confirmar.config(state="normal")
            self._lbl_aviso.config(text="")
        else:
            self._capturas_ok = 0
            self._btn_captura.config(
                text="REINTENTAR CAPTURA",
                bg=p["verde_btn"], activebackground=p["verde_hover"], state="normal")
            self._lbl_cam_msg.config(text="CAPTURA INCOMPLETA")
            self._lbl_cam_sub.config(
                text=f"Solo {n}/{CAPTURAS_REQUERIDAS}. Presione Reintentar.",
                fg="#ef9a9a")

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDAR / CANCELAR
    # ══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        cod       = self._entradas["cod_institucional"].get().strip()
        nombre    = self._entradas["nombre"].get().strip()
        apellidop = self._entradas["apellido_paterno"].get().strip()

        if not cod or not nombre or not apellidop:
            self._lbl_aviso.config(
                text="Código, Nombre y Apellido Paterno son requeridos.")
            return
        if self._capturas_ok < CAPTURAS_REQUERIDAS:
            self._lbl_aviso.config(
                text=f"Se requieren {CAPTURAS_REQUERIDAS} capturas.")
            return

        self._btn_confirmar.config(state="disabled", text="GUARDANDO...")
        self._lbl_aviso.config(text="Generando encoding facial...")

        def _en_hilo():
            import face_recognition
            import numpy as np

            carpeta  = os.path.join(_BASE, "data", "rostros", cod)
            imagenes = sorted([
                os.path.join(carpeta, f)
                for f in os.listdir(carpeta) if f.lower().endswith(".jpg")])

            encodings = []
            for ruta in imagenes:
                try:
                    img  = face_recognition.load_image_file(ruta)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        encodings.append(encs[0])
                except Exception as e:
                    print(f"[ENCODING] {ruta}: {e}")

            if not encodings:
                self.pantalla.after(0, lambda: (
                    self._lbl_aviso.config(
                        text="No se pudo generar encoding. Intente de nuevo."),
                    self._btn_confirmar.config(state="normal", text="CONFIRMAR")))
                return

            encoding_promedio = np.mean(encodings, axis=0)

            # ── Validar que el rostro no esté ya registrado ───────────────────
            from core.database import cargar_todos_encodings
            self.pantalla.after(0, lambda: self._lbl_aviso.config(
                text="Verificando que el rostro no esté registrado..."))

            registrados = cargar_todos_encodings()
            if registrados:
                enc_existentes = [r["encoding"] for r in registrados]
                distancias = face_recognition.face_distance(
                    enc_existentes, encoding_promedio)
                # Umbral 0.45: más estricto que el reconocimiento (0.50)
                # para evitar falsos positivos en el registro
                idx_min = int(np.argmin(distancias))
                if distancias[idx_min] < 0.45:
                    nombre_dup = registrados[idx_min].get("nombre", "—")
                    cod_dup    = registrados[idx_min].get("cod", "—")
                    # Borrar fotos temporales antes de rechazar
                    try:
                        shutil.rmtree(carpeta)
                    except Exception:
                        pass
                    def _rostro_duplicado():
                        self._lbl_aviso.config(
                            text=f"Rostro ya registrado como: {nombre_dup} ({cod_dup})")
                        self._btn_confirmar.config(state="normal", text="CONFIRMAR")
                        # Reiniciar captura para que vuelva a escanear
                        self._capturas_ok = 0
                        self._btn_captura.config(
                            text="REINTENTAR CAPTURA",
                            bg=self._p["verde_btn"],
                            activebackground=self._p["verde_hover"],
                            state="normal")
                        self._lbl_cam_msg.config(text="ROSTRO YA REGISTRADO")
                        self._lbl_cam_sub.config(
                            text="Este rostro ya existe en el sistema",
                            fg="#ef9a9a")
                    self.pantalla.after(0, _rostro_duplicado)
                    return

            try:
                shutil.rmtree(carpeta)
            except Exception as e:
                print(f"[ENCODING] No se pudieron eliminar las fotos: {e}")

            rol_map  = {"Alumno": 4, "Maestro": 3, "Admin": 2, "Super Admin": 1}
            datos_bd = {
                "cod_institucional": cod,
                "id_rol":            rol_map.get(self._rol_var.get(), 4),
                "primer_nombre":     nombre,
                "segundo_nombre":    None,
                "apellido_paterno":  apellidop,
                "apellido_materno":  self._entradas["apellido_materno"].get().strip() or None,
                "carrera":           self._entradas["carrera"].get().strip() or None,
                "grado": None, "grupo": None,
                "face_encoding":     encoding_promedio,
            }

            from core.database import registrar_usuario, inicializar_bd
            inicializar_bd()
            ok, msg = registrar_usuario(datos_bd)

            def _resultado():
                if ok:
                    messagebox.showinfo("Éxito", msg)
                    self.app.mostrar_pantalla("gestion_real")
                else:
                    self._lbl_aviso.config(text=msg)
                    self._btn_confirmar.config(state="normal", text="CONFIRMAR")
            self.pantalla.after(0, _resultado)

        threading.Thread(target=_en_hilo, daemon=True).start()

    def _cancelar(self):
        self._capturando = False
        self.app.mostrar_pantalla("gestion_real")


def crear_pantalla_agregar_usuario(parent, app, datos=None):
    PantallaAgregarUsuario(parent, app, datos)