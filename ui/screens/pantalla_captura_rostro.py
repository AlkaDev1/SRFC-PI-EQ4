"""
ui/screens/pantalla_captura_rostro.py

LIVENESS DETECTION (sin sensor IR):
  - Etapas: FRENTE → PESTAÑEO
  - Anti-foto: movimiento entre frames + variación de textura + cambio de fondo
  - Pestañeo: EAR (Eye Aspect Ratio) usando landmarks de face_recognition

FIXES v2:
  - Pestañeo ya no se dispara cuando la cara desaparece y reaparece (foto retirada/acercada)
  - Pestañeo requiere: EAR bajo DURANTE al menos 1 frame Y reaparición dentro de 600ms
  - Se valida liveness (movimiento) también en etapa pestañeo
  - _cara_ausente_antes invalida el siguiente ciclo de detección de cierre de ojo

FIXES v3:
  - Duplicado detectado → muestra overlay rojo pero NO detiene el escaneo;
    resetea contadores y limpia el aviso a los 3s para que la persona correcta
    pueda registrarse sin reiniciar manualmente.
  - Persona diferente en pestañeo → overlay rojo pero NO detiene el hilo;
    en cuanto la verificación de identidad confirma que es la misma persona
    el flag se limpia y el pestañeo continúa donde iba.

FIXES v4:
  - _identidad_confirmada: el EAR/pestañeo solo se procesa cuando la identidad
    ha sido verificada al menos una vez en la etapa de pestañeo. Evita que una
    persona diferente acumule pestañeos antes de que llegue la verificación async.
  - La verificación se lanza cada 4 frames (antes 8) para confirmar identidad
    más rápido al entrar a la etapa de pestañeo.
  - Al activarse _persona_diferente_activa se resetean los pestañeos acumulados
    por la persona incorrecta.
"""

import tkinter as tk
import threading
import queue
import time
import cv2
import numpy as np
import platform
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont

from ui.components.barra_superior import crear_encabezado
from ui.styles import PALETA
from ui.components.modal_dialogo import modal_error

try:
    import face_recognition
    FR_DISPONIBLE = True
except ImportError:
    FR_DISPONIBLE = False

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")
_CAM_INDEX    = 1 if _ES_RASPBERRY else 0

CAPTURAS_REQUERIDAS     = 30
CAPTURAS_REFERENCIA     = 3
CAPTURAS_PARA_CHEQUEO   = 5
_UMBRAL_DUPLICADO       = 0.50
_UMBRAL_CONSISTENCIA    = 0.45
_MAX_DESCARTES_SEGUIDOS = 15

SKIP_FRAMES     = 2
MAX_FRAMES_COLA = 4

# Liveness
_UMBRAL_MOVIMIENTO    = 2.5
_UMBRAL_TEXTURA       = 8.0
_UMBRAL_FONDO_CAMBIO  = 1.5
_FRAMES_LIVENESS      = 6
_EAR_UMBRAL           = 0.21
_PESTANEOS_REQUERIDOS = 2

# Pestañeo robusto
_EAR_FRAMES_MINIMOS  = 1      # cuántos frames seguidos debe estar el ojo cerrado
_PESTANEO_TIMEOUT_MS = 600    # ms máximos entre cierre y apertura para contar como pestañeo

# Umbral de identidad en etapa pestaneo (mas permisivo que UMBRAL_CONSISTENCIA
# porque el ROI puede tener diferente escala/iluminacion al de referencia)
_UMBRAL_IDENTIDAD_PESTANEO = 0.70

# Cada cuántos frames se recalcula el encoding para verificar identidad en pestañeo.
# Valor bajo = más seguro pero más lento; 3 es un balance razonable con SKIP_FRAMES=2.
_ID_VERIFY_INTERVAL = 3

_C = {
    "bg":"#f3f4f5","feed_bg":"#1c1c1c","panel_bg":"#ffffff",
    "panel_borde":"#e0e0e0","texto":"#1a1a1a","texto2":"#757575",
    "verde":"#43a047","verde_m":"#4caf50","verde_ok":"#2e7d32",
    "verde_hover":"#388e3c","rojo":"#e53935","rojo_hover":"#b71c1c",
    "prog_bg":"#e0e0e0","prog_fg":"#43a047","naranja":"#f57c00",
}
_O = {
    "bg":"#071E07","feed_bg":"#0a0a0a","panel_bg":"#0d2a0d",
    "panel_borde":"#1a3a1a","texto":"#d0f0d0","texto2":"#7aaa7a",
    "verde":"#2D531A","verde_m":"#477023","verde_ok":"#1a3a1a",
    "verde_hover":"#477023","rojo":"#7f1d1d","rojo_hover":"#991b1b",
    "prog_bg":"#1a3a1a","prog_fg":"#477023","naranja":"#b85c00",
}

_ETAPA_FRENTE   = 0
_ETAPA_PESTANEO = 1

_FALLBACK_ETAPA = {
    _ETAPA_FRENTE:   "Mira al frente",
    _ETAPA_PESTANEO: "Pestañea 2 veces",
}


def _paleta(app) -> dict:
    return _O if (hasattr(app, "tema") and app.tema.es_oscuro()) else _C


