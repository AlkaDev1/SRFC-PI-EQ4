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

Secuencia acceso concedido:
  1. LED verde ON
  2. Solenoide ON → 1.5s → OFF
  3. Espera 0.5s
  4. Actuador sale ON → 7s → OFF
  5. LED verde OFF
  6. Actuador entra ON → 7s → OFF

Secuencia acceso denegado:
  1. LED rojo ON → 2s → OFF
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

    # Relé activo en LOW → active_high=False, initial_value=True (relé abierto)
    solenoide      = OutputDevice(17, active_high=False, initial_value=True)
    actuador_sale  = OutputDevice(27, active_high=False, initial_value=True)
    actuador_entra = OutputDevice(22, active_high=False, initial_value=True)
    led_rojo       = OutputDevice(18, active_high=False, initial_value=True)
    led_verde      = OutputDevice(23, active_high=False, initial_value=True)
    # buzzer       = OutputDevice(25, active_high=False, initial_value=True)

    _GPIO_OK = True

except Exception as e:
    print(f"[GPIO] Error al inicializar: {e}")
    _GPIO_OK = False

    class _Dummy:
        def on(self):  print(f"[GPIO SIM] ON")
        def off(self): print(f"[GPIO SIM] OFF")

    solenoide = _Dummy()
    actuador_sale = _Dummy()
    actuador_entra = _Dummy()
    led_rojo = _Dummy()
    led_verde = _Dummy()


# ── Tiempos ───────────────────────────────────────────────────────────────────
_T_SOLENOIDE    = 1.5   # segundos que el solenoide permanece abierto
_T_PAUSA        = 0.5   # pausa entre solenoide y actuador
_T_ACTUADOR     = 7.0   # segundos que tarda el actuador (200mm / 30mm·s⁻¹ ≈ 6.7s)
_T_LED_DENEGADO = 2.0   # segundos que el LED rojo permanece encendido


# ── API pública ───────────────────────────────────────────────────────────────
def acceso_concedido():
    """
    Secuencia de acceso concedido (no bloqueante).

      1. LED verde ON
      2. Solenoide ON → 1.5s → OFF
      3. Espera 0.5s
      4. Actuador sale ON → 7s → OFF
      5. LED verde OFF
      6. Actuador entra ON → 7s → OFF
    """
    def _secuencia():
        print("[GPIO] Acceso concedido — iniciando secuencia")

        # 1. LED verde
        led_verde.on()
        print("[GPIO] LED verde ON")

        # 2. Solenoide
        solenoide.on()
        print(f"[GPIO] Solenoide ON → {_T_SOLENOIDE}s")
        time.sleep(_T_SOLENOIDE)
        solenoide.off()
        print("[GPIO] Solenoide OFF")

        # 3. Pausa
        time.sleep(_T_PAUSA)

        # 4. Actuador sale
        actuador_sale.on()
        print(f"[GPIO] Actuador SALE ON → {_T_ACTUADOR}s")
        time.sleep(_T_ACTUADOR)
        actuador_sale.off()
        print("[GPIO] Actuador SALE OFF")

        # 5. LED verde OFF
        led_verde.off()
        print("[GPIO] LED verde OFF")

        # 6. Actuador entra
        actuador_entra.on()
        print(f"[GPIO] Actuador ENTRA ON → {_T_ACTUADOR}s")
        time.sleep(_T_ACTUADOR)
        actuador_entra.off()
        print("[GPIO] Actuador ENTRA OFF — secuencia completa")

    threading.Thread(target=_secuencia, daemon=True).start()


def acceso_denegado():
    """
    Secuencia de acceso denegado (no bloqueante).
      - LED rojo ON → 2s → OFF
      - Solenoide NO se activa
    """
    def _secuencia():
        print("[GPIO] Acceso denegado")
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