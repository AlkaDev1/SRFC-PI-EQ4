"""
ui/screens/pantalla_acceso.py
Diseño según mockup:
  - Escaneando: video full + texto arriba + recuadro verde + botón volver abajo izq
  - Acceso OK:  pantalla verde completa con icono usuario, nombre, hora
  - Acceso DENY: pantalla roja completa con X grande
"""

import tkinter as tk
import threading
import queue
import os
import cv2
import numpy as np
import math 
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


class PantallaAcceso:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

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
        self._cargar_perfiles()

        self._cap       = None
        self._corriendo = False
        self._cola_bio  = queue.Queue(maxsize=2)

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

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg="#000000")
        self.pantalla.pack(fill="both", expand=True)

        ventana_principal = self.parent.winfo_toplevel()
        ventana_principal.protocol("WM_DELETE_WINDOW", self.ignorar_cierre)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        
        self.contenedor = tk.Frame(self.pantalla, bg="#000000")
        self.contenedor.pack(fill="both", expand=True)

        self._construir_capa_escaneo()
        self._construir_capa_ok()
        self._construir_capa_deny()
        self._mostrar_capa("escaneo")

    # Método centralizado para crear rectángulos con bordes curvos
    def _crear_rect_redondeado(self, canvas, x1, y1, x2, y2, r, **kwargs):
        puntos = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return canvas.create_polygon(puntos, smooth=True, **kwargs)

    def _crear_boton_volver(self, parent, bg_normal, bg_hover):
        w, h = 100, 60  
        canvas = tk.Canvas(parent, width=w, height=h, bg=parent["bg"], highlightthickness=0)

        rect_id = self._crear_rect_redondeado(
            canvas, 2, 2, w-2, h-2, 16, 
            fill=bg_normal,
            outline="#ffffff",  # Color del borde (blanco)
            width=2             # Grosor del borde (ajustable)
        )

        if not hasattr(self, '_img_return'):
            ruta_icono = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "return_icon.png"
            if ruta_icono.exists():
                try:
                    self._img_return = tk.PhotoImage(file=str(ruta_icono))
                except Exception as e:
                    print(f"[UI] Error cargando return_icon.png: {e}")
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

    # ── Capa escaneo ─────────────────────────
    def _construir_capa_escaneo(self):
        self.capa_escaneo = tk.Frame(self.contenedor, bg="#000000")

        self.label_video = tk.Label(
            self.capa_escaneo, bg="#000000",
            text="Iniciando cámara...",
            font=("Segoe UI", 13),
            fg=PALETA["topbar_sistema_fg"])
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        top = tk.Frame(self.capa_escaneo, bg="#000000", pady=8)
        top.place(relx=0.5, y=0, anchor="n", relwidth=1.0)

        self.lbl_instruccion = tk.Label(
            top, text="POR FAVOR NO SE MUEVA",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff", bg="#000000")
        self.lbl_instruccion.pack()

        self.lbl_sub = tk.Label(
            top, text="ESCANEANDO ROSTRO...",
            font=("Segoe UI", 10),
            fg=PALETA["topbar_sistema_fg"], bg="#000000")
        self.lbl_sub.pack()

        btn_volver = self._crear_boton_volver(self.capa_escaneo, bg_normal="#333333", bg_hover="#444444")
        btn_volver.place(x=14, rely=1.0, anchor="sw", y=-14)

        # Ahora el bg es igual al del frame (#000000) para que las esquinas se disimulen 
        self.canvas_icono = tk.Canvas(
            self.capa_escaneo, width=44, height=44,
            bg="#000000", highlightthickness=0)
        self.canvas_icono.place(
            relx=1.0, rely=1.0, anchor="se", x=-14, y=-14)

    # ── Capa acceso OK ────────────────────────
    def _construir_capa_ok(self):
        verde = PALETA["central_circulo"]
        self.capa_ok = tk.Frame(self.contenedor, bg=verde)

        self.canvas_foto = tk.Canvas(
            self.capa_ok, width=120, height=120,
            bg=verde, highlightthickness=0)
        self.canvas_foto.place(relx=0.5, rely=0.22, anchor="center")

        badge = tk.Label(self.capa_ok, text="✓",
                         font=("Segoe UI", 14, "bold"),
                         fg="#ffffff", bg=PALETA["central_onda"],
                         padx=4, pady=2, relief="flat")
        badge.place(relx=0.5, rely=0.22, anchor="sw", x=44, y=-4)

        tk.Label(self.capa_ok, text="ACCESO CONCEDIDO",
                 font=("Segoe UI", 17, "bold"),
                 fg="#ffffff", bg=verde).place(
                     relx=0.5, rely=0.52, anchor="center")

        self.lbl_nombre_ok = tk.Label(
            self.capa_ok, text="",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff", bg=verde)
        self.lbl_nombre_ok.place(relx=0.5, rely=0.63, anchor="center")

        self.lbl_info_ok = tk.Label(
            self.capa_ok, text="",
            font=("Segoe UI", 9),
            fg="#c8eec8", bg=verde)
        self.lbl_info_ok.place(relx=0.5, rely=0.73, anchor="center")

        btn_volver = self._crear_boton_volver(self.capa_ok, bg_normal="#2d7d32", bg_hover="#1b5e20")
        btn_volver.place(x=14, rely=1.0, anchor="sw", y=-14)

    # ── Capa acceso DENY ─────────────────────
    def _construir_capa_deny(self):
        rojo = "#c62828"
        self.capa_deny = tk.Frame(self.contenedor, bg=rojo)

        c = tk.Canvas(self.capa_deny, width=130, height=130,
                      bg=rojo, highlightthickness=0)
        c.place(relx=0.5, rely=0.25, anchor="center")
        c.create_oval(4, 4, 126, 126, outline="#ffffff", width=4, fill="")
        c.create_line(36, 36, 94, 94, fill="#ffffff", width=7, capstyle="round")
        c.create_line(94, 36, 36, 94, fill="#ffffff", width=7, capstyle="round")

        tk.Label(self.capa_deny, text="ACCESO DENEGADO",
                 font=("Segoe UI", 17, "bold"),
                 fg="#ffffff", bg=rojo).place(
                     relx=0.5, rely=0.58, anchor="center")

        tk.Label(self.capa_deny, text="Usuario no autorizado",
                 font=("Segoe UI", 11),
                 fg="#ffcdd2", bg=rojo).place(
                     relx=0.5, rely=0.70, anchor="center")

        tk.Label(self.capa_deny,
                 text="Intente de nuevo o contacte a administración",
                 font=("Segoe UI", 9),
                 fg="#ffcdd2", bg=rojo).place(
                     relx=0.5, rely=0.80, anchor="center")

        btn_volver = self._crear_boton_volver(self.capa_deny, bg_normal="#b71c1c", bg_hover="#7f0000")
        btn_volver.place(x=14, rely=1.0, anchor="sw", y=-14)

    def _mostrar_capa(self, capa):
        for c in (self.capa_escaneo, self.capa_ok, self.capa_deny):
            c.place_forget()
        mapa = {"escaneo": self.capa_escaneo,
                "ok":      self.capa_ok,
                "deny":    self.capa_deny}
        mapa[capa].place(x=0, y=0, relwidth=1, relheight=1)

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
        while self._corriendo:
            ok, frame = self._cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            try:
                self._cola_bio.put_nowait(frame.copy())
            except queue.Full:
                pass

            if self._estado not in ("acceso_ok", "acceso_deny"):
                try:
                    cw = self.label_video.winfo_width()
                    ch = self.label_video.winfo_height()
                    if cw < 10 or ch < 10:
                        time.sleep(0.04)
                        continue
                    resized = cv2.resize(frame, (cw, ch))
                    if self._bbox:
                        x1, y1, x2, y2 = self._bbox
                        cv2.rectangle(resized, (x1, y1), (x2, y2),
                                      (76, 175, 80), 2)
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
                self.label_video.after(
                    0, lambda r=resultado: self._aplicar_resultado(r))
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
            rostros = cascade.detectMultiScale(
                gris, scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
            if len(rostros) == 0:
                return {"hay_rostro": False}
            x, y, w, h = max(rostros, key=lambda r: r[2]*r[3])
            return {"hay_rostro": True, "reconocido": False,
                    "confianza": 0.3, "ubicacion": (y, x+w, y+h, x),
                    "nombre": ""}

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
            self._bbox = (int(left*sx), int(top*sy),
                          int(right*sx), int(bottom*sy))
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
                self._after_reset = self.canvas_icono.after(
                    4000, self._resetear)
        else:
            self._frames_ok    = 0
            self._frames_deny += 1
            self._cambiar_estado("detectado")
            if self._frames_deny >= FRAMES_CONFIRMAR:
                self._frames_deny = 0
                self._bloqueado   = True
                self._cambiar_estado("acceso_deny")
                self._after_reset = self.canvas_icono.after(
                    4000, self._resetear)

    def _resetear(self):
        self._bloqueado = False
        self._bbox      = None
        self._cambiar_estado("escaneando")

    # ══════════════════════════════════════════
    #  Cambio de estado
    # ══════════════════════════════════════════
    def _cambiar_estado(self, estado, nombre=""):
        self._estado = estado

        if estado == "acceso_ok":
            self._mostrar_capa("ok")
            hora = datetime.now().strftime("%I:%M %p").lower()
            self.lbl_nombre_ok.config(text=nombre or "Usuario")
            self.lbl_info_ok.config(text=f"Acceso registrado · {hora}")
            c = self.canvas_foto
            c.delete("all")
            c.create_oval(5, 5, 115, 115,
                          fill="#ffffff", outline="#c8f0c8", width=3)
            c.create_text(60, 60, text="👤",
                          font=("Segoe UI", 40),
                          fill=PALETA["central_circulo"])

        elif estado == "acceso_deny":
            self._mostrar_capa("deny")

        else:
            self._mostrar_capa("escaneo")
            msgs = {
                "escaneando": ("POR FAVOR NO SE MUEVA",   "ESCANEANDO ROSTRO..."),
                "detectado":  ("ROSTRO DETECTADO",        "Verificando identidad..."),
                "sin_rostro": ("ACÉRCATE A LA CÁMARA",    "No se detecta ningún rostro"),
                "sin_camara": ("CÁMARA NO DISPONIBLE",    "Verifique la conexión"),
            }
            titulo, sub = msgs.get(estado, ("ESCANEANDO...", ""))
            self.lbl_instruccion.config(text=titulo)
            self.lbl_sub.config(text=sub)

    # ══════════════════════════════════════════
    #  Animación Mejorada
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
        
        # 1. Dibujamos el fondo redondeado (margen de 2px)
        self._crear_rect_redondeado(c, 2, 2, 42, 42, 10, fill="#333333")

        cx, cy, r = 22, 22, 13 # Ajustamos el radio para darle espacio al grosor
        grosor = 4
        
        if self._estado in ("escaneando", "sin_rostro", "sin_camara"):
            # 2. Círculo base gris (pista)
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline="#555555", width=grosor)
            
            # 3. Arco de progreso principal
            color_onda = PALETA.get("central_onda", "#4caf50")
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=self._angulo, extent=240,
                         style="arc", outline=color_onda, width=grosor)
            
            # 4. Puntas redondeadas usando Trigonometría
            rad_start = math.radians(self._angulo)
            rad_end = math.radians(self._angulo + 240)
            
            # (Recordatorio: en Tkinter el eje Y está invertido, por eso es `cy - ...`)
            x_start = cx + r * math.cos(rad_start)
            y_start = cy - r * math.sin(rad_start)
            
            x_end = cx + r * math.cos(rad_end)
            y_end = cy - r * math.sin(rad_end)
            
            cr = grosor / 2.0 # Radio de los circulitos tapa
            c.create_oval(x_start-cr, y_start-cr, x_start+cr, y_start+cr, fill=color_onda, outline="")
            c.create_oval(x_end-cr, y_end-cr, x_end+cr, y_end+cr, fill=color_onda, outline="")

        elif self._estado == "detectado":
            color_onda = PALETA.get("central_onda", "#4caf50")
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                          outline=color_onda, width=grosor,
                          fill="#2d4a2d")
            c.create_oval(cx-5, cy-5, cx+5, cy+5,
                          fill=color_onda, outline="")

    # ══════════════════════════════════════════
    #  Limpieza
    # ══════════════════════════════════════════
    def ignorar_cierre(self):
        pass
        
    def _volver(self):
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


def crear_pantalla_acceso(parent, app):
    PantallaAcceso(parent, app)