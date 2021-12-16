# Импортирование необходимых библиотек
from gpiozero.pins.pigpio import PiGPIOFactory
from bluedot import BlueDot
from gpiozero import Device, Motor, Servo
from signal import pause
import time

# Создание экземпляра объекта связи с android-приложением
bd = BlueDot()

# Настройка параметров подключения драйвера тягового мотора и сервопривода
Device.pin_factory = PiGPIOFactory('127.0.0.1')
motor = Motor(23,24,25,pwm=True)
servo = Servo(17)
# Выставление среднего положения сервопривода и пауза в 1 секунду
servo.mid()
time.sleep(1)

# функция управления движением мобильной платформы 
# по данным от координат касания пальца голубой точки приложения
def move(pos):
    if pos.top:
        print("[DRIVE] - Forward", pos.distance)
        motor.forward(speed=pos.distance)
    elif pos.bottom:
        print("[DRIVE] - Backward", pos.distance)
        motor.backward(speed=pos.distance)
    elif pos.right:
        print("[DRIVE] - Right", pos.distance)
        servo.value = pos.distance
    elif pos.left:
        print("[DRIVE] - Left", pos.distance)
        servo.value = -pos.distance

# фунцкция остановки тяговых моторов и возвращения сенсора в среднее положение
def stop():
    motor.stop()
    servo.value = 0

# вызов функции управления движением платформы при нажатии или перемещения пальца на экране
bd.when_pressed = move
bd.when_moved = move
# вызов функции остановки платформы при отпускании пальца с экрана
bd.when_released = stop

pause()