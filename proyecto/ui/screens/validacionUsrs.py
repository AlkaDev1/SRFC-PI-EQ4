"""
ui/screens/validacionUsrs.py
CAMBIOS v3:
  - _ir_a_pantalla_destino() pasa {"id_rol": ...} a mostrar_pantalla()
    para que historial_accesos sepa a qué pantalla regresar al cerrar
  - self._id_rol_reconocido se guarda en _cambiar_estado() al confirmar acceso
  - _limpiar() centraliza el cleanup de cámara/tema/afters
"""

import tkinter as tk
import threading
import queue
import os
import cv2
import numpy as np
import math
import platform
from pathlib import Path
from PIL import Image, ImageTk

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado

try:
    import face_recognition
    FR_DISPONIBLE = True
except ImportError:
    FR_DISPONIBLE = False

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")
_CAM_INDEX    = 1 if _ES_RASPBERRY else 0

FRAMES_CONFIRMAR = 8
FRAMES_PERDER    = 8
SKIP_FRAMES      = 2
MAX_FRAMES_COLA  = 4

_ROL_CONFIG = {
    1: ("ADMINISTRADOR RECONOCIDO", "gestion_real", "gestion_real"),
    2: ("ADMINISTRADOR RECONOCIDO", "gestion_real", "gestion_real"),
    3: ("USUARIO RECONOCIDO",       "historial",    "gestion_real"),
    4: None,
}


