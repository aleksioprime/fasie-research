# Импортирование необходимых библиотек
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, Motor, Servo
import time
import os
import pygame

# Настройка параметров подключения драйвера тягового мотора и сервопривода
Device.pin_factory = PiGPIOFactory('127.0.0.1')
motor = Motor(23,24,25,pwm=True)
servo = Servo(17)
# Выставление среднего положения сервопривода и пауза в 1 секунду
servo.mid()
time.sleep(1)

# Инициализация экземпляра объекта и виртуального окна pygame
os.environ["DISPLAY"] = ":0"
pygame.init()
pygame.display.init()

# Инициализация подключённого геймпада
controller = pygame.joystick.Joystick(0)
controller.init()

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

print("[INFO] Start")

# Основной цикл программы
run = True
while run:
    # перебор всех событий pygame
    for event in pygame.event.get():
        # если произошло событие изменения оси геймпада, то 
        # выполнять реакции на эти изменения
        if event.type == pygame.JOYAXISMOTION:
            print("Axis:", event.axis, "Value:", event.value)
            if event.axis == 5:
                if event.value >= 0.2:
                    motor_speed = event.value/1.5
                    print("[DRIVE] - Backward", motor_speed)
                    motor.backward(speed=motor_speed)
                else:
                    motor.stop()
            elif event.axis == 4:
                if event.value >= 0.2:
                    motor_speed = event.value/1.5
                    print("[DRIVE] - Forward", motor_speed)
                    motor.forward(speed=motor_speed)
                else:
                    motor.stop()
            elif event.axis == 0 or event.axis == 2:
                motor_value = correct_turn(event.value, 0.2, 0.7)
                print("[DRIVE] - Turn", motor_value)
                servo.value = motor_value
        # если произошло событие нажатия кнопки, то 
        # выполнить реакции на эти нажатия
        elif event.type == pygame.JOYBUTTONDOWN:
            print("Button:", event.button)
            if event.button == 1:
                print("[INFO] Exit")
                run = False