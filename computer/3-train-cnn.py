from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras import layers, models
from tensorflow import lite
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import os
import time
import cv2

# функция построения модели нейронной сети
def build_model(width, height, depth, classes):
    model = models.Sequential()
    model.add(layers.Conv2D(8, (5, 5), padding='same', input_shape=(height, width, depth)))
    model.add(layers.Activation("relu"))
    model.add(layers.BatchNormalization(axis=-1))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    # CONV => RELU => POOL
    model.add(layers.Conv2D(16, (3, 3), padding='same'))
    model.add(layers.Activation("relu"))
    model.add(layers.BatchNormalization(axis=-1))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    # CONV => RELU => POOL
    model.add(layers.Conv2D(32, (3, 3), padding='same'))
    model.add(layers.Activation("relu"))
    model.add(layers.BatchNormalization(axis=-1))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    # FC => RELU layers
    model.add(layers.Flatten())
    model.add(layers.Dense(128))
    model.add(layers.Activation("relu"))
    model.add(layers.BatchNormalization())
    model.add(layers.Dropout(0.5))
    # Softmax classifier
    model.add(layers.Dense(classes))
    model.add(layers.Activation("softmax"))
    return model


# функция загрузки и преобразования изображений
def dataset_load(im_paths, width, height, verbose):
    data = []
    labels = []
    for (i, im_path) in enumerate(im_paths):
        # загружаем изображение в переменную image
        image = cv2.imread(im_path)
        # определяем класс изображения из строки пути
        # формат пути: ../dataset/{class}/{image}.jpg
        label = im_path.split(os.path.sep)[-2]
        # изменяем размер изображения на заданный (изображение должно быть квадратным)
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        # переводим изображение в массив numpy
        image_array = img_to_array(image, data_format=None)
        # добавляем массив изображения в список data
        data.append(image_array)
        # добавляем в список labels метку соответствующего изображения из списка data
        labels.append(label)
        # выводим на экран количество обработанных изображений в периодичностью verbose
        if verbose > 0 and i > 0 and (i + 1) % verbose == 0:
            print("[INFO] Обработано {}/{}".format(i + 1, len(im_paths)))
    # возвращаем numpy массивы data и labels
    return (np.array(data), np.array(labels))


# указываем название каталога набора данных в папке datasets
dataset_name = "signs"
# задаём размеры изображения
width_image = 64
height_image = 64
# задаём количество эпох для обучения модели
num_epochs = 30
# определяем пути набора данных, сохранения графика обучения и модели нейронной сети keras
dataset_path = os.path.join("C:\datasets", dataset_name)
name_labels = open(os.path.join(dataset_path, "labels.csv")).read().strip().split("\n")
name_labels = [l.split(",")[1] for l in name_labels]
num_classes = len(name_labels)
plot_name = "{}_output/{}_plot.png".format(dataset_name, dataset_name)
weights_name = "{}_output/{}_weights.h5".format(dataset_name, dataset_name)
tflite_name = "{}_output/{}_weights.tflite".format(dataset_name, dataset_name)
# загружаем набор данных с диска, преобразуя изображения в массив
# и масштабируя значения пикселей из диапазона [0, 255] в диапазон [0, 1]
start_time = time.time()
image_paths = list(paths.list_images(dataset_path))
print("[INFO] Загрузка изображений ...")
(data, labels) = dataset_load(image_paths, width=width_image, height=height_image, verbose=500)
data = data.astype("float") / 255.0
# разделяем данные на обучающий и тестовый наборы (75% и 25%)
(trainX, testX, trainY, testY) = train_test_split(data, labels, test_size=0.25, random_state=42)
print("[INFO] Форма матрицы признаков: {}".format(data.shape))
print("[INFO] Размер матрицы признаков: {:.1f}MB".format(data.nbytes / (1024 * 1000.0)))
# преобразуем метки из целых чисел в векторы
trainY = LabelBinarizer().fit_transform(trainY)
testY = LabelBinarizer().fit_transform(testY)
print("[INFO] Время подготовки данных: {} сек".format(round(time.time() - start_time, 2)))
# активация оптимизатора Adam со скоростью обучения learning_rate и распадом decay
opt = Adam(learning_rate=0.01, decay=0.01 / num_epochs)
# сборка и компиляция модели нейронной сети
print("[INFO] Компиляция модели...")
model = build_model(width=width_image, height=height_image, depth=3, classes=num_classes)
print(model.summary())
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=["accuracy"])
# создание функции обратного вызова для сохранения на диск только лучшей модели
# на основе проверки ошибки валидации
checkpoint = ModelCheckpoint(weights_name, monitor="val_loss",
                             mode="min", save_best_only=True, verbose=1)
# настройка метода увеличения выборки данных для обучения через модификацию существующих данных (аугментация)
aug = ImageDataGenerator(rotation_range=20, zoom_range=0.15,
                         width_shift_range=0.2, height_shift_range=0.2,
                         shear_range=0.15, horizontal_flip=True, fill_mode="nearest")
# обучение модели
print("[INFO] Обучение нейронной сети...")
start_time = time.time()
H = model.fit(aug.flow(trainX, trainY, batch_size=32),
              validation_data=(testX, testY), batch_size=64, epochs=num_epochs,
              callbacks=[checkpoint], verbose=0)
print("[INFO] Время обучения: {} сек".format(round(time.time() - start_time, 2)))
# оценка модели нейронной сети
print("[INFO] Оценка нейронной сети...")
predictions = model.predict(testX, batch_size=32)
print(classification_report(testY.argmax(axis=1),
                            predictions.argmax(axis=1),
                            target_names=name_labels))
# построение и сохранение графика потерь и точности тренировок
plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(0, num_epochs), H.history["loss"], label="train_loss")
plt.plot(np.arange(0, num_epochs), H.history["val_loss"], label="val_loss")
plt.plot(np.arange(0, num_epochs), H.history["accuracy"], label="train_acc")
plt.plot(np.arange(0, num_epochs), H.history["val_accuracy"], label="val_acc")
plt.title("Training Loss and Accuracy")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend()
plt.savefig(plot_name)
print("[INFO] Сохранение модели TFLite с квантованием...")
# конвертирование модели keras в квантованную модель tflite
converter = lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [lite.Optimize.DEFAULT]
tflite_model = converter.convert()
# сохранение модели tflite.
with open(tflite_name, 'wb') as f:
    f.write(tflite_model)
