import tkinter as tk
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from views.gestion import app as abrir_gestion


def ir_a_gestion(ventana: tk.Tk) -> None:
    """Cierra la ventana actual y abre la pantalla de gestion."""
    ventana.destroy()
    abrir_gestion()


def abrir_principal() -> None:
    #__________________________1__________________________#
    #configuraciones generales
    
    ventana = tk.Tk()
    ventana.title("Pantalla Principal")
    ventana.geometry("1024x600") #este es el tamaño en pulgadas de la pantalla que usamos
    titulo = tk.Label(ventana, text="Pantalla Principal", font=("Arial", 16, "bold"))
    titulo.pack(pady=25)
    #__________________________FIN_1______________________#

    #__________________________2__________________________#
    #mensaje de bienvenida
    label_bienvenida = tk.Label(ventana, text="Bienvenido a la pantalla principal", font=("Arial", 12))
    label_bienvenida.pack(pady=10)
    #__________________________FIN_2______________________#

    #__________________________3__________________________#
    #boton para ir a gestion
    boton_gestion = tk.Button(
        ventana,
        text="Ir a Gestion",
        font=("Arial", 12),
        command=lambda: ir_a_gestion(ventana),
    )
    boton_gestion.pack(pady=10)
    #__________________________FIN_3______________________#

    #__________________________4__________________________#
    #bucle principal de la ventana
    ventana.mainloop()
    #__________________________FIN_4______________________#


if __name__ == "__main__":
    #__________________________5__________________________#
    #punto de entrada del archivo
    abrir_principal()
    #__________________________FIN_5______________________#
