# Импортирование необходимых библиотек для технического зрения
from flask import Flask, render_template, Response
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2

# Создание экземпляра приложения Flask с именем app
app = Flask(__name__)

def generate_frames():
    # Цикл получения и обработки кадров потока
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
    config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)
    # Старт потока данных с заданной конфигурацией
    pipeline.start(config)
    # запуск web-приложения по ip-адресу самого устройства и порту 5000
    app.run(host='0.0.0.0', debug=False)
