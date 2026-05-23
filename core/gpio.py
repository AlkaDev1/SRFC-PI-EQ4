"""
core/gpio.py
Control de GPIO para el sistema de acceso biométrico.
Usa gpiozero con relé activo en LOW (active_high=False).

Componentes:
  Solenoide  (IN1 relé)      → GPIO 17  (PIN 11)  ← en producción
  Actuador sale (IN2 relé)   → GPIO 27  (PIN 13)
  Actuador entra (IN3 relé)  → GPIO 22  (PIN 15)
  LED RGB Rojo               → GPIO 18  (PIN 12)
  LED RGB Verde              → GPIO 23  (PIN 16)
  Buzzer                     → GPIO 25  (PIN 22)  ← producción
                               GPIO 17  (PIN 11)  ← pruebas temporales

  BOTÓN COMODÍN:
    - Producción : GPIO físico (definir pin al conectar)
    - Pruebas    : tecla F1 del teclado (manejado desde la UI)

Secuencia acceso concedido:
  1. Buzzer beep doble (concedido)
  2. LED verde ON
  3. Solenoide ON + Actuador sale ON juntos
  4. Solenoide OFF a los 2s
  5. Actuador sale OFF a los 7s
  6. Espera 3s
  7. Actuador entra ON → 7s → OFF
  8. LED verde OFF

Secuencia acceso denegado:
  1. Buzzer beep largo (denegado)
  2. LED rojo ON → 2s → OFF

Secuencia botón comodín (salida):
  1. Buzzer sonido salida (2 cortos + 1 largo)
  2. LED amarillo → simulado (no hay pin físico asignado aún)
  3. Solenoide ON → 2s → OFF  (abre puerta)
  4. Espera PUERTA_ABIERTA_SEGUNDOS
  5. Callback on_fin() → la UI navega a pantalla principal
"""

import platform
import threading
import time

_ES_RASPBERRY = platform.machine() in ("aarch64", "armv7l")

# ── Pines ─────────────────────────────────────────────────────────────────────
_PIN_SOLENOIDE      = 17   # producción (cambiar cuando llegue el solenoide)
_PIN_ACTUADOR_SALE  = 27
_PIN_ACTUADOR_ENTRA = 22
_PIN_LED_ROJO       = 18
_PIN_LED_VERDE      = 23
_PIN_BUZZER         = 17   # ← pruebas (mover a 25 en producción)
_PIN_BTN_COMODIN    = None # ← asignar cuando se conecte el botón físico

# ── Tiempos ───────────────────────────────────────────────────────────────────
_T_SOLENOIDE           = 2.0
_T_ACTUADOR            = 7.0
_T_ESPERA              = 3.0
_T_LED_DENEGADO        = 2.0
PUERTA_ABIERTA_SEGUNDOS = 5.0

# ── Setup gpiozero ────────────────────────────────────────────────────────────
try:
    import os
    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"
    from gpiozero import OutputDevice, Button

    # En pruebas el buzzer ocupa GPIO 17 (mismo que solenoide en producción)
    # Por eso inicializamos solo el buzzer si estamos en modo pruebas sin solenoide
    buzzer         = OutputDevice(_PIN_BUZZER, active_high=True,  initial_value=False)
    actuador_sale  = OutputDevice(_PIN_ACTUADOR_SALE,  active_high=False, initial_value=False)
    actuador_entra = OutputDevice(_PIN_ACTUADOR_ENTRA, active_high=False, initial_value=False)
    led_rojo       = OutputDevice(_PIN_LED_ROJO,  active_high=True, initial_value=False)
    led_verde      = OutputDevice(_PIN_LED_VERDE, active_high=True, initial_value=False)

    # Solenoide: solo inicializar si no comparte pin con el buzzer
    if _PIN_SOLENOIDE != _PIN_BUZZER:
        solenoide = OutputDevice(_PIN_SOLENOIDE, active_high=False, initial_value=False)
    else:
        # Comparte pin con buzzer → solenoide simulado en pruebas
        class _Dummy:
            def on(self):  print("[GPIO SIM] Solenoide ON")
            def off(self): print("[GPIO SIM] Solenoide OFF")
        solenoide = _Dummy()

    # Botón comodín físico (si ya está conectado)
    _btn_comodin_hw = None
    if _PIN_BTN_COMODIN is not None:
        _btn_comodin_hw = Button(_PIN_BTN_COMODIN, pull_up=True)

    _GPIO_OK = True
    print("[GPIO] Inicializado correctamente")

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
    buzzer         = _Dummy()
    _btn_comodin_hw = None


