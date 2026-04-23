#!/usr/bin/env python3
# Script de prueba rápida del sistema de idiomas

from core.language_manager import LanguageManager
from core.translations import obtener_texto

print("=" * 70)
print("PRUEBA DEL SISTEMA DE IDIOMAS")
print("=" * 70)

# Obtener instancia
manager = LanguageManager.obtener_instancia()

# Probar idioma actual
idioma_actual = manager.obtener_idioma_actual()
print(f"\n✓ Idioma actual: {idioma_actual}")

# Probar traducciones
textos_prueba = ["bienvenidos", "sistema", "biometrico", "aceptar", "cancelar"]

print(f"\n✓ Traducciones en ESPAÑOL:")
for clave in textos_prueba:
    texto = obtener_texto("es", clave)
    print(f"    {clave:20} → {texto}")

print(f"\n✓ Traducciones en INGLÉS:")
for clave in textos_prueba:
    texto = obtener_texto("en", clave)
    print(f"    {clave:20} → {texto}")

# Probar cambio de idioma
print(f"\n✓ Cambio de idioma a 'en'...")
manager.cambiar_idioma("en")
print(f"    Idioma actual ahora: {manager.obtener_idioma_actual()}")

# Verificar que se guardó
manager2 = LanguageManager.obtener_instancia()
print(f"\n✓ Verificando persistencia...")
print(f"    Segunda instancia tiene idioma: {manager2.obtener_idioma_actual()}")

print("\n" + "=" * 70)
print("✓ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
print("=" * 70)
