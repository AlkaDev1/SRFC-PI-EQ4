#!/usr/bin/env python3
"""
====================================================
  TEST DE BUZZER - Raspberry Pi 5
  Sistema de Acceso por Reconocimiento Facial
====================================================
  Compatible con Raspberry Pi 5 usando gpiozero + lgpio

  Circuito:
    Buzzer (+) --> GPIO 17 (pin físico 11)
    Buzzer (-) --> GND     (pin físico 6 o 14)
====================================================
"""

import time
import sys
import os

# Forzar backend lgpio (requerido en Raspberry Pi 5)
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

try:
    from gpiozero import Buzzer, TonalBuzzer
    from gpiozero.tones import Tone
except ImportError:
    print("[ERROR] gpiozero no está instalado.")
    print("        Instálalo con: pip install gpiozero lgpio")
    sys.exit(1)

# ─── CONFIGURACIÓN ────────────────────────────────
BUZZER_PIN  = 17       # GPIO BCM — pin físico 11
BUZZER_TYPE = "activo" # "activo" o "pasivo"
# ──────────────────────────────────────────────────


# ══════════════════════════════════════════════════
#  FUNCIONES PARA BUZZER ACTIVO
# ══════════════════════════════════════════════════

def beep_simple(bz, duracion=0.2):
    """Un beep corto."""
    bz.on()
    time.sleep(duracion)
    bz.off()
    time.sleep(0.1)

def beep_acceso_concedido(bz):
    """Dos beeps cortos = acceso OK."""
    print("  → Acceso CONCEDIDO")
    for _ in range(2):
        beep_simple(bz, 0.15)
    time.sleep(0.3)

def beep_acceso_denegado(bz):
    """Un beep largo = acceso DENEGADO."""
    print("  → Acceso DENEGADO")
    bz.on()
    time.sleep(1.0)
    bz.off()
    time.sleep(0.3)

def beep_alerta(bz):
    """Tres beeps rápidos = alerta."""
    print("  → ALERTA")
    for _ in range(3):
        beep_simple(bz, 0.08)

def beep_inicio(bz):
    """Beep de arranque del sistema."""
    print("  → Sistema iniciado")
    beep_simple(bz, 0.05)
    time.sleep(0.05)
    beep_simple(bz, 0.05)
    time.sleep(0.05)
    beep_simple(bz, 0.3)


# ══════════════════════════════════════════════════
#  FUNCIONES PARA BUZZER PASIVO (TonalBuzzer)
# ══════════════════════════════════════════════════

def beep_tono(tbz, freq=440, duracion=0.3):
    """Tono a frecuencia dada en Hz."""
    tbz.play(Tone(frequency=freq))
    time.sleep(duracion)
    tbz.stop()
    time.sleep(0.1)

def melodia_acceso_pwm(tbz):
    """Melodía corta de acceso concedido."""
    print("  → Acceso CONCEDIDO (tonal)")
    for freq, dur in [(880, 0.15), (1100, 0.25)]:
        beep_tono(tbz, freq, dur)

def melodia_denegado_pwm(tbz):
    """Tono bajo de acceso denegado."""
    print("  → Acceso DENEGADO (tonal)")
    for freq, dur in [(400, 0.3), (300, 0.5)]:
        beep_tono(tbz, freq, dur)


# ══════════════════════════════════════════════════
#  MENÚS
# ══════════════════════════════════════════════════

def menu_activo():
    print("\n╔══════════════════════════════════════╗")
    print("║   TEST BUZZER ACTIVO - GPIO 17        ║")
    print("║   (pin físico 11)  [gpiozero+lgpio]   ║")
    print("╠══════════════════════════════════════╣")
    print("║  [1] Beep simple                      ║")
    print("║  [2] Acceso CONCEDIDO (2 beeps)       ║")
    print("║  [3] Acceso DENEGADO  (1 beep largo)  ║")
    print("║  [4] Alerta           (3 beeps rápido)║")
    print("║  [5] Beep de inicio del sistema       ║")
    print("║  [6] Secuencia completa               ║")
    print("║  [0] Salir                            ║")
    print("╚══════════════════════════════════════╝")

    bz = Buzzer(BUZZER_PIN)

    while True:
        opcion = input("\nElige una opción: ").strip()

        if opcion == "0":
            bz.off()
            bz.close()
            break
        elif opcion == "1":
            beep_simple(bz)
        elif opcion == "2":
            beep_acceso_concedido(bz)
        elif opcion == "3":
            beep_acceso_denegado(bz)
        elif opcion == "4":
            beep_alerta(bz)
        elif opcion == "5":
            beep_inicio(bz)
        elif opcion == "6":
            print("\n  ► Secuencia completa de prueba...")
            beep_inicio(bz)
            time.sleep(0.5)
            beep_acceso_concedido(bz)
            time.sleep(0.5)
            beep_acceso_denegado(bz)
            time.sleep(0.5)
            beep_alerta(bz)
        else:
            print("  Opción no válida.")


def menu_pasivo():
    print("\n╔══════════════════════════════════════╗")
    print("║   TEST BUZZER PASIVO - GPIO 17        ║")
    print("║   (pin físico 11)  [gpiozero+lgpio]   ║")
    print("╠══════════════════════════════════════╣")
    print("║  [1] Tono 440 Hz  (La)                ║")
    print("║  [2] Tono 880 Hz  (La agudo)          ║")
    print("║  [3] Melodía acceso concedido         ║")
    print("║  [4] Melodía acceso denegado          ║")
    print("║  [5] Barrido de frecuencias           ║")
    print("║  [0] Salir                            ║")
    print("╚══════════════════════════════════════╝")

    tbz = TonalBuzzer(BUZZER_PIN)

    while True:
        opcion = input("\nElige una opción: ").strip()

        if opcion == "0":
            tbz.stop()
            tbz.close()
            break
        elif opcion == "1":
            beep_tono(tbz, 440, 0.5)
        elif opcion == "2":
            beep_tono(tbz, 880, 0.5)
        elif opcion == "3":
            melodia_acceso_pwm(tbz)
        elif opcion == "4":
            melodia_denegado_pwm(tbz)
        elif opcion == "5":
            print("  → Barrido 200 Hz → 2000 Hz")
            for freq in range(200, 2001, 100):
                tbz.play(Tone(frequency=freq))
                time.sleep(0.05)
            tbz.stop()
        else:
            print("  Opción no válida.")


# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════

def main():
    print("\n🔔 TEST DE BUZZER - Raspberry Pi 5")
    print(f"   Pin físico:     11")
    print(f"   Pin GPIO (BCM): {BUZZER_PIN}")
    print(f"   Tipo de buzzer: {BUZZER_TYPE.upper()}")
    print(f"   Backend:        lgpio (Pi 5 compatible)")

    try:
        if BUZZER_TYPE == "activo":
            menu_activo()
        elif BUZZER_TYPE == "pasivo":
            menu_pasivo()
        else:
            print("[ERROR] BUZZER_TYPE debe ser 'activo' o 'pasivo'")

    except KeyboardInterrupt:
        print("\n\n  Prueba interrumpida por el usuario.")

    print("  ¡Hasta luego!")


if __name__ == "__main__":
    main()