from gpiozero import PWMLED, PWMOutputDevice
from time import sleep

rojo   = PWMLED(18)
verde  = PWMLED(12)
buzzer = PWMOutputDevice(17)

while True:
    # Rojo
    rojo.on(); verde.off()
    buzzer.frequency = 440; buzzer.value = 0.5
    sleep(1)

    # Verde
    rojo.off(); verde.on()
    buzzer.frequency = 660; buzzer.value = 0.5
    sleep(1)

    # Amarillo
    rojo.on(); verde.on()
    buzzer.frequency = 880; buzzer.value = 0.5
    sleep(1)

    buzzer.value = 0
    sleep(0.2)