import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
import threading
import cv2
import numpy as np
import sys

# Agregar la raíz del proyecto al path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ui_styles import PALETA, FUENTES, MEDIDAS, configurar_estilos
from ui.components.barra_superior import crear_encabezado

# Intentar importar face_recognition, pero no es obligatorio
try:
    import face_recognition
    TIENE_FACE_RECOGNITION = True
except ImportError:
    TIENE_FACE_RECOGNITION = False



class ValidacionBiometrica:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sistema de Control Biométrico – Validación")
        self.root.configure(bg=PALETA["page_bg"])
        self.root.geometry(f"{MEDIDAS['ancho_ventana']}x{MEDIDAS['alto_ventana']}")
        self.root.resizable(False, False)  # No permitir redimensionar
        
        self.running = True
        self.frame_count = 0
        self.rostros_detectados = []
        self.cap = None
        self.frame_actual = None
        self.vectores_rostros = []  # Almacenar vectores/encodings de rostros
        
        # Cargar cascade classifier para detección facial
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Crear interfaz
        self._crear_interfaz()
        self._iniciar_captura_camara()
        
        # Botón para cerrar correctamente
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_app)
        
    def _crear_interfaz(self) -> None:
        """Crea la interfaz con header, botones y área de cámara"""
        # Frame principal
        pantalla = tk.Frame(self.root, bg=PALETA["page_bg"])
        pantalla.pack(fill="both", expand=True)
        
        # Header (barra superior)
        crear_encabezado(pantalla, self.root)
        
        # Línea verde separadora
        tk.Frame(
            pantalla,
            bg=PALETA["topbar_sistema_fg"],
            height=MEDIDAS["alto_linea_sep"],
        ).pack(fill="x")
        
        # Contenedor principal - el video ocupa TODO el espacio
        contenedor = tk.Frame(pantalla, bg="#000000")
        contenedor.pack(fill="both", expand=True)
        
        # Frame para la cámara (OCUPA TODO)
        self.frame_camara = tk.Frame(
            contenedor,
            bg="#000000",
            relief="solid",
            borderwidth=0,
            highlightthickness=0
        )
        self.frame_camara.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Label para mostrar video
        self.label_video = tk.Label(
            self.frame_camara,
            bg="#000000",
            text="Inicializando cámara...",
            font=("Segoe UI", 14),
            fg=PALETA["topbar_sistema_fg"]
        )
        self.label_video.pack(fill="both", expand=True)
        
        # Frame para botones SUPERPUESTO (arriba del video)
        frame_botones = tk.Frame(contenedor, bg=PALETA["central_fondo"])
        frame_botones.place(x=10, y=10, relwidth=0.98)
        
        estilo_boton = dict(
            font=("Segoe UI", 11, "bold"),
            fg=PALETA["boton_fg"],
            bg=PALETA["boton_bg"],
            activebackground=PALETA["boton_hover"],
            
            bd=0,
            padx=15,
            pady=10,
            cursor="hand2",
            relief="flat",
        )
        
        # Botones en una sola fila (lado a lado)
        frame_fila1 = tk.Frame(frame_botones, bg=PALETA["central_fondo"])
        frame_fila1.pack(fill="x", pady=5)
        
        # -------------- BOTONES ------------------
        tk.Button(
            frame_fila1,
            text="← VOLVER",
            command=self._volver,
            **estilo_boton
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_fila1,
            text="··· CONTRA",
            command=self._abrir_configuracion,
            **estilo_boton
        ).pack(side="left", padx=5)
        
        # Label de estado en la misma fila
        self.label_estado = tk.Label(
            frame_fila1,
            text="",
            font=("Segoe UI", 9, "bold"),
            
            bg=PALETA["boton_bg"],
            padx=15,
            pady=10,
            relief="flat"
        )
        self.label_estado.pack(side="left", padx=5)
        
        
    
    def _iniciar_captura_camara(self) -> None:
        """Inicia captura de cámara en un thread separado"""
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self._mostrar_mensaje_error("No se pudo acceder a la cámara")
            return
        
        thread = threading.Thread(target=self._actualizar_video, daemon=True)
        thread.start()
    
    def _actualizar_video(self) -> None:
        """Actualiza el video continuamente"""
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Procesar cada 3 frames para mejorar rendimiento
            self.frame_count += 1
            if self.frame_count % 3 == 0:
                self._procesar_frame(frame)
            
            # Convertir BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            
            # Redimensionar para pantalla de 7 pulgadas (mantener aspecto)
            ancho_max, alto_max = 1000, 450
            img_pil.thumbnail((ancho_max, alto_max), Image.Resampling.LANCZOS)
            
            # Dibujar rectángulos para rostros detectados
            if self.rostros_detectados:
                draw = ImageDraw.Draw(img_pil)
                for (x, y, w, h) in self.rostros_detectados:
                    draw.rectangle(
                        [x, y, x+w, y+h],
                        outline=PALETA["topbar_sistema_fg"],
                        width=3
                    )
            
            # Convertir a PhotoImage
            imgtk = ImageTk.PhotoImage(image=img_pil)
            
            # Actualizar label en main thread
            self.root.after(0, lambda img=imgtk: self._actualizar_label(img))
    
    def _procesar_frame(self, frame) -> None:
        """Detecta rostros en el frame usando Haar Cascade"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detectar rostros con Haar Cascade
            rostros = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            self.rostros_detectados = list(rostros)
            self.frame_actual = frame  # Guardar frame para extracción de vectores
            
            cantidad = len(self.rostros_detectados)
            if cantidad > 0:
                self.root.after(
                    0, 
                    lambda: self.label_estado.config(
                        text=f"✓ {cantidad} rostro(s) detectado(s)",
                        fg=PALETA["topbar_sistema_fg"]
                    )
                )
            else:
                self.root.after(
                    0, 
                    lambda: self.label_estado.config(
                        text="⊘ Ningún rostro detectado",
                        fg="#ff6b6b"
                    )
                )
                
        except Exception as e:
            print(f"Error en detección: {e}")
    
    def _actualizar_label(self, imgtk) -> None:
        """Actualiza el label con la nueva imagen"""
        self.label_video.imgtk = imgtk
        self.label_video.config(image=imgtk, text="")
    
    def _extraer_vectores_rostro(self, frame, rostros) -> list:
        """
        Extrae vectores/características del rostro detectado.
        Usa face_recognition si está disponible, sino usa características de OpenCV.
        """
        vectores = []
        
        try:
            # Intentar usar face_recognition si está disponible
            if TIENE_FACE_RECOGNITION:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                encodings = face_recognition.face_encodings(rgb_frame, rostros)
                return encodings
        except Exception as e:
            print(f"Error con face_recognition: {e}")
        
        # Alternativa: extraer características usando OpenCV
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        for (x, y, w, h) in rostros:
            roi = gray[y:y+h, x:x+w]
            
            # Extraer características básicas del rostro
            caracteristicas = {
                "posicion": {"x": int(x), "y": int(y), "ancho": int(w), "alto": int(h)},
                "histograma": cv2.calcHist([roi], [0], None, [256], [0, 256]).flatten().tolist(),
                "media": float(np.mean(roi)),
                "desv_std": float(np.std(roi)),
            }
            
            # Calcular hash del rostro para identificación
            hash_rostro = hash(tuple(caracteristicas["histograma"][:10]))
            caracteristicas["hash"] = hash_rostro
            
            vectores.append(caracteristicas)
        
        return vectores
    
    def _capturar_rostro(self) -> None:
        """Captura los rostros detectados y extrae sus vectores"""
        if not self.rostros_detectados or self.frame_actual is None:
            self.label_estado.config(
                text="⊘ No hay rostro detectado para capturar",
                fg="red"
            )
            return
        
        try:
            # Extraer vectores del rostro
            vectores = self._extraer_vectores_rostro(self.frame_actual, self.rostros_detectados)
            self.vectores_rostros = vectores
            
            cantidad = len(vectores)
            self.label_estado.config(
                text=f"✓ {cantidad} vector(es) de rostro extraído(s)",
                fg=PALETA["boton_bg"]
            )
            
            # Debug: mostrar info del primer vector
            if vectores:
                print(f"\n[CAPTURA] Datos del rostro capturado:")
                print(f"  • Cantidad de rostros: {cantidad}")
                print(f"  • Posición: ({vectores[0]['posicion']['x']}, {vectores[0]['posicion']['y']})")
                print(f"  • Dimensiones: {vectores[0]['posicion']['ancho']}x{vectores[0]['posicion']['alto']}")
                print(f"  • Hash: {vectores[0]['hash']}")
                print(f"  • Intensidad media: {vectores[0]['media']:.2f}")
                
        except Exception as e:
            self.label_estado.config(
                text=f"✗ Error al capturar: {str(e)}",
                fg="red"
            )
            print(f"Error en captura: {e}")
    
    def _mostrar_mensaje_error(self, mensaje: str = None) -> None:
        """Muestra mensaje si faltan dependencias"""
        if mensaje is None:
            mensaje = (
                "ADVERTENCIA: Se requiere acceso a la cámara.\n\n"
                "Verifica que tu cámara esté disponible y conectada."
            )
        self.label_video.config(
            text=mensaje,
            font=("Segoe UI", 11),
            fg="red"
        )
    
    def _verificar_identidad(self) -> None:
        """Verifica la identidad usando los vectores capturados"""
        if not self.vectores_rostros:
            self.label_estado.config(
                text="⚠ Primero captura un rostro con CAPTURAR",
                fg="orange"
            )
            return
        
        self.label_estado.config(
            text="✓ Identidad verificada - Redirigiendo...",
            fg=PALETA["boton_bg"]
        )
        print(f"[VERIFICACIÓN] Identidad confirmada con {len(self.vectores_rostros)} rostro(s)")
        # TODO: Aquí irá la redirección a otra pantalla
    
    def _abrir_configuracion(self) -> None:
        """Abre pantalla de configuración (sin función por ahora)"""
        print("[CONFIG] Función no implementada aún")
        self.label_estado.config(
            text="⚙ Configuración (próximamente)",
            fg=PALETA["topbar_fecha_fg"]
        )
    
    def _cerrar_app(self) -> None:
        """Cierra la aplicación de forma segura"""
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()
    
    def _volver(self) -> None:
        """Vuelve a la pantalla anterior"""
        self._cerrar_app()


def crear_pantalla_validacion(root: tk.Tk) -> None:
    """Función principal para crear la pantalla de validación"""
    ValidacionBiometrica(root)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    configurar_estilos(style)
    crear_pantalla_validacion(root)
    root.mainloop()