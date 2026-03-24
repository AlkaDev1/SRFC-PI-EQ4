"""
ui/screens/pantalla_acceso.py
Pantalla de acceso biométrico — diseño limpio.
Video grande, recuadro completo sobre el rostro, barra de estado arriba.
"""

import tkinter as tk
import threading
import math
import queue
import os
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado

try:
    import face_recognition
    FR_DISPONIBLE = True
except ImportError:
    FR_DISPONIBLE = False

FRAMES_CONFIRMAR = 8
FRAMES_PERDER    = 8   # frames sin rostro para limpiar bbox


class PantallaAcceso:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        self._estado         = "escaneando"
        self._angulo         = 0
        self._pulso          = 0.0
        self._pulso_dir      = 1
        self._confianza      = 0.0
        self._bbox           = None   # (x, y, w, h) en coords del frame escalado
        self._photo          = None
        self._bloqueado      = False
        self._frames_ok      = 0
        self._frames_deny    = 0
        self._frames_perdido = 0
        self._after_anim     = None
        self._after_reset    = None

        self._nombres    = []
        self._encodings  = []
        self._cargar_perfiles()

        self._cap        = None
        self._corriendo  = False
        self._cola_bio   = queue.Queue(maxsize=2)

        self._construir_ui()
        self._iniciar_animacion()
        self._abrir_camara()

    # ══════════════════════════════════════════
    #  Perfiles
    # ══════════════════════════════════════════
    def _cargar_perfiles(self):
        if not FR_DISPONIBLE:
            return
        base    = os.path.dirname(os.path.dirname(
                  os.path.dirname(os.path.abspath(__file__))))
        carpeta = os.path.join(base, "data", "profiles")
        os.makedirs(carpeta, exist_ok=True)
        for archivo in os.listdir(carpeta):
            if not archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ruta   = os.path.join(carpeta, archivo)
            nombre = os.path.splitext(archivo)[0].replace("_", " ").title()
            try:
                img  = face_recognition.load_image_file(ruta)
                encs = face_recognition.face_encodings(img)
                if encs:
                    self._encodings.append(encs[0])
                    self._nombres.append(nombre)
            except Exception as e:
                print(f"[PERFIL] {archivo}: {e}")
        print(f"[PERFILES] Cargados: {len(self._nombres)}")

    # ══════════════════════════════════════════
    #  Cámara
    # ══════════════════════════════════════════
    def _abrir_camara(self):
        self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._cambiar_estado("sin_camara")
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._corriendo = True
        threading.Thread(target=self._hilo_camara,    daemon=True).start()
        threading.Thread(target=self._hilo_biometria, daemon=True).start()

    def _hilo_camara(self):
        import time
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while self._corriendo:
            ok, frame = self._cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)

            # Encolar para face_recognition
            try:
                self._cola_bio.put_nowait(frame.copy())
            except queue.Full:
                pass

            try:
                # Escalar al canvas
                cw = self.label_video.winfo_width()
                ch = self.label_video.winfo_height()
                if cw < 10 or ch < 10:
                    time.sleep(0.04)
                    continue

                resized = cv2.resize(frame, (cw, ch))

                # Dibujar recuadro completo (no esquinas) sobre el frame
                if self._bbox:
                    x1, y1, x2, y2 = self._bbox
                    color_bgr = {
                        "escaneando":  (76, 175, 80),
                        "detectado":   (139, 195, 74),
                        "acceso_ok":   (76, 175, 80),
                        "acceso_deny": (54,  54, 244),
                        "sin_rostro":  (158, 158, 158),
                    }.get(self._estado, (76, 175, 80))
                    cv2.rectangle(resized, (x1, y1), (x2, y2), color_bgr, 2)

                rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._photo = photo
                self.label_video.after(0, self._pintar_frame)
            except Exception:
                pass

            time.sleep(1 / 30)

    def _hilo_biometria(self):
        cnt = 0
        while self._corriendo:
            try:
                frame = self._cola_bio.get(timeout=0.5)
            except queue.Empty:
                continue
            cnt += 1
            if cnt % 4 != 0:
                continue
            resultado = self._reconocer(frame)
            try:
                self.label_video.after(0, lambda r=resultado: self._aplicar_resultado(r))
            except Exception:
                pass

    def _reconocer(self, frame):
        if FR_DISPONIBLE:
            pequeño = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb     = cv2.cvtColor(pequeño, cv2.COLOR_BGR2RGB)
            ubs     = face_recognition.face_locations(rgb, model="hog")
            if not ubs:
                return {"hay_rostro": False}
            ub      = max(ubs, key=lambda u: (u[2]-u[0]) * (u[1]-u[3]))
            ub_orig = (ub[0]*2, ub[1]*2, ub[2]*2, ub[3]*2)
            if not self._encodings:
                return {"hay_rostro": True, "reconocido": False,
                        "confianza": 0.0, "ubicacion": ub_orig, "nombre": ""}
            encs = face_recognition.face_encodings(rgb, [ub])
            if not encs:
                return {"hay_rostro": True, "reconocido": False,
                        "confianza": 0.0, "ubicacion": ub_orig, "nombre": ""}
            dists = face_recognition.face_distance(self._encodings, encs[0])
            idx   = int(np.argmin(dists))
            dist  = float(dists[idx])
            conf  = round(max(0.0, 1.0 - dist), 3)
            if dist <= 0.50:
                return {"hay_rostro": True, "reconocido": True,
                        "confianza": conf, "ubicacion": ub_orig,
                        "nombre": self._nombres[idx]}
            return {"hay_rostro": True, "reconocido": False,
                    "confianza": conf, "ubicacion": ub_orig, "nombre": ""}
        else:
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            # minNeighbors alto para reducir falsos positivos (monitores, fondos)
            rostros = cascade.detectMultiScale(
                gris, scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
            if len(rostros) == 0:
                return {"hay_rostro": False}
            # Tomar el rostro más grande detectado
            x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
            # Formato: (top, right, bottom, left) — igual que face_recognition
            return {"hay_rostro": True, "reconocido": False,
                    "confianza": 0.3, "ubicacion": (y, x+w, y+h, x), "nombre": ""}

    # ══════════════════════════════════════════
    #  Resultado
    # ══════════════════════════════════════════
    def _aplicar_resultado(self, r):
        if self._bloqueado:
            return

        if r.get("hay_rostro") and r.get("ubicacion"):
            top, right, bottom, left = r["ubicacion"]
            cw = self.label_video.winfo_width()
            ch = self.label_video.winfo_height()
            sx, sy = cw / 640.0, ch / 480.0
            # El frame ya viene volteado (espejo aplicado antes de encolar)
            # por lo que las coordenadas son directas, sin corrección extra
            self._bbox = (int(left*sx), int(top*sy), int(right*sx), int(bottom*sy))
            self._frames_perdido = 0
        else:
            self._frames_perdido += 1
            if self._frames_perdido >= FRAMES_PERDER:
                self._bbox = None

        if not r.get("hay_rostro"):
            self._frames_ok = self._frames_deny = 0
            if self._frames_perdido >= FRAMES_PERDER:
                self._cambiar_estado("sin_rostro", 0.0)
            return

        if r.get("reconocido"):
            self._frames_deny  = 0
            self._frames_ok   += 1
            self._cambiar_estado("detectado", r["confianza"])
            if self._frames_ok >= FRAMES_CONFIRMAR:
                self._frames_ok = 0
                self._bloqueado = True
                self._cambiar_estado("acceso_ok", r["confianza"], r["nombre"])
                self._after_reset = self.label_video.after(3000, self._resetear)
        else:
            self._frames_ok    = 0
            self._frames_deny += 1
            self._cambiar_estado("detectado", r["confianza"])
            if self._frames_deny >= FRAMES_CONFIRMAR:
                self._frames_deny = 0
                self._bloqueado   = True
                self._cambiar_estado("acceso_deny", r["confianza"])
                self._after_reset = self.label_video.after(3000, self._resetear)

    def _resetear(self):
        self._bloqueado = False
        self._bbox      = None
        self._cambiar_estado("escaneando", 0.0)

    # ══════════════════════════════════════════
    #  UI — layout limpio (estilo validacionUsrs)
    # ══════════════════════════════════════════
    def _construir_ui(self):
        pantalla = tk.Frame(self.parent, bg=PALETA["page_bg"])
        pantalla.pack(fill="both", expand=True)

        crear_encabezado(pantalla, self.parent.winfo_toplevel())
        tk.Frame(pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        # Contenedor oscuro — video ocupa todo
        contenedor = tk.Frame(pantalla, bg="#000000")
        contenedor.pack(fill="both", expand=True)

        # Video de fondo
        self.label_video = tk.Label(
            contenedor, bg="#000000",
            text="Iniciando cámara...",
            font=("Segoe UI", 14),
            fg=PALETA["topbar_sistema_fg"],
        )
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        # ── Barra superior superpuesta ────────
        self.barra_top = tk.Frame(contenedor, bg=PALETA["central_fondo"])
        self.barra_top.place(x=10, y=10, relwidth=0.98)

        estilo_btn = dict(
            font=("Segoe UI", 11, "bold"),
            fg=PALETA["boton_fg"],
            bg=PALETA["boton_bg"],
            activebackground=PALETA["boton_hover"],
            bd=0, padx=15, pady=10,
            cursor="hand2", relief="flat",
        )

        tk.Button(self.barra_top, text="← VOLVER",
                  command=self._volver, **estilo_btn).pack(side="left", padx=5, pady=5)

        # Icono de estado animado (canvas pequeño)
        self.canvas_icono = tk.Canvas(
            self.barra_top, width=34, height=34,
            bg=PALETA["central_fondo"], highlightthickness=0)
        self.canvas_icono.pack(side="left", padx=(10, 4), pady=5)

        # Texto de estado
        self.lbl_estado = tk.Label(
            self.barra_top, text="Buscando rostro...",
            font=("Segoe UI", 11, "bold"),
            fg=PALETA["topbar_sistema_fg"],
            bg=PALETA["central_fondo"],
            pady=10,
        )
        self.lbl_estado.pack(side="left", padx=4)

        # Barra de confianza (pequeña, al lado del texto)
        self.canvas_barra = tk.Canvas(
            self.barra_top, width=120, height=8,
            bg=PALETA["ghost_bg"], highlightthickness=0)
        self.canvas_barra.pack(side="left", padx=(4, 10), pady=5)

    # ══════════════════════════════════════════
    #  Animación
    # ══════════════════════════════════════════
    def _iniciar_animacion(self):
        self._animar()

    def _animar(self):
        self._angulo = (self._angulo + 4) % 360
        self._pulso += 0.05 * self._pulso_dir
        if   self._pulso >= 1.0: self._pulso, self._pulso_dir = 1.0, -1
        elif self._pulso <= 0.0: self._pulso, self._pulso_dir = 0.0,  1

        self._dibujar_icono()
        self._dibujar_barra()
        try:
            self._after_anim = self.canvas_icono.after(33, self._animar)
        except Exception:
            pass

    def _dibujar_icono(self):
        c = self.canvas_icono
        c.delete("all")
        cx, cy, r = 17, 17, 13

        if self._estado in ("escaneando", "sin_rostro", "sin_camara"):
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline="#cccccc", width=2, fill=PALETA["ghost_bg"])
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=self._angulo, extent=230,
                         style="arc", outline=PALETA["central_onda"], width=2)
        elif self._estado == "detectado":
            ai = int(40 + self._pulso * 80)
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline=f"#{ai:02x}af{ai:02x}", width=3,
                          fill=PALETA["topbar_btn_bg"])
            c.create_oval(cx-4, cy-4, cx+4, cy+4,
                          fill=PALETA["central_onda"], outline="")
        elif self._estado == "acceso_ok":
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline="#4CAF50", width=2, fill="#e8f5e9")
            c.create_text(cx, cy, text="✓",
                          font=("Segoe UI", 12, "bold"), fill="#2e7d32")
        elif self._estado == "acceso_deny":
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline="#e53935", width=2, fill="#ffebee")
            c.create_text(cx, cy, text="✕",
                          font=("Segoe UI", 12, "bold"), fill="#c62828")

    def _dibujar_barra(self):
        c = self.canvas_barra
        c.delete("all")
        w, h = 120, 8
        c.create_rectangle(0, 0, w, h, fill=PALETA["ghost_bg"], outline="")
        fw = int(w * min(max(self._confianza, 0), 1))
        if fw > 0:
            col = ("#4CAF50" if self._confianza > 0.6 else
                   "#FFC107" if self._confianza > 0.3 else "#9E9E9E")
            c.create_rectangle(0, 0, fw, h, fill=col, outline="")

    def _pintar_frame(self):
        if self._photo is None: return
        self.label_video.imgtk = self._photo
        self.label_video.config(image=self._photo, text="")

    # ══════════════════════════════════════════
    #  Estado
    # ══════════════════════════════════════════
    def _cambiar_estado(self, estado, confianza=0.0, nombre=""):
        self._estado    = estado
        self._confianza = confianza

        textos = {
            "escaneando":  ("Buscando rostro...",   PALETA["topbar_sistema_fg"]),
            "detectado":   ("Rostro detectado",     PALETA["topbar_sistema_fg"]),
            "acceso_ok":   (f"¡Bienvenido{', '+nombre if nombre else ''}!", "#2e7d32"),
            "acceso_deny": ("Rostro no reconocido", "#c62828"),
            "sin_rostro":  ("Acércate a la cámara", "#888888"),
            "sin_camara":  ("Cámara no disponible", "#888888"),
        }
        txt, color = textos.get(estado, ("", PALETA["topbar_sistema_fg"]))
        self.lbl_estado.config(text=txt, fg=color)

    # ══════════════════════════════════════════
    #  Limpieza
    # ══════════════════════════════════════════
    def _volver(self):
        self._corriendo = False
        if self._cap:
            self._cap.release()
        for aid in (self._after_anim, self._after_reset):
            if aid:
                try: self.canvas_icono.after_cancel(aid)
                except: pass
        self.app.mostrar_pantalla("principal")


def crear_pantalla_acceso(parent, app):
    PantallaAcceso(parent, app)