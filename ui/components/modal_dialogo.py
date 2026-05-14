"""
ui/components/modal_dialogo.py
Modal de diálogo personalizado — reemplaza messagebox

Usa tk.Toplevel centrado sobre la ventana principal, sin overlay oscuro.

USO:
    from ui.components.modal_dialogo import modal_info, modal_error, modal_warning, modal_confirm

    modal_info(parent, "Usuario guardado correctamente.",
               on_ok=lambda: app.mostrar_pantalla("gestion_real"))

    modal_error(parent, "No se pudo conectar a la base de datos.")

    modal_warning(parent, "El nombre no puede estar vacío.")

    modal_confirm(parent, "¿Eliminar este usuario?",
                  on_ok=lambda: eliminar())
"""

import tkinter as tk
from pathlib import Path

_TIPOS = {
    "info": {
        "barra":     "#43a047",
        "icono_bg":  "#e8f5e9",
        "icono_fg":  "#2e7d32",
        "icono":     "✓",
        "btn_bg":    "#43a047",
        "btn_hover": "#388e3c",
    },
    "error": {
        "barra":     "#e53935",
        "icono_bg":  "#ffebee",
        "icono_fg":  "#c62828",
        "icono":     "✕",
        "btn_bg":    "#e53935",
        "btn_hover": "#b71c1c",
    },
    "warning": {
        "barra":     "#fb8c00",
        "icono_bg":  "#fff3e0",
        "icono_fg":  "#e65100",
        "icono":     "!",
        "btn_bg":    "#fb8c00",
        "btn_hover": "#e65100",
    },
    "confirm": {
        "barra":     "#43a047",
        "icono_bg":  "#e8f5e9",
        "icono_fg":  "#2e7d32",
        "icono":     "?",
        "btn_bg":    "#43a047",
        "btn_hover": "#388e3c",
    },
}


def _es_oscuro(widget) -> bool:
    try:
        root = widget.winfo_toplevel()
        for attr in ("app", "_app"):
            app = getattr(root, attr, None)
            if app and hasattr(app, "tema"):
                return app.tema.es_oscuro()
    except Exception:
        pass
    return False


