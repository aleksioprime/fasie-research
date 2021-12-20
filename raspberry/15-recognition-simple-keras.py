# Импортирование необходимых библиотек
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from datetime import datetime
from collections import OrderedDict

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
cut_startx, cut_endx = width_stream - width_stream // 5 - 5, width_stream - width_stream // 14 + 10
cut_starty, cut_endy = height_stream // 7, height_stream * 2 // 5 + 10

# загрузка модели нейронной сети и списка меток
# model = load_model('research/models_tm/model.h5')
model = load_model('research/models_cnn/model.h5')
# labels = open("research/models_tm/labels.csv").read().strip().split("\n")
labels = open("research/models_cnn/labels.csv").read().strip().split("\n")
labels = [l.split(",")[1] for l in labels]

# Получение и вывод на экран формы входного слоя модели
_, model_width, model_height, _ = model.get_config()["layers"][0]["config"]["batch_input_shape"]
print("Форма входного слоя модели: {}x{}".format(model_width, model_height))

# Обозначение тестируемого класса
label_test = 2
print("Тестируемый класс:", labels[label_test])

# Начальные значения счётчиков и таймера
count_frames = 0
right_predictions = 0
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
    # Обработка изображения для подачи во входной слой нейронной сети
    image_prediction = cv2.resize(cut_image, (model_width, model_height))
    image_prediction = image_prediction.astype("float32") / 255.0
    image_prediction = np.expand_dims(image_prediction, axis=0)
    # Классификация изображения в нейронной сети
    prediction = model.predict(image_prediction)
    # Запись в переменную максимального значения прогноза классификации
    prob_label = round(prediction.max() * 100, 2)
    # Запись в переменные номера и имени метки класса,
    # имеющего наибольший прогноз классификации
    number_label = prediction.argmax()
    name_label = labels[number_label]

    # Подсчёт количество правильно распознанных классов, 
    # обводка области интереса в кадре, вывод номера метки, 
    # имени и значения вероятности распознанного класса изображений 
    # в зависимости правильно распознавания
    if number_label == label_test:
        right_predictions += 1
        cv2.rectangle(color_image, (cut_startx, cut_starty), (cut_endx, cut_endy), (255, 0, 255), 3)
        cv2.putText(color_image, "{} - {}%".format(number_label, prob_label), (cut_startx, cut_starty-5*fres),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2) 
        cv2.putText(color_image, name_label, (cut_startx, cut_endy+10*fres),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2) 
    else: 
        cv2.rectangle(color_image, (cut_startx, cut_starty), (cut_endx, cut_endy), (255, 0, 255), 3)
        cv2.putText(color_image, "{} - {}%".format(number_label, prob_label), (cut_startx, cut_starty-5*fres),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2) 
        cv2.putText(color_image, name_label, (cut_startx, cut_endy+10*fres),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2) 

    # Запись прогнозов классификатора в словарь с упорядоченными по убыванию значениями
    predlabels = dict()
    for i, l in enumerate(labels):
        predlabels[str(i) + " " + l] = round(prediction[0][i] * 100, 2)
    ordered_predlabels = OrderedDict(sorted(predlabels.items(), key=lambda x: x[1], reverse=True))
    # Вывод на экран всех прогнозов классификатора
    for i, key in enumerate(ordered_predlabels):
        cv2.putText(color_image, "{} - {}%".format(key, ordered_predlabels[key]), (5, 17 + 10*fres * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0), 2) 
    
    # Увеличение счётчика сгенерированных кадров
    count_frames += 1
    # Вычисление разницы между временем старта и текущим временем 
    delta_time = abs(datetime.now() - time_now).seconds
    # Наложение на изображение количества прошедших секунд
    cv2.putText(color_image, "{}/30 sec".format(delta_time), (2*fres, height_stream - 5*fres),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Вывод numpy-массив изображения на рабочий стол
    cv2.imshow('RealSense', color_image)
    # Выход из цикла при нажатии на клавишу "Пробел" или по истечению заданного временм delta_time
    if cv2.waitKey(1) == ord(' ') or delta_time == 30:
        print("FPS:", round(count_frames / delta_time, 2))
        print("Accuracy:", round(right_predictions / count_frames, 2))
        break

# Закрытие всех окон программы
cv2.destroyAllWindows()
# Остановка потока данных
pipeline.stop()
