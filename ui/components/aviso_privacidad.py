import tkinter as tk
from ui.styles import PALETA, FUENTES
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path

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

    # 1. Crear modal sin bloquear la pantalla
    modal = tk.Toplevel(root)
    modal.title("Aviso de Privacidad")
    modal.configure(bg=PALETA["modal_bg"])
    modal.resizable(False, False)
    modal.transient(root)
    
    def ignorar_cierre():
        pass
    modal.protocol("WM_DELETE_WINDOW", ignorar_cierre)

    #calcular el tamaño real de la ventana de fondo
    root.update_idletasks()

    # Fijar tamaño y centrar
    px = root.winfo_rootx() + (root.winfo_width()  // 2) - (ancho // 2)
    py = root.winfo_rooty() + (root.winfo_height() // 2) - (alto  // 2)
    
    px = max(0, px)
    py = max(0, py)
    modal.geometry(f"{ancho}x{alto}+{px}+{py}")

    encabezado = tk.Frame(modal, bg=PALETA["modal_header_bg"], height=55)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)

    label_titulo = tk.Label(
        encabezado,
        text=" Aviso de Privacidad",
        font=FUENTES["modal_titulo"],
        fg=PALETA["modal_header_fg"],
        bg=PALETA["modal_header_bg"],
        compound="left" 
    )
    label_titulo.pack(side="left", padx=20, pady=12)
    _RAIZ = Path(__file__).resolve().parent.parent.parent
    ruta_candado = _RAIZ / "assets" / "img" / "lock_icon.png"
    ruta_check_icon = _RAIZ / "assets" / "img" / "check_icon.png"

    # 3. Cargamos la imagen
    if ruta_candado.exists():
        try:
            img_pil = Image.open(ruta_candado).resize((24, 24), Image.Resampling.LANCZOS)
            
            modal.icono_candado = ImageTk.PhotoImage(img_pil)
            
            label_titulo.config(image=modal.icono_candado)
            
        except Exception as e:
            label_titulo.config(text="🔒  Aviso de Privacidad", image="")
    else:
        label_titulo.config(text="🔒  Aviso de Privacidad", image="")

    frame_botones = tk.Frame(modal, bg=PALETA["modal_bg"])
    frame_botones.pack(fill="x", side="bottom", padx=16, pady=(4, 16))

    def presionar_aceptar():
        if al_aceptar:
            al_aceptar()
        modal.destroy()

    def crear_fondo_redondeado_con_icono(ancho, alto, radio, color, ruta_icono=None):
        factor = 3

        img = Image.new("RGBA", (ancho * factor, alto * factor), (255, 255, 255, 0))
        dibujo = ImageDraw.Draw(img)
        dibujo.rounded_rectangle(
            (0, 0, ancho * factor, alto * factor), 
            fill=color, 
            radius=radio * factor
        )

        img_suave = img.resize((ancho, alto), Image.Resampling.LANCZOS)

        if ruta_icono and Path(ruta_icono).exists():
            try:
                icono = Image.open(ruta_icono).convert("RGBA")

                # --- AJUSTES DE TAMAÑO Y POSICIÓN DEL ICONO ---
                tam_icono = 26  # Antes era 20
                icono = icono.resize((tam_icono, tam_icono), Image.Resampling.LANCZOS)
                
                pos_x = 18  # Antes era 28 (Más cerca del borde izquierdo)
                pos_y = (alto - tam_icono) // 2
                # ---------------------------------------------

                img_suave.paste(icono, (pos_x, pos_y), icono)
            except Exception:
                pass

        return ImageTk.PhotoImage(img_suave)
    
    modal.btn_bg_normal = crear_fondo_redondeado_con_icono(160, 45, 8, PALETA["boton_bg"], ruta_check_icon)
    modal.btn_bg_hover = crear_fondo_redondeado_con_icono(160, 45, 8, PALETA["boton_hover"], ruta_check_icon)

    btn_aceptar = tk.Button(
        frame_botones,
        text="     Aceptar", # Se agregó un poco más de espacio para balancearlo
        image=modal.btn_bg_normal,
        compound="center",        
        font=FUENTES["boton_principal"],
        fg=PALETA["boton_fg"],
        bg=PALETA["modal_bg"],      
        activebackground=PALETA["modal_bg"],
        activeforeground=PALETA["boton_fg"],
        bd=0,
        cursor="hand2",
        relief="flat",
        command=presionar_aceptar,
    )
    btn_aceptar.pack(expand=True, pady=(10, 0))

    # 3. Efectos Hover
    btn_aceptar.bind("<Enter>", lambda e: btn_aceptar.config(image=modal.btn_bg_hover))
    btn_aceptar.bind("<Leave>", lambda e: btn_aceptar.config(image=modal.btn_bg_normal))

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