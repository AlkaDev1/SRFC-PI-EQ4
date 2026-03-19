import tkinter as tk
from ui_styles import PALETA, FUENTES

TEXTO_AVISO = (
    "AVISO DE PRIVACIDAD\n\n"
    "La Universidad de Colima, a través de la Facultad de Ingeniería "
    "Electromecánica, es responsable del tratamiento de sus datos biométricos.\n\n"
    "DATOS QUE RECOPILAMOS\n"
    "  • Imagen facial para reconocimiento biométrico\n"
    "  • Registros de acceso (fecha, hora, laboratorio)\n"
    "  • Datos de identificación (nombre, matrícula o número de empleado)\n\n"
    "FINALIDAD\n"
    "Los datos recabados se utilizarán exclusivamente para:\n"
    "  • Control de acceso a laboratorios\n"
    "  • Trazabilidad de uso de instalaciones\n"
    "  • Seguridad institucional\n\n"
    "ALMACENAMIENTO\n"
    "Toda la información se procesa y almacena de forma local en el dispositivo. "
    "No se transmite ningún dato a servidores externos ni servicios en la nube.\n\n"
    "DERECHOS ARCO\n"
    "Usted tiene derecho a Acceder, Rectificar, Cancelar u Oponerse al tratamiento "
    "de sus datos personales, conforme a la Ley Federal de Protección de Datos "
    "Personales en Posesión de los Particulares.\n\n"
    "Al presionar 'Aceptar', usted otorga su consentimiento para el tratamiento "
    "de sus datos biométricos bajo los términos descritos."
)


def mostrar_aviso(root: tk.Tk, al_aceptar=None) -> None:
    ancho = 620
    alto  = 560

    #crea el modal
    modal = tk.Toplevel(root)
    modal.title("Aviso de Privacidad")
    modal.configure(bg=PALETA["modal_bg"])
    modal.resizable(False, False)
    modal.transient(root)
    modal.grab_set()
    modal.focus_set()

    # Fijar tamaño y centrar
    px = root.winfo_x() + (root.winfo_width()  // 2) - (ancho // 2)
    py = root.winfo_y() + (root.winfo_height() // 2) - (alto  // 2)
    modal.geometry(f"{ancho}x{alto}+{px}+{py}")

    encabezado = tk.Frame(modal, bg=PALETA["modal_header_bg"], height=55)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    tk.Label(
        encabezado,
        text="🔒  Aviso de Privacidad",
        font=FUENTES["modal_titulo"],
        fg=PALETA["modal_header_fg"],
        bg=PALETA["modal_header_bg"],
    ).pack(side="left", padx=20, pady=12)

    frame_botones = tk.Frame(modal, bg=PALETA["modal_bg"])
    frame_botones.pack(fill="x", side="bottom", padx=16, pady=(4, 16))

    def presionar_aceptar():
        if al_aceptar:
            al_aceptar()
        modal.destroy()

    # Botón Aceptar
    tk.Button(
        frame_botones,
        text="✓  Aceptar",
        font=FUENTES["boton_principal"],
        fg=PALETA["boton_fg"],
        bg=PALETA["boton_bg"],
        activebackground=PALETA["boton_hover"],
        activeforeground="#ffffff",
        bd=0,
        padx=20,
        pady=8,
        cursor="hand2",
        relief="flat",
        command=presionar_aceptar,
    ).pack(side="right")

    # Botón Cerrar
    tk.Button(
        frame_botones,
        text="Cerrar",
        font=FUENTES["modal_texto"],
        fg=PALETA["modal_btn_cerrar_fg"],
        bg=PALETA["modal_btn_cerrar_bg"],
        activebackground=PALETA["topbar_btn_hover"],
        bd=0,
        padx=14,
        pady=8,
        cursor="hand2",
        relief="flat",
        command=modal.destroy,
    ).pack(side="right", padx=(0, 8))

    frame_texto = tk.Frame(modal, bg=PALETA["modal_bg"])
    frame_texto.pack(fill="both", expand=True, padx=16, pady=(12, 6))

    scrollbar = tk.Scrollbar(frame_texto)
    scrollbar.pack(side="right", fill="y")

    cuadro = tk.Text(
        frame_texto,
        font=FUENTES["modal_texto"],
        fg=PALETA["modal_texto_fg"],
        bg=PALETA["modal_texto_bg"],
        wrap="word",
        yscrollcommand=scrollbar.set,
        bd=0,
        padx=12,
        pady=10,
        relief="flat",
    )
    cuadro.pack(fill="both", expand=True)
    scrollbar.config(command=cuadro.yview)
    cuadro.insert("1.0", TEXTO_AVISO)
    cuadro.config(state="disabled")