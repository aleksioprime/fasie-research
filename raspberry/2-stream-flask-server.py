# Импортирование необходимых библиотек для технического зрения
from flask import Flask, render_template, Response
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
from datetime import datetime

# Создание экземпляра приложения Flask с именем app
app = Flask(__name__)

def generate_frames():
    # Счётчик количества кадров
    count_frames = 0
    # Счётчик количества кадров
    time_now = datetime.now()
    # Переменная для вывода кол-во кадров в секунду
    frame_rate = 0
    # Цикл получения и обработки кадров потока
    while True:
        # Получение набора кадров с потока
        frames = pipeline.wait_for_frames()
        # Выравнивание набора кадров
        aligned_frames = align.process(frames)
        # Получение двух выровненных кадров по отдельности
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        # Если какого-то кадра не получено, то пропуск итерации цикла
        if not depth_frame or not color_frame:
            continue
        # Конвертирование кадров в массив изображения numpy
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        # Применение цветовой карты к изображению глубины  
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        color_image[:, color_image.shape[1]//2:] = depth_colormap[:, depth_colormap.shape[1]//2:]
        
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
        
        # Конвертирование массива в формат потоковых данных и назначение в кэше памяти
        ret, buffer = cv2.imencode('.jpg', color_image)
        frame = buffer.tobytes()
        # Продолжение генерирования фрейма, пока он существует
        yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# функция на запрос маршрута '/' возвращает web-страницу по шаблону
@app.route('/')
def index():
    return render_template('index.html')

# функция на запрос маршрута '/video' возвращает потоковую передачу изображений
@app.route('/video')
def video():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    # Создание и конфигурирование потока данных с rgb-кадрами
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 424, 240, rs.format.z16, 30)
    # config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)
    # config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
    # config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    # config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    # Старт потока данных с заданной конфигурацией
    pipeline.start(config)
    # Создание объекта выравнивания по rgb-видеопотоку
    align = rs.align(rs.stream.color)
    # Запуск web-приложения по ip-адресу самого устройства и порту 5000
    app.run(host='0.0.0.0', debug=False)
