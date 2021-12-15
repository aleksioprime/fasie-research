# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2

# Создание и конфигурирование потока данных с rgb-кадрами
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)

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
    # Вывод numpy-массив изображения на рабочий стол
    cv2.imshow('RealSense', color_image)
    # Выход из цикла при нажатии на клавишу "Пробел"
    if cv2.waitKey(1) == ord(' '):
        break

# Закрытие всех окон программы
cv2.destroyAllWindows()
# Остановка потока данных
pipeline.stop()
