"""
ui/screens/validacionUsrs.py
Pantalla de Gestión — integrada con el sistema de navegación.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import cv2
from PIL import Image, ImageTk, ImageDraw

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado

try:
    import face_recognition
    TIENE_FACE_RECOGNITION = True
except ImportError:
    TIENE_FACE_RECOGNITION = False


class PantallaGestion:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        self.running           = True
        self.frame_count       = 0
        self.rostros_detectados = []
        self.cap               = None
        self.frame_actual      = None

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        self._crear_interfaz()
        self._iniciar_camara()

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _crear_interfaz(self):
        pantalla = tk.Frame(self.parent, bg=PALETA["page_bg"])
        pantalla.pack(fill="both", expand=True)

        crear_encabezado(pantalla, self.parent.winfo_toplevel())
        tk.Frame(pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        # Contenedor principal — video ocupa todo
        contenedor = tk.Frame(pantalla, bg="#000000")
        contenedor.pack(fill="both", expand=True)

        # Canvas de video (fondo completo)
        self.label_video = tk.Label(
            contenedor, bg="#000000",
            text="Inicializando cámara...",
            font=("Segoe UI", 14),
            fg=PALETA["topbar_sistema_fg"],
        )
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        # Barra de botones superpuesta al video
        barra = tk.Frame(contenedor, bg=PALETA["central_fondo"])
        barra.place(x=10, y=10, relwidth=0.98)

        estilo = dict(
            font=("Segoe UI", 11, "bold"),
            fg=PALETA["boton_fg"],
            bg=PALETA["boton_bg"],
            activebackground=PALETA["boton_hover"],
            bd=0, padx=15, pady=10,
            cursor="hand2", relief="flat",
        )

        tk.Button(barra, text="← VOLVER",
                  command=self._volver, **estilo).pack(side="left", padx=5)

        tk.Button(barra, text="⚙ CONFIG",
                  command=self._abrir_configuracion, **estilo).pack(side="left", padx=5)

        tk.Button(barra, text="+ REGISTRAR USUARIO",
                  command=lambda: self.app.mostrar_pantalla("registro"), **estilo).pack(side="left", padx=5)

        self.label_estado = tk.Label(
            barra, text="",
            font=("Segoe UI", 9, "bold"),
            bg=PALETA["boton_bg"],
            padx=15, pady=10, relief="flat",
        )
        self.label_estado.pack(side="left", padx=5)

    # ══════════════════════════════════════════
    #  Cámara
    # ══════════════════════════════════════════
    def _iniciar_camara(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label_video.config(text="No se pudo acceder a la cámara", fg="red")
            return
        threading.Thread(target=self._hilo_video, daemon=True).start()

    def _hilo_video(self):
        import time
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # Espejo horizontal
            frame = cv2.flip(frame, 1)

            self.frame_count += 1
            if self.frame_count % 3 == 0:
                self._detectar_rostros(frame)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil   = Image.fromarray(frame_rgb)
            img_pil.thumbnail((1000, 450), Image.Resampling.LANCZOS)

            # Dibujar recuadros sobre la imagen PIL
            if self.rostros_detectados:
                draw = ImageDraw.Draw(img_pil)
                for (x, y, w, h) in self.rostros_detectados:
                    draw.rectangle([x, y, x+w, y+h],
                                   outline=PALETA["topbar_sistema_fg"], width=3)

            imgtk = ImageTk.PhotoImage(image=img_pil)
            try:
                self.label_video.after(0, lambda img=imgtk: self._actualizar_label(img))
            except Exception:
                break
            time.sleep(1 / 25)

    def _detectar_rostros(self, frame):
        try:
            gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5,
                minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
            self.rostros_detectados = list(rostros)
            self.frame_actual       = frame
            n = len(self.rostros_detectados)
            txt   = f"✓ {n} rostro(s) detectado(s)" if n > 0 else "⊘ Ningún rostro detectado"
            color = PALETA["topbar_sistema_fg"] if n > 0 else "#ff6b6b"
            try:
                self.label_estado.after(0,
                    lambda t=txt, c=color: self.label_estado.config(text=t, fg=c))
            except Exception:
                pass
        except Exception as e:
            print(f"[GESTIÓN] Error detección: {e}")

    def _actualizar_label(self, imgtk):
        self.label_video.imgtk = imgtk
        self.label_video.config(image=imgtk, text="")

    # ══════════════════════════════════════════
    #  Acciones
    # ══════════════════════════════════════════
    def _abrir_configuracion(self):
        self.label_estado.config(text="⚙ Configuración (próximamente)",
                                 fg=PALETA["topbar_fecha_fg"])

    def _volver(self):
        self._limpiar()
        self.app.mostrar_pantalla("principal")

    def _limpiar(self):
        self.running = False
        if self.cap:
            self.cap.release()


# ── Punto de entrada ──────────────────────────
def crear_pantalla_gestion(parent, app):
    PantallaGestion(parent, app)