"""
ui/screens/pantalla_registro.py
Pantalla de registro de usuario biométrico.
Cámara a la izquierda con botón de captura, formulario a la derecha.
Se navega desde Gestión: app.mostrar_pantalla("registro")
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import cv2
from PIL import Image, ImageTk, ImageDraw

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from core.database import inicializar_bd, registrar_usuario, obtener_roles

try:
    import face_recognition
    FR_DISPONIBLE = True
except ImportError:
    FR_DISPONIBLE = False


# Roles disponibles
# Roles se cargan desde la BD en tiempo de ejecución
CARRERAS = ["Programación", "Ofimática", "Electrónica", "Contabilidad"]
GRADOS = ["1", "2", "3", "4", "5", "6"]
GRUPOS = ["A", "B", "C"]


class PantallaRegistro:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        self._cap             = None
        self._corriendo       = False
        self._photo           = None
        self._encoding        = None   # np.ndarray con los 128 floats del rostro
        self._photo_capturada = None   # PhotoImage para preview visual

        # Cargar roles desde BD
        inicializar_bd()
        self._roles_bd = obtener_roles()

        self._construir_ui()
        self._abrir_camara()

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent, bg=PALETA["page_bg"])
        self.pantalla.pack(fill="both", expand=True)

        crear_encabezado(self.pantalla, self.parent.winfo_toplevel())
        tk.Frame(self.pantalla, bg=PALETA["topbar_sistema_fg"],
                 height=MEDIDAS["alto_linea_sep"]).pack(fill="x")

        # ── Barra superior ────────────────────
        barra = tk.Frame(self.pantalla, bg=PALETA["page_bg"], pady=8)
        barra.pack(fill="x", padx=20)

        tk.Button(barra, text="← VOLVER",
                  font=("Segoe UI", 11, "bold"),
                  fg=PALETA["topbar_btn_fg"], bg=PALETA["topbar_btn_bg"],
                  activebackground=PALETA["topbar_btn_hover"],
                  bd=0, padx=15, pady=8, cursor="hand2", relief="flat",
                  command=self._volver).pack(side="left")

        tk.Label(barra, text="REGISTRO DE USUARIO",
                 font=("Segoe UI", 14, "bold"),
                 fg=PALETA["topbar_sistema_fg"],
                 bg=PALETA["page_bg"]).pack(side="left", padx=20)

        # ── Cuerpo: cámara izq + formulario der ─
        cuerpo = tk.Frame(self.pantalla, bg=PALETA["page_bg"])
        cuerpo.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, minsize=400, weight=0)
        cuerpo.rowconfigure(0, weight=1)

        self._construir_camara(cuerpo)
        self._construir_formulario(cuerpo)

    # ── Columna izquierda: cámara ─────────────
    def _construir_camara(self, parent):
        col = tk.Frame(parent, bg=PALETA["page_bg"])
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(col, text="Vista de cámara",
                 font=("Segoe UI", 10, "bold"),
                 fg="#888888", bg=PALETA["page_bg"]).pack(anchor="w", pady=(0, 4))

        # Marco del video
        marco = tk.Frame(col, bg=PALETA["central_circulo"], bd=2)
        marco.pack(fill="both", expand=True)

        self.label_video = tk.Label(marco, bg="#1a1a2e",
                                    text="Iniciando cámara...",
                                    font=("Segoe UI", 11),
                                    fg=PALETA["topbar_sistema_fg"])
        self.label_video.pack(fill="both", expand=True)

        # Botón capturar
        self.btn_capturar = tk.Button(
            col, text="📷  CAPTURAR DATOS BIOMÉTRICOS",
            font=("Segoe UI", 12, "bold"),
            fg=PALETA["boton_fg"], bg=PALETA["boton_bg"],
            activebackground=PALETA["boton_hover"],
            bd=0, pady=12, cursor="hand2", relief="flat",
            command=self._capturar_foto,
        )
        self.btn_capturar.pack(fill="x", pady=(8, 0))

        # Preview de la foto capturada
        tk.Label(col, text="Foto capturada",
                 font=("Segoe UI", 10, "bold"),
                 fg="#888888", bg=PALETA["page_bg"]).pack(anchor="w", pady=(10, 4))

        self.canvas_preview = tk.Canvas(col, height=120, bg=PALETA["ghost_bg"],
                                        highlightthickness=1,
                                        highlightbackground=PALETA["topbar_separador"])
        self.canvas_preview.pack(fill="x")

        self.lbl_preview_txt = tk.Label(col,
                                        text="Sin foto — presiona CAPTURAR",
                                        font=("Segoe UI", 9), fg="#aaaaaa",
                                        bg=PALETA["page_bg"])
        self.lbl_preview_txt.pack(pady=2)

    # ── Columna derecha: formulario ───────────
    def _construir_formulario(self, parent):
        col = tk.Frame(parent, bg=PALETA["page_bg"], width=400)
        col.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        col.grid_propagate(False)

        tk.Label(col, text="Datos del usuario",
                 font=("Segoe UI", 10, "bold"),
                 fg="#888888", bg=PALETA["page_bg"]).pack(anchor="w", pady=(0, 8))

        # ── Campos ────────────────────────────
        self._campos = {}

        def campo(etiqueta, key, opciones=None):
            fila = tk.Frame(col, bg=PALETA["page_bg"])
            fila.pack(fill="x", pady=4)
            tk.Label(fila, text=etiqueta,
                     font=("Segoe UI", 10), fg="#444444",
                     bg=PALETA["page_bg"], width=18, anchor="w").pack(side="left")
            if opciones:
                var = tk.StringVar(value=opciones[0])
                w = ttk.Combobox(fila, textvariable=var,
                                 values=opciones, state="readonly",
                                 font=("Segoe UI", 10), width=20)
                w.pack(side="left", fill="x", expand=True)
                self._campos[key] = var
            else:
                var = tk.StringVar()
                w = tk.Entry(fila, textvariable=var,
                             font=("Segoe UI", 10),
                             bg=PALETA["ghost_bg"],
                             relief="flat", bd=0,
                             highlightthickness=1,
                             highlightbackground=PALETA["topbar_separador"],
                             highlightcolor=PALETA["topbar_sistema_fg"])
                w.pack(side="left", fill="x", expand=True, ipady=5)
                self._campos[key] = var

        campo("Código institucional", "codigo")
        campo("Primer nombre",        "primer_nombre")
        campo("Segundo nombre",       "segundo_nombre")
        campo("Apellido paterno",     "apellido_paterno")
        campo("Apellido materno",     "apellido_materno")
        roles_nombres = [r["nombre"] for r in self._roles_bd] or ["Alumno"]
        campo("Rol",                  "rol",     roles_nombres)
        campo("Carrera",              "carrera", CARRERAS)
        campo("Grado",                "grado",   GRADOS)
        campo("Grupo",                "grupo",   GRUPOS)

        # Separador
        tk.Frame(col, bg=PALETA["topbar_separador"], height=1).pack(
            fill="x", pady=12)

        # Mensaje de estado
        self.lbl_msg = tk.Label(col, text="",
                                font=("Segoe UI", 9, "bold"),
                                bg=PALETA["page_bg"], wraplength=320,
                                justify="left")
        self.lbl_msg.pack(anchor="w", pady=(0, 8))

        # Botón guardar
        tk.Button(col, text="✓  GUARDAR REGISTRO",
                  font=("Segoe UI", 12, "bold"),
                  fg=PALETA["boton_fg"], bg=PALETA["boton_bg"],
                  activebackground=PALETA["boton_hover"],
                  bd=0, pady=12, cursor="hand2", relief="flat",
                  command=self._guardar).pack(fill="x")

        # Botón limpiar
        tk.Button(col, text="↺  LIMPIAR",
                  font=("Segoe UI", 10),
                  fg=PALETA["topbar_btn_fg"], bg=PALETA["topbar_btn_bg"],
                  activebackground=PALETA["topbar_btn_hover"],
                  bd=0, pady=8, cursor="hand2", relief="flat",
                  command=self._limpiar_form).pack(fill="x", pady=(6, 0))

    # ══════════════════════════════════════════
    #  Cámara
    # ══════════════════════════════════════════
    def _abrir_camara(self):
        self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self.label_video.config(text="Cámara no disponible", fg="red")
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._corriendo = True
        threading.Thread(target=self._hilo_video, daemon=True).start()

    def _hilo_video(self):
        import time
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while self._corriendo:
            ok, frame = self._cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)

            # Detectar rostro y dibujar recuadro
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = cascade.detectMultiScale(
                gris, scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))

            for (x, y, w, h) in rostros:
                cv2.rectangle(frame, (x, y), (x+w, y+h),
                              (76, 175, 80), 2)

            # Guardar frame actual para captura
            self._frame_actual = frame.copy()

            # Escalar al label
            try:
                lw = self.label_video.winfo_width()
                lh = self.label_video.winfo_height()
                if lw > 10 and lh > 10:
                    resized = cv2.resize(frame, (lw, lh))
                else:
                    resized = frame
                rgb   = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._photo = photo
                self.label_video.after(0, self._pintar_frame)
            except Exception:
                pass

            time.sleep(1 / 25)

    def _pintar_frame(self):
        if self._photo is None:
            return
        self.label_video.imgtk = self._photo
        self.label_video.config(image=self._photo, text="")

    # ══════════════════════════════════════════
    #  Captura de foto
    # ══════════════════════════════════════════
    def _capturar_foto(self):
        if not hasattr(self, "_frame_actual") or self._frame_actual is None:
            self._mostrar_msg("No hay imagen de cámara disponible.", error=True)
            return

        self._mostrar_msg("Procesando rostro...", error=False)
        self.pantalla.update_idletasks()

        frame = self._frame_actual.copy()
        encoding = None

        if FR_DISPONIBLE:
            # Extraer encoding con face_recognition (128 floats)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ubicaciones = face_recognition.face_locations(rgb, model="hog")
            if not ubicaciones:
                self._mostrar_msg("⚠ No se detectó ningún rostro.\nAcércate a la cámara.", error=True)
                return
            encodings = face_recognition.face_encodings(rgb, ubicaciones)
            if not encodings:
                self._mostrar_msg("⚠ No se pudo extraer el encoding.", error=True)
                return
            encoding = encodings[0]
        else:
            # Fallback: detectar con OpenCV (no identifica, solo registra presencia)
            gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            rostros = cascade.detectMultiScale(
                gris, scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
            if len(rostros) == 0:
                self._mostrar_msg("⚠ No se detectó ningún rostro.\nAcércate a la cámara.", error=True)
                return
            # Sin face_recognition no podemos hacer encoding real
            self._mostrar_msg(
                "⚠ face_recognition no instalado.\n"
                "El rostro se detecta pero no se puede identificar.", error=True)
            return

        # Guardar encoding (la foto se desecha)
        self._encoding = encoding

        # Mostrar preview del frame capturado (solo visual, no se guarda)
        self._mostrar_preview_frame(frame)
        self._mostrar_msg("✓ Datos biométricos extraídos correctamente.La foto no será almacenada.", error=False)

    def _mostrar_preview_frame(self, frame):
        """Muestra snapshot visual del momento de captura (no se guarda)."""
        try:
            c = self.canvas_preview
            c.update_idletasks()
            cw = c.winfo_width()  or 300
            ch = c.winfo_height() or 120
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((cw, ch), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._photo_capturada = photo
            c.delete("all")
            c.create_image(cw//2, ch//2, image=photo, anchor="center")
            # Indicador visual de que es solo preview
            c.create_text(cw//2, ch-10, text="Solo vista previa — no se almacena",
                          font=("Segoe UI", 7), fill="#aaaaaa")
            self.lbl_preview_txt.config(text="")
        except Exception:
            pass

    # ══════════════════════════════════════════
    #  Guardar
    # ══════════════════════════════════════════
    def _guardar(self):
        # Validar que se haya capturado foto/encoding
        if self._encoding is None:
            self._mostrar_msg("⚠ Debes capturar el rostro primero.", error=True)
            return

        # Validar campos obligatorios
        for key, nombre in [("codigo","Código institucional"),
                             ("primer_nombre","Primer nombre"),
                             ("apellido_paterno","Apellido paterno")]:
            if not self._campos[key].get().strip():
                self._mostrar_msg(f"⚠ El campo '{nombre}' es obligatorio.", error=True)
                return

        # Obtener id_rol a partir del nombre seleccionado
        rol_nombre = self._campos["rol"].get()
        id_rol = next((r["id_rol"] for r in self._roles_bd
                       if r["nombre"] == rol_nombre), 4)

        datos = {
            "cod_institucional": self._campos["codigo"].get().strip().upper(),
            "id_rol":            id_rol,
            "primer_nombre":     self._campos["primer_nombre"].get().strip(),
            "segundo_nombre":    self._campos["segundo_nombre"].get().strip(),
            "apellido_paterno":  self._campos["apellido_paterno"].get().strip(),
            "apellido_materno":  self._campos["apellido_materno"].get().strip(),
            "carrera":           self._campos["carrera"].get(),
            "grado":             self._campos["grado"].get(),
            "grupo":             self._campos["grupo"].get(),
            "face_encoding":     self._encoding,
        }

        self._mostrar_msg("Guardando...", error=False)
        self.pantalla.update_idletasks()

        exito, msg = registrar_usuario(datos)
        self._mostrar_msg(("✓ " if exito else "✗ ") + msg, error=not exito)

        if exito:
            print(f"[REGISTRO] Usuario {datos['cod_institucional']} guardado con encoding.")
            self.pantalla.after(2000, self._limpiar_todo)

    # ══════════════════════════════════════════
    #  Utilidades
    # ══════════════════════════════════════════
    def _mostrar_msg(self, texto, error=False):
        color = "#c62828" if error else "#2e7d32"
        self.lbl_msg.config(text=texto, fg=color)

    def _limpiar_form(self):
        for key, var in self._campos.items():
            if key == "rol":
                var.set(ROLES[0])
            elif key == "carrera":
                var.set(CARRERAS[0])
            elif key == "grado":
                var.set(GRADOS[0])
            elif key == "grupo":
                var.set(GRUPOS[0])
            else:
                var.set("")
        self._mostrar_msg("")

    def _limpiar_todo(self):
        self._encoding        = None
        self._photo_capturada = None
        self.canvas_preview.delete("all")
        self.lbl_preview_txt.config(text="Sin datos — presiona CAPTURAR")
        self._limpiar_form()

    def _volver(self):
        self._corriendo = False
        if self._cap:
            self._cap.release()
        self.app.mostrar_pantalla("gestion")


def crear_pantalla_registro(parent, app):
    PantallaRegistro(parent, app)