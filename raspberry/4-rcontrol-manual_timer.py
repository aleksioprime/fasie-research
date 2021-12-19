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

# Функция коррекции данных оси геймпада для поворота сервопривода
def correct_turn(value, minn, maxx):
    if value > minn or value < -minn:
        if value >= maxx:
            return maxx
        elif value <= -maxx:
            return -maxx
        else:
            return value
    else:
        return 0

# Установка таймера на 10 секунд и создание первой отметки времени
timer = 10
check_time = time.time()

print("[INFO] Start")
print("[RUN]", timer, "seconds left")

# Работа цикла с заданным временем по таймеру
while timer:
    motor.forward(speed=0.1)
    # motor.forward(speed=0.2)
    # motor.forward(speed=0.3)
    # motor.forward(speed=0.4)
    # motor.forward(speed=0.5)
    # motor.forward(speed=0.6)
    # motor.forward(speed=0.7)
    # motor.forward(speed=0.8)
    # motor.forward(speed=0.9)
    # motor.forward(speed=0.1)
    if time.time() - check_time >= 1:
        check_time = time.time()
        timer -= 1
        print("[RUN]", timer, "seconds left")

# Остановка мотора
servo.mid()
motor.stop()
print("[INFO] Finish")