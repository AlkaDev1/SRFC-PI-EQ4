"""
ui/screens/pantalla_login.py

SOPORTE DE TEMA OSCURO:
  - Fondo claro:  fondo2.jpeg
  - Fondo oscuro: fondo_login_oscuro.jpeg
  - Tarjeta claro:  blanco (#ffffff)
  - Tarjeta oscuro: verde oscuro (#0d2a0d)
  - Campos oscuro:  fondo #1a3a1a, texto blanco
  - Botón INGRESAR oscuro: #2D531A (Dark Moss)
  - Botón ← oscuro: #477023 (Fern Green)
  - Se registra en GestorTema y se desregistra al destruirse

FIX: al cambiar tema en vivo, se fuerza redibujado del fondo con
     event_generate("<Configure>") para que la nueva imagen se aplique.
"""

import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado

# ── Paleta modo claro ─────────────────────────────────────────────────────────
_LC = {
    "fondo":        "assets/img/fondo2.jpeg",
    "card_bg":      "#ffffff",
    "texto":        "#111827",
    "texto_sec":    "#6B7280",
    "verde":        "#22C55E",
    "verde_hover":  "#16A34A",
    "borde":        "#D1D5DB",
    "borde_focus":  "#22C55E",
    "rojo":         "#DC2626",
    "campo_bg":     "#F9FAFB",
    "btn_back_bg":  "#1F5C2E",
    "btn_back_hov": "#174D26",
}

# ── Paleta modo oscuro ────────────────────────────────────────────────────────
_LO = {
    "fondo":        "assets/img/fondo_login_oscuro.jpeg",
    "card_bg":      "#0d2a0d",
    "texto":        "#ffffff",
    "texto_sec":    "#d0f0d0",
    "verde":        "#2D531A",
    "verde_hover":  "#477023",
    "borde":        "#1a3a1a",
    "borde_focus":  "#477023",
    "rojo":         "#f87171",
    "campo_bg":     "#1a3a1a",
    "btn_back_bg":  "#477023",
    "btn_back_hov": "#2D531A",
}

BLANCO = "#ffffff"


