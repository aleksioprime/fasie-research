from PIL import Image, ImageTk
# sudo apt-get install python3-pil python3-pil.imagetk
import tkinter as tk
import time
import datetime
import cv2
import os
import pyrealsense2.pyrealsense2 as rs
import numpy as np

class Application:
    def __init__(self):
        # создание переменных ширины и высоты кадра
        self.width = 848
        self.height = 480
        # инициализация камеры Intel RealSense
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, 30)
        self.pipeline.start(self.config)
        # создание переменных путей по умолчанию и каталога датасета
        self.dataset_path = "signs"
        self.label_path = "label_test"
        # создание переменных полного и обрезанного кадра
        self.current_full_image = None
        self.current_cut_image = None
        # создание окна Tkinter и его фреймов для вывода кадров
        self.root = tk.Tk()
        self.root.title("Create dataset")
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        self.root.resizable(0, 0)
        self.full_video = tk.Label(self.root)
        self.full_video.grid(row=0, column=0, padx=10, pady=10)
        self.setting_frame = tk.Frame(self.root)
        self.setting_frame.grid(row=0, column=1, padx=10, pady=10)
        self.cut_video = tk.Label(self.setting_frame)
        self.cut_video.grid(row=5, columnspan=2, padx=10, pady=5)
        # создание переменной количества кадров для записи
        self.count_frames = 500
        # создание переменной статуса записи стопкадров
        self.record = False
        # создание переменной счётчика стопкадров
        self.count = 1
        # создание переменной текущего состояния таймера
        self.check_time = time.time()
        # создание переменных для обрезки кадра
        self.crop_size = 200
        self.offset_y = -50
        self.offset_x = 0
        # создание надписи и поля ввода размера кадра для обрезки
        name = tk.Label(self.setting_frame, text="Crop settings")
        name.grid(row=0, columnspan=2, padx=5, pady=5)
        crop_name = tk.Label(self.setting_frame, text="Size:")
        crop_name.grid(row=1, column=0, padx=5, pady=1, sticky="w")
        self.crop_input = tk.Entry(self.setting_frame, width="5")
        self.crop_input.grid(row=1, column=1, padx=5, pady=1, sticky="w")
        self.crop_input.insert(0, self.crop_size)
        # создание надписи и поля ввода смещения по X
        x_name = tk.Label(self.setting_frame, text="Offset X:")
        x_name.grid(row=2, column=0, padx=5, pady=1, sticky="w")
        self.x_input = tk.Entry(self.setting_frame, width="5")
        self.x_input.grid(row=2, column=1, padx=5, pady=1, sticky="w")
        self.x_input.insert(0, self.offset_x)
        # создание надписи и поля ввода смещения по Y
        y_name = tk.Label(self.setting_frame, text="Offset Y:")
        y_name.grid(row=3, column=0, padx=5, pady=1, sticky="w")
        self.y_input = tk.Entry(self.setting_frame, width="5")
        self.y_input.grid(row=3, column=1, padx=5, pady=1, sticky="w")
        self.y_input.insert(0, self.offset_y)
        # создание кнопки применения настроек
        self.button_apply = tk.Button(self.setting_frame, text="Apply", command=self.apply_settings)
        self.button_apply.grid(row=4, columnspan=2, padx=10, pady=5)
        # создание надписи и поля ввода количества стопкадров
        label_count = tk.Label(self.setting_frame, text="Frames:")
        label_count.grid(row=6, column=0, padx=5, pady=1, sticky="w")
        self.count_input = tk.Entry(self.setting_frame, width="5")
        self.count_input.grid(row=6, column=1, padx=5, pady=1, sticky="w")
        self.count_input.insert(0, self.count_frames)
        # создание надписи и поля ввода для имени набора данных
        dataset_name = tk.Label(self.setting_frame, text="Dataset:")
        dataset_name.grid(row=7, column=0, padx=5, pady=1, sticky="w")
        self.dataset_input = tk.Entry(self.setting_frame, width="14")
        self.dataset_input.grid(row=7, column=1, padx=5, pady=1, sticky="w")
        self.dataset_input.insert(0, self.dataset_path)
        # создание надписи и поля ввода для имени класса
        label_name = tk.Label(self.setting_frame, text="Label:")
        label_name.grid(row=8, column=0, padx=5, pady=1, sticky="w")
        self.name_input = tk.Entry(self.setting_frame, width="14")
        self.name_input.grid(row=8, column=1, padx=5, pady=1, sticky="w")
        self.name_input.insert(0, self.label_path)
        # создание кнопки старта записи набора данных
        self.button = tk.Button(self.setting_frame, text="Record", command=self.start_record)
        self.button.grid(row=9, columnspan=2, padx=10, pady=5)
        # вызов функции вывода на экран видеокадров
        self.video_loop()

    def video_loop(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            return
        color_image = np.asanyarray(color_frame.get_data())
        full_image = color_image[:, (self.width - self.height) // 2:(self.width - self.height) // 2 + self.height]
        w_start, w_end, h_start, h_end = self.get_frame_cut(self.crop_size,self.offset_x,self.offset_y)
        cut_image = full_image[h_start:h_end,w_start:w_end]
        self.current_full_image = full_image
        self.current_cut_image = cut_image
        full_cv2image = cv2.cvtColor(full_image, cv2.COLOR_BGR2RGB)
        cut_cv2image = cv2.cvtColor(cut_image, cv2.COLOR_BGR2RGB)
        cv2.putText(full_cv2image, "{}x{}".format(full_cv2image.shape[0], full_cv2image.shape[1]),
                    (10, self.height-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if self.record:
            self.recording(0.1, self.count_frames);
            cv2.putText(full_cv2image, "Record {}/{}".format(self.count, self.count_input.get()), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.rectangle(full_cv2image, (w_start, h_start), (w_end, h_end), (255, 0, 0), 3)
            cv2.putText(full_cv2image, "{}x{}".format(cut_cv2image.shape[0], cut_cv2image.shape[1]),
                    (w_start, h_end+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        else:
            cv2.putText(full_cv2image, "View", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.rectangle(full_cv2image, (w_start, h_start), (w_end, h_end), (0, 0, 255), 3)
            cv2.putText(full_cv2image, "{}x{}".format(cut_cv2image.shape[0], cut_cv2image.shape[1]),
                    (w_start, h_end+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.line(full_cv2image,(w_start,0),(w_start,h_start),(0, 0, 255),1)
            cv2.line(full_cv2image,(0,h_start),(w_start,h_start),(0, 0, 255),1)
            cv2.putText(full_cv2image, "{}".format(h_start),
                    (w_start+5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(full_cv2image, "{}".format(w_start),
                    (0, h_start+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            cv2.line(full_cv2image,(w_end,h_end),(w_end,self.height),(0, 0, 255),1)
            cv2.line(full_cv2image,(w_end,h_end),(self.height,h_end),(0, 0, 255),1)
            cv2.putText(full_cv2image, "{}".format(self.height-h_end),
                    (w_end+5, self.height-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(full_cv2image, "{}".format(self.height-w_end),
                    (self.height-35, h_end+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        full_imgtk = ImageTk.PhotoImage(image=Image.fromarray(full_cv2image))
        resize_cut = cv2.resize(cut_cv2image, (200,200))
        cut_imgtk = ImageTk.PhotoImage(image=Image.fromarray(resize_cut))
        
        self.full_video.imgtk = full_imgtk
        self.full_video.config(image=full_imgtk)
        
        self.cut_video.imgtk = cut_imgtk
        self.cut_video.config(image=cut_imgtk)
        self.root.after(10, self.video_loop)

    def get_frame_cut(self, size, ox, oy):
        x1 = (self.height - size) // 2 + ox
        x2 = x1 + size + ox
        y1 = x1 + oy
        y2 = x2 + oy
        if (0 <= x1 <= self.height) and (0 <= x2 <= self.height) and \
           (0 <= y1 <= self.height) and (0 <= y2 <= self.height):
            return x1, x2, y1, y2
        else:
            return 0, self.height, 0, self.height
    
    def recording(self, m, c):
        if time.time() - self.check_time > m:
            # ts = datetime.datetime.now()
            # filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
            filename = "{}_{}.jpg".format(self.label_path, self.count)
            path = os.path.join(self.dataset_path, self.label_path, filename)
            cv2.imwrite(path, self.current_cut_image)
            print("Запись файла", path)
            self.count += 1
            self.check_time = time.time()
            if self.count > int(c):
                self.record = False
                self.count = 1
                self.button.config(state=tk.NORMAL)

    def start_record(self):
        self.dataset_path = self.dataset_input.get()
        if self.dataset_path:
            if not(os.path.exists(self.dataset_path)):
                os.mkdir(self.dataset_path)
        self.count_frames = self.count_input.get()
        self.check_time = time.time()
        self.record = True
        self.button.config(state=tk.DISABLED)
        self.label_path = os.path.join(self.name_input.get())
        label_path = os.path.join(self.dataset_path, self.label_path)
        if not (os.path.exists(label_path)):
            os.mkdir(label_path)
        else:
            filelist = os.listdir(label_path)
            for file in filelist:
                os.remove(os.path.join(label_path, file))
        print("Label path:", label_path)
                
    def apply_settings(self):
        self.crop_size = int(self.crop_input.get())
        self.offset_y = int(self.y_input.get())
        self.offset_x = int(self.x_input.get())
        
    def destructor(self):
        print("[INFO] closing...")
        self.root.destroy()
        self.pipeline.stop()

print("[INFO] starting...")
pba = Application()
pba.root.mainloop()