def _mostrar_modal(
    parent,
    mensaje: str,
    tipo: str = "info",
    titulo: str = None,
    on_ok=None,
    on_cancel=None,
    btn_ok_txt: str = "Aceptar",
    btn_cancel_txt: str = "Cancelar",
):
    cfg    = _TIPOS.get(tipo, _TIPOS["info"])
    oscuro = _es_oscuro(parent)

    bg_card = "#0d2a0d" if oscuro else "#ffffff"
    fg_txt  = "#d0f0d0" if oscuro else "#1a1a1a"
    fg_gris = "#7aaa7a" if oscuro else "#757575"
    borde   = "#1a3a1a" if oscuro else "#e0e0e0"
    sep     = "#1a3a1a" if oscuro else "#e8e8e8"

    root = parent.winfo_toplevel()

    # ── Toplevel sin decoraciones del WM ─────────────────────────────────────
    dlg = tk.Toplevel(root)
    dlg.overrideredirect(True)          # sin barra de título del SO
    dlg.resizable(False, False)
    dlg.configure(bg=bg_card)

    # ── Card interior ─────────────────────────────────────────────────────────
    card = tk.Frame(dlg, bg=bg_card,
                    highlightthickness=1,
                    highlightbackground=cfg["barra"])
    card.pack()

    # Barra superior de color
    tk.Frame(card, bg=cfg["barra"], height=5).pack(fill="x")

    # Cuerpo
    cuerpo = tk.Frame(card, bg=bg_card)
    cuerpo.pack(fill="both", expand=True, padx=28, pady=(18, 8))

    # Icono circular
    c_ico = tk.Canvas(cuerpo, width=48, height=48,
                      bg=bg_card, highlightthickness=0)
    c_ico.pack(pady=(0, 10))
    c_ico.create_oval(2, 2, 46, 46,
                      fill=cfg["icono_bg"],
                      outline=cfg["barra"], width=2)
    c_ico.create_text(24, 24, text=cfg["icono"],
                      font=("Segoe UI", 20, "bold"),
                      fill=cfg["icono_fg"])

    # Título
    if titulo:
        tk.Label(cuerpo, text=titulo,
                 font=("Segoe UI", 12, "bold"),
                 fg=fg_txt, bg=bg_card,
                 wraplength=300, justify="center").pack(pady=(0, 4))

    # Mensaje
    tk.Label(cuerpo, text=mensaje,
             font=("Segoe UI", 10),
             fg=fg_gris, bg=bg_card,
             wraplength=300, justify="center").pack(pady=(0, 18))

    # Separador
    tk.Frame(card, bg=sep, height=1).pack(fill="x")

    # Pie con botones
    pie = tk.Frame(card, bg=bg_card)
    pie.pack(fill="x", padx=20, pady=14)

    def _ok():
        dlg.destroy()
        if on_ok:
            on_ok()

    def _cancel():
        dlg.destroy()
        if on_cancel:
            on_cancel()

    if tipo == "confirm":
        btn_c = tk.Button(
            pie, text=btn_cancel_txt,
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff", bg="#757575",
            activebackground="#424242", activeforeground="#ffffff",
            bd=0, padx=18, pady=8, relief="flat", cursor="hand2",
            command=_cancel)
        btn_c.pack(side="left", padx=(0, 8))
        btn_c.bind("<Enter>", lambda e: btn_c.config(bg="#424242"))
        btn_c.bind("<Leave>", lambda e: btn_c.config(bg="#757575"))

    btn_ok = tk.Button(
        pie, text=btn_ok_txt,
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff", bg=cfg["btn_bg"],
        activebackground=cfg["btn_hover"], activeforeground="#ffffff",
        bd=0, padx=18, pady=8, relief="flat", cursor="hand2",
        command=_ok)

    if tipo == "confirm":
        btn_ok.pack(side="left")
    else:
        btn_ok.pack(expand=True)

    btn_ok.bind("<Enter>", lambda e: btn_ok.config(bg=cfg["btn_hover"]))
    btn_ok.bind("<Leave>", lambda e: btn_ok.config(bg=cfg["btn_bg"]))

    # ── Centrar sobre la ventana principal ────────────────────────────────────
    dlg.update_idletasks()
    w = dlg.winfo_reqwidth()
    h = dlg.winfo_reqheight()
    rx = root.winfo_x()
    ry = root.winfo_y()
    rw = root.winfo_width()
    rh = root.winfo_height()
    x  = rx + (rw - w) // 2
    y  = ry + (rh - h) // 2
    dlg.geometry(f"{w}x{h}+{x}+{y}")

    # ── Foco y teclas ─────────────────────────────────────────────────────────
    dlg.transient(root)     # se mantiene sobre la ventana padre
    dlg.grab_set()          # bloquea interacción con el resto
    dlg.focus_force()
    btn_ok.focus_set()

    dlg.bind("<Return>",  lambda e: _ok())
    dlg.bind("<Escape>",  lambda e: _cancel())

    dlg.wait_window()       # esperar a que se cierre (bloquea el hilo UI)


# ── Accesos directos ──────────────────────────────────────────────────────────

def modal_info(parent, mensaje: str, titulo: str = None, on_ok=None):
    _mostrar_modal(parent, mensaje, tipo="info", titulo=titulo, on_ok=on_ok)

def modal_error(parent, mensaje: str, titulo: str = None, on_ok=None):
    _mostrar_modal(parent, mensaje, tipo="error", titulo=titulo, on_ok=on_ok)

def modal_warning(parent, mensaje: str, titulo: str = None, on_ok=None):
    _mostrar_modal(parent, mensaje, tipo="warning", titulo=titulo, on_ok=on_ok)

def modal_confirm(parent, mensaje: str, titulo: str = None,
                  on_ok=None, on_cancel=None,
                  btn_ok_txt="Confirmar", btn_cancel_txt="Cancelar"):
    _mostrar_modal(parent, mensaje, tipo="confirm", titulo=titulo,
                   on_ok=on_ok, on_cancel=on_cancel,
                   btn_ok_txt=btn_ok_txt, btn_cancel_txt=btn_cancel_txt)