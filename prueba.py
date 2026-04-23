from gpiozero import PWMLED, ToneBuzzer
from time import sleep

rojo  = PWMLED(18)
verde = PWMLED(12)
buzzer = ToneBuzzer(17)

while True:
    # Rojo
    rojo.on(); verde.off()
    buzzer.play(440)
    sleep(1)

    # Verde
    rojo.off(); verde.on()
    buzzer.play(660)
    sleep(1)

    # Amarillo
    rojo.on(); verde.on()
    buzzer.play(880)
    sleep(1)

    buzzer.stop()
    sleep(0.2)
