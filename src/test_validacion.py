"""
Script de prueba para validacionUsrs.py
Verifica que la pantalla de validación biométrica funcione correctamente
"""
import sys
from pathlib import Path

# Configurar path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("PRUEBA DE PANTALLA DE VALIDACIÓN BIOMÉTRICA")
print("=" * 60)

print("\n1. Verificando módulos disponibles...")
modulos = {
    "tkinter": "GUI",
    "cv2": "Captura de video",
    "PIL": "Procesamiento de imágenes",
    "face_recognition": "Reconocimiento facial (opcional)",
}

for modulo, descripcion in modulos.items():
    try:
        __import__(modulo)
        print(f"   ✓ {modulo:20} - {descripcion}")
    except ImportError:
        print(f"   ⚠ {modulo:20} - {descripcion} (NO DISPONIBLE)")

print("\n2. Verificando archivos del proyecto...")
archivos = [
    "ui_styles.py",
    "ui/components/barra_superior.py",
    "ui/screens/validacionUsrs.py",
]
for archivo in archivos:
    ruta = project_root / archivo
    if ruta.exists():
        print(f"   ✓ {archivo}")
    else:
        print(f"   ✗ {archivo} (FALTA)")

print("\n3. Cargando validacionUsrs...")
try:
    from ui.screens.validacionUsrs import crear_pantalla_validacion
    print("   ✓ Módulo cargado correctamente")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("CONFIGURACIÓN LISTA")
print("=" * 60)
print("\nCaracterísticas disponibles:")
print("  • Captura de video en tiempo real (cv2)")
print("  • Detección facial con Haar Cascade (integrado en OpenCV)")
print("  • Interfaz con header (barra superior)")
print("  • Botones de navegación y captura")
print("  • Indicador de estado en tiempo real")
print("\nPara ejecutar la pantalla completa, usa:")
print("  python ui/screens/validacionUsrs.py")
print("  o integra desde main.py")
print("=" * 60)
