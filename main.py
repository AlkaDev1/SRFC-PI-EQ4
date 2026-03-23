import tkinter as tk
from tkinter import messagebox

from core.database import obtener_conexion
from ui.styles import (
	ALTO_VENTANA,
	ANCHO_VENTANA,
	COLOR_FONDO,
	COLOR_TEXTO,
	COLOR_TEXTO_SUAVE,
	FUENTE_SUBTITULO,
	FUENTE_TITULO,
	TITULO_APP,
	estilo_boton_primario,
	estilo_frame_tarjeta,
)


# [BLOQUE 1] INICIO - Clase principal de la app
class SRFCApp(tk.Tk):
	def __init__(self) -> None:
		super().__init__()
		self.title(TITULO_APP)
		self.configure(bg=COLOR_FONDO)
		self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
		self.minsize(760, 480)

		self._centrar_ventana()
		self._construir_layout()

	def _centrar_ventana(self) -> None:
		"""Centra la ventana en la pantalla del usuario."""
		self.update_idletasks()
		ancho_pantalla = self.winfo_screenwidth()
		alto_pantalla = self.winfo_screenheight()
		x = (ancho_pantalla // 2) - (ANCHO_VENTANA // 2)
		y = (alto_pantalla // 2) - (ALTO_VENTANA // 2)
		self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}+{x}+{y}")

	def _construir_layout(self) -> None:
		"""Crea la interfaz inicial (pantalla de bienvenida)."""
		contenedor = tk.Frame(self, bg=COLOR_FONDO)
		contenedor.pack(fill="both", expand=True, padx=24, pady=24)

		tarjeta = tk.Frame(contenedor, **estilo_frame_tarjeta())
		tarjeta.pack(fill="both", expand=True)

		titulo = tk.Label(
			tarjeta,
			text="Sistema de Registro Facial y Control",
			font=FUENTE_TITULO,
			bg=tarjeta["bg"],
			fg=COLOR_TEXTO,
		)
		titulo.pack(pady=(48, 8))

		subtitulo = tk.Label(
			tarjeta,
			text="Base del proyecto restaurada. Ya puedes continuar con modulos de login, registro y dashboard.",
			font=FUENTE_SUBTITULO,
			bg=tarjeta["bg"],
			fg=COLOR_TEXTO_SUAVE,
			wraplength=620,
			justify="center",
		)
		subtitulo.pack(pady=(0, 24))

		boton_db = tk.Button(
			tarjeta,
			text="Probar conexion con SQLite",
			command=self._probar_conexion,
			**estilo_boton_primario(),
		)
		boton_db.pack()
# [BLOQUE 1] FIN - Clase principal de la app


# [BLOQUE 2] INICIO - Acciones de interfaz
	def _probar_conexion(self) -> None:
		"""Intenta abrir y cerrar la conexion para validar el archivo de BD."""
		conexion = obtener_conexion()
		if conexion is None:
			messagebox.showerror(
				"Conexion fallida",
				"No se pudo conectar con la base de datos. Revisa la ruta en core/database.py",
			)
			return

		conexion.close()
		messagebox.showinfo("Conexion OK", "La conexion SQLite fue exitosa.")
# [BLOQUE 2] FIN - Acciones de interfaz


# [BLOQUE 3] INICIO - Punto de entrada
def main() -> None:
	app = SRFCApp()
	app.mainloop()


if __name__ == "__main__":
	main()
# [BLOQUE 3] FIN - Punto de entrada