class PantallaLogin:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._mostrar_clave = False
        self.canvas_card    = None
        self.canvas_back    = None
        self._bg_img        = None
        self._bg_original   = None
        self._campos_refs   = []

        self._p = _LO if (hasattr(app, "tema") and app.tema.es_oscuro()) else _LC

        self._construir_ui()

        if hasattr(app, "tema"):
            app.tema.registrar(self._aplicar_tema)
        self.pantalla.bind("<Destroy>", self._limpiar_tema)

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent)
        self.pantalla.pack(fill="both", expand=True)

        self.bg_label = tk.Label(self.pantalla)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._cargar_fondo(self._p["fondo"])
        self.bg_label.lower()
        self.pantalla.bind("<Configure>", self._resize_bg)

        crear_encabezado(self.pantalla, self.app)

        centro = tk.Frame(self.pantalla, bg="")
        centro.place(relx=0.5, rely=0.55, anchor="center")
        self._tarjeta_login(centro)
        self._construir_boton_volver()

    def _cargar_fondo(self, ruta: str):
        try:
            self._bg_original = Image.open(ruta)
        except Exception:
            self._bg_original = None

    def _resize_bg(self, event):
        """Redibuja el fondo cuando cambia el tamaño O cuando se llama manualmente."""
        try:
            if event.width < 10 or event.height < 10:
                return
            if self._bg_original is None:
                return
            img = self._bg_original.resize((event.width, event.height), Image.LANCZOS)
            self._bg_img = ImageTk.PhotoImage(img)
            self.bg_label.config(image=self._bg_img)

            # Sincronizar color de fondo del canvas con el pixel central de la imagen
            cx = event.width  // 2
            cy = event.height // 2
            r, g, b = img.getpixel((cx, cy))
            color = f"#{r:02x}{g:02x}{b:02x}"

            if self.canvas_card and self.canvas_card.winfo_exists():
                self.canvas_card.config(bg=color)
            if self.canvas_back and self.canvas_back.winfo_exists():
                self.canvas_back.config(bg=color)
        except Exception:
            pass

    # ── Tarjeta de login ──────────────────────────────────────────────────────
    def _tarjeta_login(self, parent):
        p     = self._p
        RADIO = 20

        self.canvas_card = tk.Canvas(parent, highlightthickness=0, bd=0, bg="#8DC98D")
        self.canvas_card.pack()

        card = tk.Frame(self.canvas_card, bg=p["card_bg"], bd=0)

        self._avatar(card)

        self._lbl_instruccion = tk.Label(
            card,
            text="Indique su número de trabajador\ny su clave de acceso.",
            font=("Segoe UI", 9),
            fg=p["texto_sec"], bg=p["card_bg"], justify="center")
        self._lbl_instruccion.pack(pady=(8, 20))

        self._campo_con_icono(card, "Número de trabajador", "entry_usuario", False)
        self._spacer = tk.Frame(card, height=10, bg=p["card_bg"])
        self._spacer.pack()
        self._campo_con_icono(card, "Contraseña", "entry_clave", True)
        self._spacer2 = tk.Frame(card, height=6, bg=p["card_bg"])
        self._spacer2.pack()

        # Botón INGRESAR
        ANCHO_BTN, ALTO_BTN, RADIO_BTN = 240, 40, 10
        self._cv_btn = tk.Canvas(card, width=ANCHO_BTN, height=ALTO_BTN,
                                  bg=p["card_bg"], highlightthickness=0, cursor="hand2")
        self._cv_btn.pack(pady=(14, 4), padx=4)

        def _dibujar_btn(color):
            self._cv_btn.delete("all")
            self._rect_redondeado(self._cv_btn, 0, 0, ANCHO_BTN, ALTO_BTN, RADIO_BTN, color)
            self._cv_btn.create_text(ANCHO_BTN // 2, ALTO_BTN // 2,
                                      text="INGRESAR",
                                      font=("Segoe UI", 10, "bold"),
                                      fill=BLANCO, anchor="center")

        self._dibujar_btn_login = _dibujar_btn
        _dibujar_btn(p["verde"])
        self._cv_btn.bind("<Button-1>", lambda e: self._login())
        self._cv_btn.bind("<Enter>",    lambda e: _dibujar_btn(self._p["verde_hover"]))
        self._cv_btn.bind("<Leave>",    lambda e: _dibujar_btn(self._p["verde"]))

        self.lbl_error = tk.Label(card, text="", fg=p["rojo"],
                                   bg=p["card_bg"], font=("Segoe UI", 9))
        self.lbl_error.pack(pady=(2, 0))

        card.update_idletasks()
        card_w = card.winfo_reqwidth() + 60
        card_h = card.winfo_reqheight() + 48

        self.canvas_card.config(width=card_w, height=card_h)
        self._rect_redondeado(self.canvas_card, 0, 0, card_w, card_h, RADIO, p["card_bg"])
        self.canvas_card.create_window(card_w // 2, card_h // 2, window=card, anchor="center")

        self._card_frame = card
        self._card_w     = card_w
        self._card_h     = card_h
        self._card_radio = RADIO
        self._btn_ancho  = ANCHO_BTN
        self._btn_alto   = ALTO_BTN
        self._btn_radio  = RADIO_BTN

    # ── Botón volver ──────────────────────────────────────────────────────────
    def _crear_rect_redondeado(self, canvas, x1, y1, x2, y2, r, **kwargs):
        """Crea un rectángulo redondeado usando puntos suaves."""
        puntos = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                  x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return canvas.create_polygon(puntos, smooth=True, **kwargs)

    def _construir_boton_volver(self):
        """Crea el botón de regresar idéntico a pantalla_acceso."""
        p = self._p
        BG_NORMAL = "#333333"
        BG_HOVER = "#444444"
        
        w, h = 60, 40
        self.canvas_back = tk.Canvas(self.pantalla, width=w, height=h,
                                      bg=BG_NORMAL, highlightthickness=0, cursor="hand2")
        self.canvas_back.place(x=14, rely=1.0, anchor="sw", y=-14)
        
        rect_id = self._crear_rect_redondeado(
            self.canvas_back, 2, 2, w-2, h-2, 8,
            fill=BG_NORMAL, outline="#ffffff", width=2)

        if not hasattr(self, '_img_return'):
            ruta = Path(__file__).resolve().parent.parent.parent / "assets" / "img" / "return_icon.png"
            try:
                self._img_return = tk.PhotoImage(file=str(ruta)) if ruta.exists() else None
            except Exception:
                self._img_return = None

        if self._img_return:
            content_id = self.canvas_back.create_image(w//2, h//2, image=self._img_return)
        else:
            content_id = self.canvas_back.create_text(w//2, h//2, text="←",
                                                      fill="#ffffff", font=("Segoe UI", 16, "bold"))

        self.canvas_back.bind("<Enter>",    lambda e: self.canvas_back.itemconfig(rect_id, fill=BG_HOVER))
        self.canvas_back.bind("<Leave>",    lambda e: self.canvas_back.itemconfig(rect_id, fill=BG_NORMAL))
        self.canvas_back.bind("<Button-1>", lambda e: self._volver())
        self.canvas_back.tag_bind(rect_id,    "<Button-1>", lambda e: self._volver())
        self.canvas_back.tag_bind(content_id, "<Button-1>", lambda e: self._volver())

    def _volver(self):
        """Regresa a la pantalla principal."""
        self._limpiar_tema()
        self.app.mostrar_pantalla("principal")

    # ══════════════════════════════════════════
    #  SOPORTE DE TEMA
    # ══════════════════════════════════════════
    def _aplicar_tema(self, paleta_nueva: dict):
        """Cambia fondo, tarjeta, campos y botones al nuevo tema."""
        self._p = _LO if self.app.tema.es_oscuro() else _LC
        p = self._p

        try:
            # ── 1. Cambiar imagen de fondo y forzar redibujado ────────────────
            self._cargar_fondo(p["fondo"])
            # Disparar _resize_bg manualmente con las dimensiones actuales
            w = self.pantalla.winfo_width()
            h = self.pantalla.winfo_height()
            if w > 10 and h > 10 and self.pantalla.winfo_exists():
                try:
                    self.pantalla.event_generate("<Configure>", width=w, height=h)
                except tk.TclError:
                    pass

            # ── 2. Tarjeta ────────────────────────────────────────────────────
            if self.canvas_card and self.canvas_card.winfo_exists():
                self.canvas_card.delete("all")
                self._rect_redondeado(self.canvas_card, 0, 0,
                                      self._card_w, self._card_h,
                                      self._card_radio, p["card_bg"])
                self.canvas_card.create_window(self._card_w // 2, self._card_h // 2,
                                               window=self._card_frame, anchor="center")
            if self._card_frame.winfo_exists():
                self._card_frame.configure(bg=p["card_bg"])
                # Actualizar fondo del avatar
            if hasattr(self, "_avatar_lbl") and self._avatar_lbl.winfo_exists():
                self._avatar_lbl.configure(bg=p["card_bg"])

            # Spacers internos de la tarjeta
            for w_frame in self._card_frame.winfo_children():
                try:
                    if isinstance(w_frame, tk.Frame):
                        w_frame.configure(bg=p["card_bg"])
                except tk.TclError:
                    pass

            # ── 3. Textos ─────────────────────────────────────────────────────
            if self._lbl_instruccion.winfo_exists():
                self._lbl_instruccion.configure(fg=p["texto_sec"], bg=p["card_bg"])
            if self.lbl_error.winfo_exists():
                self.lbl_error.configure(fg=p["rojo"], bg=p["card_bg"])

            # ── 4. Campos de entrada ──────────────────────────────────────────
            for wrapper, entry, icono_lbl, es_pass in self._campos_refs:
                try:
                    wrapper.configure(bg=p["campo_bg"], highlightbackground=p["borde"])
                    entry.configure(bg=p["campo_bg"], fg=p["texto"],
                                    insertbackground=p["texto"])
                    icono_lbl.configure(bg=p["campo_bg"], fg=p["texto_sec"])
                    if es_pass and hasattr(self, "_ojo_lbl") and self._ojo_lbl.winfo_exists():
                        self._ojo_lbl.configure(bg=p["campo_bg"])
                except tk.TclError:
                    pass

            # ── 5. Botón INGRESAR ─────────────────────────────────────────────
            if self._cv_btn.winfo_exists():
                self._cv_btn.configure(bg=p["card_bg"])
                self._dibujar_btn_login(p["verde"])

        except tk.TclError:
            pass

    def _limpiar_tema(self, event=None):
        if hasattr(self.app, "tema"):
            self.app.tema.desregistrar(self._aplicar_tema)

    # ══════════════════════════════════════════
    #  HELPERS UI
    # ══════════════════════════════════════════
    def _rect_redondeado(self, canvas, x1, y1, x2, y2, radio, color):
        r = radio
        canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90,  fill=color, outline=color)
        canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=90,  extent=-90, fill=color, outline=color)
        canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  fill=color, outline=color)
        canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  fill=color, outline=color)
        canvas.create_rectangle(x1+r, y1,   x2-r, y2,     fill=color, outline=color)
        canvas.create_rectangle(x1,   y1+r, x2,   y2-r,   fill=color, outline=color)

    def _avatar(self, parent):
        p = self._p
        try:
            img = Image.open("assets/img/iconloginverde.png")
            img = img.resize((64, 64), Image.LANCZOS)
            self._avatar_img = ImageTk.PhotoImage(img)
            self._avatar_lbl = tk.Label(parent, image=self._avatar_img, bg=p["card_bg"])
            self._avatar_lbl.pack(pady=(0, 4))
        except Exception:
            SIZE = 64
            c = tk.Canvas(parent, width=SIZE, height=SIZE,
                          bg=p["card_bg"], highlightthickness=0)
            c.pack(pady=(0, 4))
            c.create_oval(2,  2,  SIZE-2, SIZE-2, outline=p["borde"],    width=1.5, fill=p["card_bg"])
            c.create_oval(22, 12, 42,     30,     outline=p["texto_sec"], width=1.5, fill=p["card_bg"])
            c.create_arc(12,  34, 52,     60,     start=0, extent=180,
                         style="arc", outline=p["texto_sec"], width=1.5)

    def _campo_con_icono(self, parent, placeholder, attr, es_password):
        p     = self._p
        ANCHO = 330
        ALTO  = 36

        wrapper = tk.Frame(parent, bg=p["campo_bg"],
                           highlightthickness=1, highlightbackground=p["borde"],
                           width=ANCHO, height=ALTO)
        wrapper.pack(fill="x", padx=4)
        wrapper.pack_propagate(False)

        icono_lbl = tk.Label(wrapper, bg=p["campo_bg"], fg=p["texto_sec"],
                             font=("Segoe UI", 11))
        icono_lbl.pack(side="left", padx=(8, 4))

        if es_password:
            try:
                img_lock = Image.open("assets/img/lock_icon_dk.png").resize((18, 18), Image.LANCZOS)
                self._img_lock = ImageTk.PhotoImage(img_lock)
                icono_lbl.config(image=self._img_lock)
            except Exception:
                icono_lbl.config(text="🔒")
        else:
            try:
                img_person = Image.open("assets/img/person_icon.png").resize((18, 18), Image.LANCZOS)
                self._img_person = ImageTk.PhotoImage(img_person)
                icono_lbl.config(image=self._img_person)
            except Exception:
                icono_lbl.config(text="👤")

        entry = tk.Entry(wrapper, font=("Segoe UI", 10), bd=0, relief="flat",
                         bg=p["campo_bg"], fg=p["texto_sec"],
                         insertbackground=p["texto"],
                         show="")
        entry.pack(side="left", fill="both", expand=True, ipady=6)
        entry.insert(0, placeholder)

        if es_password:
            try:
                img_vis     = Image.open("assets/img/visibility_icon.png").resize((18, 18), Image.LANCZOS)
                img_vis_off = Image.open("assets/img/visibility_off_icon.png").resize((18, 18), Image.LANCZOS)
                self._img_ojo_on  = ImageTk.PhotoImage(img_vis)
                self._img_ojo_off = ImageTk.PhotoImage(img_vis_off)
                ojo = tk.Label(wrapper, image=self._img_ojo_on,
                               bg=p["campo_bg"], cursor="hand2")
            except Exception:
                ojo = tk.Label(wrapper, text="👁", bg=p["campo_bg"],
                               fg=p["texto_sec"], font=("Segoe UI", 11), cursor="hand2")
            ojo.pack(side="right", padx=(4, 8))
            ojo.bind("<Button-1>", lambda e: self._toggle_clave(entry, ojo))
            self._ojo_lbl = ojo

        def focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg=self._p["texto"])
                if es_password and not self._mostrar_clave:
                    entry.config(show="●")
            wrapper.config(highlightbackground=self._p["borde_focus"], bg=self._p["campo_bg"])
            icono_lbl.config(bg=self._p["campo_bg"])
            entry.config(bg=self._p["campo_bg"])
            if es_password and hasattr(self, "_ojo_lbl"):
                self._ojo_lbl.config(bg=self._p["campo_bg"])

        def focus_out(e):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(fg=self._p["texto_sec"], show="")
            else:
                if es_password and not self._mostrar_clave:
                    entry.config(show="●")
            wrapper.config(highlightbackground=self._p["borde"], bg=self._p["campo_bg"])
            icono_lbl.config(bg=self._p["campo_bg"])
            entry.config(bg=self._p["campo_bg"])
            if es_password and hasattr(self, "_ojo_lbl"):
                self._ojo_lbl.config(bg=self._p["campo_bg"])

        entry.bind("<FocusIn>",  focus_in)
        entry.bind("<FocusOut>", focus_out)

        self._campos_refs.append((wrapper, entry, icono_lbl, es_password))
        setattr(self, attr, entry)

    def _toggle_clave(self, entry, ojo_lbl):
        placeholder = "Contraseña"
        if entry.get() == placeholder:
            return
        self._mostrar_clave = not self._mostrar_clave
        entry.config(show="" if self._mostrar_clave else "●")
        if hasattr(self, "_img_ojo_on") and hasattr(self, "_img_ojo_off"):
            ojo_lbl.config(image=self._img_ojo_off if self._mostrar_clave else self._img_ojo_on)
        else:
            ojo_lbl.config(text="🙈" if self._mostrar_clave else "👁")

    # ══════════════════════════════════════════
    #  LOGIN
    # ══════════════════════════════════════════
    def _login(self):
        u = self.entry_usuario.get().strip()
        c = self.entry_clave.get()
        
        if not u or not c or u == "Número de trabajador" or c == "Contraseña":
            self.lbl_error.config(text="⚠ Ingrese todos los campos")
            return

        import hashlib
        from core.database import obtener_conexion

        # Generar hash de la contraseña ingresada
        password_hash = hashlib.sha256(c.encode("utf-8")).hexdigest()

        con = obtener_conexion()
        if not con:
            self.lbl_error.config(text="⚠ Error de conexión a la base de datos")
            return

        try:
            # Buscar el usuario en la BD
            # cod_institucional es la llave primaria / "Número de trabajador"
            row = con.execute(
                "SELECT password_hash, estado FROM Usuarios WHERE cod_institucional = ?",
                (u,)
            ).fetchone()

            if row:
                if row["estado"] != 1:
                    self.lbl_error.config(text="⚠ El usuario está inactivo")
                elif row["password_hash"] == password_hash:
                    # Usuario y contraseña correctos
                    self.lbl_error.config(text="")
                    self.app.mostrar_pantalla("gestion_real")
                else:
                    self.lbl_error.config(text="⚠ Credenciales incorrectas")
            else:
                self.lbl_error.config(text="⚠ Credenciales incorrectas")
        except Exception as e:
            print(f"[Login Error]: {e}")
            self.lbl_error.config(text="⚠ Error interno al validar")
        finally:
            con.close()


def crear_pantalla_login(parent, app):
    PantallaLogin(parent, app)