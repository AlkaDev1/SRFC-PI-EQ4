"""
ui/screens/validacionUsrs.py
Pantalla de validación biométrica para administradores.
Si el acceso es correcto, redirige a la pantalla de gestión real.

SOPORTE DE TEMA OSCURO:
  - Al construirse, obtiene la paleta activa de app.tema
  - Se registra en GestorTema para recibir cambios automáticos
  - _aplicar_tema(p) repinta: capa_ok, label_video, canvas_icono
  - Al destruirse (_volver / _ir_a_gestion_real), se desregistra del GestorTema
  - La cámara siempre es negra — eso no cambia con el tema
"""

import tkinter as tk
import threading
import queue
import os
import cv2
import numpy as np
import math
import time
from pathlib import Path
from PIL import Image, ImageTk
from datetime import datetime

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado

try:
    import face_recognition
    FR_DISPONIBLE = True
except ImportError:
    FR_DISPONIBLE = False

FRAMES_CONFIRMAR = 8
FRAMES_PERDER    = 8
SKIP_FRAMES      = 2      # Procesar cada 2 frames (más responsive)
MAX_FRAMES_COLA  = 4      # Buffer optimizado


class ValidacionUsrs:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        # ── Obtener paleta inicial del tema activo ────────────────────────────
        self._p = app.tema.paleta() if hasattr(app, "tema") else _paleta_fallback()

        self._estado         = "escaneando"
        self._confianza      = 0.0
        self._bbox           = None
        self._photo          = None
        self._bloqueado      = False
        self._frames_ok      = 0
        self._frames_deny    = 0
        self._frames_perdido = 0
        self._angulo         = 0
        self._after_anim     = None
        self._after_reset    = None

        self._nombres    = []
        self._encodings  = []
        self._cargar_perfiles_lista = []  # Flag para cargar perfiles en background
        
        self._cap       = None
        self._corriendo = False
        self._cola_bio  = queue.Queue(maxsize=MAX_FRAMES_COLA)
        self._contador_frames = 0

        # ── Construir UI PRIMERO (sin bloqueos) ────────────────────────────────
        self._construir_ui()
        self._iniciar_animacion()
        
        # ── Cargar perfiles EN BACKGROUND (no bloquea UI) ────────────────────────
        threading.Thread(target=self._cargar_perfiles, daemon=True).start()
        
        # ── Abrir cámara AHORA (ella sola optimiza su inicio) ────────────────────
        self._abrir_camara()

        # ── Registrar en GestorTema ──────────────────────────────────────────────
        if hasattr(app, "tema"):
            app.tema.registrar(self._aplicar_tema)

    # ══════════════════════════════════════════
    #  Perfiles — carga asincrónica
    # ══════════════════════════════════════════
    def _cargar_perfiles(self):
        """Carga perfiles en background sin bloquear UI."""
        if not FR_DISPONIBLE:
            return
        base    = os.path.dirname(os.path.dirname(
                  os.path.dirname(os.path.abspath(__file__))))
        carpeta = os.path.join(base, "data", "profiles")
        os.makedirs(carpeta, exist_ok=True)
        
        perfiles_temp = []
        for archivo in os.listdir(carpeta):
            if not archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ruta   = os.path.join(carpeta, archivo)
            nombre = os.path.splitext(archivo)[0].replace("_", " ").title()
            try:
                img  = face_recognition.load_image_file(ruta)
                encs = face_recognition.face_encodings(img)
                if encs:
                    perfiles_temp.append((encs[0], nombre))
                    print(f"[PERFIL] Cargado: {nombre}")
            except Exception as e:
                print(f"[PERFIL] Error {archivo}: {e}")
        
        # ── Actualizar listas (thread-safe) ──────────────────────────────────
        self._encodings = [p[0] for p in perfiles_temp]
        self._nombres   = [p[1] for p in perfiles_temp]
        print(f"[ACCESO] {len(self._encodings)} perfiles listos para reconocimiento")

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["acceso_fondo"])
        self.pantalla.pack(fill="both", expand=True)

        ventana_principal = self.parent.winfo_toplevel()
        ventana_principal.protocol("WM_DELETE_WINDOW", self.ignorar_cierre)

        crear_encabezado(self.pantalla, self.app)

        self.contenedor = tk.Frame(self.pantalla, bg=p["acceso_fondo"])
        self.contenedor.pack(fill="both", expand=True)

        self._construir_capa_escaneo()
        self._construir_capa_ok()
        self._mostrar_capa("escaneo")

    def _crear_rect_redondeado(self, canvas, x1, y1, x2, y2, r, **kwargs):
        puntos = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return canvas.create_polygon(puntos, smooth=True, **kwargs)

    def _crear_boton_volver(self, parent, bg_normal, bg_hover):
        w, h = 100, 60
        canvas = tk.Canvas(parent, width=w, height=h, bg=parent["bg"], highlightthickness=0)

        rect_id = self._crear_rect_redondeado(
            canvas, 2, 2, w-2, h-2, 16,
            fill=bg_normal, outline="#ffffff", width=2)

        if not hasattr(self, '_img_return'):
            ruta_icono = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "return_icon.png"
            if ruta_icono.exists():
                try:
                    self._img_return = tk.PhotoImage(file=str(ruta_icono))
                except Exception:
                    self._img_return = None
            else:
                self._img_return = None

        if self._img_return:
            content_id = canvas.create_image(w//2, h//2, image=self._img_return)
        else:
            content_id = canvas.create_text(w//2, h//2, text="←", fill="#ffffff", font=("Segoe UI", 20, "bold"))

        def on_enter(e): canvas.itemconfig(rect_id, fill=bg_hover)
        def on_leave(e): canvas.itemconfig(rect_id, fill=bg_normal)
        def on_click(e): self._volver()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        canvas.tag_bind(rect_id, "<Button-1>", on_click)
        canvas.tag_bind(content_id, "<Button-1>", on_click)
        return canvas

    def _crear_boton_login_manual(self, parent, bg_normal, bg_hover):
        w, h = 100, 60
        canvas = tk.Canvas(parent, width=w, height=h, bg=parent["bg"], highlightthickness=0)

        rect_id = self._crear_rect_redondeado(
            canvas, 2, 2, w-2, h-2, 16,
            fill=bg_normal, outline="#ffffff", width=2)

        if not hasattr(self, '_img_password'):
            ruta_icono = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "password_icon.png"
            if ruta_icono.exists():
                try:
                    self._img_password = tk.PhotoImage(file=str(ruta_icono))
                except Exception:
                    self._img_password = None
            else:
                self._img_password = None

        if self._img_password:
            content_id = canvas.create_image(w//2, h//2, image=self._img_password)
        else:
            content_id = canvas.create_text(w//2, h//2, text="🔑", fill="#ffffff", font=("Segoe UI", 20))

        def on_enter(e): canvas.itemconfig(rect_id, fill=bg_hover)
        def on_leave(e): canvas.itemconfig(rect_id, fill=bg_normal)
        def on_click(e): self._ir_a_login()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        canvas.tag_bind(rect_id, "<Button-1>", on_click)
        canvas.tag_bind(content_id, "<Button-1>", on_click)
        return canvas

    # ── Capa escaneo ──────────────────────────────────────────────────────────
    def _construir_capa_escaneo(self):
        p = self._p
        self.capa_escaneo = tk.Frame(self.contenedor, bg=p["acceso_fondo"])

        self.label_video = tk.Label(
            self.capa_escaneo, bg=p["acceso_fondo"],
            text="Iniciando cámara...",
            font=("Segoe UI", 13),
            fg=p["acceso_hud_fg"])
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        btn_volver = self._crear_boton_volver(self.capa_escaneo, bg_normal="#333333", bg_hover="#444444")
        btn_volver.place(x=14, rely=1.0, anchor="sw", y=-14)

        self.canvas_icono = tk.Canvas(
            self.capa_escaneo, width=44, height=44,
            bg=p["acceso_fondo"], highlightthickness=0)
        self.canvas_icono.place(relx=1.0, rely=0.0, anchor="ne", x=-14, y=14)

        self.btn_login = self._crear_boton_login_manual(
            self.capa_escaneo, bg_normal="#d32f2f", bg_hover="#b71c1c")

    # ── Capa acceso OK ────────────────────────────────────────────────────────
    def _construir_capa_ok(self):
        p     = self._p
        verde = p["acceso_ok_bg"]
        self.capa_ok = tk.Frame(self.contenedor, bg=verde)

        self.canvas_foto = tk.Canvas(
            self.capa_ok, width=120, height=120,
            bg=verde, highlightthickness=0)
        self.canvas_foto.place(relx=0.5, rely=0.22, anchor="center")

        self._badge_ok = tk.Label(self.capa_ok, text="✓",
                         font=("Segoe UI", 14, "bold"),
                         fg="#ffffff", bg=verde,
                         padx=4, pady=2, relief="flat")
        self._badge_ok.place(relx=0.5, rely=0.22, anchor="sw", x=44, y=-4)

        self._lbl_admin_reconocido = tk.Label(
            self.capa_ok, text="ADMINISTRADOR RECONOCIDO",
            font=("Segoe UI", 17, "bold"),
            fg=p["acceso_ok_texto"], bg=verde)
        self._lbl_admin_reconocido.place(relx=0.5, rely=0.52, anchor="center")

        self.lbl_nombre_ok = tk.Label(
            self.capa_ok, text="",
            font=("Segoe UI", 13, "bold"),
            fg=p["acceso_ok_texto"], bg=verde)
        self.lbl_nombre_ok.place(relx=0.5, rely=0.63, anchor="center")

        self.lbl_info_ok = tk.Label(
            self.capa_ok, text="",
            font=("Segoe UI", 10),
            fg=p["acceso_ok_texto"], bg=verde)
        self.lbl_info_ok.place(relx=0.5, rely=0.73, anchor="center")

        btn_volver = self._crear_boton_volver(self.capa_ok, bg_normal="#2d7d32", bg_hover="#1b5e20")
        btn_volver.place(x=14, rely=1.0, anchor="sw", y=-14)

    def _mostrar_capa(self, capa):
        if getattr(self, "_capa_actual", None) == capa:
            return
        self._capa_actual = capa
        for c in (self.capa_escaneo, self.capa_ok):
            c.place_forget()
        mapa = {"escaneo": self.capa_escaneo, "ok": self.capa_ok}
        mapa[capa].place(x=0, y=0, relwidth=1, relheight=1)

    # ══════════════════════════════════════════
    #  Soporte de tema
    # ══════════════════════════════════════════
    def _aplicar_tema(self, p: dict):
        """Recibe la nueva paleta y repinta los widgets de esta pantalla.

        Llamado automáticamente por GestorTema cuando el usuario presiona 🌙/☀️.
        La cámara siempre es negra — solo repintamos los marcos y la capa OK.
        """
        self._p = p
        try:
            self.pantalla.configure(bg=p["acceso_fondo"])
            self.contenedor.configure(bg=p["acceso_fondo"])

            # Capa escaneo
            self.capa_escaneo.configure(bg=p["acceso_fondo"])
            self.label_video.configure(bg=p["acceso_fondo"], fg=p["acceso_hud_fg"])
            self.canvas_icono.configure(bg=p["acceso_fondo"])

            # Capa OK
            self.capa_ok.configure(bg=p["acceso_ok_bg"])
            self.canvas_foto.configure(bg=p["acceso_ok_bg"])
            self._badge_ok.configure(bg=p["acceso_ok_bg"])
            self._lbl_admin_reconocido.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
            self.lbl_nombre_ok.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
            self.lbl_info_ok.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
        except tk.TclError:
            pass

    # ══════════════════════════════════════════
    #  Cámara — inicio rápido
    # ══════════════════════════════════════════
    def _abrir_camara(self):
        self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._cambiar_estado("sin_camara")
            return
        
        # ── Configuración MÍNIMA para inicio rápido ──────────────────────────────
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)        # Latencia baja
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # No setear FPS, resolution ni otras props innecesarias
        
        self._corriendo = True
        threading.Thread(target=self._hilo_camara,    daemon=True, name="cam_capture").start()
        threading.Thread(target=self._hilo_biometria, daemon=True, name="bio_recognition").start()

    def _dibujar_texto_con_borde(self, img, texto, pos, fuente, escala, grosor_borde, grosor_texto, color_texto):
        cv2.putText(img, texto, pos, fuente, escala, (0, 0, 0), grosor_borde, cv2.LINE_AA)
        cv2.putText(img, texto, pos, fuente, escala, color_texto, grosor_texto, cv2.LINE_AA)

    def _hilo_camara(self):
        self._contador_frames = 0
        while self._corriendo:
            ok, frame = self._cap.read()
            if not ok:
                break
            
            frame = cv2.flip(frame, 1)
            self._contador_frames += 1
            
            # ── Enviar a biometría cada N frames ─────────────────────────────────
            if self._contador_frames % SKIP_FRAMES == 0:
                try:
                    self._cola_bio.put_nowait(frame.copy())
                except queue.Full:
                    pass

            # ── Renderizar en pantalla si no está en acceso_ok ─────────────────────
            if self._estado not in ("acceso_ok",):
                try:
                    cw = self.label_video.winfo_width()
                    ch = self.label_video.winfo_height()
                    if cw < 10 or ch < 10:
                        continue

                    # ── Resize rápido ────────────────────────────────────────────────
                    resized = cv2.resize(frame, (cw, ch), interpolation=cv2.INTER_LINEAR)

                    if self._bbox:
                        x1, y1, x2, y2 = self._bbox
                        color_bbox = (0, 0, 255) if self._estado == "acceso_deny" else (80, 175, 76)
                        cv2.rectangle(resized, (x1, y1), (x2, y2), color_bbox, 2)

                    msgs = {
                        "escaneando":  ("VALIDACION DE GESTION",   "ESCANEANDO ROSTRO..."),
                        "detectado":   ("ROSTRO DETECTADO",        "Verificando permisos..."),
                        "sin_rostro":  ("ACERCATE A LA CAMARA",    "No se detecta ningun rostro"),
                        "sin_camara":  ("CAMARA NO DISPONIBLE",    "Verifique la conexion"),
                        "acceso_deny": ("ACCESO DENEGADO",         "No eres administrador..."),
                    }
                    titulo, sub = msgs.get(self._estado, ("ESCANEANDO...", ""))

                    fuente = cv2.FONT_HERSHEY_SIMPLEX
                    (w_titulo, _), _ = cv2.getTextSize(titulo, fuente, 0.8, 2)
                    (w_sub, _), _    = cv2.getTextSize(sub,    fuente, 0.5, 1)

                    pos_titulo = ((cw - w_titulo) // 2, 40)
                    pos_sub    = ((cw - w_sub)    // 2, 70)

                    color_titulo = (0, 0, 255) if self._estado == "acceso_deny" else (255, 255, 255)

                    self._dibujar_texto_con_borde(
                        img=resized, texto=titulo, pos=pos_titulo,
                        fuente=fuente, escala=0.8, grosor_borde=5, grosor_texto=2, color_texto=color_titulo)
                    self._dibujar_texto_con_borde(
                        img=resized, texto=sub, pos=pos_sub,
                        fuente=fuente, escala=0.5, grosor_borde=3, grosor_texto=1, color_texto=(200, 200, 200))

                    rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                    self._photo = photo
                    self.label_video.after(0, self._pintar_frame)
                except Exception:
                    pass

    def _hilo_biometria(self):
        while self._corriendo:
            try:
                frame = self._cola_bio.get(timeout=1.0)
            except queue.Empty:
                continue
            
            resultado = self._reconocer(frame)
            try:
                self.label_video.after(0, lambda r=resultado: self._aplicar_resultado(r))
            except Exception:
                pass

    def _reconocer(self, frame):
        if FR_DISPONIBLE:
            # ── Procesamiento a baja resolución (más rápido) ──────────────────────
            pequeño = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_LINEAR)
            rgb     = cv2.cvtColor(pequeño, cv2.COLOR_BGR2RGB)
            ubs     = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=0)
            if not ubs:
                return {"hay_rostro": False}
            ub = max(ubs, key=lambda u: (u[2]-u[0]) * (u[1]-u[3]))
            alto_rostro  = ub[2] - ub[0]
            ancho_rostro = ub[1] - ub[3]
            area_rostro  = alto_rostro * ancho_rostro
            alto_frame, ancho_frame, _ = pequeño.shape
            area_frame = alto_frame * ancho_frame
            if (area_rostro / area_frame) < 0.10:
                return {"hay_rostro": False}
            
            # ── Escalar ubicación de vuelta a original ───────────────────────────
            scale_y = frame.shape[0] / pequeño.shape[0]
            scale_x = frame.shape[1] / pequeño.shape[1]
            ub_orig = (int(ub[0]*scale_y), int(ub[1]*scale_x), int(ub[2]*scale_y), int(ub[3]*scale_x))
            
            if not self._encodings:
                return {"hay_rostro": True, "reconocido": False,
                        "confianza": 0.0, "ubicacion": ub_orig, "nombre": ""}
            
            # ── Encoding rápido (num_jitters=1) ──────────────────────────────────
            encs = face_recognition.face_encodings(rgb, [ub], num_jitters=1)
            if not encs:
                return {"hay_rostro": True, "reconocido": False,
                        "confianza": 0.0, "ubicacion": ub_orig, "nombre": ""}
            
            dists = face_recognition.face_distance(self._encodings, encs[0])
            idx   = int(np.argmin(dists))
            dist  = float(dists[idx])
            conf  = round(max(0.0, 1.0 - dist), 3)
            if dist <= 0.50:
                return {"hay_rostro": True, "reconocido": True,
                        "confianza": conf, "ubicacion": ub_orig, "nombre": self._nombres[idx]}
            return {"hay_rostro": True, "reconocido": False,
                    "confianza": conf, "ubicacion": ub_orig, "nombre": ""}
        else:
            # ── Fallback con Cascade (sin face_recognition) ───────────────────────
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            rostros = cascade.detectMultiScale(gris, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))
            if len(rostros) == 0:
                return {"hay_rostro": False}
            x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
            area_rostro_hc = w * h
            area_frame_hc  = frame.shape[0] * frame.shape[1]
            if (area_rostro_hc / area_frame_hc) < 0.10:
                return {"hay_rostro": False}
            return {"hay_rostro": True, "reconocido": False,
                    "confianza": 0.3, "ubicacion": (y, x+w, y+h, x), "nombre": ""}

    def _pintar_frame(self):
        if self._photo is None:
            return
        self.label_video.imgtk = self._photo
        self.label_video.config(image=self._photo, text="")

    # ══════════════════════════════════════════
    #  Resultado biométrico
    # ══════════════════════════════════════════
    def _aplicar_resultado(self, r):
        if self._bloqueado:
            return
        if r.get("hay_rostro") and r.get("ubicacion"):
            top, right, bottom, left = r["ubicacion"]
            cw = self.label_video.winfo_width()
            ch = self.label_video.winfo_height()
            sx, sy = cw / 640.0, ch / 480.0
            self._bbox = (int(left*sx), int(top*sy), int(right*sx), int(bottom*sy))
            self._frames_perdido = 0
        else:
            self._frames_perdido += 1
            if self._frames_perdido >= FRAMES_PERDER:
                self._bbox = None

        if not r.get("hay_rostro"):
            self._frames_ok = self._frames_deny = 0
            if self._frames_perdido >= FRAMES_PERDER:
                self._cambiar_estado("sin_rostro")
            return

        if r.get("reconocido"):
            self._frames_deny  = 0
            self._frames_ok   += 1
            self._cambiar_estado("detectado")
            if self._frames_ok >= FRAMES_CONFIRMAR:
                self._frames_ok = 0
                self._bloqueado = True
                self._cambiar_estado("acceso_ok", nombre=r.get("nombre", ""))
        else:
            self._frames_ok    = 0
            self._frames_deny += 1
            self._cambiar_estado("detectado")
            if self._frames_deny >= FRAMES_CONFIRMAR:
                self._frames_deny = 0
                self._bloqueado   = True
                self._cambiar_estado("acceso_deny")
                self._after_reset = self.canvas_icono.after(5000, self._resetear)

    def _resetear(self):
        self._bloqueado = False
        self._bbox      = None
        self._cambiar_estado("escaneando")

    # ══════════════════════════════════════════
    #  Cambio de estado
    # ══════════════════════════════════════════
    def _cambiar_estado(self, estado, nombre=""):
        if self._estado == estado and estado not in ("acceso_ok", "acceso_deny"):
            return
        self._estado = estado
        p = self._p

        if estado == "acceso_ok":
            self._mostrar_capa("ok")
            self.lbl_nombre_ok.config(text=nombre or "Administrador")
            self.lbl_info_ok.config(text="Redirigiendo al panel de gestión...")
            c = self.canvas_foto
            c.delete("all")
            c.create_oval(5, 5, 115, 115, fill="#ffffff", outline="#c8f0c8", width=3)
            c.create_text(60, 60, text="👤", font=("Segoe UI", 40), fill=p["acceso_ok_bg"])
            self.pantalla.after(1500, self._ir_a_gestion_real)

        elif estado == "acceso_deny":
            self._mostrar_capa("escaneo")
            if hasattr(self, 'btn_login'):
                self.btn_login.place(relx=1.0, rely=1.0, anchor="se", x=-14, y=-14)
        else:
            self._mostrar_capa("escaneo")
            if hasattr(self, 'btn_login'):
                self.btn_login.place_forget()

    # ══════════════════════════════════════════
    #  Navegación
    # ══════════════════════════════════════════
    def _ir_a_gestion_real(self):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._aplicar_tema)
        self._corriendo = False
        if self._cap:
            self._cap.release()
        for aid in (self._after_anim, self._after_reset):
            if aid:
                try:
                    self.canvas_icono.after_cancel(aid)
                except Exception:
                    pass
        self.app.mostrar_pantalla("gestion_real")

    def _ir_a_login(self):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._aplicar_tema)
        self._corriendo = False
        if self._cap:
            self._cap.release()
        for aid in (self._after_anim, self._after_reset):
            if aid:
                try:
                    self.canvas_icono.after_cancel(aid)
                except Exception:
                    pass
        self.app.mostrar_pantalla("login")

    # ══════════════════════════════════════════
    #  Animación
    # ══════════════════════════════════════════
    def _iniciar_animacion(self):
        self._animar()

    def _animar(self):
        self._angulo = (self._angulo + 4) % 360
        self._dibujar_icono()
        try:
            self._after_anim = self.canvas_icono.after(33, self._animar)
        except Exception:
            pass

    def _dibujar_icono(self):
        c = self.canvas_icono
        c.delete("all")
        p = self._p

        self._crear_rect_redondeado(c, 2, 2, 42, 42, 10, fill="#333333")
        cx, cy, r = 22, 22, 13
        grosor = 4

        if self._estado in ("escaneando", "sin_rostro", "sin_camara", "acceso_deny"):
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#555555", width=grosor)
            color_onda = "#ff0000" if self._estado == "acceso_deny" else p["acceso_barra_ok"]
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=self._angulo, extent=240,
                         style="arc", outline=color_onda, width=grosor)
            rad_start = math.radians(self._angulo)
            rad_end   = math.radians(self._angulo + 240)
            x_start = cx + r * math.cos(rad_start)
            y_start = cy - r * math.sin(rad_start)
            x_end   = cx + r * math.cos(rad_end)
            y_end   = cy - r * math.sin(rad_end)
            cr = grosor / 2.0
            c.create_oval(x_start-cr, y_start-cr, x_start+cr, y_start+cr, fill=color_onda, outline="")
            c.create_oval(x_end-cr,   y_end-cr,   x_end+cr,   y_end+cr,   fill=color_onda, outline="")

        elif self._estado == "detectado":
            color_onda = p["acceso_barra_ok"]
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color_onda, width=grosor, fill="#2d4a2d")
            c.create_oval(cx-5, cy-5, cx+5, cy+5, fill=color_onda, outline="")

    # ══════════════════════════════════════════
    #  Limpieza
    # ══════════════════════════════════════════
    def ignorar_cierre(self):
        print("Cerrando forzosamente desde validación biométrica...")
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._aplicar_tema)
        self._corriendo = False
        if self._cap:
            self._cap.release()
        ventana_principal = self.parent.winfo_toplevel()
        ventana_principal.destroy()
        os._exit(0)

    def _volver(self):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._aplicar_tema)
        self._corriendo = False
        if self._cap:
            self._cap.release()
        for aid in (self._after_anim, self._after_reset):
            if aid:
                try:
                    self.canvas_icono.after_cancel(aid)
                except Exception:
                    pass
        ventana_principal = self.parent.winfo_toplevel()
        ventana_principal.protocol("WM_DELETE_WINDOW", ventana_principal.destroy)
        self.app.mostrar_pantalla("principal")


# ──────────────────────────────────────────────────────────────────────────────
#  FALLBACK — colores originales si no hay GestorTema
# ──────────────────────────────────────────────────────────────────────────────
def _paleta_fallback() -> dict:
    return {
        "acceso_fondo":      "#000000",
        "acceso_ok_bg":      "#43A047",
        "acceso_ok_texto":   "#ffffff",
        "acceso_deny_texto": "#f44336",
        "acceso_hud_fg":     "#ffffff",
        "acceso_barra_ok":   "#4CAF50",
    }


def crear_pantalla_gestion(parent, app):
    """Función de entrada que main.py espera encontrar."""
    ValidacionUsrs(parent, app)