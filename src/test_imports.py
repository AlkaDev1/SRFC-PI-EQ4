import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("Importando módulos...")
try:
    import tkinter as tk
    print("✓ tkinter")
    from PIL import Image, ImageTk, ImageDraw
    print("✓ PIL")
    import cv2
    print("✓ cv2")
    import threading
    print("✓ threading")
    from ui_styles import PALETA, FUENTES, MEDIDAS, configurar_estilos
    print("✓ ui_styles")
    from ui.components.barra_superior import crear_encabezado
    print("✓ barra_superior")
    print("\nTodos los módulos importados correctamente!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