class ValidacionUsrs:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        self._p = app.tema.paleta() if hasattr(app, "tema") else _paleta_fallback()

        self._estado            = "escaneando"
        self._bbox              = None
        self._photo             = None
        self._bloqueado         = False
        self._frames_ok         = 0
        self._frames_deny       = 0
        self._frames_perdido    = 0
        self._angulo            = 0
        self._after_anim        = None
        self._after_reset       = None
        self._pantalla_destino  = "gestion_real"
        self._id_rol_reconocido = None   # ← se guarda al confirmar acceso

        self._nombres   = []
        self._encodings = []
        self._id_roles  = []
        self._roles     = []

        self._cap             = None
        self._corriendo       = False
        self._cola_bio        = queue.Queue(maxsize=MAX_FRAMES_COLA)
        self._contador_frames = 0

        self._construir_ui()
        self._iniciar_animacion()
        threading.Thread(target=self._cargar_perfiles, daemon=True).start()
        self._abrir_camara()

        if hasattr(app, "tema"):
            app.tema.registrar(self._aplicar_tema)

    # ══════════════════════════════════════════
    #  Perfiles
    # ══════════════════════════════════════════
    def _cargar_perfiles(self):
        from core.database import inicializar_bd, cargar_todos_encodings
        inicializar_bd()
        perfiles = cargar_todos_encodings()
        for p in perfiles:
            self._encodings.append(p["encoding"])
            self._nombres.append(p["nombre"])
            self._id_roles.append(p["id_rol"])
            self._roles.append(p["rol"])
            print(f"[PERFIL] {p['nombre']} - rol id={p['id_rol']}")
        print(f"[ACCESO] {len(self._encodings)} perfiles listos")

    # ══════════════════════════════════════════
    #  Helpers de navegación
    # ══════════════════════════════════════════
    def _resolver_destino(self, id_rol):
        config = _ROL_CONFIG.get(id_rol)
        return config[1] if config else None

    def _titulo_para_rol(self, id_rol):
        config = _ROL_CONFIG.get(id_rol)
        return config[0] if config else "USUARIO RECONOCIDO"

    def _msg_redireccion(self, id_rol):
        destino = self._resolver_destino(id_rol)
        if destino == "historial":
            return "Redirigiendo al historial de accesos..."
        if destino == "gestion_real":
            return "Redirigiendo al panel de gestión..."
        return "Redirigiendo..."

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        p = self._p
        self.pantalla = tk.Frame(self.parent, bg=p["acceso_fondo"])
        self.pantalla.pack(fill="both", expand=True)
        self.parent.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.ignorar_cierre)
        crear_encabezado(self.pantalla, self.app)
        self.contenedor = tk.Frame(self.pantalla, bg=p["acceso_fondo"])
        self.contenedor.pack(fill="both", expand=True)
        self._construir_capa_escaneo()
        self._construir_capa_ok()
        self._mostrar_capa("escaneo")

    def _crear_rect_redondeado(self, canvas, x1, y1, x2, y2, r, **kwargs):
        puntos = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
                  x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return canvas.create_polygon(puntos, smooth=True, **kwargs)

    def _boton_canvas(self, parent, bg_n, bg_h, icono_attr, icono_path, fallback_txt, comando):
        w, h = 100, 60
        c = tk.Canvas(parent, width=w, height=h, bg=parent["bg"], highlightthickness=0)
        rid = self._crear_rect_redondeado(c, 2, 2, w-2, h-2, 16,
                                          fill=bg_n, outline="#ffffff", width=2)
        if not hasattr(self, icono_attr):
            ruta = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / icono_path
            try:
                setattr(self, icono_attr, tk.PhotoImage(file=str(ruta)) if ruta.exists() else None)
            except Exception:
                setattr(self, icono_attr, None)
        ico = getattr(self, icono_attr)
        cid = c.create_image(w//2, h//2, image=ico) if ico else \
              c.create_text(w//2, h//2, text=fallback_txt, fill="#ffffff",
                            font=("Segoe UI", 20, "bold"))
        c.bind("<Enter>",    lambda e: c.itemconfig(rid, fill=bg_h))
        c.bind("<Leave>",    lambda e: c.itemconfig(rid, fill=bg_n))
        c.bind("<Button-1>", lambda e: comando())
        c.tag_bind(rid, "<Button-1>", lambda e: comando())
        c.tag_bind(cid, "<Button-1>", lambda e: comando())
        return c

    def _construir_capa_escaneo(self):
        p = self._p
        self.capa_escaneo = tk.Frame(self.contenedor, bg=p["acceso_fondo"])
        self.label_video  = tk.Label(self.capa_escaneo, bg=p["acceso_fondo"],
                                     text="Iniciando cámara...",
                                     font=("Segoe UI", 13), fg=p["acceso_hud_fg"])
        self.label_video.place(x=0, y=0, relwidth=1, relheight=1)

        self._boton_canvas(self.capa_escaneo, "#333333", "#444444",
                           "_img_return", "return_icon.png", "←",
                           self._volver
                           ).place(x=14, rely=1.0, anchor="sw", y=-14)

        self.canvas_icono = tk.Canvas(self.capa_escaneo, width=44, height=44,
                                      bg=p["acceso_fondo"], highlightthickness=0)
        self.canvas_icono.place(relx=1.0, rely=0.0, anchor="ne", x=-14, y=14)

        self.btn_login = self._boton_canvas(
            self.capa_escaneo, "#d32f2f", "#b71c1c",
            "_img_password", "password_icon.png", "🔑", self._ir_a_login)

    def _construir_capa_ok(self):
        p     = self._p
        verde = p["acceso_ok_bg"]
        self.capa_ok = tk.Frame(self.contenedor, bg=verde)

        self.canvas_foto = tk.Canvas(self.capa_ok, width=120, height=120,
                                     bg=verde, highlightthickness=0)
        self.canvas_foto.place(relx=0.5, rely=0.22, anchor="center")

        self._badge_ok = tk.Label(self.capa_ok, text="✓",
                                  font=("Segoe UI", 14, "bold"),
                                  fg="#ffffff", bg=verde, padx=4, pady=2)
        self._badge_ok.place(relx=0.5, rely=0.22, anchor="sw", x=44, y=-4)

        self._lbl_titulo_ok = tk.Label(self.capa_ok, text="USUARIO RECONOCIDO",
                                       font=("Segoe UI", 17, "bold"),
                                       fg=p["acceso_ok_texto"], bg=verde)
        self._lbl_titulo_ok.place(relx=0.5, rely=0.52, anchor="center")

        self.lbl_nombre_ok = tk.Label(self.capa_ok, text="",
                                      font=("Segoe UI", 13, "bold"),
                                      fg=p["acceso_ok_texto"], bg=verde)
        self.lbl_nombre_ok.place(relx=0.5, rely=0.63, anchor="center")

        self.lbl_info_ok = tk.Label(self.capa_ok, text="",
                                    font=("Segoe UI", 10),
                                    fg=p["acceso_ok_texto"], bg=verde)
        self.lbl_info_ok.place(relx=0.5, rely=0.73, anchor="center")

        self._boton_canvas(self.capa_ok, "#2d7d32", "#1b5e20",
                           "_img_return", "return_icon.png", "←",
                           self._volver
                           ).place(x=14, rely=1.0, anchor="sw", y=-14)

    def _mostrar_capa(self, capa):
        if getattr(self, "_capa_actual", None) == capa:
            return
        self._capa_actual = capa
        for c in (self.capa_escaneo, self.capa_ok):
            c.place_forget()
        {"escaneo": self.capa_escaneo, "ok": self.capa_ok}[capa].place(
            x=0, y=0, relwidth=1, relheight=1)

    # ══════════════════════════════════════════
    #  Tema
    # ══════════════════════════════════════════
    def _aplicar_tema(self, p):
        self._p = p
        try:
            self.pantalla.configure(bg=p["acceso_fondo"])
            self.contenedor.configure(bg=p["acceso_fondo"])
            self.capa_escaneo.configure(bg=p["acceso_fondo"])
            self.label_video.configure(bg=p["acceso_fondo"], fg=p["acceso_hud_fg"])
            self.canvas_icono.configure(bg=p["acceso_fondo"])
            self.capa_ok.configure(bg=p["acceso_ok_bg"])
            self.canvas_foto.configure(bg=p["acceso_ok_bg"])
            self._badge_ok.configure(bg=p["acceso_ok_bg"])
            self._lbl_titulo_ok.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
            self.lbl_nombre_ok.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
            self.lbl_info_ok.configure(bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"])
        except tk.TclError:
            pass

    # ══════════════════════════════════════════
    #  Cámara
    # ══════════════════════════════════════════
    def _abrir_camara(self):
        self._cap = cv2.VideoCapture(_CAM_INDEX)
        if not self._cap.isOpened():
            otro = 1 - _CAM_INDEX
            self._cap = cv2.VideoCapture(otro)
        if not self._cap.isOpened():
            self._cambiar_estado("sin_camara")
            return
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._corriendo = True
        threading.Thread(target=self._hilo_camara,    daemon=True).start()
        threading.Thread(target=self._hilo_biometria, daemon=True).start()

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
                    self._cola_bio.put_nowait(frame.copy())
                except queue.Full:
                    pass
            if self._estado not in ("acceso_ok",):
                try:
                    cw = self.label_video.winfo_width()
                    ch = self.label_video.winfo_height()
                    if cw < 10 or ch < 10:
                        continue
                    resized = cv2.resize(frame, (cw, ch), interpolation=cv2.INTER_LINEAR)
                    if self._bbox:
                        x1,y1,x2,y2 = self._bbox
                        color = (0,0,255) if self._estado=="acceso_deny" else (80,175,76)
                        cv2.rectangle(resized, (x1,y1), (x2,y2), color, 2)
                    msgs = {
                        "escaneando":  ("VALIDACION DE GESTION",  "ESCANEANDO ROSTRO..."),
                        "detectado":   ("ROSTRO DETECTADO",       "Verificando permisos..."),
                        "sin_rostro":  ("ACERCATE A LA CAMARA",   "No se detecta ningun rostro"),
                        "sin_camara":  ("CAMARA NO DISPONIBLE",   "Verifique la conexion"),
                        "acceso_deny": ("ACCESO DENEGADO",        "No eres administrador..."),
                    }
                    titulo, sub = msgs.get(self._estado, ("ESCANEANDO...", ""))
                    fn = cv2.FONT_HERSHEY_SIMPLEX
                    (wt,_),_ = cv2.getTextSize(titulo, fn, 0.8, 2)
                    (ws,_),_ = cv2.getTextSize(sub,    fn, 0.5, 1)
                    ct = (0,0,255) if self._estado=="acceso_deny" else (255,255,255)
                    for txt,pos,sc,gb,gt,col in [
                        (titulo,((cw-wt)//2,40),0.8,5,2,ct),
                        (sub,   ((cw-ws)//2,70),0.5,3,1,(200,200,200))]:
                        cv2.putText(resized,txt,pos,fn,sc,(0,0,0),gb,cv2.LINE_AA)
                        cv2.putText(resized,txt,pos,fn,sc,col,gt,cv2.LINE_AA)
                    rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    from PIL import Image as PILImage
                    photo = ImageTk.PhotoImage(image=PILImage.fromarray(rgb))
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
            r = self._reconocer(frame)
            try:
                self.label_video.after(0, lambda r=r: self._aplicar_resultado(r))
            except Exception:
                pass

    def _reconocer(self, frame):
        if FR_DISPONIBLE:
            pequeño = cv2.resize(frame, (320,240), interpolation=cv2.INTER_LINEAR)
            rgb     = cv2.cvtColor(pequeño, cv2.COLOR_BGR2RGB)
            ubs     = face_recognition.face_locations(rgb, model="hog",
                                                      number_of_times_to_upsample=0)
            if not ubs:
                return {"hay_rostro": False}
            ub = max(ubs, key=lambda u: (u[2]-u[0])*(u[1]-u[3]))
            if ((ub[2]-ub[0])*(ub[1]-ub[3])) / (pequeño.shape[0]*pequeño.shape[1]) < 0.10:
                return {"hay_rostro": False}
            sy = frame.shape[0]/pequeño.shape[0]
            sx = frame.shape[1]/pequeño.shape[1]
            ub_orig = (int(ub[0]*sy),int(ub[1]*sx),int(ub[2]*sy),int(ub[3]*sx))
            if not self._encodings:
                return {"hay_rostro":True,"reconocido":False,"confianza":0.0,
                        "ubicacion":ub_orig,"nombre":"","id_rol":None,"rol":None}
            encs = face_recognition.face_encodings(rgb, [ub], num_jitters=1)
            if not encs:
                return {"hay_rostro":True,"reconocido":False,"confianza":0.0,
                        "ubicacion":ub_orig,"nombre":"","id_rol":None,"rol":None}
            dists = face_recognition.face_distance(self._encodings, encs[0])
            idx   = int(np.argmin(dists))
            dist  = float(dists[idx])
            conf  = round(max(0.0, 1.0-dist), 3)
            if dist <= 0.50:
                return {"hay_rostro":True,"reconocido":True,"confianza":conf,
                        "ubicacion":ub_orig,"nombre":self._nombres[idx],
                        "id_rol":self._id_roles[idx],"rol":self._roles[idx]}
            return {"hay_rostro":True,"reconocido":False,"confianza":conf,
                    "ubicacion":ub_orig,"nombre":"","id_rol":None,"rol":None}
        else:
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
            rostros = cascade.detectMultiScale(gris,1.3,5,minSize=(80,80))
            if len(rostros)==0:
                return {"hay_rostro":False}
            x,y,w,h = max(rostros, key=lambda r:r[2]*r[3])
            if (w*h)/(frame.shape[0]*frame.shape[1]) < 0.10:
                return {"hay_rostro":False}
            return {"hay_rostro":True,"reconocido":False,"confianza":0.3,
                    "ubicacion":(y,x+w,y+h,x),"nombre":"","id_rol":None,"rol":None}

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
            top,right,bottom,left = r["ubicacion"]
            cw = self.label_video.winfo_width()
            ch = self.label_video.winfo_height()
            sx,sy = cw/640.0, ch/480.0
            self._bbox = (int(left*sx),int(top*sy),int(right*sx),int(bottom*sy))
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
            self._frames_deny = 0
            self._frames_ok  += 1
            self._cambiar_estado("detectado")
            if self._frames_ok >= FRAMES_CONFIRMAR:
                self._frames_ok = 0
                self._bloqueado = True
                self._cambiar_estado("acceso_ok",
                                     nombre=r.get("nombre",""),
                                     id_rol=r.get("id_rol"),
                                     rol=r.get("rol"))
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
        p = self._p
        self.capa_ok.configure(bg=p["acceso_ok_bg"])
        self.canvas_foto.configure(bg=p["acceso_ok_bg"])
        self._badge_ok.configure(bg=p["acceso_ok_bg"], text="✓")
        self._lbl_titulo_ok.configure(bg=p["acceso_ok_bg"], text="USUARIO RECONOCIDO")
        self._cambiar_estado("escaneando")

    def _cambiar_estado(self, estado, nombre="", id_rol=None, rol=None):
        if self._estado == estado and estado not in ("acceso_ok","acceso_deny"):
            return
        self._estado = estado
        p = self._p

        if estado == "acceso_ok":
            self._mostrar_capa("ok")
            if id_rol == 4 or _ROL_CONFIG.get(id_rol) is None:
                self.capa_ok.configure(bg="#d32f2f")
                self.canvas_foto.configure(bg="#d32f2f")
                self._badge_ok.configure(bg="#d32f2f", text="✗")
                self._lbl_titulo_ok.configure(bg="#d32f2f",
                                              text="USUARIO NO AUTORIZADO", fg="#ffffff")
                self.lbl_nombre_ok.configure(bg="#d32f2f", text="ACCESO DENEGADO")
                self.lbl_info_ok.configure(bg="#d32f2f", text="Solo personal autorizado")
                self.pantalla.after(2000, self._resetear)
                return

            # ── Guardar id_rol para pasarlo como datos ────────────────────────
            self._id_rol_reconocido = id_rol
            self._pantalla_destino  = self._resolver_destino(id_rol)

            self._lbl_titulo_ok.configure(
                bg=p["acceso_ok_bg"], fg=p["acceso_ok_texto"],
                text=self._titulo_para_rol(id_rol))
            self.lbl_nombre_ok.configure(text=nombre or "Usuario")
            self.lbl_info_ok.configure(text=self._msg_redireccion(id_rol))

            c = self.canvas_foto
            c.delete("all")
            c.create_oval(5,5,115,115, fill="#ffffff", outline="#c8f0c8", width=3)
            c.create_text(60,60, text="👤", font=("Segoe UI",40), fill=p["acceso_ok_bg"])

            self.pantalla.after(1500, self._ir_a_pantalla_destino)

        elif estado == "acceso_deny":
            self._mostrar_capa("escaneo")
            if hasattr(self, "btn_login"):
                self.btn_login.place(relx=1.0, rely=1.0, anchor="se", x=-14, y=-14)
        else:
            self._mostrar_capa("escaneo")
            if hasattr(self, "btn_login"):
                self.btn_login.place_forget()

    # ══════════════════════════════════════════
    #  Navegación
    # ══════════════════════════════════════════
    def _limpiar(self):
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

    def _ir_a_pantalla_destino(self):
        destino = getattr(self, "_pantalla_destino", "gestion_real")
        id_rol  = getattr(self, "_id_rol_reconocido", None)
        self._limpiar()
        # Pasar id_rol como datos → historial_accesos lo usa en _cerrar()
        self.app.mostrar_pantalla(destino, {"id_rol": id_rol})

    def _ir_a_login(self):
        self._limpiar()
        self.app.mostrar_pantalla("login")

    def _volver(self):
        self._limpiar()
        self.parent.winfo_toplevel().protocol("WM_DELETE_WINDOW",
            self.parent.winfo_toplevel().destroy)
        self.app.mostrar_pantalla("principal")

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
        if self._estado in ("escaneando","sin_rostro","sin_camara","acceso_deny"):
            c.create_oval(cx-r,cy-r,cx+r,cy+r, outline="#555555", width=grosor)
            col = "#ff0000" if self._estado=="acceso_deny" else p["acceso_barra_ok"]
            c.create_arc(cx-r,cy-r,cx+r,cy+r, start=self._angulo, extent=240,
                         style="arc", outline=col, width=grosor)
            for ang in (self._angulo, self._angulo+240):
                import math
                rad = math.radians(ang)
                xp,yp = cx+r*math.cos(rad), cy-r*math.sin(rad)
                cr = grosor/2.0
                c.create_oval(xp-cr,yp-cr,xp+cr,yp+cr, fill=col, outline="")
        elif self._estado == "detectado":
            col = p["acceso_barra_ok"]
            c.create_oval(cx-r,cy-r,cx+r,cy+r, outline=col, width=grosor, fill="#2d4a2d")
            c.create_oval(cx-5,cy-5,cx+5,cy+5, fill=col, outline="")

    # ══════════════════════════════════════════
    #  Limpieza forzada
    # ══════════════════════════════════════════
    def ignorar_cierre(self):
        self._limpiar()
        self.parent.winfo_toplevel().destroy()
        os._exit(0)


def _paleta_fallback():
    return {
        "acceso_fondo":     "#000000",
        "acceso_ok_bg":     "#43A047",
        "acceso_ok_texto":  "#ffffff",
        "acceso_deny_texto":"#f44336",
        "acceso_hud_fg":    "#ffffff",
        "acceso_barra_ok":  "#4CAF50",
    }


def crear_pantalla_gestion(parent, app):
    ValidacionUsrs(parent, app)