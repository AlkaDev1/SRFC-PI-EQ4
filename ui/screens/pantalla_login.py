import tkinter as tk
from PIL import Image, ImageTk

from ui.styles import PALETA, FUENTES, MEDIDAS
from ui.components.barra_superior import crear_encabezado
from ui.screens.pantalla_principal import _rr

# ── Colores ─────────────────────
BLANCO      = "#FFFFFF"
TEXTO       = "#111827"
TEXTO_SEC   = "#6B7280"
VERDE       = "#22C55E"
VERDE_HOVER = "#16A34A"
BORDE       = "#D1D5DB"
BORDE_FOCUS = "#22C55E"
ROJO        = "#DC2626"
FONDO_CAMPO = "#F9FAFB"


class PantallaLogin:

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app
        self._mostrar_clave = False
        self.canvas_card    = None
        self.canvas_back = None
        self._construir_ui()

    def _construir_ui(self):
        self.pantalla = tk.Frame(self.parent)
        self.pantalla.pack(fill="both", expand=True)

        self.bg_label = tk.Label(self.pantalla)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_original = Image.open("assets/img/fondo2.jpeg")
        self.bg_label.lower()
        self.pantalla.bind("<Configure>", self._resize_bg)

        crear_encabezado(self.pantalla, self.app.root)

        centro = tk.Frame(self.pantalla, bg="")
        centro.place(relx=0.5, rely=0.55, anchor="center")
        self._tarjeta_login(centro)


        # Botón regresar redondeado
        ANCHO_BACK = 60
        ALTO_BACK  = 40
        RADIO_BACK = 10

        cv_back = tk.Canvas(
            self.pantalla,
            width=ANCHO_BACK, height=ALTO_BACK,
            highlightthickness=0, cursor="hand2",
        )
        cv_back.place(relx=0.03, rely=0.88)

        def _dibujar_back(color):
            cv_back.delete("all")
            _rr(cv_back, 0, 0, ANCHO_BACK, ALTO_BACK, RADIO_BACK, color)
            cv_back.create_text(
                ANCHO_BACK // 2, ALTO_BACK // 2,
                text="←",
                font=("Segoe UI", 16, "bold"),
                fill=BLANCO,
                anchor="center",
            )

        _dibujar_back("#1F5C2E")
        
        cv_back.bind("<Button-1>", lambda e: self.app.mostrar_pantalla("principal"))
        cv_back.bind("<Enter>",    lambda e: _dibujar_back("#174D26"))
        cv_back.bind("<Leave>",    lambda e: _dibujar_back("#1F5C2E"))
        self.canvas_back = cv_back

    def _resize_bg(self, event):
        try:
            if event.width < 10 or event.height < 10:
                return
            img = self.bg_original.resize(
                (event.width, event.height), Image.LANCZOS
            )
            self.bg_img = ImageTk.PhotoImage(img)
            self.bg_label.config(image=self.bg_img)

            cx = event.width  // 2
            cy = event.height // 2
            r, g, b = img.getpixel((cx, cy))
            color = f"#{r:02x}{g:02x}{b:02x}"

            if self.canvas_card is not None:
                self.canvas_card.config(bg=color)

            if self.canvas_back is not None:    
                self.canvas_back.config(bg=color)

        except Exception:
            pass

    def _tarjeta_login(self, parent):
        RADIO = 20

        self.canvas_card = tk.Canvas(
            parent, highlightthickness=0, bd=0, bg="#8DC98D",
        )
        self.canvas_card.pack()

        card = tk.Frame(self.canvas_card, bg=BLANCO, bd=0)

        self._avatar(card)

        tk.Label(
            card,
            text="Indique su número de trabajador\ny su clave de acceso.",
            font=("Segoe UI", 9),
            fg=TEXTO_SEC,
            bg=BLANCO,
            justify="center",
        ).pack(pady=(8, 20))

        self._campo_con_icono(card, "Número de trabajador", "entry_usuario", False)
        tk.Frame(card, height=10, bg=BLANCO).pack()
        self._campo_con_icono(card, "Contraseña", "entry_clave", True)
        tk.Frame(card, height=6, bg=BLANCO).pack()

        ANCHO_BTN = 240
        ALTO_BTN  = 40
        RADIO_BTN = 10

        cv_btn = tk.Canvas(
            card, width=ANCHO_BTN, height=ALTO_BTN,
            bg=BLANCO, highlightthickness=0, cursor="hand2",
        )
        cv_btn.pack(pady=(14, 4), padx=4)

        def _dibujar_btn(color):
            cv_btn.delete("all")
            _rr(cv_btn, 0, 0, ANCHO_BTN, ALTO_BTN, RADIO_BTN, color)
            cv_btn.create_text(
                ANCHO_BTN // 2, ALTO_BTN // 2,
                text="INGRESAR",
                font=("Segoe UI", 10, "bold"),
                fill=BLANCO, anchor="center",
            )

        _dibujar_btn(VERDE)
        cv_btn.bind("<Button-1>", lambda e: self._login())
        cv_btn.bind("<Enter>",    lambda e: _dibujar_btn(VERDE_HOVER))
        cv_btn.bind("<Leave>",    lambda e: _dibujar_btn(VERDE))

        self.lbl_error = tk.Label(
            card, text="", fg=ROJO, bg=BLANCO, font=("Segoe UI", 9)
        )
        self.lbl_error.pack(pady=(2, 0))

        # Calcular tamaño y dibujar tarjeta redondeada
        card.update_idletasks()
        card_w = card.winfo_reqwidth() + 60
        card_h = card.winfo_reqheight() + 48

        self.canvas_card.config(width=card_w, height=card_h)
        self._rect_redondeado(self.canvas_card, 0, 0, card_w, card_h, RADIO, BLANCO)
        self.canvas_card.create_window(
            card_w // 2, card_h // 2, window=card, anchor="center",
        )

    def _rect_redondeado(self, canvas, x1, y1, x2, y2, radio, color):
        r = radio
        canvas.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90,  fill=color, outline=color)
        canvas.create_arc(x2-2*r,  y1,      x2,     y1+2*r, start=90,  extent=-90, fill=color, outline=color)
        canvas.create_arc(x1,      y2-2*r,  x1+2*r, y2,     start=180, extent=90,  fill=color, outline=color)
        canvas.create_arc(x2-2*r,  y2-2*r,  x2,     y2,     start=270, extent=90,  fill=color, outline=color)
        canvas.create_rectangle(x1+r, y1,   x2-r, y2,       fill=color, outline=color)
        canvas.create_rectangle(x1,   y1+r, x2,   y2-r,     fill=color, outline=color)

    def _avatar(self, parent):
        try:
            from PIL import Image, ImageTk
            img = Image.open("assets/img/iconloginverde.png")
            img = img.resize((64, 64), Image.LANCZOS)
            self._avatar_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(parent, image=self._avatar_img, bg=BLANCO)
            lbl.pack(pady=(0, 4))
        except Exception:
            # fallback al avatar dibujado si no encuentra la imagen
            SIZE = 64
            c = tk.Canvas(parent, width=SIZE, height=SIZE,
                          bg=BLANCO, highlightthickness=0)
            c.pack(pady=(0, 4))
            c.create_oval(2,  2,  SIZE-2, SIZE-2, outline=BORDE,    width=1.5, fill=BLANCO)
            c.create_oval(22, 12, 42,     30,     outline=TEXTO_SEC, width=1.5, fill=BLANCO)
            c.create_arc(12,  34, 52,     60,     start=0, extent=180,
                         style="arc", outline=TEXTO_SEC, width=1.5)

    def _campo_con_icono(self, parent, placeholder, attr, es_password):
        ANCHO = 330
        ALTO  = 36

        wrapper = tk.Frame(
            parent,
            bg=FONDO_CAMPO,
            highlightthickness=1,
            highlightbackground=BORDE,
            width=ANCHO,
            height=ALTO,
        )
        wrapper.pack(fill="x", padx=4)
        wrapper.pack_propagate(False)

        icono_lbl = tk.Label(wrapper, bg=FONDO_CAMPO, fg=TEXTO_SEC,
                             font=("Segoe UI", 11))
        icono_lbl.pack(side="left", padx=(8, 4))

        if es_password:
            # --- MODIFICADO: Cargar lock_icon_dk.png en lugar del emoji ---
            try:
                ruta_icono_lock = "assets/img/lock_icon_dk.png"
                img_icono_lock = Image.open(ruta_icono_lock).resize((18, 18), Image.LANCZOS)
                # Guardamos la referencia en self para que no se borre de la memoria
                self._img_lock = ImageTk.PhotoImage(img_icono_lock)
                icono_lbl.config(image=self._img_lock)
            except Exception as e:
                print(f"[UI] Error cargando lock_icon_dk.png: {e}")
                icono_lbl.config(text="🔒") # Plan B si no encuentra la imagen
        else:
            # --- MODIFICADO: Cargar person_icon.png en lugar del emoji ---
            try:
                ruta_icono = "assets/img/person_icon.png"
                img_icono = Image.open(ruta_icono).resize((18, 18), Image.LANCZOS)
                # Guardamos la referencia en self para que no se borre de la memoria
                self._img_person = ImageTk.PhotoImage(img_icono)
                icono_lbl.config(image=self._img_person)
            except Exception as e:
                print(f"[UI] Error cargando person_icon.png: {e}")
                icono_lbl.config(text="👤") # Plan B si no encuentra la imagen

        entry = tk.Entry(
            wrapper,
            font=("Segoe UI", 10),
            bd=0, relief="flat",
            bg=FONDO_CAMPO,
            fg=TEXTO_SEC,
            insertbackground=TEXTO,
            show="●" if es_password else "",
        )
        entry.pack(side="left", fill="both", expand=True, ipady=6)
        entry.insert(0, placeholder)

        if es_password:
            # --- MODIFICADO: Cargar iconos de visibilidad ---
            try:
                img_vis = Image.open("assets/img/visibility_icon.png").resize((18, 18), Image.LANCZOS)
                img_vis_off = Image.open("assets/img/visibility_off_icon.png").resize((18, 18), Image.LANCZOS)
                
                # Guardamos las referencias en self
                self._img_ojo_on = ImageTk.PhotoImage(img_vis)
                self._img_ojo_off = ImageTk.PhotoImage(img_vis_off)
                
                ojo = tk.Label(wrapper, image=self._img_ojo_on, bg=FONDO_CAMPO, cursor="hand2")
            except Exception as e:
                print(f"[UI] Error cargando iconos de visibilidad: {e}")
                # Plan B si no encuentra la imagen
                ojo = tk.Label(wrapper, text="👁", bg=FONDO_CAMPO, fg=TEXTO_SEC, font=("Segoe UI", 11), cursor="hand2")
                
            ojo.pack(side="right", padx=(4, 8))
            ojo.bind("<Button-1>", lambda e: self._toggle_clave(entry, ojo))

        def focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg=TEXTO)
            wrapper.config(highlightbackground=BORDE_FOCUS, bg=BLANCO)
            icono_lbl.config(bg=BLANCO)
            entry.config(bg=BLANCO)
            if es_password:
                ojo.config(bg=BLANCO)

        def focus_out(e):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(fg=TEXTO_SEC,
                             show="" if entry.get() == placeholder else "●")
            wrapper.config(highlightbackground=BORDE, bg=FONDO_CAMPO)
            icono_lbl.config(bg=FONDO_CAMPO)
            entry.config(bg=FONDO_CAMPO)
            if es_password:
                ojo.config(bg=FONDO_CAMPO)

        entry.bind("<FocusIn>",  focus_in)
        entry.bind("<FocusOut>", focus_out)

        setattr(self, attr, entry)

    def _toggle_clave(self, entry, ojo_lbl):
        placeholder = "Contraseña"
        if entry.get() == placeholder:
            return
        self._mostrar_clave = not self._mostrar_clave
        entry.config(show="" if self._mostrar_clave else "●")
        
        # --- MODIFICADO: Alternar entre las imágenes cargadas ---
        if hasattr(self, '_img_ojo_on') and hasattr(self, '_img_ojo_off'):
            if self._mostrar_clave:
                ojo_lbl.config(image=self._img_ojo_off)
            else:
                ojo_lbl.config(image=self._img_ojo_on)
        else:
            # Plan B si fallaron las imágenes
            ojo_lbl.config(text="🙈" if self._mostrar_clave else "👁")

    def _login(self):
        u = self.entry_usuario.get()
        c = self.entry_clave.get()
        if u == "admin" and c == "1234":
            self.app.mostrar_pantalla("principal")
        else:
            self.lbl_error.config(text="⚠ Credenciales incorrectas")


def crear_pantalla_login(parent, app):
    PantallaLogin(parent, app)