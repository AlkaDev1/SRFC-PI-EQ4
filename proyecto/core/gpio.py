"""
core/gpio.py
Control de GPIO para el sistema de acceso biométrico.
Usa gpiozero con relé activo en LOW (active_high=False).

Componentes:
  Solenoide  (IN1 relé)      → GPIO 17  (PIN 11)
  Actuador sale (IN2 relé)   → GPIO 27  (PIN 13)
  Actuador entra (IN3 relé)  → GPIO 22  (PIN 15)
  LED RGB Rojo               → GPIO 18  (PIN 12)
  LED RGB Verde              → GPIO 23  (PIN 16)
  Buzzer                     → GPIO 25  (PIN 22)  ← pendiente de conectar

Secuencia acceso concedido (True):
  1. LED verde ON
  2. Solenoide ON ──┐ al mismo tiempo
     Actuador sale  ┘ ambos arrancan juntos
  3. Solenoide OFF a los 2s (actuador sigue su recorrido de 7s)
  4. Actuador sale OFF al terminar su recorrido
  5. Espera 3s (persona entra)
  6. Actuador entra ON → 7s → OFF (puerta cierra)
  7. LED verde OFF

Secuencia acceso denegado (False):
  1. LED rojo ON → 2s → OFF
  (solenoide y actuador NO se activan)
"""

import platform
import threading
import time

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

# ── Setup gpiozero ────────────────────────────────────────────────────────────
try:
    from gpiozero import OutputDevice
    from gpiozero import Device

    if not _ES_RASPBERRY:
        from gpiozero.pins.mock import MockFactory
        Device.pin_factory = MockFactory()
        print("[GPIO] Modo simulación (MockFactory)")
    else:
        print("[GPIO] Inicializado en Raspberry Pi con gpiozero")

    # Relé activo en LOW → active_high=False, initial_value=False (relé cerrado al inicio)
    solenoide      = OutputDevice(17, active_high=False, initial_value=False)
    actuador_sale  = OutputDevice(27, active_high=False, initial_value=False)
    actuador_entra = OutputDevice(22, active_high=False, initial_value=False)
    # LED cátodo común → active_high=True, initial_value=False (apagado)
    led_rojo       = OutputDevice(18, active_high=True, initial_value=False)
    led_verde      = OutputDevice(23, active_high=True, initial_value=False)
    # buzzer       = OutputDevice(25, active_high=False, initial_value=False)

    _GPIO_OK = True

except Exception as e:
    print(f"[GPIO] Error al inicializar: {e}")
    _GPIO_OK = False

    class _Dummy:
        def on(self):  print("[GPIO SIM] ON")
        def off(self): print("[GPIO SIM] OFF")

    solenoide      = _Dummy()
    actuador_sale  = _Dummy()
    actuador_entra = _Dummy()
    led_rojo       = _Dummy()
    led_verde      = _Dummy()


# ── Tiempos ───────────────────────────────────────────────────────────────────
_T_SOLENOIDE    = 2.0   # segundos que el solenoide permanece abierto
_T_ACTUADOR     = 7.0   # segundos que tarda el actuador (200mm / 30mm·s⁻¹ ≈ 6.7s)
_T_ESPERA       = 3.0   # segundos que espera con la puerta abierta (persona entra)
_T_LED_DENEGADO = 2.0   # segundos que el LED rojo permanece encendido


# ── API pública ───────────────────────────────────────────────────────────────
def acceso_concedido():
    """
    Secuencia TRUE — acceso concedido (no bloqueante):

      1. LED verde ON
      2. Solenoide ON y Actuador sale ON — arrancan juntos
      3. Solenoide OFF a los 2s (actuador sigue)
      4. Actuador sale OFF al terminar su recorrido (7s)
      5. Espera 3s (persona entra)
      6. Actuador entra ON → 7s → OFF (puerta cierra)
      7. LED verde OFF
    """
    def _apagar_solenoide():
        time.sleep(_T_SOLENOIDE)
        solenoide.off()
        print("[GPIO] Solenoide OFF")

    def _secuencia():
        print("[GPIO] >>> Acceso CONCEDIDO — iniciando secuencia")

        # 1. LED verde
        led_verde.on()
        print("[GPIO] LED verde ON")

        # 2. Solenoide y actuador arrancan al mismo tiempo
        solenoide.on()
        print(f"[GPIO] Solenoide ON → {_T_SOLENOIDE}s")
        actuador_sale.on()
        print(f"[GPIO] Actuador SALE ON → {_T_ACTUADOR}s")

        # Solenoide se apaga en paralelo después de 2s
        threading.Thread(target=_apagar_solenoide, daemon=True).start()

        # Actuador completa su recorrido (7s)
        time.sleep(_T_ACTUADOR)
        actuador_sale.off()
        print("[GPIO] Actuador SALE OFF — puerta abierta")

        # 5. Espera para que la persona entre
        print(f"[GPIO] Esperando {_T_ESPERA}s (persona entra)")
        time.sleep(_T_ESPERA)

        # 6. Actuador entra (puerta cierra)
        actuador_entra.on()
        print(f"[GPIO] Actuador ENTRA ON → {_T_ACTUADOR}s")
        time.sleep(_T_ACTUADOR)
        actuador_entra.off()
        print("[GPIO] Actuador ENTRA OFF — puerta cerrada")

        # 7. LED verde OFF
        led_verde.off()
        print("[GPIO] LED verde OFF — secuencia completa")

    threading.Thread(target=_secuencia, daemon=True).start()


def acceso_denegado():
    """
    Secuencia FALSE — acceso denegado (no bloqueante):

      1. LED rojo ON → 2s → OFF
      (solenoide y actuador NO se activan)
    """
    def _secuencia():
        print("[GPIO] >>> Acceso DENEGADO")
        led_rojo.on()
        print(f"[GPIO] LED rojo ON → {_T_LED_DENEGADO}s")
        time.sleep(_T_LED_DENEGADO)
        led_rojo.off()
        print("[GPIO] LED rojo OFF")

    threading.Thread(target=_secuencia, daemon=True).start()


def apagar_todo():
    """Apaga todos los dispositivos. Llamar al cerrar la app."""
    for device in (solenoide, actuador_sale, actuador_entra, led_rojo, led_verde):
        device.off()
    print("[GPIO] Todos los pines apagados")