# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, Motor, Servo
from datetime import datetime
import time

# Настройка параметров подключения драйвера тягового мотора и сервопривода
Device.pin_factory = PiGPIOFactory('127.0.0.1')
motor = Motor(23,24,25,pwm=True)
servo = Servo(17)
# Выставление среднего положения сервопривода и пауза в 1 секунду
servo.mid()
time.sleep(1)

# Функция коррекции для поворота сервопривода
def correct_turn(value, minn, maxx):
    if value != 0:
        value = value * 1/100
    if value > minn or value < -minn:
        if value >= maxx:
            return maxx
        elif value <= -maxx:
            return -maxx
        else:
            return value
    else:
        return 0

# Конфигурирование rgb и depth потоков
pipeline = rs.pipeline()
config = rs.config()
# config.enable_stream(rs.stream.depth, 424, 240, rs.format.z16, 30)
# config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)
# Старт потока с заданной конфигурацией
profile = pipeline.start(config)
# Создание объекта выравнивания по rgb-видеопотоку
align = rs.align(rs.stream.color)

# Определение координат полигона области интереса
X_MID = 250 * 2
Y_MIN = 200 * 2
Y_MAX = 220 * 2
# roi_poligon = np.array([[(X_MID-110, Y_MAX), (X_MID+115, Y_MAX), (X_MID+65, Y_MIN), (X_MID-85, Y_MIN)]])
roi_poligon = np.array([[(X_MID-230, Y_MAX), (X_MID+230, Y_MAX), (X_MID+170, Y_MIN), (X_MID-190, Y_MIN)]])

# функция получения координат усреднённых линий разметки
def make_points(line):
    slope, intercept = line
    y1 = Y_MAX
    y2 = Y_MIN
    x1 = int((y1 - intercept)/slope)
    x2 = int((y2 - intercept)/slope)
    return [[x1, y1, x2, y2]]

# функция получения усреднённых значений угловых коэффициентов 
# и свободных членов уравнения прямой, возвравщение координат левой и правой линий разметки
def average_slope_intercept(lines):
    left_fit = []
    right_fit = []
    if lines is None:
        return None
    # Цикл по обнаруженным линиям
    for line in lines:
        for x1, y1, x2, y2 in line:
            # Получение из координат каждого отрезка коэффициентов уравнения прямой
            fit = np.polyfit((x1,x2), (y1,y2), 1)
            slope = fit[0]
            intercept = fit[1]
            # if slope > 0.001 and slope < 1 or slope < -0.001 and slope > -1:
            if slope < 0: 
                left_fit.append((slope, intercept))
            else:
                right_fit.append((slope, intercept))
    # Если обнаружены линии левых и правых линий разметки, 
    # то вычисляются средние коэффициенты уравнения этих прямых 
    # и координаты усреднённых отрезков, иначе возвращается None
    if len(left_fit) and len(right_fit):
        left_fit_average  = np.average(left_fit, axis=0)
        left_line  = make_points(left_fit_average)
        right_fit_average = np.average(right_fit, axis=0)
        right_line = make_points(right_fit_average)
        return [left_line, right_line]
    else:
        return None

# функция определения краёв объектов в кадре
def edge_detector(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edge = cv2.Canny(blur, 100, 200)
    return edge

# функция выделения линий в кадре и формирование отдельного изображения с ними
def display_lines(image, lines):
    line_image = np.zeros_like(image)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image,(x1,y1),(x2,y2),(0,255,255),5)
    return line_image

# функция получения области интереса кадра по координатам полигона
def region_of_interest(image, polygon):
    mask = np.zeros_like(image)
    cv2.fillPoly(mask, polygon, 255)
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image

# функция получения x-координат линий
def get_x_lines(lines):
    x_lns = []
    for line in lines:
        for x1, _, x2, _ in line:
            x_lns.append(int((x1 + x2)/2))
    return x_lns

# time_now = datetime.now()
print("[INFO] Start")

# Работа цикла с заданным временем по таймеру
while True:
    # Получение набора кадров с rgb и depth потоков
    frames = pipeline.wait_for_frames()
    # Выравнивание набора кадров
    aligned_frames = align.process(frames)
    # Получение двух выровненных кадров по отдельности
    depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    # Если какого-то кадра не получено, то пропуск итерации цикла
    if not depth_frame or not color_frame:
        continue
    # Конвертирование кадра в массив изображения numpy
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    
    # Получение изображения с выделенными краями объектов в кадре
    edge_image = edge_detector(color_image)
    # Получение области интереса из кадра с выделенными краями объектов
    roi_image = region_of_interest(edge_image, roi_poligon)
    # Обнаружение линий в области интереса 
    lines = cv2.HoughLinesP(roi_image, 4, np.pi/180, 20,
                            np.array([]), minLineLength=3, maxLineGap=10)
    
    # Получение усреднённых вертикальных наклонных линий 
    averaged_lines = average_slope_intercept(lines)
    # Если усреднённые линии не вычислены, то платформа едет прямо (или останавливается)
    if averaged_lines is not None:
        # выделение в кадре усреднённых линий полосы разметки
        line_image = display_lines(color_image, averaged_lines)
        color_image = cv2.addWeighted(color_image, 0.8, line_image, 1, 1)
        # Получение x-координат усреднённый левой и правой линии разметки
        x_lines = get_x_lines(averaged_lines)

        xl_left, xl_right = x_lines
        # Вычисление средней x-координаты
        x_avr = int((xl_left + xl_right) / 2)
        # Вычисление ошибки отклонения от центральной линии кадра области интереса
        x_error = x_avr - X_MID
        # Коррекция поворота сервопривода на величину ошибки отклонения от линии
        servo.value = correct_turn(x_error, 0, 0.7)

        # вывод вычисляемых спомогательных линий и текста на кадр
        y_avr = (Y_MAX-Y_MIN)//2 + Y_MIN
        cv2.line(color_image,(x_avr,Y_MAX-30),(x_avr,Y_MIN+30),(0,255,255),3)
        if x_avr < X_MID:
            cv2.line(color_image,(x_avr,y_avr),(X_MID,y_avr),(0,255,0),3)
            cv2.putText(color_image, "{}".format(abs(x_error)), (x_avr, Y_MIN-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.line(color_image,(X_MID,y_avr),(x_avr,y_avr),(0,0,255),3)
            cv2.putText(color_image, "{}".format(abs(x_error)), (x_avr, Y_MIN-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    else:
        cv2.putText(color_image, "[STOP] - No data", (5, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 100), 2)
        servo.value = 0

    # вывод на кадр обводку полигона области интереса
    cv2.polylines(color_image, [roi_poligon], True, (255, 0, 0), 2)
    cv2.line(color_image,(X_MID,Y_MAX),(X_MID,Y_MIN),(255, 0, 0), 2)

    # вывод кадра
    cv2.imshow('RealSense', color_image)
    
    if cv2.waitKey(1) == ord(' '):
        break
        
# Закрытие всех окон программы
cv2.destroyAllWindows()
# Остановка потока данных с камеры
pipeline.stop()