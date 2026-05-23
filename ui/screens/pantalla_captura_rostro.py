"""
ui/screens/pantalla_captura_rostro.py

CAMBIOS:
  - Conectado a GestorIdioma: etiquetas, botones y mensajes de estado
    leen del idioma activo.
  - _limpiar() desregistra también el listener de idioma.
"""

import tkinter as tk
import threading
import queue
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

_C = {
    "bg":"#f3f4f5","feed_bg":"#1c1c1c","panel_bg":"#ffffff",
    "panel_borde":"#e0e0e0","texto":"#1a1a1a","texto2":"#757575",
    "verde":"#43a047","verde_m":"#4caf50","verde_ok":"#2e7d32",
    "verde_hover":"#388e3c","rojo":"#e53935","rojo_hover":"#b71c1c",
    "prog_bg":"#e0e0e0","prog_fg":"#43a047",
}
_O = {
    "bg":"#071E07","feed_bg":"#0a0a0a","panel_bg":"#0d2a0d",
    "panel_borde":"#1a3a1a","texto":"#d0f0d0","texto2":"#7aaa7a",
    "verde":"#2D531A","verde_m":"#477023","verde_ok":"#1a3a1a",
    "verde_hover":"#477023","rojo":"#7f1d1d","rojo_hover":"#991b1b",
    "prog_bg":"#1a3a1a","prog_fg":"#477023",
}


def _paleta(app) -> dict:
    return _O if (hasattr(app, "tema") and app.tema.es_oscuro()) else _C


