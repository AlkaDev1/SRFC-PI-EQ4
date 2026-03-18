import tkinter as tk


def abrir_gestion(ventana_actual: tk.Tk) -> None:
    ventana_actual.withdraw()  # Oculta la pantalla principal sin cerrarla.

    ventana_gestion = tk.Toplevel(ventana_actual)
    ventana_gestion.title("Gestion")
    ventana_gestion.geometry("1024x600")  # este es el tamaño en pulgadas de la pantalla que usamos

    mensaje = tk.Label(ventana_gestion, text="Bienvenido a gestion", font=("Arial", 16, "bold"))
    mensaje.pack(pady=35)

    boton_volver = tk.Button(
        ventana_gestion,
        text="Volver",
        font=("Arial", 12),
        command=lambda: volver_a_principal(ventana_gestion, ventana_actual),
    )
    boton_volver.pack(pady=10)

    ventana_gestion.protocol(
        "WM_DELETE_WINDOW",
        lambda: volver_a_principal(ventana_gestion, ventana_actual),
    )


def volver_a_principal(ventana_gestion: tk.Toplevel, ventana_principal: tk.Tk) -> None:
    ventana_gestion.destroy()
    ventana_principal.deiconify()
