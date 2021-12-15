# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
import socket, pickle, struct
from datetime import datetime

# Создание сокета
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# Привязка к сокету и его прослушка
server_socket.bind(('0.0.0.0',9999))
server_socket.listen(5)
print("INFO: waiting connect")

# Создание и конфигурирование потока данных с rgb-кадрами
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)

while True:
    # Ожидание подключения к сокету
    client_socket,addr = server_socket.accept()
    print('INFO: connection', addr)
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
        cv2.putText(color_image, datetime.now().strftime("%H:%M:%S:%f"), (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # Создание байтового представление данных изображения
        byte_image = pickle.dumps(color_image)
        # упаковывание данных изображения в строковое представление указанного типа
        message_image = struct.pack("Q", len(byte_image)) + byte_image
        try:
            # отправка сообщения всем подключённым клиентам
            client_socket.sendall(message_image)
        except:
            print("INFO: close stream", addr)
            client_socket.close()
            print("INFO: waiting connect")
            # Остановка потока данных
            pipeline.stop()
            break