def _calcular_ear_frame(frame_rgb, face_loc):
    if not FR_DISPONIBLE:
        return None
    try:
        lm_list = face_recognition.face_landmarks(frame_rgb, [face_loc], model="large")
        if not lm_list:
            return None
        lm = lm_list[0]
        ojo_izq = lm.get("left_eye", [])
        ojo_der = lm.get("right_eye", [])
        if len(ojo_izq) < 6 or len(ojo_der) < 6:
            return None

        def _ear_pts(pts):
            A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
            B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
            C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
            return (A + B) / (2.0 * C + 1e-6)

        return (_ear_pts(ojo_izq) + _ear_pts(ojo_der)) / 2.0
    except Exception:
        return None


def _chequeo_liveness_frame(frame_bgr, frame_anterior_bgr, bbox):
    if frame_anterior_bgr is None:
        return True, ""
    h, w = frame_bgr.shape[:2]
    x, y, bw, bh = bbox

    diff = cv2.absdiff(
        cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(frame_anterior_bgr, cv2.COLOR_BGR2GRAY))
    if float(np.mean(diff)) < _UMBRAL_MOVIMIENTO:
        return False, "foto_estatica"

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(w, x+bw), min(h, y+bh)
    roi = cv2.cvtColor(frame_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    if roi.size > 0 and float(cv2.Laplacian(roi, cv2.CV_64F).var()) < _UMBRAL_TEXTURA:
        return False, "baja_textura"

    mascara = np.ones((h, w), dtype=np.uint8)
    mascara[max(0,y-20):min(h,y+bh+20), max(0,x-20):min(w,x+bw+20)] = 0
    diff_fondo = cv2.absdiff(
        cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(frame_anterior_bgr, cv2.COLOR_BGR2GRAY))
    zona = diff_fondo[mascara == 1]
    if zona.size > 0 and float(np.mean(zona)) < _UMBRAL_FONDO_CAMBIO:
        return False, "fondo_estatico"

    return True, ""


class PantallaCaptura:

    def __init__(self, parent, app, datos=None):
        self.parent = parent
        self.app    = app
        self.datos  = datos or {}
        self._p     = _paleta(app)

        self._capturando         = False
        self._capturas_ok        = 0
        self._encodings          = []
        self._photo              = None
        self._chequeo_rapido     = False
        self._duplicado_nombre   = None
        self._ultimo_bbox        = None
        self._enc_referencia     = None
        self._descartes_seguidos = 0

        self._etapa_actual             = _ETAPA_FRENTE
        self._pestaneos_ok             = 0
        self._persona_diferente_activa = False   # flag overlay rojo en video
        self._identidad_confirmada     = False   # True cuando verificación async confirmó identidad

        # ── Estado pestañeo robusto ──────────────────────────────────────────
        self._ojo_cerrado        = False   # ojo estaba cerrado en frame anterior
        self._ear_cerrado_frames = 0       # frames consecutivos con ojo cerrado
        self._t_ojo_cerrado      = None    # timestamp cuando se detectó cierre
        self._cara_ausente_antes        = False   # cara desapareció en frame anterior
        self._frames_diferente        = 0       # frames seguidos con cara diferente
        # ────────────────────────────────────────────────────────────────────

        self._liveness_ok_streak = 0
        self._frame_anterior     = None

        self._cap             = None
        self._corriendo       = False
        self._cola_frames     = queue.Queue(maxsize=MAX_FRAMES_COLA)
        self._contador_frames = 0

        self._det_frontal = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        if hasattr(app, "idioma"):
            app.idioma.registrar(self._aplicar_idioma)
        self.pantalla.bind("<Destroy>", self._limpiar)

    def _t(self, clave, fallback=""):
        if hasattr(self.app, "idioma"):
            return self.app.idioma.t(clave, fallback)
        return fallback or clave

    def _aplicar_idioma(self):
        try:
            nombre = f"{self.datos.get('nombre','')} {self.datos.get('apellido_paterno','')}".strip()
            self._lbl_reg.config(text=self._t("captura_rostro.registrando", "REGISTRANDO"))
            self._lbl_nombre.config(text=nombre or self._t("captura_rostro.usuario_default", "Usuario"))
            self._lbl_cap_titulo.config(text=self._t("captura_rostro.label_capturas", "CAPTURAS"))
            if not self._capturando:
                self._lbl_estado.config(text=self._t("captura_rostro.listo", "Listo para\nescanear"))
                self._btn_iniciar.config(text=self._t("captura_rostro.btn_iniciar", "▶  INICIAR"))
            self._btn_cancelar.config(text=self._t("captura_rostro.btn_cancelar", "✕  CANCELAR"))
        except tk.TclError:
            pass

    def _on_tema_cambio(self, _):
        self._p = _O if self.app.tema.es_oscuro() else _C
        self._aplicar_tema()

    def _limpiar(self, event=None):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._on_tema_cambio)
        if hasattr(self.app, "idioma"):
            self.app.idioma.desregistrar(self._aplicar_idioma)

    def _aplicar_tema(self):
        p = self._p
        try:
            self.pantalla.configure(bg=p["bg"])
            self._cuerpo.configure(bg=p["bg"])
            self._col_feed.configure(bg=p["feed_bg"])
            self.label_video.configure(bg=p["feed_bg"])
            self._panel.configure(bg=p["panel_bg"], highlightbackground=p["panel_borde"])
            self._lbl_reg.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._lbl_nombre.configure(bg=p["panel_bg"], fg=p["texto"])
            self._sep1.configure(bg=p["panel_borde"])
            self._lbl_cap_titulo.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._lbl_contador.configure(bg=p["panel_bg"], fg=p["verde"])
            self._prog_outer.configure(bg=p["prog_bg"])
            self._prog_inner.configure(bg=p["prog_fg"])
            self._lbl_estado.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._lbl_etapa.configure(bg=p["panel_bg"], fg=p["naranja"])
            self._sep2.configure(bg=p["panel_borde"])
            self._btn_frame.configure(bg=p["panel_bg"])
            self._btn_iniciar.configure(bg=p["verde"], activebackground=p["verde_hover"])
            self._btn_cancelar.configure(bg=p["rojo"], activebackground=p["rojo_hover"])
        except tk.TclError:
            pass

    # ═════════════════════════════════════════════════════════════════════
    #  UI
    # ═════════════════════════════════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.app)
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        self._cuerpo = tk.Frame(self.pantalla, bg=p["bg"])
        self._cuerpo.pack(fill="both", expand=True)
        self._cuerpo.columnconfigure(0, weight=1)
        self._cuerpo.columnconfigure(1, weight=0)
        self._cuerpo.rowconfigure(0, weight=1)

        self._col_feed = tk.Frame(self._cuerpo, bg=p["feed_bg"])
        self._col_feed.grid(row=0, column=0, sticky="nsew")

        self.label_video = tk.Label(
            self._col_feed, bg=p["feed_bg"],
            text=self._t("acceso.iniciando_camara", "Iniciando cámara..."),
            font=("Segoe UI", 13), fg="#aaaaaa")
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        self._panel = tk.Frame(self._cuerpo, bg=p["panel_bg"], width=210,
                               highlightthickness=1, highlightbackground=p["panel_borde"])
        self._panel.grid(row=0, column=1, sticky="nsew")
        self._panel.pack_propagate(False)

        tk.Frame(self._panel, bg=p["verde_m"], height=4).pack(fill="x")

        nombre = f"{self.datos.get('nombre','')} {self.datos.get('apellido_paterno','')}".strip()

        self._lbl_reg = tk.Label(self._panel,
            text=self._t("captura_rostro.registrando", "REGISTRANDO"),
            font=("Segoe UI", 8), fg=p["texto2"], bg=p["panel_bg"])
        self._lbl_reg.pack(pady=(14, 2))

        self._lbl_nombre = tk.Label(self._panel,
            text=nombre or self._t("captura_rostro.usuario_default", "Usuario"),
            font=("Segoe UI", 11, "bold"), fg=p["texto"],
            bg=p["panel_bg"], wraplength=185, justify="center")
        self._lbl_nombre.pack()

        self._sep1 = tk.Frame(self._panel, bg=p["panel_borde"], height=1)
        self._sep1.pack(fill="x", pady=10, padx=10)

        self._lbl_cap_titulo = tk.Label(self._panel,
            text=self._t("captura_rostro.label_capturas", "CAPTURAS"),
            font=("Segoe UI", 8), fg=p["texto2"], bg=p["panel_bg"])
        self._lbl_cap_titulo.pack()

        self._lbl_contador = tk.Label(self._panel,
            text=f"0 / {CAPTURAS_REQUERIDAS}",
            font=("Segoe UI", 22, "bold"), fg=p["verde"], bg=p["panel_bg"])
        self._lbl_contador.pack(pady=(4, 8))

        self._prog_outer = tk.Frame(self._panel, bg=p["prog_bg"], height=8)
        self._prog_outer.pack(fill="x", padx=16, pady=(0, 10))
        self._prog_inner = tk.Frame(self._prog_outer, bg=p["prog_fg"], height=8, width=0)
        self._prog_inner.place(x=0, y=0, height=8)

        self._lbl_etapa = tk.Label(self._panel, text="",
            font=("Segoe UI", 9, "bold"), fg=p["naranja"],
            bg=p["panel_bg"], justify="center", wraplength=185)
        self._lbl_etapa.pack(pady=(0, 2))

        self._lbl_estado = tk.Label(self._panel,
            text=self._t("captura_rostro.listo", "Listo para\nescanear"),
            font=("Segoe UI", 10), fg=p["texto2"],
            bg=p["panel_bg"], justify="center", wraplength=185)
        self._lbl_estado.pack(pady=(0, 10))

        self._sep2 = tk.Frame(self._panel, bg=p["panel_borde"], height=1)
        self._sep2.pack(fill="x", padx=10)

        self._btn_frame = tk.Frame(self._panel, bg=p["panel_bg"])
        self._btn_frame.pack(fill="x", padx=12, pady=10)

        self._btn_iniciar = tk.Button(self._btn_frame,
            text=self._t("captura_rostro.btn_iniciar", "▶  INICIAR"),
            font=("Segoe UI", 10, "bold"), fg="#ffffff", bg=p["verde"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2", command=self._toggle)
        self._btn_iniciar.pack(fill="x", pady=(0, 6))

        self._btn_cancelar = tk.Button(self._btn_frame,
            text=self._t("captura_rostro.btn_cancelar", "✕  CANCELAR"),
            font=("Segoe UI", 10, "bold"), fg="#ffffff", bg=p["rojo"],
            activebackground=p["rojo_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2", command=self._cancelar)
        self._btn_cancelar.pack(fill="x")

    # ═════════════════════════════════════════════════════════════════════
    #  CAPTURA
    # ═════════════════════════════════════════════════════════════════════
    def _toggle(self):
        if self._capturando:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        self._encodings          = []
        self._capturas_ok        = 0
        self._capturando         = True
        self._chequeo_rapido     = False
        self._duplicado_nombre   = None
        self._ultimo_bbox        = None
        self._enc_referencia     = None
        self._descartes_seguidos = 0
        self._etapa_actual             = _ETAPA_FRENTE
        self._pestaneos_ok             = 0
        self._persona_diferente_activa = False
        self._identidad_confirmada     = False

        # Reset estado pestañeo robusto
        self._ojo_cerrado              = False
        self._ear_cerrado_frames       = 0
        self._t_ojo_cerrado            = None
        self._cara_ausente_antes       = False
        self._frames_diferente         = 0
        self._frames_pestaneo_count    = 0
        self._enc_pestaneo_cache       = None

        self._liveness_ok_streak = 0
        self._frame_anterior     = None

        p = self._p
        self._btn_iniciar.config(
            text=self._t("captura_rostro.btn_detener", "⏹  DETENER"),
            bg=p["rojo"], activebackground=p["rojo_hover"])
        self._lbl_etapa.config(text="👁  Mira al frente")
        self._lbl_estado.config(
            text=self._t("captura_rostro.escaneando", "No te muevas\nescaneando..."),
            fg="#43a047")

        self._cap = cv2.VideoCapture(_CAM_INDEX)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(1 - _CAM_INDEX)
        if not self._cap.isOpened():
            modal_error(self.pantalla,
                self._t("captura_rostro.error_camara_msg", "No se pudo abrir la cámara."),
                titulo=self._t("captura_rostro.error_camara_titulo", "Error de cámara"))
            self._capturando = False
            return

        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._corriendo = True

        threading.Thread(target=self._hilo_camara,  daemon=True).start()
        threading.Thread(target=self._hilo_captura, daemon=True).start()

    def _detener(self):
        self._capturando = False
        self._corriendo  = False
        p = self._p
        self._btn_iniciar.config(
            text=self._t("captura_rostro.btn_iniciar", "▶  INICIAR"),
            bg=p["verde"], activebackground=p["verde_hover"])
        self._lbl_estado.config(
            text=self._t("captura_rostro.detenido", "Detenido"), fg=p["texto2"])
        self._lbl_etapa.config(text="")

    # ═════════════════════════════════════════════════════════════════════
    #  HILO CÁMARA (render)
    # ═════════════════════════════════════════════════════════════════════
    def _hilo_camara(self):
        self._contador_frames = 0
        while self._corriendo:
            ok, frame = self._cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            self._contador_frames += 1

            if self._contador_frames % SKIP_FRAMES == 0:
                try:
                    self._cola_frames.put_nowait(frame.copy())
                except queue.Full:
                    pass

            try:
                cw = self.label_video.winfo_width()
                ch = self.label_video.winfo_height()
                if cw < 10 or ch < 10:
                    continue
                resized = cv2.resize(frame, (cw, ch), interpolation=cv2.INTER_LINEAR)

                gris    = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                rostros = self._det_frontal.detectMultiScale(
                    gris, scaleFactor=1.3, minNeighbors=5, minSize=(60, 60))
                if len(rostros) > 0:
                    x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
                    self._ultimo_bbox = (x, y, w, h)

                dup_nombre = self._duplicado_nombre
                etapa      = self._etapa_actual

                if dup_nombre and self._ultimo_bbox is not None:
                    self._dibujar_duplicado(resized, dup_nombre)
                elif self._persona_diferente_activa and self._ultimo_bbox is not None:
                    # Overlay rojo: persona diferente en etapa pestañeo
                    bx, by, bw, bh = self._ultimo_bbox
                    cv2.rectangle(resized, (bx-2, by-2), (bx+bw+2, by+bh+2), (0, 0, 160), 1)
                    cv2.rectangle(resized, (bx, by), (bx+bw, by+bh), (0, 0, 255), 3)
                    fn = cv2.FONT_HERSHEY_SIMPLEX
                    msg1 = "NO ES LA MISMA PERSONA"
                    (wt1, _), _ = cv2.getTextSize(msg1, fn, 0.65, 2)
                    cx1 = (cw - wt1) // 2
                    cv2.putText(resized, msg1, (cx1, by - 12 if by > 30 else by + bh + 24),
                                fn, 0.65, (0, 0, 0), 4, cv2.LINE_AA)
                    cv2.putText(resized, msg1, (cx1, by - 12 if by > 30 else by + bh + 24),
                                fn, 0.65, (80, 80, 255), 2, cv2.LINE_AA)
                else:
                    color_overlay = (80, 175, 76) if etapa == _ETAPA_FRENTE else (200, 80, 200)

                    n   = self._capturas_ok
                    pct = int(n / CAPTURAS_REQUERIDAS * 100)
                    txt = f"ESCANEANDO... {n}/{CAPTURAS_REQUERIDAS}  ({pct}%)"
                    fn  = cv2.FONT_HERSHEY_SIMPLEX
                    (wt, _), _ = cv2.getTextSize(txt, fn, 0.7, 2)
                    cv2.putText(resized, txt, ((cw-wt)//2, 36),
                                fn, 0.7, (0,0,0), 4, cv2.LINE_AA)
                    cv2.putText(resized, txt, ((cw-wt)//2, 36),
                                fn, 0.7, (255,255,255), 2, cv2.LINE_AA)

                    if self._ultimo_bbox is not None:
                        bx, by, bw, bh = self._ultimo_bbox
                        cv2.rectangle(resized, (bx, by), (bx+bw, by+bh), color_overlay, 2)

                    if etapa == _ETAPA_PESTANEO:
                        txt_p = f"Pestañeos: {self._pestaneos_ok}/{_PESTANEOS_REQUERIDOS}"
                        cv2.putText(resized, txt_p, (10, ch - 16),
                                    fn, 0.65, (0,0,0), 3, cv2.LINE_AA)
                        cv2.putText(resized, txt_p, (10, ch - 16),
                                    fn, 0.65, (200, 80, 200), 2, cv2.LINE_AA)

                rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._photo = photo
                self.label_video.after(0, self._pintar_frame)
            except Exception:
                pass

    def _dibujar_duplicado(self, resized, dup_nombre):
        if self._ultimo_bbox is None:
            return
        x, y, w, h = self._ultimo_bbox
        cv2.rectangle(resized, (x-2, y-2), (x+w+2, y+h+2), (0, 0, 180), 1)
        cv2.rectangle(resized, (x, y), (x+w, y+h), (0, 0, 255), 3)

        pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        draw    = ImageDraw.Draw(pil_img)
        try:
            _fp = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "segoeui.ttf"
            font_nom = ImageFont.truetype(str(_fp), 18)
            font_avi = ImageFont.truetype(str(_fp), 16)
        except Exception:
            font_nom = ImageFont.load_default()
            font_avi = font_nom

        pad = 6
        bb  = draw.textbbox((0, 0), dup_nombre, font=font_nom)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        ty = max(th + pad*2 + 2, y)
        draw.rectangle([x, ty-th-pad*2, x+tw+pad*2, ty], fill=(200, 0, 0))
        draw.text((x+pad, ty-th-pad+1), dup_nombre, font=font_nom, fill=(255, 255, 255))

        aviso = self._t("captura_rostro.dup_encontrado", "Rostro ya registrado:").strip()
        ab  = draw.textbbox((0, 0), aviso, font=font_avi)
        ax  = x + (w-(ab[2]-ab[0]))//2
        ay  = y + h + 8
        draw.text((ax+1, ay+1), aviso, font=font_avi, fill=(0, 0, 0))
        draw.text((ax,   ay),   aviso, font=font_avi, fill=(255, 80, 80))

        resized[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def _pintar_frame(self):
        if self._photo is None:
            return
        self.label_video.imgtk = self._photo
        self.label_video.config(image=self._photo, text="")

    # ═════════════════════════════════════════════════════════════════════
    #  HILO CAPTURA
    # ═════════════════════════════════════════════════════════════════════
    def _hilo_captura(self):
        while self._corriendo and self._capturas_ok < CAPTURAS_REQUERIDAS:
            try:
                frame = self._cola_frames.get(timeout=1.0)
            except queue.Empty:
                continue

            if self._etapa_actual == _ETAPA_PESTANEO:
                self._procesar_etapa_pestaneo(frame)
            else:
                self._procesar_etapa_frente(frame)

        self._corriendo = False
        if self._cap:
            self._cap.release()
        cv2.destroyAllWindows()
        self.label_video.after(0, self._finalizar, self._capturas_ok)

    # ── FRENTE ────────────────────────────────────────────────────────────────
    def _procesar_etapa_frente(self, frame):
        gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self._det_frontal.detectMultiScale(
            gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

        if len(rostros) == 0:
            self._frame_anterior = frame.copy()
            return

        x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])

        lv_ok, razon = _chequeo_liveness_frame(frame, self._frame_anterior, (x, y, w, h))
        self._frame_anterior = frame.copy()

        if not lv_ok:
            self._liveness_ok_streak = 0
            self.label_video.after(0, self._avisar_liveness, razon)
            return

        self._liveness_ok_streak += 1
        if self._liveness_ok_streak < _FRAMES_LIVENESS:
            return

        margen = 10
        x1 = max(0, x-margen);  y1 = max(0, y-margen)
        x2 = min(frame.shape[1], x+w+margen)
        y2 = min(frame.shape[0], y+h+margen)
        roi = frame[y1:y2, x1:x2]
        h_r, w_r = roi.shape[:2]
        if w_r > 160:
            s   = 160/w_r
            roi = cv2.resize(roi, (160, int(h_r*s)), interpolation=cv2.INTER_LINEAR)
        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

        if not FR_DISPONIBLE:
            self._capturas_ok += 1
            self.label_video.after(0, self._actualizar_contador, self._capturas_ok)
            self._checar_avance_frente()
            return

        encs = face_recognition.face_encodings(roi_rgb, num_jitters=1, model="small")
        if not encs:
            return

        enc_nuevo = encs[0]

        if len(self._encodings) < CAPTURAS_REFERENCIA:
            self._encodings.append(enc_nuevo)
            self._capturas_ok += 1
            self._descartes_seguidos = 0
            if len(self._encodings) == CAPTURAS_REFERENCIA:
                self._enc_referencia = np.mean(self._encodings, axis=0)
            self.label_video.after(0, self._actualizar_contador, self._capturas_ok)
            self._checar_avance_frente()
            return

        distancia = face_recognition.face_distance([self._enc_referencia], enc_nuevo)[0]

        if distancia > _UMBRAL_CONSISTENCIA:
            self._descartes_seguidos += 1
            if self._descartes_seguidos >= _MAX_DESCARTES_SEGUIDOS:
                self.label_video.after(0, self._avisar_rostro_extrano)
                self._descartes_seguidos = 0
            return

        self._descartes_seguidos = 0
        self._encodings.append(enc_nuevo)
        self._capturas_ok += 1
        self.label_video.after(0, self._actualizar_contador, self._capturas_ok)

        if not self._chequeo_rapido and self._capturas_ok >= CAPTURAS_PARA_CHEQUEO:
            self._chequeo_rapido = True
            enc_parcial = np.mean(self._encodings[:CAPTURAS_PARA_CHEQUEO], axis=0)
            threading.Thread(target=self._verificar_duplicado_rapido,
                             args=(enc_parcial,), daemon=True).start()

        self._checar_avance_frente()

    def _checar_avance_frente(self):
        if self._capturas_ok >= 20 and self._etapa_actual == _ETAPA_FRENTE:
            self._etapa_actual       = _ETAPA_PESTANEO
            self._pestaneos_ok       = 0
            # Reset completo del estado de pestañeo al entrar a la etapa
            self._ojo_cerrado        = False
            self._ear_cerrado_frames = 0
            self._t_ojo_cerrado      = None
            self._cara_ausente_antes      = False
            self._frames_diferente        = 0
            self._frames_pestaneo_count   = 0
            self._enc_pestaneo_cache      = None
            self._identidad_confirmada    = False   # exige verificación antes de contar EAR
            self.label_video.after(0, self._cambiar_etapa_ui, _ETAPA_PESTANEO)

    # ── PESTAÑEO (robusto) ────────────────────────────────────────────────────
    def _procesar_etapa_pestaneo(self, frame):
        gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self._det_frontal.detectMultiScale(
            gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

        # ── Sin cara en este frame ──────────────────────────────────────────
        if len(rostros) == 0:
            self._cara_ausente_antes   = True
            self._ojo_cerrado          = False
            self._ear_cerrado_frames   = 0
            self._t_ojo_cerrado        = None
            self._frames_diferente     = 0
            self._identidad_confirmada = False
            self._enc_pestaneo_cache   = None   # invalidar cache de encoding
            return

        x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
        self._frame_anterior = frame.copy()

        # ── Si la cara acaba de reaparecer, ignorar este frame ─────────────
        if self._cara_ausente_antes:
            self._cara_ausente_antes   = False
            self._ojo_cerrado          = False
            self._ear_cerrado_frames   = 0
            self._t_ojo_cerrado        = None
            self._frames_diferente     = 0
            self._identidad_confirmada = False
            self._enc_pestaneo_cache   = None
            return

        # ── Verificación de identidad SINCRÓNICA cada N frames ─────────────
        # Se calcula el encoding aquí mismo (en el hilo de captura) pero solo
        # cada _ID_VERIFY_INTERVAL frames para no saturar la CPU. El resultado
        # se guarda en _enc_pestaneo_cache y se usa para decidir si contar EAR.
        self._frames_pestaneo_count = getattr(self, '_frames_pestaneo_count', 0) + 1

        if FR_DISPONIBLE and self._enc_referencia is not None:
            if self._frames_pestaneo_count % _ID_VERIFY_INTERVAL == 0:
                # Calcular encoding del frame actual (sincrónico, mismo hilo)
                margen = 10
                fx1 = max(0, x - margen);  fy1 = max(0, y - margen)
                fx2 = min(frame.shape[1], x + w + margen)
                fy2 = min(frame.shape[0], y + h + margen)
                roi_v = frame[fy1:fy2, fx1:fx2]
                hr, wr = roi_v.shape[:2]
                if wr > 160:
                    roi_v = cv2.resize(roi_v, (160, int(hr * 160 / wr)),
                                       interpolation=cv2.INTER_LINEAR)
                try:
                    roi_rgb_v = cv2.cvtColor(roi_v, cv2.COLOR_BGR2RGB)
                    encs_v    = face_recognition.face_encodings(
                        roi_rgb_v, num_jitters=1, model="small")
                    self._enc_pestaneo_cache = encs_v[0] if encs_v else None
                except Exception:
                    self._enc_pestaneo_cache = None

            # Decidir identidad con el encoding cacheado (puede ser del frame actual
            # o de hasta _ID_VERIFY_INTERVAL frames atrás)
            enc_cache = getattr(self, '_enc_pestaneo_cache', None)
            if enc_cache is None:
                # Aún no tenemos encoding → no contar EAR todavía
                return
            dist_cache = face_recognition.face_distance([self._enc_referencia], enc_cache)[0]
            es_correcta = float(dist_cache) <= _UMBRAL_IDENTIDAD_PESTANEO

            if not es_correcta:
                if not self._persona_diferente_activa:
                    self._pestaneos_ok = 0   # anular pestañeos acumulados
                    self.label_video.after(0, self._on_persona_diferente_pestaneo)
                self._identidad_confirmada = False
                # Resetear estado de ojo para no heredar cierre de la persona incorrecta
                self._ojo_cerrado        = False
                self._ear_cerrado_frames = 0
                self._t_ojo_cerrado      = None
                return
            else:
                if self._persona_diferente_activa:
                    self._pestaneos_ok = 0
                    self.label_video.after(0, self._limpiar_overlay_persona_diferente)
                self._identidad_confirmada = True

        elif not FR_DISPONIBLE:
            # Sin librería, no hay verificación de identidad; continuar directo
            self._identidad_confirmada = True

        if not self._identidad_confirmada:
            return

        # ── Calcular EAR ───────────────────────────────────────────────────
        if FR_DISPONIBLE:
            frame_rgb         = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ear               = _calcular_ear_frame(frame_rgb, (y, x+w, y+h, x))
            if ear is None:
                return
            ojo_cerrado_ahora = ear < _EAR_UMBRAL
        else:
            ojo_y1  = max(0, y + int(h * 0.15))
            ojo_y2  = max(0, y + int(h * 0.45))
            ojo_roi = gris[ojo_y1:ojo_y2, x:x+w]
            if ojo_roi.size == 0:
                return
            brillo = float(np.mean(ojo_roi))
            if not hasattr(self, "_brillo_anterior"):
                self._brillo_anterior = brillo
                return
            ojo_cerrado_ahora = (self._brillo_anterior - brillo) > 8
            self._brillo_anterior = brillo

        ahora = time.monotonic()

        # ── Máquina de estados del pestañeo ────────────────────────────────
        if ojo_cerrado_ahora:
            if not self._ojo_cerrado:
                self._t_ojo_cerrado      = ahora
                self._ear_cerrado_frames = 1
            else:
                self._ear_cerrado_frames += 1
        else:
            if (self._ojo_cerrado
                    and self._ear_cerrado_frames >= _EAR_FRAMES_MINIMOS
                    and self._t_ojo_cerrado is not None
                    and (ahora - self._t_ojo_cerrado) <= (_PESTANEO_TIMEOUT_MS / 1000.0)):
                # ✓ Pestañeo válido
                self._pestaneos_ok += 1
                self._ear_cerrado_frames = 0
                self._t_ojo_cerrado      = None
                self.label_video.after(0, self._on_pestaneo_detectado)

                if self._pestaneos_ok >= _PESTANEOS_REQUERIDOS:
                    self._etapa_actual       = _ETAPA_FRENTE
                    self._cara_ausente_antes = False
                    self.label_video.after(0, self._cambiar_etapa_ui, _ETAPA_FRENTE)
            elif not self._ojo_cerrado:
                pass
            else:
                self._ear_cerrado_frames = 0
                self._t_ojo_cerrado      = None

        self._ojo_cerrado = ojo_cerrado_ahora

    # ── Callbacks UI ──────────────────────────────────────────────────────────
    def _cambiar_etapa_ui(self, etapa):
        try:
            if etapa == _ETAPA_PESTANEO:
                self._lbl_etapa.config(text="👁  Pestañea 2 veces")
                self._lbl_estado.config(
                    text=self._t("captura_rostro.etapa_pestañeo", "Pestañea 2 veces"),
                    fg="#9c27b0")
            else:
                self._lbl_etapa.config(text="👁  Mira al frente")
                self._lbl_estado.config(
                    text=self._t("captura_rostro.escaneando", "No te muevas\nescaneando..."),
                    fg="#43a047")
        except tk.TclError:
            pass

    def _on_pestaneo_detectado(self):
        try:
            self._lbl_estado.config(
                text=f"✓ Pestañeo {self._pestaneos_ok}/{_PESTANEOS_REQUERIDOS}",
                fg="#9c27b0")
        except tk.TclError:
            pass

    def _on_persona_diferente_pestaneo(self):
        """
        Activa overlay rojo de persona diferente pero NO detiene el escaneo.
        En cuanto la verificación confirme que es la misma persona,
        _limpiar_overlay_persona_diferente() quita el flag y continúa.
        """
        p = self._p
        try:
            self._persona_diferente_activa = True
            self._lbl_etapa.config(text="🚫 Persona diferente", fg=p["rojo"])
            self._lbl_estado.config(
                text="No es la misma\npersona registrada",
                fg=p["rojo"])
        except tk.TclError:
            pass

    def _limpiar_overlay_persona_diferente(self):
        """La persona correcta regresó; retomar la etapa de pestañeo normal."""
        p = self._p
        try:
            self._persona_diferente_activa = False
            self._pestaneos_ok             = 0   # empezar pestañeos desde 0 con la correcta
            self._ojo_cerrado              = False
            self._ear_cerrado_frames       = 0
            self._t_ojo_cerrado            = None
            self._lbl_etapa.config(text="👁  Pestañea 2 veces", fg=p["naranja"])
            self._lbl_estado.config(
                text=self._t("captura_rostro.etapa_pestañeo", "Pestañea 2 veces"),
                fg="#9c27b0")
        except tk.TclError:
            pass

    def _avisar_liveness(self, razon):
        mensajes = {
            "foto_estatica":  "⚠ Imagen estática\ndetectada",
            "baja_textura":   "⚠ Posible foto\nimpresa",
            "fondo_estatico": "⚠ Muévete un poco",
        }
        try:
            self._lbl_estado.config(
                text=mensajes.get(razon, "⚠ Liveness falló"),
                fg=self._p["rojo"])
            self.label_video.after(
                1500,
                lambda: self._lbl_estado.config(
                    text=_FALLBACK_ETAPA.get(self._etapa_actual, ""),
                    fg="#43a047") if self._capturando else None)
        except tk.TclError:
            pass

    def _avisar_rostro_extrano(self):
        try:
            self._lbl_estado.config(text="Aleja a otras\npersonas", fg=self._p["rojo"])
            self.label_video.after(
                2000,
                lambda: self._lbl_estado.config(
                    text=self._t("captura_rostro.escaneando", "No te muevas\nescaneando..."),
                    fg="#43a047") if self._capturando else None)
        except tk.TclError:
            pass

    def _verificar_duplicado_rapido(self, encoding_parcial):
        """
        Chequeo rápido de duplicados. Si hay coincidencia muestra el overlay
        pero NO detiene el escaneo; el aviso se limpia solo a los 3s para que
        la persona correcta pueda continuar registrándose.
        """
        try:
            from core.database import cargar_todos_encodings
            registrados = cargar_todos_encodings()
            if not registrados:
                return
            enc_existentes = [r["encoding"] for r in registrados]
            distancias     = face_recognition.face_distance(enc_existentes, encoding_parcial)
            idx_min        = int(np.argmin(distancias))
            if float(distancias[idx_min]) <= _UMBRAL_DUPLICADO:
                nombre_dup = registrados[idx_min].get("nombre", "—")
                self.label_video.after(0, self._on_duplicado_detectado, nombre_dup)
        except Exception as e:
            print(f"[CAPTURA-RÁPIDO] Error: {e}")

    def _on_duplicado_detectado(self, nombre_dup: str):
        """
        Muestra overlay de duplicado pero NO detiene el escaneo.
        Resetea contadores para que la persona correcta pueda registrarse.
        El overlay se limpia automáticamente a los 3s.
        """
        p = self._p
        try:
            self._duplicado_nombre   = nombre_dup
            self._chequeo_rapido     = False
            self._encodings          = []
            self._capturas_ok        = 0
            self._enc_referencia     = None
            self._descartes_seguidos = 0
            self._lbl_contador.config(text=f"0 / {CAPTURAS_REQUERIDAS}", fg=p["rojo"])
            self._prog_inner.place(x=0, y=0, height=8, width=0)
            self._lbl_estado.config(
                text=self._t("captura_rostro.dup_encontrado",
                             "Rostro ya registrado:\n") + nombre_dup,
                fg=p["rojo"])
            self._lbl_etapa.config(text="⚠ Rostro duplicado", fg=p["rojo"])
            # Limpiar el overlay a los 3s; el escaneo ya sigue corriendo
            self.label_video.after(3000, self._limpiar_overlay_duplicado)
        except tk.TclError:
            pass

    def _limpiar_overlay_duplicado(self):
        """Limpia el flag de duplicado; el escaneo ya venía corriendo."""
        try:
            if not self._capturando:
                return
            self._duplicado_nombre = None
            p = self._p
            self._lbl_etapa.config(text="👁  Mira al frente", fg=p["naranja"])
            self._lbl_estado.config(
                text=self._t("captura_rostro.escaneando", "No te muevas\nescaneando..."),
                fg="#43a047")
            self._lbl_contador.config(fg=p["verde"])
        except tk.TclError:
            pass

    def _actualizar_contador(self, n):
        self._lbl_contador.config(text=f"{n} / {CAPTURAS_REQUERIDAS}")
        try:
            ancho = self._prog_outer.winfo_width()
            if ancho > 0:
                self._prog_inner.place(
                    x=0, y=0, height=8,
                    width=int(ancho * n / CAPTURAS_REQUERIDAS))
        except Exception:
            pass

    def _finalizar(self, n):
        self._capturando = False
        p = self._p

        if n >= CAPTURAS_REQUERIDAS:
            self._lbl_estado.config(
                text=self._t("captura_rostro.completo", "¡Escaneo\ncompleto!"),
                fg=p["verde"])
            self._lbl_etapa.config(text="✓ Liveness OK", fg=p["verde"])
            self._btn_iniciar.config(
                text=self._t("captura_rostro.btn_completado", "✓  COMPLETADO"),
                bg=p["verde_ok"], state="disabled")
            self._lbl_contador.config(fg=p["verde"])
            self._lbl_estado.config(
                text=self._t("captura_rostro.verificando_dup", "Verificando\nduplicados..."),
                fg=p["texto2"])
            encoding_final = np.mean(self._encodings, axis=0)
            threading.Thread(target=self._verificar_y_regresar,
                             args=(encoding_final,), daemon=True).start()
        else:
            if not self._chequeo_rapido or n > 0:
                self._lbl_estado.config(
                    text=self._t("captura_rostro.incompleto", "Incompleto\n") +
                         f"{n}/{CAPTURAS_REQUERIDAS}",
                    fg=p["rojo"])
                self._lbl_etapa.config(text="")
                self._btn_iniciar.config(
                    text=self._t("captura_rostro.btn_reintentar", "▶  REINTENTAR"),
                    bg=p["verde"], state="normal")

    def _verificar_y_regresar(self, encoding):
        try:
            from core.database import cargar_todos_encodings
            registrados = cargar_todos_encodings()

            if registrados and FR_DISPONIBLE:
                enc_existentes = [r["encoding"] for r in registrados]
                coincidencias  = face_recognition.compare_faces(
                    enc_existentes, encoding, tolerance=_UMBRAL_DUPLICADO)
                distancias = face_recognition.face_distance(enc_existentes, encoding)

                if any(coincidencias):
                    idx_min    = int(np.argmin(distancias))
                    nombre_dup = registrados[idx_min].get("nombre", "—")
                    self.label_video.after(0, self._on_duplicado_detectado, nombre_dup)
                    return

            datos_con_enc = dict(self.datos)
            datos_con_enc["face_encoding"] = encoding
            self.label_video.after(
                0, lambda: self.app.mostrar_pantalla("agregar_usuario", datos_con_enc))

        except Exception as e:
            print(f"[CAPTURA] Error: {e}")
            self.label_video.after(0, lambda: modal_error(
                self.pantalla, str(e), titulo="Error"))

    def _cancelar(self):
        self._capturando = False
        self._corriendo  = False
        if self._cap:
            self._cap.release()
        self.app.mostrar_pantalla("agregar_usuario", self.datos)


def crear_pantalla_captura(parent, app, datos=None):
    PantallaCaptura(parent, app, datos)