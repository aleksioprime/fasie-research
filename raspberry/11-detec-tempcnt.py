# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
from datetime import datetime
from imutils import paths

# множитель разрешения для отступов
fres = 2
# Создание переменных разрешения кадра
# width_stream, height_stream = (424, 240)
width_stream, height_stream = (848, 480)
# width_stream, height_stream = (1280, 720)

# Создание и конфигурирование потока данных с rgb-кадрами
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, width_stream, height_stream, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, width_stream, height_stream, rs.format.z16, 30)

# Старт потока данных с заданной конфигурацией
pipeline.start(config)
# Создание объекта выравнивания по rgb-видеопотоку
align = rs.align(rs.stream.color)

# Координаты точки прямоугольника области интереса
cut_startx, cut_endx = width_stream - width_stream // 3, width_stream
cut_starty, cut_endy = height_stream // 7, height_stream // 2

# Подготовка шаблонов контуров для детектирования
image_paths = list(paths.list_images("research/forms"))
templates = []
for (i, image_path) in enumerate(image_paths):
    img_template = cv2.imread(image_path, 0)
    ret, img_thresh = cv2.threshold(img_template, 127, 255, 0)
    contours_temp, _ = cv2.findContours(img_thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contour_temp = sorted(contours_temp, key=cv2.contourArea, reverse=True)[1]
    templates.append(contour_temp)

# Функция поиска контура по шаблону, отношения длины и ширины описывающего прямоугольника и его площади
def find_template(contours, temp):
    for c in contours:
        peri = cv2.arcLength(c, True)
        c = cv2.approxPolyDP(c, 0.04 * peri, True)
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        for t in temp:
            match = cv2.matchShapes(t, c, 2, 0)
            if match < 0.3 and (area > 3500 and area < 9000) and (w / h < 1.3 and w / h > 0.7):
                return c, t
        return None, None

# Функция определения краёв объектов в кадре
def edge_detector(image):
    # kernel = np.ones((5, 5), 'uint8')
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # img = cv2.erode(img, kernel, iterations=1)
    canny = cv2.Canny(gray, 100, 250, apertureSize = 5)
    return canny

# Начальные значения счётчиков и таймера
count_detected = 0
count_frames = 0
time_now = datetime.now()

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
    # Извлечение области интереса из кадра
    cut_image = color_image[cut_starty:cut_endy, cut_startx:cut_endx]
    cut_image_test = cut_image.copy()
    # Получение изображения с выделенными краями объектов в кадре
    edged_image = edge_detector(cut_image)
    # Извлечение контуров из кадра с выделенными границами и рисование в кадре всех контуров
    contours, _ = cv2.findContours(edged_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(cut_image, contours, -1, (255,0,0), 1)
    # Сортировка массива с координатами контуров по убыванию
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    # Выборка контуров заданных параметров
    cnt, tmp = find_template(sorted_contours, templates)  
    if cnt is not None:
        cv2.drawContours(cut_image_test, [cnt], -1, (0,0,255), 2)
        cv2.drawContours(cut_image_test, [tmp], -1, (0,255,255), 2)
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        cv2.rectangle(color_image, (x + cut_startx, y + cut_starty), (x + cut_startx + w, y + cut_starty + h), (0, 0, 255), 3)
        cv2.putText(color_image, "DETECTED", (cut_startx, cut_starty-5*fres),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)   
        cv2.putText(color_image, "Area: {}".format(area), (cut_startx, cut_endy+8*fres),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        # Увеличение счётчика кадров с детектированием знака
        count_detected += 1
   
    # Наложение на кадр фрагмента с обведёнными контурами и обводка самого фрагмента
    color_image[cut_starty:cut_endy, cut_startx:cut_endx] = cut_image
    cv2.rectangle(color_image, (cut_startx, cut_starty), (cut_endx, cut_endy), (255, 0, 255), 3)

    # Увеличение счётчика сгенерированных кадров
    count_frames += 1
    # Вычисление разницы между временем старта и текущим временем 
    delta_time = abs(datetime.now() - time_now).seconds
    # Наложение на изображение количества прошедших секунд
    cv2.putText(color_image, "{}/20 sec".format(delta_time), (2*fres, 14*fres),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Формирование составного кадра и вывод на экран
    edged_image = np.dstack((edged_image, edged_image, edged_image))
    test_image = np.hstack((edged_image, cut_image_test))
    test_height = int(width_stream * test_image.shape[0] / test_image.shape[1])
    test_image = cv2.resize(test_image, (width_stream, test_height))
    cv2.imshow('RealSense', np.vstack((color_image, test_image)))
    # Вывод numpy-массив изображения на рабочий стол
    # cv2.imshow('RealSense', color_image)
    # Выход из цикла при нажатии на клавишу "Пробел" или по истечению заданного временм delta_time
    if cv2.waitKey(1) == ord(' ') or delta_time == 20:
        print("Detection accuracy:", round(count_detected / count_frames, 3))
        break

# Закрытие всех окон программы
cv2.destroyAllWindows()
# Остановка потока данных
pipeline.stop()
