#!/usr/bin/env python3
"""
====================================================
  TEST MÍNIMO — Buzzer ACTIVO
  GPIO 17 (pin físico 11)
====================================================
"""

import time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

from gpiozero import Buzzer

BUZZER_PIN = 17

def beep(bz, dur, pausa=0.1):
    bz.on()
    time.sleep(dur)
    bz.off()
    time.sleep(pausa)

bz = Buzzer(BUZZER_PIN)

print("\n🔔 Probando buzzer ACTIVO en GPIO 17...\n")

print("  [1] Beep simple")
beep(bz, 0.3)

print("  [2] Dos beeps cortos — Acceso concedido")
beep(bz, 0.15)
beep(bz, 0.15)

print("  [3] Beep largo — Acceso denegado")
beep(bz, 1.0)

print("  [4] Tres beeps rápidos — Alerta")
for _ in range(3):
    beep(bz, 0.08, 0.06)

print("  [5] Melodía salida (botón comodín)")
beep(bz, 0.1, 0.05)
beep(bz, 0.1, 0.05)
beep(bz, 0.3)

print("\n  ✔ Listo.\n")
bz.close()