class PantallaCaptura:

    def __init__(self, parent, app, datos=None):
        self.parent  = parent
        self.app     = app
        self.datos   = datos or {}
        self._p      = _paleta(app)

        self._capturando        = False
        self._capturas_ok       = 0
        self._encodings         = []
        self._photo             = None
        self._chequeo_rapido    = False
        self._duplicado_nombre  = None
        self._ultimo_bbox       = None
        self._enc_referencia     = None
        self._descartes_seguidos = 0

        self._cap             = None
        self._corriendo       = False
        self._cola_frames     = queue.Queue(maxsize=MAX_FRAMES_COLA)
        self._contador_frames = 0

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._on_tema_cambio)
        if hasattr(app, "idioma"):
            app.idioma.registrar(self._aplicar_idioma)
        self.pantalla.bind("<Destroy>", self._limpiar)

    # ── Idioma ────────────────────────────────────────────────────────────────
    def _t(self, clave, fallback=""):
        if hasattr(self.app, "idioma"):
            return self.app.idioma.t(clave, fallback)
        return fallback or clave

    def _aplicar_idioma(self):
        try:
            nombre = f"{self.datos.get('nombre','')} {self.datos.get('apellido_paterno','')}".strip()
            self._lbl_reg.config(
                text=self._t("captura_rostro.registrando", "REGISTRANDO"))
            self._lbl_nombre.config(
                text=nombre or self._t("captura_rostro.usuario_default", "Usuario"))
            self._lbl_cap_titulo.config(
                text=self._t("captura_rostro.label_capturas", "CAPTURAS"))
            # Estado: solo actualizar si no está en medio de una captura activa
            if not self._capturando:
                self._lbl_estado.config(
                    text=self._t("captura_rostro.listo", "Listo para\nescanear"))
            # Botones
            if not self._capturando:
                self._btn_iniciar.config(
                    text=self._t("captura_rostro.btn_iniciar", "▶  INICIAR"))
            self._btn_cancelar.config(
                text=self._t("captura_rostro.btn_cancelar", "✕  CANCELAR"))
        except tk.TclError:
            pass

    # ── Tema ──────────────────────────────────────────────────────────────────
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
            self._panel.configure(bg=p["panel_bg"],
                                   highlightbackground=p["panel_borde"])
            self._lbl_reg.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._lbl_nombre.configure(bg=p["panel_bg"], fg=p["texto"])
            self._sep1.configure(bg=p["panel_borde"])
            self._lbl_cap_titulo.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._lbl_contador.configure(bg=p["panel_bg"], fg=p["verde"])
            self._prog_outer.configure(bg=p["prog_bg"])
            self._prog_inner.configure(bg=p["prog_fg"])
            self._lbl_estado.configure(bg=p["panel_bg"], fg=p["texto2"])
            self._sep2.configure(bg=p["panel_borde"])
            self._btn_frame.configure(bg=p["panel_bg"])
            self._btn_iniciar.configure(bg=p["verde"],
                                         activebackground=p["verde_hover"])
            self._btn_cancelar.configure(bg=p["rojo"],
                                          activebackground=p["rojo_hover"])
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════════════════════
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
                               highlightthickness=1,
                               highlightbackground=p["panel_borde"])
        self._panel.grid(row=0, column=1, sticky="nsew")
        self._panel.pack_propagate(False)

        tk.Frame(self._panel, bg=p["verde_m"], height=4).pack(fill="x")

        nombre = f"{self.datos.get('nombre','')} {self.datos.get('apellido_paterno','')}".strip()

        self._lbl_reg = tk.Label(
            self._panel,
            text=self._t("captura_rostro.registrando", "REGISTRANDO"),
            font=("Segoe UI", 8), fg=p["texto2"], bg=p["panel_bg"])
        self._lbl_reg.pack(pady=(14, 2))

        self._lbl_nombre = tk.Label(
            self._panel,
            text=nombre or self._t("captura_rostro.usuario_default", "Usuario"),
            font=("Segoe UI", 11, "bold"), fg=p["texto"],
            bg=p["panel_bg"], wraplength=185, justify="center")
        self._lbl_nombre.pack()

        self._sep1 = tk.Frame(self._panel, bg=p["panel_borde"], height=1)
        self._sep1.pack(fill="x", pady=10, padx=10)

        self._lbl_cap_titulo = tk.Label(
            self._panel,
            text=self._t("captura_rostro.label_capturas", "CAPTURAS"),
            font=("Segoe UI", 8), fg=p["texto2"], bg=p["panel_bg"])
        self._lbl_cap_titulo.pack()

        self._lbl_contador = tk.Label(
            self._panel, text=f"0 / {CAPTURAS_REQUERIDAS}",
            font=("Segoe UI", 22, "bold"),
            fg=p["verde"], bg=p["panel_bg"])
        self._lbl_contador.pack(pady=(4, 8))

        self._prog_outer = tk.Frame(self._panel, bg=p["prog_bg"], height=8)
        self._prog_outer.pack(fill="x", padx=16, pady=(0, 10))
        self._prog_inner = tk.Frame(self._prog_outer, bg=p["prog_fg"],
                                     height=8, width=0)
        self._prog_inner.place(x=0, y=0, height=8)

        self._lbl_estado = tk.Label(
            self._panel,
            text=self._t("captura_rostro.listo", "Listo para\nescanear"),
            font=("Segoe UI", 10), fg=p["texto2"],
            bg=p["panel_bg"], justify="center", wraplength=185)
        self._lbl_estado.pack(pady=(0, 10))

        self._sep2 = tk.Frame(self._panel, bg=p["panel_borde"], height=1)
        self._sep2.pack(fill="x", padx=10)

        self._btn_frame = tk.Frame(self._panel, bg=p["panel_bg"])
        self._btn_frame.pack(fill="x", padx=12, pady=10)

        self._btn_iniciar = tk.Button(
            self._btn_frame,
            text=self._t("captura_rostro.btn_iniciar", "▶  INICIAR"),
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["verde"],
            activebackground=p["verde_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2",
            command=self._toggle)
        self._btn_iniciar.pack(fill="x", pady=(0, 6))

        self._btn_cancelar = tk.Button(
            self._btn_frame,
            text=self._t("captura_rostro.btn_cancelar", "✕  CANCELAR"),
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg=p["rojo"],
            activebackground=p["rojo_hover"], activeforeground="#ffffff",
            bd=0, pady=10, relief="flat", cursor="hand2",
            command=self._cancelar)
        self._btn_cancelar.pack(fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  CAPTURA
    # ══════════════════════════════════════════════════════════════════════════
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

        p = self._p
        self._btn_iniciar.config(
            text=self._t("captura_rostro.btn_detener", "⏹  DETENER"),
            bg=p["rojo"], activebackground=p["rojo_hover"])
        self._lbl_estado.config(
            text=self._t("captura_rostro.escaneando", "No te muevas\nescaneando..."),
            fg="#43a047")

        self._cap = cv2.VideoCapture(_CAM_INDEX)
        if not self._cap.isOpened():
            otro = 1 - _CAM_INDEX
            self._cap = cv2.VideoCapture(otro)
        if not self._cap.isOpened():
            modal_error(self.pantalla,
                        self._t("captura_rostro.error_camara_msg",
                                "No se pudo abrir la cámara."),
                        titulo=self._t("captura_rostro.error_camara_titulo",
                                       "Error de cámara"))
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
            text=self._t("captura_rostro.detenido", "Detenido"),
            fg=p["texto2"])

    # ══════════════════════════════════════════════════════════════════════════
    #  HILOS
    # ══════════════════════════════════════════════════════════════════════════
    def _hilo_camara(self):
        self._contador_frames = 0
        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

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
                resized = cv2.resize(frame, (cw, ch),
                                     interpolation=cv2.INTER_LINEAR)

                gris    = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                rostros = detector.detectMultiScale(
                    gris, scaleFactor=1.3, minNeighbors=5, minSize=(60, 60))
                if len(rostros) > 0:
                    x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
                    self._ultimo_bbox = (x, y, w, h)

                dup_nombre = self._duplicado_nombre

                if dup_nombre and self._ultimo_bbox is not None:
                    x, y, w, h = self._ultimo_bbox
                    cv2.rectangle(resized, (x-2, y-2), (x+w+2, y+h+2),
                                  (0, 0, 180), 1)
                    cv2.rectangle(resized, (x, y), (x+w, y+h),
                                  (0, 0, 255), 3)

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
                    draw.rectangle([x, ty-th-pad*2, x+tw+pad*2, ty],
                                   fill=(200, 0, 0))
                    draw.text((x+pad, ty-th-pad+1),
                              dup_nombre, font=font_nom, fill=(255, 255, 255))

                    # Texto "YA REGISTRADO" desde idioma (hardcoded en CV2 overlay)
                    aviso = self._t("captura_rostro.dup_encontrado",
                                    "Rostro ya\nregistrado:\n").replace("\n", " ").strip()
                    ab  = draw.textbbox((0, 0), aviso, font=font_avi)
                    aw  = ab[2]-ab[0]
                    ax  = x + (w-aw)//2
                    ay  = y + h + 8
                    draw.text((ax+1, ay+1), aviso, font=font_avi, fill=(0, 0, 0))
                    draw.text((ax,   ay),   aviso, font=font_avi, fill=(255, 80, 80))

                    resized = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                else:
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
                        cv2.rectangle(resized, (bx, by), (bx+bw, by+bh),
                                      (80, 175, 76), 2)

                rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._photo = photo
                self.label_video.after(0, self._pintar_frame)
            except Exception:
                pass

    def _pintar_frame(self):
        if self._photo is None:
            return
        self.label_video.imgtk = self._photo
        self.label_video.config(image=self._photo, text="")

    def _hilo_captura(self):
        detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while self._corriendo and self._capturas_ok < CAPTURAS_REQUERIDAS:
            try:
                frame = self._cola_frames.get(timeout=1.0)
            except queue.Empty:
                continue

            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

            if len(rostros) == 0:
                continue

            x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
            margen = 10
            x1 = max(0, x-margen);  y1 = max(0, y-margen)
            x2 = min(frame.shape[1], x+w+margen)
            y2 = min(frame.shape[0], y+h+margen)
            roi = frame[y1:y2, x1:x2]

            h_r, w_r = roi.shape[:2]
            if w_r > 160:
                s   = 160/w_r
                roi = cv2.resize(roi, (160, int(h_r*s)),
                                 interpolation=cv2.INTER_LINEAR)

            roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

            if not FR_DISPONIBLE:
                self._capturas_ok += 1
                self.label_video.after(0, self._actualizar_contador, self._capturas_ok)
                continue

            encs = face_recognition.face_encodings(
                roi_rgb, num_jitters=1, model="small")
            if not encs:
                continue

            enc_nuevo = encs[0]

            if len(self._encodings) < CAPTURAS_REFERENCIA:
                self._encodings.append(enc_nuevo)
                self._capturas_ok += 1
                self._descartes_seguidos = 0

                if len(self._encodings) == CAPTURAS_REFERENCIA:
                    self._enc_referencia = np.mean(self._encodings, axis=0)

                self.label_video.after(0, self._actualizar_contador, self._capturas_ok)
                continue

            distancia = face_recognition.face_distance(
                [self._enc_referencia], enc_nuevo)[0]

            if distancia > _UMBRAL_CONSISTENCIA:
                self._descartes_seguidos += 1
                if self._descartes_seguidos >= _MAX_DESCARTES_SEGUIDOS:
                    self.label_video.after(0, self._avisar_rostro_extrano)
                    self._descartes_seguidos = 0
                continue

            self._descartes_seguidos = 0
            self._encodings.append(enc_nuevo)
            self._capturas_ok += 1
            self.label_video.after(0, self._actualizar_contador, self._capturas_ok)

            if (not self._chequeo_rapido
                    and self._capturas_ok >= CAPTURAS_PARA_CHEQUEO):
                self._chequeo_rapido = True
                enc_parcial = np.mean(self._encodings[:CAPTURAS_PARA_CHEQUEO], axis=0)
                threading.Thread(
                    target=self._verificar_duplicado_rapido,
                    args=(enc_parcial,), daemon=True).start()

        self._corriendo = False
        if self._cap:
            self._cap.release()
        cv2.destroyAllWindows()
        self.label_video.after(0, self._finalizar, self._capturas_ok)

    def _avisar_rostro_extrano(self):
        try:
            self._lbl_estado.config(
                text=self._t("captura_rostro.incompleto",
                             "Incompleto\n").replace("\n", "") +
                     "\nAleja a otras personas",
                fg=self._p["rojo"])
            self.label_video.after(
                2000,
                lambda: self._lbl_estado.config(
                    text=self._t("captura_rostro.escaneando",
                                 "No te muevas\nescaneando..."),
                    fg="#43a047") if self._capturando else None)
        except tk.TclError:
            pass

    def _verificar_duplicado_rapido(self, encoding_parcial):
        try:
            from core.database import cargar_todos_encodings
            registrados = cargar_todos_encodings()
            if not registrados:
                return
            enc_existentes = [r["encoding"] for r in registrados]
            distancias     = face_recognition.face_distance(enc_existentes, encoding_parcial)
            idx_min        = int(np.argmin(distancias))
            dist_min       = float(distancias[idx_min])
            if dist_min <= _UMBRAL_DUPLICADO:
                nombre_dup = registrados[idx_min].get("nombre", "—")
                self._corriendo  = False
                self._capturando = False
                self.label_video.after(0, self._on_duplicado_detectado, nombre_dup)
        except Exception as e:
            print(f"[CAPTURA-RÁPIDO] Error: {e}")

    def _on_duplicado_detectado(self, nombre_dup: str):
        p = self._p
        try:
            self._duplicado_nombre   = nombre_dup
            self._lbl_estado.config(
                text=self._t("captura_rostro.dup_encontrado",
                             "Rostro ya\nregistrado:\n") + nombre_dup,
                fg=p["rojo"])
            self._btn_iniciar.config(
                text=self._t("captura_rostro.btn_reintentar", "▶  REINTENTAR"),
                bg=p["verde"], activebackground=p["verde_hover"], state="normal")
            self._lbl_contador.config(
                text=f"0 / {CAPTURAS_REQUERIDAS}", fg=p["rojo"])
            self._prog_inner.place(x=0, y=0, height=8, width=0)
            self._encodings          = []
            self._capturas_ok        = 0
            self._chequeo_rapido     = False
            self._enc_referencia     = None
            self._descartes_seguidos = 0
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
            self._btn_iniciar.config(
                text=self._t("captura_rostro.btn_completado", "✓  COMPLETADO"),
                bg=p["verde_ok"], state="disabled")
            self._lbl_contador.config(fg=p["verde"])
            self._lbl_estado.config(
                text=self._t("captura_rostro.verificando_dup",
                             "Verificando\nduplicados..."),
                fg=p["texto2"])
            encoding_final = np.mean(self._encodings, axis=0)
            threading.Thread(
                target=self._verificar_y_regresar,
                args=(encoding_final,), daemon=True).start()
        else:
            if not self._chequeo_rapido or n > 0:
                self._lbl_estado.config(
                    text=self._t("captura_rostro.incompleto",
                                 "Incompleto\n") + f"{n}/{CAPTURAS_REQUERIDAS}",
                    fg=p["rojo"])
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
                0, lambda: self.app.mostrar_pantalla(
                    "agregar_usuario", datos_con_enc))

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