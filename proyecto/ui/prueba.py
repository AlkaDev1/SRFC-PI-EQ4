from gpiozero import OutputDevice
import time

solenoide      = OutputDevice(17, initial_value=True, active_high=False)
actuador_sale  = OutputDevice(27, initial_value=True, active_high=False)
actuador_entra = OutputDevice(22, initial_value=True, active_high=False)
led_rojo       = OutputDevice(18, initial_value=True, active_high=False)
led_verde      = OutputDevice(23, initial_value=True, active_high=False)

print("=== TEST GPIO ===")

print("LED VERDE — 2s")
led_verde.on()
time.sleep(2)
led_verde.off()
time.sleep(0.5)

print("LED ROJO — 2s")
led_rojo.on()
time.sleep(2)
led_rojo.off()
time.sleep(0.5)

print("SOLENOIDE — 1s")
solenoide.on()
time.sleep(1)
solenoide.off()
time.sleep(0.5)

print("ACTUADOR SALE — 2s")
actuador_sale.on()
time.sleep(2)
actuador_sale.off()
time.sleep(0.5)

print("ACTUADOR ENTRA — 2s")
actuador_entra.on()
time.sleep(2)
actuador_entra.off()

print("=== FIN ===")