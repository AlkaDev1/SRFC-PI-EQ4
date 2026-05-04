"""
core/gpio.py
Control de GPIO para el sistema de acceso biométrico.

Componentes:
  - Relé (solenoide)  → GPIO 17
  - LED Verde         → GPIO 22
  - LED Rojo          → GPIO 27
  - Buzzer            → GPIO 24

En entorno de desarrollo (laptop) simula las llamadas sin error.
"""

import platform
import threading

# ── Detectar si estamos en Raspberry Pi ────────────────────────────────────────
_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

# ── Pines ──────────────────────────────────────────────────────────────────────
PIN_RELE   = 17
PIN_LED_V  = 22
PIN_LED_R  = 27
PIN_BUZZER = 24

# ── Setup ──────────────────────────────────────────────────────────────────────
if _ES_RASPBERRY:
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_RELE,   GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_V,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_R,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_BUZZER, GPIO.OUT, initial=GPIO.LOW)
        _GPIO_OK = True
        print("[GPIO] Inicializado correctamente")
    except Exception as e:
        print(f"[GPIO] Error al inicializar: {e}")
        _GPIO_OK = False
else:
    _GPIO_OK = False
    print("[GPIO] Modo simulación (no es Raspberry Pi)")


# ── Helpers internos ───────────────────────────────────────────────────────────
def _set(pin, estado):
    if _ES_RASPBERRY and _GPIO_OK:
        import RPi.GPIO as GPIO
        GPIO.output(pin, GPIO.HIGH if estado else GPIO.LOW)
    else:
        print(f"[GPIO SIM] Pin {pin} → {'HIGH' if estado else 'LOW'}")


def _pulso(pin, duracion):
    """Enciende un pin por `duracion` segundos y lo apaga."""
    _set(pin, True)
    threading.Timer(duracion, lambda: _set(pin, False)).start()


def _beep(frecuencia_ms, repeticiones, pausa_ms):
    """Genera beeps en el buzzer."""
    def _secuencia():
        import time
        for _ in range(repeticiones):
            _set(PIN_BUZZER, True)
            time.sleep(frecuencia_ms / 1000)
            _set(PIN_BUZZER, False)
            time.sleep(pausa_ms / 1000)
    threading.Thread(target=_secuencia, daemon=True).start()


# ── API pública ────────────────────────────────────────────────────────────────
def acceso_concedido():
    """
    Acceso OK:
    - Abre el solenoide por 3 segundos
    - LED verde por 3 segundos
    - 2 beeps cortos agradables
    """
    _pulso(PIN_RELE,  3.0)
    _pulso(PIN_LED_V, 3.0)
    _beep(frecuencia_ms=100, repeticiones=2, pausa_ms=80)


def acceso_denegado():
    """
    Acceso DENEGADO:
    - LED rojo por 2 segundos
    - 3 beeps largos de alerta
    - Solenoide no se activa
    """
    _pulso(PIN_LED_R, 2.0)
    _beep(frecuencia_ms=300, repeticiones=3, pausa_ms=100)


def apagar_todo():
    """Apaga todos los pines. Llamar al cerrar la app."""
    for pin in (PIN_RELE, PIN_LED_V, PIN_LED_R, PIN_BUZZER):
        _set(pin, False)
    if _ES_RASPBERRY and _GPIO_OK:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            print("[GPIO] Cleanup realizado")
        except Exception:
            pass