# ── Helpers de buzzer ─────────────────────────────────────────────────────────
def _beep(dur, pausa=0.08):
    buzzer.on()
    time.sleep(dur)
    buzzer.off()
    time.sleep(pausa)

def _sonido_concedido():
    """Dos beeps cortos — acceso concedido."""
    _beep(0.15, 0.08)
    _beep(0.15)

def _sonido_denegado():
    """Un beep largo — acceso denegado."""
    _beep(1.0)

def _sonido_comodin():
    """Dos beeps cortos + uno largo — salida por comodín."""
    _beep(0.1, 0.05)
    _beep(0.1, 0.05)
    _beep(0.3)


# ── API pública ───────────────────────────────────────────────────────────────
def acceso_concedido():
    """Secuencia acceso concedido — no bloqueante."""
    def _secuencia():
        print("[GPIO] >>> Acceso CONCEDIDO")
        _sonido_concedido()
        led_verde.on()

        solenoide.on()
        actuador_sale.on()

        # Solenoide se apaga a los 2s en paralelo
        def _apagar_sol():
            time.sleep(_T_SOLENOIDE)
            solenoide.off()
        threading.Thread(target=_apagar_sol, daemon=True).start()

        time.sleep(_T_ACTUADOR)
        actuador_sale.off()
        print("[GPIO] Puerta abierta")

        time.sleep(_T_ESPERA)

        actuador_entra.on()
        time.sleep(_T_ACTUADOR)
        actuador_entra.off()

        led_verde.off()
        print("[GPIO] Secuencia concedido completa")

    threading.Thread(target=_secuencia, daemon=True).start()


def acceso_denegado():
    """Secuencia acceso denegado — no bloqueante."""
    def _secuencia():
        print("[GPIO] >>> Acceso DENEGADO")
        _sonido_denegado()
        led_rojo.on()
        time.sleep(_T_LED_DENEGADO)
        led_rojo.off()

    threading.Thread(target=_secuencia, daemon=True).start()


def activar_comodin(on_fin=None):
    """
    Secuencia botón comodín — no bloqueante.

    Parámetros:
        on_fin: callable opcional que se llama cuando termina la secuencia.
                La UI lo usa para navegar a pantalla principal.

    Secuencia:
        1. Buzzer sonido comodín
        2. Solenoide ON → PUERTA_ABIERTA_SEGUNDOS → OFF
        3. Llama on_fin() si se proporcionó
    """
    def _secuencia():
        print("[GPIO] >>> Botón COMODÍN activado")
        _sonido_comodin()

        solenoide.on()
        print(f"[GPIO] Solenoide ON → {PUERTA_ABIERTA_SEGUNDOS}s (comodín)")
        time.sleep(PUERTA_ABIERTA_SEGUNDOS)
        solenoide.off()
        print("[GPIO] Solenoide OFF — puerta cerrada")

        if on_fin:
            try:
                on_fin()
            except Exception as e:
                print(f"[GPIO] Error en on_fin: {e}")

    threading.Thread(target=_secuencia, daemon=True).start()


def registrar_btn_comodin_hw(callback):
    """
    Registra el callback para el botón comodín físico.
    Llamar desde la UI una vez que el botón esté conectado.

    Ejemplo:
        from core.gpio import registrar_btn_comodin_hw
        registrar_btn_comodin_hw(lambda: activar_comodin(on_fin=mi_funcion))
    """
    if _btn_comodin_hw is not None:
        _btn_comodin_hw.when_pressed = callback
        print("[GPIO] Botón comodín HW registrado")
    else:
        print("[GPIO] Botón comodín HW no disponible (pin no asignado)")


def apagar_todo():
    """Apaga todos los dispositivos. Llamar al cerrar la app."""
    for device in (solenoide, actuador_sale, actuador_entra,
                   led_rojo, led_verde, buzzer):
        try:
            device.off()
        except Exception:
            pass
    print("[GPIO] Todos los pines apagados")