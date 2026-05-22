#!/usr/bin/env python3
"""
====================================================
  SIMULADOR DE BOTÓN COMODÍN — teclado + buzzer real
  Raspberry Pi 5  |  Buzzer ACTIVO GPIO 17
====================================================
  Presiona Enter para simular el botón.
  El buzzer suena de verdad, LED y relay simulados.
====================================================
"""

import time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

from gpiozero import Buzzer

BUZZER_PIN              = 17
PUERTA_ABIERTA_SEGUNDOS = 5


# ══════════════════════════════════════════════════
#  BEEPS
# ══════════════════════════════════════════════════

def beep(bz, dur, pausa=0.08):
    bz.on()
    time.sleep(dur)
    bz.off()
    time.sleep(pausa)

def sonido_salida(bz):
    beep(bz, 0.1, 0.05)
    beep(bz, 0.1, 0.05)
    beep(bz, 0.3)


# ══════════════════════════════════════════════════
#  SECUENCIA
# ══════════════════════════════════════════════════

def ejecutar_secuencia(bz):
    print("\n  [1/5] LED amarillo  → ON  (simulado)")

    print("\n" + "═" * 42)
    print("  🟡  S A L I E N D O  . . .")
    print("      Puerta abierta — pase con cuidado")
    print("═" * 42)

    print("  [3/5] Buzzer        → sonando...")
    sonido_salida(bz)

    print("  [4/5] Relay         → ABRE cerrojo (simulado)")

    for i in range(PUERTA_ABIERTA_SEGUNDOS, 0, -1):
        print(f"  [5/5] Cerrando en {i}s...", end="\r")
        time.sleep(1)

    print("\n  [5/5] Relay         → CIERRA cerrojo (simulado)")
    print("  [1/5] LED amarillo  → OFF (simulado)")
    print("  🔒  Puerta cerrada. Sistema en espera.\n")


# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════

def main():
    print("\n🟡 SIMULADOR — Botón comodín con buzzer real")
    print(f"   Buzzer ACTIVO: GPIO {BUZZER_PIN} (pin físico 11)")
    print(f"   LED y relay:   simulados en consola")
    print("\n   Enter → simula presionar el botón")
    print("   q     → salir\n")

    bz = Buzzer(BUZZER_PIN)

    try:
        while True:
            cmd = input("  Presiona Enter para simular el botón: ").strip().lower()
            if cmd == "q":
                break
            ejecutar_secuencia(bz)

    except KeyboardInterrupt:
        print("\n  Interrumpido.")
    finally:
        bz.off()
        bz.close()
        print("  GPIO liberados.\n")


if __name__ == "__main__":
    main()