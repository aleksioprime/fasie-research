# Импортирование необходимых библиотек
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, Motor, Servo
import time
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
import socket, pickle, struct

# Создание сокета
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# Привязка сокета к ip-адресу и порту и его прослушка
server_socket.bind(('0.0.0.0',9999))
server_socket.listen(5)
print("INFO: Waiting connect")

# Настройка параметров подключения драйвера тягового мотора и сервопривода
Device.pin_factory = PiGPIOFactory('127.0.0.1')
motor = Motor(23,24,25,pwm=True)
servo = Servo(17)
# Выставление среднего положения сервопривода и пауза в 1 секунду
servo.mid()
time.sleep(1)

# Конфигурирование rgb и depth потоков
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 424, 240, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 30)
# config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
# config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)

while True:
    # Ожидание подключения к сокету
    client_socket,addr = server_socket.accept()
    print('INFO: Connection', addr)

    # старт потока с заданной конфигурацией
    profile = pipeline.start(config)
    # Настройка шкалы глубин и установка границы дальности области интереса
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    end_dist = 0.4 / depth_scale # 40 сантиметров
    # Создание объекта выравнивания по rgb-видеопотоку
    align = rs.align(rs.stream.color)
    # задание начальной и конечной координаты прямоугольника области интереса
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = (130, 160, 400, 220)
    # xmin_roi, ymin_roi, xmax_roi, ymax_roi = (200, 320, 600, 420)
    
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

        # извлечение из кадра карты глубины региона области интереса
        depth_cut = depth_image[ymin_roi:ymax_roi, xmin_roi:xmax_roi]
        # замена на ноль тех значений карты глубины, которые дальше границы дальности области интереса
        depth_removed = np.where((depth_cut > end_dist), 0, depth_cut)
        # вычисление значение дальности пикселей области интереса в соответствии со шкалой
        depth = depth_removed * depth_scale
        # вычисление среднего значения дальности пикселей области интереса
        mean_dist,_,_,_ = cv2.mean(depth)
        # перевод numpy-массива области интереса из 1-канального в 3-канальный и наложение на rgb-кадр
        color_image[ymin_roi:ymax_roi, xmin_roi:xmax_roi] = np.dstack((depth_removed, depth_removed, depth_removed))
        
        # вывод на кадры границу области интереса и значение средней дальности её карты глубин 
        cv2.rectangle(color_image, (xmin_roi, ymin_roi),
                    (xmax_roi, ymax_roi), (255, 255, 255), 2)
        cv2.putText(color_image, "ROI mean distance: {:.3f}".format(mean_dist), (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1) 
        
        # выполнение действий при определённо значении средней дальности карты глубин области интереса
        if mean_dist <= 0.03:
            cv2.putText(color_image, "Drive Forward", (xmin_roi, ymin_roi-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) 
        else:
            cv2.putText(color_image, "Drive Stop", (xmin_roi, ymin_roi-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2) 
        
        # Создание байтового представления данных изображения
        byte_image = pickle.dumps(color_image)
        # упаковывание данных изображения в строковое представление указанного типа
        message_image = struct.pack("Q", len(byte_image)) + byte_image
        try:
            # отправка сообщения всем подключённым клиентам
            client_socket.sendall(message_image)
        except:
            print("INFO: Close stream", addr)
            client_socket.close()
            print("INFO: Waiting connect")
            # Остановка потока данных
            pipeline.stop()
            break