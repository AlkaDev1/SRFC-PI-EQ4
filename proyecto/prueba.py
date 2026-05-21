from gpiozero import OutputDevice
import time

ACT_SALE  = 27  # K2
ACT_ENTRA = 22  # K3

# active_high=False porque los relés activan con LOW
sale  = OutputDevice(ACT_SALE,  active_high=False, initial_value=False)
entra = OutputDevice(ACT_ENTRA, active_high=False, initial_value=False)

def detener():
    sale.off()
    entra.off()

try:
    print("=== PRUEBA ACTUADOR ===")

    print("1. Vástago SALE... (3 segundos)")
    sale.on()
    time.sleep(3)
    detener()
    print("   Detenido")
    time.sleep(2)

    print("2. Vástago ENTRA... (3 segundos)")
    entra.on()
    time.sleep(3)
    detener()
    print("   Detenido")

    print("=== PRUEBA COMPLETADA ===")

except KeyboardInterrupt:
    print("Cancelado")

finally:
    detener()
    sale.close()
    entra.close()