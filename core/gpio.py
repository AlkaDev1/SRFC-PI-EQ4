"""
core/gpio.py
Control de GPIO para el sistema de acceso biométrico.

Componentes según especificación del equipo:
  Solenoide  (IN1 relé)      → GPIO 17  (PIN 11)
  Actuador sale (IN2 relé)   → GPIO 27  (PIN 13)
  Actuador entra (IN3 relé)  → GPIO 22  (PIN 15)
  LED RGB Rojo               → GPIO 18  (PIN 12)
  LED RGB Verde              → GPIO 23  (PIN 16)
  Buzzer                     → GPIO 25  (PIN 22)

En entorno de desarrollo (laptop) simula las llamadas sin error.
"""

import platform
import threading

# ── Detectar si estamos en Raspberry Pi ───────────────────────────────────────
_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

# ── Pines BCM ─────────────────────────────────────────────────────────────────
PIN_SOLENOIDE      = 17   # IN1 — abre la puerta
PIN_ACTUADOR_SALE  = 27   # IN2 — actuador lineal sale
PIN_ACTUADOR_ENTRA = 22   # IN3 — actuador lineal entra
PIN_LED_R          = 18   # LED RGB rojo
PIN_LED_V          = 23   # LED RGB verde
PIN_BUZZER         = 25   # Buzzer

# ── Setup ─────────────────────────────────────────────────────────────────────
if _ES_RASPBERRY:
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_SOLENOIDE,      GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_ACTUADOR_SALE,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_ACTUADOR_ENTRA, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_R,          GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_LED_V,          GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_BUZZER,         GPIO.OUT, initial=GPIO.LOW)
        _GPIO_OK = True
        print("[GPIO] Inicializado correctamente")
    except Exception as e:
        print(f"[GPIO] Error al inicializar: {e}")
        _GPIO_OK = False
else:
    _GPIO_OK = False
    print("[GPIO] Modo simulación (no es Raspberry Pi)")


# ── Helpers internos ──────────────────────────────────────────────────────────
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


# ── API pública ───────────────────────────────────────────────────────────────
def acceso_concedido():
    """
    Acceso OK:
      - LED verde 3 segundos
      - 2 beeps cortos
      - Solenoide abre 0.5s
      - Actuador sale 2s → pausa → actuador entra 2s
    """
    def _secuencia():
        import time

        # LED verde + beeps
        _set(PIN_LED_V, True)
        _set(PIN_LED_R, False)
        _beep(frecuencia_ms=100, repeticiones=2, pausa_ms=80)

        # Solenoide abre
        _set(PIN_SOLENOIDE, True)
        time.sleep(0.5)

        # Actuador sale
        _set(PIN_ACTUADOR_SALE, True)
        time.sleep(2.0)
        _set(PIN_ACTUADOR_SALE, False)

        # Puerta abierta
        time.sleep(2.5)

        # Actuador entra
        _set(PIN_ACTUADOR_ENTRA, True)
        time.sleep(2.0)
        _set(PIN_ACTUADOR_ENTRA, False)

        # Solenoide cierra
        _set(PIN_SOLENOIDE, False)

        # LED verde apaga
        _set(PIN_LED_V, False)

    threading.Thread(target=_secuencia, daemon=True).start()


def acceso_denegado():
    """
    Acceso DENEGADO:
      - LED rojo 2 segundos
      - 3 beeps largos de alerta
      - Solenoide NO se activa
    """
    _pulso(PIN_LED_R, 2.0)
    _beep(frecuencia_ms=300, repeticiones=3, pausa_ms=100)


def apagar_todo():
    """Apaga todos los pines. Llamar al cerrar la app."""
    for pin in (PIN_SOLENOIDE, PIN_ACTUADOR_SALE, PIN_ACTUADOR_ENTRA,
                PIN_LED_R, PIN_LED_V, PIN_BUZZER):
        _set(pin, False)
    if _ES_RASPBERRY and _GPIO_OK:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            print("[GPIO] Cleanup realizado")
        except Exception:
            pass