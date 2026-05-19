"""
ui/screens/pantalla_captura_rostro.py
Pantalla de captura facial — pantalla completa 800x480

FIX cámara: usa exactamente el mismo método que pantalla_acceso.py y validacionUsrs.py
  _CAM_INDEX = 1 if _ES_RASPBERRY else 0
  cv2.VideoCapture(_CAM_INDEX) sin backend especial
"""

import tkinter as tk
import threading
import platform
from pathlib import Path

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA
from ui.components.modal_dialogo import modal_error

import cv2

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")
# ── MISMO índice que pantalla_acceso y validacionUsrs ────────────────────────
_CAM_INDEX    = 1 if _ES_RASPBERRY else 0

CAPTURAS_REQUERIDAS = 30
_UMBRAL_DUPLICADO   = 0.38

_C = {
    "bg":          "#111111",
    "feed_bg":     "#0a0a0a",
    "texto":       "#ffffff",
    "texto2":      "#aaaaaa",
    "verde":       "#43a047",
    "verde_hover": "#388e3c",
    "verde_ok":    "#2e7d32",
    "rojo":        "#e53935",
    "rojo_hover":  "#b71c1c",
    "barra_bg":    "#1a1a1a",
    "progreso_bg": "#2a2a2a",
    "progreso_fg": "#43a047",
}


