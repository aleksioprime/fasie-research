# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
import socket, pickle, struct
from datetime import datetime

# Создание сокета
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# Привязка сокета к ip-адресу и порту и его прослушка
server_socket.bind(('0.0.0.0',9999))
server_socket.listen(5)
print("INFO: Waiting connect")

# Создание и конфигурирование потока данных с rgb-кадрами
pipeline = rs.pipeline()
config = rs.config()
# config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 30)
# config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 60)
config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)
# config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 60)
# config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
# config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 60)

# Счётчик количества кадров
count_frames = 0
# Счётчик количества кадров
time_now = datetime.now()
# Переменная для вывода кол-во кадров в секунду
frame_rate = 0

while True:
    # Ожидание подключения к сокету
    client_socket,addr = server_socket.accept()
    print('INFO: Connection', addr)
    # Старт потока данных с заданной конфигурацией
    pipeline.start(config)
    while True:
        # Получение набора кадров с потока
        frames = pipeline.wait_for_frames()
        # Извлечения из набора кадров rgb-кадра
        color_frame = frames.get_color_frame()
        # Если rgb-кадра не получено, то итерация цикла пропускается
        if not color_frame:
            continue
        # Конвертирование rgb-кадра в numpy-массив
        color_image = np.asanyarray(color_frame.get_data())
        
        # Увеличение счётчика количества кадров и его обнудение, если прошло 5 секунд 
        delta_time = abs(datetime.now() - time_now).seconds
        if delta_time >= 5:
            frame_rate = count_frames // delta_time
            count_frames = 0
            time_now = datetime.now()
        else: 
            count_frames += 1
        # Наложение на изображение текущего системного времени
        cv2.putText(color_image, datetime.now().strftime("%H:%M:%S:%f"), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # Наложение на изображение количества кадров (обновляется каждые 5 секунд)
        cv2.putText(color_image, "{} frames".format(count_frames), (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        # Наложение на изображение количества кадров в секунду
        cv2.putText(color_image, "{} fps".format(frame_rate), (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        
        # Создание байтового представление данных изображения
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
