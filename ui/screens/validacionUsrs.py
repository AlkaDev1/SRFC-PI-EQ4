"""
ui/screens/validacionUsrs.py
Pantalla de Gestión — diseño coherente con pantalla_acceso.
Video grande, botones superpuestos arriba, HUD inferior con info.
"""

import tkinter as tk
from tkinter import ttk
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

        self.running            = True
        self.frame_count        = 0
        self.rostros_detectados = []
        self.cap                = None
        self.frame_actual       = None

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

        # Contenedor — video ocupa todo
        contenedor = tk.Frame(pantalla, bg=PALETA["central_fondo"])
        contenedor.pack(fill="both", expand=True)

        # Video fondo completo
        self.label_video = tk.Label(
            contenedor, bg=PALETA["central_fondo"],
            text="Inicializando cámara...",
            font=("Segoe UI", 14),
            fg=PALETA["topbar_sistema_fg"],
        )
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        # ── Botones superpuestos arriba izquierda ──
        estilo_btn = dict(
            font=("Segoe UI", 10, "bold"),
            fg=PALETA["topbar_btn_fg"],
            bg=PALETA["topbar_btn_bg"],
            activebackground=PALETA["topbar_btn_hover"],
            activeforeground=PALETA["topbar_btn_fg"],
            bd=0, padx=14, pady=8,
            cursor="hand2", relief="flat",
        )

        tk.Button(contenedor, text="← VOLVER",
                  command=self._volver,
                  **estilo_btn).place(x=16, y=16)

        tk.Button(contenedor, text="+ REGISTRAR",
                  command=lambda: self.app.mostrar_pantalla("registro"),
                  font=("Segoe UI", 10, "bold"),
                  fg=PALETA["boton_fg"],
                  bg=PALETA["boton_bg"],
                  activebackground=PALETA["boton_hover"],
                  activeforeground=PALETA["boton_fg"],
                  bd=0, padx=14, pady=8,
                  cursor="hand2", relief="flat",
                  ).place(x=130, y=16)

        # ── HUD inferior — mismo estilo que pantalla_acceso ──
        hud = tk.Frame(contenedor, bg=PALETA["page_bg"])
        hud.place(relx=0.5, rely=1.0, anchor="s", relwidth=1.0)

        tk.Frame(hud, bg=PALETA["topbar_sistema_fg"], height=3).pack(fill="x")

        contenido = tk.Frame(hud, bg=PALETA["page_bg"])
        contenido.pack(pady=12, padx=24)

        # Ícono de cámara (canvas estático decorativo)
        self.canvas_icono = tk.Canvas(contenido, width=40, height=40,
                                      bg=PALETA["page_bg"], highlightthickness=0)
        self.canvas_icono.pack(side="left", padx=(0, 14))
        self._dibujar_icono_camara()

        # Bloque estado
        bloque = tk.Frame(contenido, bg=PALETA["page_bg"])
        bloque.pack(side="left", padx=(0, 24))

        self.lbl_subtitulo = tk.Label(bloque, text="GESTIÓN BIOMÉTRICA",
                                      font=("Segoe UI", 8), fg="#aaaaaa",
                                      bg=PALETA["page_bg"], anchor="w")
        self.lbl_subtitulo.pack(anchor="w")

        self.label_estado = tk.Label(bloque,
                                     text="Iniciando cámara...",
                                     font=("Segoe UI", 13, "bold"),
                                     fg=PALETA["topbar_sistema_fg"],
                                     bg=PALETA["page_bg"], anchor="w")
        self.label_estado.pack(anchor="w")

        # Separador vertical
        tk.Frame(contenido, bg=PALETA["topbar_separador"], width=1).pack(
            side="left", fill="y", padx=(0, 24), pady=4)

        # Bloque contador de rostros
        bloque2 = tk.Frame(contenido, bg=PALETA["page_bg"])
        bloque2.pack(side="left")

        tk.Label(bloque2, text="ROSTROS EN CÁMARA",
                 font=("Segoe UI", 8), fg="#aaaaaa",
                 bg=PALETA["page_bg"], anchor="w").pack(anchor="w")

        self.lbl_contador = tk.Label(bloque2, text="0",
                                     font=("Segoe UI", 22, "bold"),
                                     fg=PALETA["topbar_sistema_fg"],
                                     bg=PALETA["page_bg"], anchor="w")
        self.lbl_contador.pack(anchor="w")



    def _dibujar_icono_camara(self):
        c = self.canvas_icono
        cx, cy = 20, 20
        # Cuerpo cámara
        c.create_rectangle(6, 12, 34, 28, outline=PALETA["topbar_sistema_fg"],
                            width=2, fill=PALETA["ghost_bg"])
        # Lente
        c.create_oval(13, 15, 27, 25, outline=PALETA["topbar_sistema_fg"],
                      width=2, fill=PALETA["topbar_btn_bg"])
        c.create_oval(16, 17, 24, 23, outline="", fill=PALETA["topbar_sistema_fg"])
        # Flash
        c.create_rectangle(28, 10, 33, 14, outline=PALETA["topbar_sistema_fg"],
                            width=1, fill=PALETA["topbar_btn_bg"])

    # ══════════════════════════════════════════
    #  Cámara
    # ══════════════════════════════════════════
    def _iniciar_camara(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label_estado.config(text="Cámara no disponible", fg="#c62828")
            return
        threading.Thread(target=self._hilo_video, daemon=True).start()

    def _hilo_video(self):
        import time
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            self.frame_count += 1
            if self.frame_count % 3 == 0:
                self._detectar_rostros(frame)

            # Escalar al label
            try:
                lw = self.label_video.winfo_width()
                lh = self.label_video.winfo_height()
                if lw > 10 and lh > 10:
                    resized = cv2.resize(frame, (lw, lh))
                else:
                    resized = frame

                # Dibujar recuadros directamente sobre el frame
                for (x, y, w, h) in self.rostros_detectados:
                    # Escalar coordenadas al tamaño del label
                    sx = lw / frame.shape[1]
                    sy = lh / frame.shape[0]
                    x1 = int(x * sx); y1 = int(y * sy)
                    x2 = int((x+w)*sx); y2 = int((y+h)*sy)
                    cv2.rectangle(resized, (x1, y1), (x2, y2),
                                  (58, 140, 63), 2)

                rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self.label_video.imgtk = photo
                self.label_video.after(0, lambda p=photo: self._actualizar_label(p))
            except Exception:
                pass

            time.sleep(1 / 25)

    def _detectar_rostros(self, frame):
        try:
            gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=8,
                minSize=(80, 80), flags=cv2.CASCADE_SCALE_IMAGE)
            self.rostros_detectados = list(rostros)
            self.frame_actual       = frame
            n     = len(self.rostros_detectados)
            txt   = "Rostro detectado" if n == 1 else \
                    f"{n} rostros detectados" if n > 1 else "Buscando rostros..."
            color = PALETA["topbar_sistema_fg"] if n > 0 else "#888888"
            try:
                self.label_estado.after(0,
                    lambda t=txt, c=color, n=n: (
                        self.label_estado.config(text=t, fg=c),
                        self.lbl_contador.config(
                            text=str(n),
                            fg=PALETA["topbar_sistema_fg"] if n > 0 else "#cccccc")
                    ))
            except Exception:
                pass
        except Exception as e:
            print(f"[GESTIÓN] Error detección: {e}")

    def _actualizar_label(self, photo):
        self.label_video.config(image=photo, text="")

    # ══════════════════════════════════════════
    #  Acciones
    # ══════════════════════════════════════════
    def _volver(self):
        self._limpiar()
        self.app.mostrar_pantalla("principal")

    def _limpiar(self):
        self.running = False
        if self.cap:
            self.cap.release()


def crear_pantalla_gestion(parent, app):
    PantallaGestion(parent, app)