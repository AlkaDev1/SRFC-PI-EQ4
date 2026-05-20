"""
core/gpio.py
Control de GPIO para el sistema de acceso biométrico.
Reescrito para usar gpiozero en lugar de RPi.GPIO.

Componentes según especificación del equipo:
  Solenoide  (IN1 relé)      → GPIO 17  (PIN 11)
  Actuador sale (IN2 relé)   → GPIO 27  (PIN 13)
  Actuador entra (IN3 relé)  → GPIO 22  (PIN 15)
  LED RGB Rojo               → GPIO 18  (PIN 12)
  LED RGB Verde              → GPIO 23  (PIN 16)
  Buzzer                     → GPIO 25  (PIN 22)

En entorno de desarrollo (laptop) gpiozero activa automáticamente
el modo simulación (mock pins) sin necesidad de hardware real.
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

# ── Setup con gpiozero ────────────────────────────────────────────────────────
try:
    from gpiozero import OutputDevice, LED, Buzzer as GZBuzzer
    from gpiozero.pins.mock import MockFactory
    from gpiozero import Device

    # En laptop usamos MockFactory para simular sin errores
    if not _ES_RASPBERRY:
        Device.pin_factory = MockFactory()
        print("[GPIO] Modo simulación (MockFactory de gpiozero)")
    else:
        print("[GPIO] Inicializado en Raspberry Pi con gpiozero")

    solenoide      = OutputDevice(PIN_SOLENOIDE,      initial_value=False)
    actuador_sale  = OutputDevice(PIN_ACTUADOR_SALE,  initial_value=False)
    actuador_entra = OutputDevice(PIN_ACTUADOR_ENTRA, initial_value=False)
    led_rojo       = LED(PIN_LED_R)
    led_verde      = LED(PIN_LED_V)
    buzzer         = GZBuzzer(PIN_BUZZER)

    _GPIO_OK = True

except Exception as e:
    print(f"[GPIO] Error al inicializar gpiozero: {e}")
    _GPIO_OK = False

    # Stubs vacíos para no romper el resto del código
    class _Dummy:
        def on(self): pass
        def off(self): pass
        def beep(self, *a, **kw): pass

    solenoide = actuador_sale = actuador_entra = _Dummy()
    led_rojo  = led_verde = buzzer = _Dummy()


# ── Helpers internos ──────────────────────────────────────────────────────────
def _pulso(device, duracion):
    """Enciende un dispositivo por `duracion` segundos y lo apaga."""
    device.on()
    threading.Timer(duracion, device.off).start()


def _beep(repeticiones, frecuencia_s=0.1, pausa_s=0.08):
    """Genera beeps en el buzzer de forma no bloqueante."""
    def _secuencia():
        import time
        for _ in range(repeticiones):
            buzzer.on()
            time.sleep(frecuencia_s)
            buzzer.off()
            time.sleep(pausa_s)
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

        # LED verde encendido, rojo apagado
        led_verde.on()
        led_rojo.off()
        _beep(repeticiones=2, frecuencia_s=0.1, pausa_s=0.08)

        # Solenoide abre
        solenoide.on()
        time.sleep(0.5)

        # Actuador sale
        actuador_sale.on()
        time.sleep(2.0)
        actuador_sale.off()

        # Puerta abierta — espera
        time.sleep(2.5)

        # Actuador entra
        actuador_entra.on()
        time.sleep(2.0)
        actuador_entra.off()

        # Solenoide cierra
        solenoide.off()

        # LED verde apaga
        led_verde.off()

    threading.Thread(target=_secuencia, daemon=True).start()


def acceso_denegado():
    """
    Acceso DENEGADO:
      - LED rojo 2 segundos
      - 3 beeps largos de alerta
      - Solenoide NO se activa
    """
    _pulso(led_rojo, 2.0)
    _beep(repeticiones=3, frecuencia_s=0.3, pausa_s=0.1)


def apagar_todo():
    """Apaga todos los dispositivos. Llamar al cerrar la app."""
    for device in (solenoide, actuador_sale, actuador_entra,
                   led_rojo, led_verde, buzzer):
        device.off()
    print("[GPIO] Todos los pines apagados")