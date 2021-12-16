# Импортирование необходимых библиотек
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, Motor, Servo
import time

# Настройка параметров подключения драйвера тягового мотора и сервопривода
Device.pin_factory = PiGPIOFactory('127.0.0.1')
motor = Motor(23,24,25,pwm=True)
servo = Servo(17)
# Выставление среднего положения сервопривода и пауза в 1 секунду
servo.mid()
time.sleep(1)

# Последовательные команды движения моторами
print("[INFO] Start")
print("[DRIVE] Forward")
motor.forward(speed=0.5)
time.sleep(1)
print("[DRIVE] Forward - Left")
servo.value = -1
time.sleep(1)
print("[DRIVE] Stop")
motor.stop()
time.sleep(0.5)
print("[DRIVE] Backward - Right")
servo.value = 1
motor.backward(speed=0.5)
time.sleep(2)
print("[DRIVE] Stop")
motor.stop()
time.sleep(0.5)
print("[DRIVE] Forward - Left")
servo.value = -1
motor.forward(speed=0.5)
time.sleep(1)
print("[DRIVE] Forward")
servo.value = 0
motor.forward(speed=0.5)
time.sleep(1)
motor.stop()

print("[INFO] Finish")