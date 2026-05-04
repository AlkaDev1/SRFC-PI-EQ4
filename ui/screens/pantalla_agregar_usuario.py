"""
ui/screens/pantalla_agregar_usuario.py
Pantalla de Agregar Usuario -- 800x480 tactil (Raspberry Pi 5)

Layout fiel al mockup de Figma:
  COL IZQ (~47%): feed camara grande (fondo oscuro) + mensaje estado + boton CAPTURAR ROSTRO
  COL DER (~53%): barra verde top | icono usuario | texto instructivo | campos | CONFIRMAR/CANCELAR
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import threading

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA

# ── Paleta ──────────────────────────────────────────────────────────────────────
_BG       = "#ffffff"
_VD       = "#2e7d32"
_VM       = "#4caf50"
_VBTN     = "#4caf50"
_VBTN_H   = "#388e3c"
_RBTN     = "#e53935"
_RBTN_H   = "#b71c1c"
_CAM_BG   = "#1c1c1c"
_TXT      = "#1c1c1c"
_TXT2     = "#757575"
_BORDE    = "#e0e0e0"

_F_LABEL   = ("Segoe UI", 8)
_F_ENTRY   = ("Segoe UI", 10)
_F_BTN     = ("Segoe UI", 10, "bold")
_F_INSTRUC = ("Segoe UI", 9)
_F_CAM_MSG = ("Segoe UI", 12, "bold")
_F_CAM_SUB = ("Segoe UI", 9, "bold")

CAPTURAS_REQUERIDAS = 30


# ═══════════════════════════════════════════════════════════════════════════════
class PantallaAgregarUsuario:

    def __init__(self, parent, app, datos=None):
        self.parent       = parent
        self.app          = app
        self.datos        = datos or {}
        self._capturas_ok = 0
        self._capturando  = False
        self._hilo_camara = None
        self._last_photo  = None
        self._construir_ui()

    # ── Raiz ────────────────────────────────────────────────────────────────────
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=_BG)
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        cuerpo = tk.Frame(self.pantalla, bg=_BG)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=47)
        cuerpo.columnconfigure(1, weight=53)
        cuerpo.rowconfigure(0, weight=1)

        self._col_camara(cuerpo)
        self._col_formulario(cuerpo)

    # ═══════════════════════════════════════════════════════════════════════════
    # COLUMNA IZQUIERDA — camara
    # ═══════════════════════════════════════════════════════════════════════════
    def _col_camara(self, parent):
        col = tk.Frame(parent, bg=_CAM_BG)
        col.grid(row=0, column=0, sticky="nsew")

        # Feed — ocupa todo el espacio vertical disponible
        feed_wrap = tk.Frame(col, bg=_CAM_BG)
        feed_wrap.pack(fill="both", expand=True)
        feed_wrap.pack_propagate(False)   # tamano fijo, imagen no empuja nada

        self._lbl_feed = tk.Label(feed_wrap, bg=_CAM_BG, relief="flat")
        self._lbl_feed.place(x=0, y=0, relwidth=1, relheight=1)

        # Icono camara centrado (se oculta al llegar imagen)
        self._icono_cam = tk.Label(
            feed_wrap, text="", font=("Segoe UI", 40),
            fg="#444466", bg=_CAM_BG
        )
        self._icono_cam.place(relx=0.5, rely=0.42, anchor="center")

        # Pie de la columna camara
        pie_cam = tk.Frame(col, bg=_CAM_BG)
        pie_cam.pack(fill="x", padx=14, pady=(6, 10))

        self._lbl_cam_msg = tk.Label(
            pie_cam,
            text="PRESIONE CAPTURAR ROSTRO",
            font=_F_CAM_MSG, fg="#ffffff", bg=_CAM_BG,
            justify="center"
        )
        self._lbl_cam_msg.pack()

        self._lbl_cam_sub = tk.Label(
            pie_cam,
            text="para iniciar el escaneo biometrico",
            font=_F_CAM_SUB, fg="#aaaaaa", bg=_CAM_BG,
            justify="center"
        )
        self._lbl_cam_sub.pack(pady=(0, 8))

        self._btn_captura = tk.Button(
            pie_cam,
            text="CAPTURAR ROSTRO",
            font=_F_BTN,
            fg="#ffffff", bg=_VBTN,
            activebackground=_VBTN_H, activeforeground="#ffffff",
            bd=0, padx=20, pady=10, relief="flat", cursor="hand2",
            command=self._toggle_captura
        )
        self._btn_captura.pack(fill="x")

    # ═══════════════════════════════════════════════════════════════════════════
    # COLUMNA DERECHA — formulario
    # ═══════════════════════════════════════════════════════════════════════════
    def _col_formulario(self, parent):
        col = tk.Frame(parent, bg="#ffffff",
                       highlightthickness=1, highlightbackground=_BORDE)
        col.grid(row=0, column=1, sticky="nsew")

        # Barra verde superior
        tk.Frame(col, bg=_VM, height=8).pack(fill="x")

        # Icono usuario + instruccion
        encab = tk.Frame(col, bg="#ffffff")
        encab.pack(fill="x", pady=(8, 2), padx=16)
        self._icono_usuario(encab)
        tk.Label(
            encab,
            text="Ingrese el rostro y los datos de la persona para ingresarla al sistema",
            font=_F_INSTRUC, fg=_TXT2, bg="#ffffff",
            justify="center", wraplength=340
        ).pack(pady=(4, 0))

        # Grid de campos
        form = tk.Frame(col, bg="#ffffff")
        form.pack(fill="both", expand=True, padx=16, pady=(4, 2))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        campos = [
            (0, 0, "Codigo Institucional", "cod_institucional", True),
            (0, 1, "Nombre(s)",            "nombre",            True),
            (1, 0, "Apellido Paterno",     "apellido_paterno",  True),
            (1, 1, "Apellido Materno",     "apellido_materno",  True),
            (2, 0, "Programa Academico",   "carrera",           True),
        ]
        self._entradas = {}
        for row, col_i, lbl, key, edit in campos:
            self._campo(form, row, col_i, lbl, key, edit)

        # Rol (fila 2, col 1)
        self._rol_var = tk.StringVar(value=self.datos.get("rol", ""))
        sub_rol = tk.Frame(form, bg="#ffffff")
        sub_rol.grid(row=2, column=1, padx=(6, 0), pady=3, sticky="ew")
        tk.Label(sub_rol, text="Rol", font=_F_LABEL,
                 fg=_TXT2, bg="#ffffff").pack(anchor="w")
        self._mk_optmenu(sub_rol, self._rol_var,
                         ["Alumno", "Maestro", "Admin", "Super Admin"]).pack(
            fill="x", ipady=4, pady=(2, 0))

        # Status (fila 3, span 2)
        self._status_var = tk.StringVar(value=self.datos.get("status", ""))
        sub_st = tk.Frame(form, bg="#ffffff")
        sub_st.grid(row=3, column=0, columnspan=2, pady=3, sticky="ew")
        tk.Label(sub_st, text="Status", font=_F_LABEL,
                 fg=_TXT2, bg="#ffffff").pack(anchor="w")
        self._mk_optmenu(sub_st, self._status_var,
                         ["Activo", "Inactivo"]).pack(
            fill="x", ipady=4, pady=(2, 0))

        # Botones
        pie = tk.Frame(col, bg="#ffffff")
        pie.pack(fill="x", padx=16, pady=(4, 10))

        self._btn_confirmar = tk.Button(
            pie, text="CONFIRMAR",
            font=_F_BTN, fg="#ffffff", bg=_VBTN,
            activebackground=_VBTN_H, activeforeground="#ffffff",
            bd=0, padx=18, pady=9, relief="flat", cursor="hand2",
            command=self._guardar, state="disabled"
        )
        self._btn_confirmar.pack(side="left", padx=(0, 8))

        tk.Button(
            pie, text="CANCELAR",
            font=_F_BTN, fg="#ffffff", bg=_RBTN,
            activebackground=_RBTN_H, activeforeground="#ffffff",
            bd=0, padx=18, pady=9, relief="flat", cursor="hand2",
            command=self._cancelar
        ).pack(side="left")

        self._lbl_aviso = tk.Label(
            pie, text="", font=("Segoe UI", 8),
            fg=_RBTN, bg="#ffffff", wraplength=170, justify="left"
        )
        self._lbl_aviso.pack(side="left", padx=10)

    # ── Helpers UI ─────────────────────────────────────────────────────────────
    def _campo(self, parent, row, col_i, etiqueta, key, editable):
        padx = (0, 6) if col_i == 0 else (6, 0)
        sub  = tk.Frame(parent, bg="#ffffff")
        sub.grid(row=row, column=col_i, padx=padx, pady=3, sticky="ew")
        tk.Label(sub, text=etiqueta, font=_F_LABEL,
                 fg=_TXT2, bg="#ffffff").pack(anchor="w")
        ent = tk.Entry(
            sub, font=_F_ENTRY,
            fg=_TXT if editable else _TXT2,
            bg="#ffffff" if editable else "#f5f5f5",
            relief="solid", bd=1, highlightthickness=0,
            insertbackground=_VD
        )
        ent.insert(0, self.datos.get(key, ""))
        if not editable:
            ent.config(state="disabled",
                       disabledforeground=_TXT2,
                       disabledbackground="#f5f5f5")
        ent.pack(fill="x", ipady=5, pady=(2, 0))
        self._entradas[key] = ent

    def _mk_optmenu(self, parent, var, opciones):
        om = tk.OptionMenu(parent, var, *opciones)
        om.config(font=_F_ENTRY, bg="#ffffff", fg=_TXT,
                  relief="solid", bd=1, highlightthickness=0,
                  activebackground="#eeeeee", cursor="hand2", anchor="w")
        om["menu"].config(font=_F_ENTRY, bg="#ffffff",
                          activebackground=_VM, activeforeground="#ffffff")
        return om

    def _icono_usuario(self, parent):
        """Canvas: circulo gris + silueta de persona, igual al mockup."""
        c = tk.Canvas(parent, width=60, height=60,
                      bg="#ffffff", highlightthickness=0)
        c.pack()
        c.create_oval(2, 2, 58, 58, fill="#e0e0e0", outline="#bdbdbd", width=1)
        c.create_oval(20, 8, 40, 28,  fill="#9e9e9e", outline="")
        c.create_arc(8, 28, 52, 66, start=0, extent=180,
                     fill="#9e9e9e", outline="", style="chord")

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGICA DE CAPTURA
    # ═══════════════════════════════════════════════════════════════════════════
    def _toggle_captura(self):
        if self._capturando:
            self._detener_captura()
        else:
            self._iniciar_captura()

    def _iniciar_captura(self):
        self._capturando = True
        self._btn_captura.config(
            text="DETENER CAPTURA", bg=_RBTN, activebackground=_RBTN_H)
        self._lbl_cam_msg.config(text="POR FAVOR NO SE MUEVA")
        self._lbl_cam_sub.config(
            text="ESCANEANDO ROSTRO...", fg="#aaaaaa")
        self._hilo_camara = threading.Thread(
            target=self._hilo_captura, daemon=True)
        self._hilo_camara.start()

    def _detener_captura(self):
        self._capturando = False
        self._btn_captura.config(
            text="CAPTURAR ROSTRO", bg=_VBTN, activebackground=_VBTN_H)
        self._lbl_cam_msg.config(text="CAPTURA PAUSADA")
        self._lbl_cam_sub.config(
            text=f"{self._capturas_ok} / {CAPTURAS_REQUERIDAS} capturas guardadas",
            fg="#aaaaaa")

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
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            self.pantalla.after(0, lambda: messagebox.showerror(
                "Error de camara", "No se pudo abrir la camara (index 0)."))
            self._capturando = False
            return

        import os
        cod     = self.datos.get("cod_institucional", "sin_cod")
        carpeta = os.path.join("data", "rostros", str(cod))
        os.makedirs(carpeta, exist_ok=True)

        try:
            from PIL import Image, ImageTk
            pil_ok = True
        except ImportError:
            pil_ok = False

        # Tracking: bbox del rostro objetivo (None = sin objetivo aun)
        # Solo capturamos cuando el rostro nuevo se solapa >= 50% con el objetivo
        rostro_objetivo = None   # (x, y, w, h) del primer rostro aceptado

        def iou(a, b):
            """Intersection-over-Union entre dos bbox (x,y,w,h)."""
            ax1, ay1, ax2, ay2 = a[0], a[1], a[0]+a[2], a[1]+a[3]
            bx1, by1, bx2, by2 = b[0], b[1], b[0]+b[2], b[1]+b[3]
            ix1, iy1 = max(ax1, bx1), max(ay1, by1)
            ix2, iy2 = min(ax2, bx2), min(ay2, by2)
            inter = max(0, ix2-ix1) * max(0, iy2-iy1)
            union = a[2]*a[3] + b[2]*b[3] - inter
            return inter / union if union > 0 else 0.0

        while self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            ok, frame = cam.read()
            if not ok:
                break

            # FIX 1: voltear horizontalmente (efecto espejo)
            frame = cv2.flip(frame, 1)

            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

            capturar_este_frame = False
            if len(rostros) > 0:
                bbox = tuple(rostros[0])   # tomamos el primer rostro detectado

                # FIX 3: si no hay objetivo, este se convierte en el objetivo
                if rostro_objetivo is None:
                    rostro_objetivo = bbox

                # Solo capturamos si el rostro detectado se solapa >= 40% con el objetivo
                if iou(rostro_objetivo, bbox) >= 0.40:
                    rostro_objetivo = bbox   # actualizar posicion (puede moverse un poco)
                    capturar_este_frame = True
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 200, 0), 2)
                    roi  = frame[y:y+h, x:x+w]
                    ruta = os.path.join(carpeta, f"{self._capturas_ok:03d}.jpg")
                    cv2.imwrite(ruta, roi)
                    self._capturas_ok += 1
                else:
                    # Rostro diferente — dibujar en rojo y NO capturar
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 2)
            else:
                # Sin rostro — el objetivo se pierde si llevamos >15 frames sin verlo
                # (simplificacion: si no hay nadie, no capturamos pero no reseteamos objetivo)
                pass

            n = self._capturas_ok
            if pil_ok:
                img_rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f = img_rgb.shape[:2]
                nw       = 370
                nh       = int(h_f * nw / w_f)
                img_pil  = Image.fromarray(img_rgb).resize(
                    (nw, nh), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img_pil)
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
        self._capturando = False
        if n >= CAPTURAS_REQUERIDAS:
            self._btn_captura.config(
                text="CAPTURA COMPLETA",
                bg=_VD, activebackground=_VD, state="disabled")
            self._lbl_cam_msg.config(text="ESCANEO COMPLETADO")
            self._lbl_cam_sub.config(
                text=f"{n} capturas registradas correctamente",
                fg="#81c784")
            self._btn_confirmar.config(state="normal")
            self._lbl_aviso.config(text="")
        else:
            # Resetear contador para que al reintentar empiece desde 0
            self._capturas_ok = 0
            self._btn_captura.config(
                text="REINTENTAR CAPTURA",
                bg=_VBTN, activebackground=_VBTN_H, state="normal")
            self._lbl_cam_msg.config(text="CAPTURA INCOMPLETA")
            self._lbl_cam_sub.config(
                text=f"Solo {n}/{CAPTURAS_REQUERIDAS}. Presione Reintentar.",
                fg="#ef9a9a")

    # ═══════════════════════════════════════════════════════════════════════════
    # GUARDAR / CANCELAR
    # ═══════════════════════════════════════════════════════════════════════════
    def _guardar(self):
        nombre    = self._entradas["nombre"].get().strip()
        apellidop = self._entradas["apellido_paterno"].get().strip()

        if not nombre or not apellidop:
            self._lbl_aviso.config(
                text="Nombre y Apellido Paterno son requeridos.")
            return

        if self._capturas_ok < CAPTURAS_REQUERIDAS:
            self._lbl_aviso.config(
                text=f"Se requieren {CAPTURAS_REQUERIDAS} capturas.")
            return

        datos_guardado = {
            "cod_institucional": self.datos.get("cod_institucional", ""),
            "nombre":            nombre,
            "apellido_paterno":  apellidop,
            "apellido_materno":  self._entradas["apellido_materno"].get().strip(),
            "carrera":           self._entradas["carrera"].get().strip(),
            "rol":               self._rol_var.get(),
            "status":            self._status_var.get(),
            "fecha_registro":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "capturas":          self._capturas_ok,
        }
        print("[AGREGAR USUARIO] Guardando:", datos_guardado)
        # TODO: from core.database import agregar_usuario; agregar_usuario(datos_guardado)
        # TODO: from core.reconocimiento import entrenar_modelo; entrenar_modelo()
        self.app.mostrar_pantalla("gestion_real")

    def _cancelar(self):
        self._capturando = False
        self.app.mostrar_pantalla("gestion_real")


# ── Funcion de acceso publico ───────────────────────────────────────────────────
def crear_pantalla_agregar_usuario(parent, app, datos=None):
    PantallaAgregarUsuario(parent, app, datos)