class PantallaCaptura:

    def __init__(self, parent, app, datos=None):
        self.parent  = parent
        self.app     = app
        self.datos   = datos or {}
        self._p      = _C

        self._capturando  = False
        self._capturas_ok = 0
        self._encodings   = []
        self._last_photo  = None
        self._cap         = None
        self._corriendo   = False

        self._construir_ui()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        cuerpo = tk.Frame(self.pantalla, bg=p["bg"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=0)
        cuerpo.rowconfigure(0, weight=1)

        # Feed de cámara
        self._feed_frame = tk.Frame(cuerpo, bg=p["feed_bg"])
        self._feed_frame.grid(row=0, column=0, sticky="nsew")

        self._lbl_feed = tk.Label(self._feed_frame, bg=p["feed_bg"])
        self._lbl_feed.place(x=0, y=0, relwidth=1, relheight=1)

        self._lbl_instruc = tk.Label(
            self._feed_frame,
            text="Presiona  INICIAR  para comenzar\nel escaneo facial",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff", bg="#222222",
            justify="center", padx=20, pady=14)
        self._lbl_instruc.place(relx=0.5, rely=0.42, anchor="center")

        # Panel de control derecho
        barra = tk.Frame(cuerpo, bg=p["barra_bg"], width=200)
        barra.grid(row=0, column=1, sticky="nsew")
        barra.pack_propagate(False)

        nombre = f"{self.datos.get('nombre','')} {self.datos.get('apellido_paterno','')}".strip()
        tk.Label(barra, text="REGISTRANDO",
                 font=("Segoe UI", 8), fg=p["texto2"],
                 bg=p["barra_bg"]).pack(pady=(16, 2))
        tk.Label(barra, text=nombre or "Usuario",
                 font=("Segoe UI", 11, "bold"), fg=p["texto"],
                 bg=p["barra_bg"], wraplength=170, justify="center").pack()

        tk.Frame(barra, bg="#333333", height=1).pack(fill="x", pady=12, padx=10)

        tk.Label(barra, text="CAPTURAS",
                 font=("Segoe UI", 8), fg=p["texto2"],
                 bg=p["barra_bg"]).pack()

        self._lbl_contador = tk.Label(
            barra, text=f"0 / {CAPTURAS_REQUERIDAS}",
            font=("Segoe UI", 20, "bold"),
            fg=p["verde"], bg=p["barra_bg"])
        self._lbl_contador.pack(pady=(4, 8))

        self._prog_outer = tk.Frame(barra, bg=p["progreso_bg"],
                                     height=8, highlightthickness=0)
        self._prog_outer.pack(fill="x", padx=16, pady=(0, 12))
        self._prog_inner = tk.Frame(self._prog_outer, bg=p["progreso_fg"],
                                     height=8, width=0)
        self._prog_inner.place(x=0, y=0, height=8)

        self._lbl_estado = tk.Label(
            barra,
            text="Listo para\nescanear",
            font=("Segoe UI", 10),
            fg=p["texto2"], bg=p["barra_bg"],
            justify="center", wraplength=170)
        self._lbl_estado.pack(pady=(0, 16))

        tk.Frame(barra, bg="#333333", height=1).pack(fill="x", padx=10)

        btns = tk.Frame(barra, bg=p["barra_bg"])
        btns.pack(fill="x", padx=12, pady=12)

        self._btn_iniciar = tk.Button(
            btns, text="▶  INICIAR",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2",
            command=self._toggle_captura)
        self._btn_iniciar.pack(fill="x", pady=(0, 6))

        tk.Button(
            btns, text="✕  CANCELAR",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["rojo"],
            activebackground=p["rojo_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2",
            command=self._cancelar).pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAPTURA
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_captura(self):
        if self._capturando:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        p = self._p
        self._encodings   = []
        self._capturas_ok = 0
        self._capturando  = True
        self._btn_iniciar.config(text="⏹  DETENER", bg=p["rojo"],
                                  activebackground=p["rojo_hover"])
        self._lbl_estado.config(text="No te muevas\nescaneando...", fg="#81c784")
        self._lbl_instruc.place_forget()
        threading.Thread(target=self._hilo, daemon=True).start()

    def _detener(self):
        p = self._p
        self._capturando = False
        self._corriendo  = False
        self._btn_iniciar.config(text="▶  INICIAR", bg=p["verde"],
                                  activebackground=p["verde_hover"])
        self._lbl_estado.config(text="Detenido", fg=p["texto2"])

    def _hilo(self):
        try:
            import face_recognition
        except ImportError as e:
            self.pantalla.after(0, lambda: modal_error(
                self.pantalla, str(e), titulo="Dependencia faltante"))
            self._capturando = False
            return

        # ── MISMO método que validacionUsrs / pantalla_acceso ────────────────
        self._cap = cv2.VideoCapture(_CAM_INDEX)
        if not self._cap.isOpened():
            # Fallback al otro índice
            otro = 1 - _CAM_INDEX
            self._cap = cv2.VideoCapture(otro)
        if not self._cap.isOpened():
            self.pantalla.after(0, lambda: modal_error(
                self.pantalla,
                "No se pudo abrir la cámara.\n"
                "Verifica que la webcam esté conectada.",
                titulo="Error de cámara"))
            self._capturando = False
            return

        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._corriendo = True

        try:
            from PIL import Image as PI, ImageTk as ITk
            pil_ok = True
        except ImportError:
            pil_ok = False

        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        rostro_obj = None

        def iou(a, b):
            ax1,ay1,ax2,ay2 = a[0],a[1],a[0]+a[2],a[1]+a[3]
            bx1,by1,bx2,by2 = b[0],b[1],b[0]+b[2],b[1]+b[3]
            ix1,iy1 = max(ax1,bx1), max(ay1,by1)
            ix2,iy2 = min(ax2,bx2), min(ay2,by2)
            inter   = max(0,ix2-ix1)*max(0,iy2-iy1)
            union   = a[2]*a[3]+b[2]*b[3]-inter
            return inter/union if union > 0 else 0.0

        while self._capturando and self._capturas_ok < CAPTURAS_REQUERIDAS:
            ok, frame = self._cap.read()
            if not ok or frame is None:
                continue

            frame = cv2.flip(frame, 1)
            gris  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

            if len(rostros) > 0:
                bbox = tuple(rostros[0])
                if rostro_obj is None:
                    rostro_obj = bbox
                if iou(rostro_obj, bbox) >= 0.40:
                    rostro_obj = bbox
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 220, 0), 3)
                    pct = int(self._capturas_ok / CAPTURAS_REQUERIDAS * 100)
                    cv2.putText(frame, f"{pct}%",
                                (x, max(y - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 220, 0), 2)

                    margen = 10
                    x1 = max(0, x - margen)
                    y1 = max(0, y - margen)
                    x2 = min(frame.shape[1], x + w + margen)
                    y2 = min(frame.shape[0], y + h + margen)
                    roi = frame[y1:y2, x1:x2]
                    h_r, w_r = roi.shape[:2]
                    if w_r > 160:
                        s = 160 / w_r
                        roi = cv2.resize(roi, (160, int(h_r*s)),
                                         interpolation=cv2.INTER_LINEAR)
                    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                    encs = face_recognition.face_encodings(
                        roi_rgb, num_jitters=1, model="small")
                    if encs:
                        self._encodings.append(encs[0])
                        self._capturas_ok += 1
                else:
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 2)

            n = self._capturas_ok
            if pil_ok:
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f = img_rgb.shape[:2]
                nw = 580
                nh = int(h_f * nw / w_f)
                img_pil = PI.fromarray(img_rgb).resize((nw, nh), PI.LANCZOS)
                photo = ITk.PhotoImage(img_pil)
                self.pantalla.after(0, self._update_ui, n, photo)
            else:
                self.pantalla.after(0, self._update_ui, n, None)

            cv2.waitKey(30)

        self._corriendo = False
        if self._cap:
            self._cap.release()
        cv2.destroyAllWindows()
        self.pantalla.after(0, self._finalizar, self._capturas_ok)

    def _update_ui(self, n, photo=None):
        if photo:
            self._last_photo = photo
            # FIX: guardar referencia en el widget igual que validacionUsrs
            # sin esto Tkinter libera la imagen y se ve negro
            self._lbl_feed.imgtk = photo
            self._lbl_feed.config(image=photo, text="")

        self._lbl_contador.config(text=f"{n} / {CAPTURAS_REQUERIDAS}")

        try:
            ancho_total = self._prog_outer.winfo_width()
            if ancho_total > 0:
                ancho_prog = int(ancho_total * n / CAPTURAS_REQUERIDAS)
                self._prog_inner.place(x=0, y=0, height=8, width=ancho_prog)
        except Exception:
            pass

    def _finalizar(self, n):
        p = self._p
        self._capturando = False

        if n >= CAPTURAS_REQUERIDAS:
            self._lbl_estado.config(text="¡Escaneo\ncompleto!", fg="#81c784")
            self._btn_iniciar.config(
                text="✓  COMPLETADO", bg=p["verde_ok"], state="disabled")
            self._lbl_contador.config(fg="#81c784")

            import numpy as np
            encoding_final = np.mean(self._encodings, axis=0)

            self._lbl_estado.config(text="Verificando\nduplicados...")
            threading.Thread(
                target=self._verificar_y_regresar,
                args=(encoding_final,), daemon=True).start()
        else:
            self._lbl_estado.config(
                text=f"Incompleto\n{n}/{CAPTURAS_REQUERIDAS}", fg=p["rojo"])
            self._btn_iniciar.config(
                text="▶  REINTENTAR", bg=p["verde"],
                activebackground=p["verde_hover"], state="normal")

    def _verificar_y_regresar(self, encoding):
        try:
            import face_recognition
            import numpy as np
            from core.database import cargar_todos_encodings

            registrados = cargar_todos_encodings()
            if registrados:
                enc_existentes = [r["encoding"] for r in registrados]
                distancias = face_recognition.face_distance(enc_existentes, encoding)
                idx_min = int(np.argmin(distancias))
                if distancias[idx_min] < _UMBRAL_DUPLICADO:
                    nombre_dup = registrados[idx_min].get("nombre", "—")
                    cod_dup    = registrados[idx_min].get("cod", "—")

                    def _dup():
                        self._lbl_estado.config(
                            text=f"Rostro ya\nregistrado:\n{nombre_dup}",
                            fg=self._p["rojo"])
                        self._btn_iniciar.config(
                            text="▶  REINTENTAR",
                            bg=self._p["verde"],
                            activebackground=self._p["verde_hover"],
                            state="normal")
                        self._encodings   = []
                        self._capturas_ok = 0
                    self.pantalla.after(0, _dup)
                    return

            # Sin duplicados → regresar con encoding
            datos_con_enc = dict(self.datos)
            datos_con_enc["face_encoding"] = encoding
            self.pantalla.after(
                0, lambda: self.app.mostrar_pantalla(
                    "agregar_usuario", datos_con_enc))

        except Exception as e:
            self.pantalla.after(0, lambda: modal_error(
                self.pantalla, str(e), titulo="Error"))

    def _cancelar(self):
        self._capturando = False
        self._corriendo  = False
        if self._cap:
            self._cap.release()
        self.app.mostrar_pantalla("agregar_usuario", self.datos)


def crear_pantalla_captura(parent, app, datos=None):
    PantallaCaptura(parent, app, datos)