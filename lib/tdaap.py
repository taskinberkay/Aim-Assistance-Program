import win32api
import win32con
import os
import sys
import time
import mss
import torch
import numpy as np
import ctypes
import cv2
import json
import math
from termcolor import colored

class Bot:
    # Ekran görüntülerini alacak mss objesini oluştur.
    screenshot_window = mss.mss()  #Screenshotları alacak mss objesinin oluşturulması.
    # config dosyasını yükle.
    with open("lib/conf/config.json") as f:
        sensitivity_config = json.load(f)
    auto_aim_status = colored("OFF", 'red')
    moving_targets_status = colored("DISABLED", 'red')
    player_team = colored(",Terrorist", 'yellow')
    iff_status = colored("OFF", 'red')

    def __init__(self, detection_box_size = 410, debug=False):
        # Algılama çerçevesinin boyutu ayarlanır.
        self.detection_box_size = detection_box_size
        # Nesne tanıma modeli yüklenir.
        self.model = torch.hub.load(
            'ultralytics/yolov5', 'custom', path='lib/best (5).pt', force_reload=True)
        self.screen_width_halved, self.screen_height_halved = ctypes.windll.user32.GetSystemMetrics(0)/2, ctypes.windll.user32.GetSystemMetrics(1)/2
        # CUDA'nın aktif olup olmadığı kontrol edilerek ekrana basılır.
        if torch.cuda.is_available():
            print(colored("CUDA IS ACTIVE", "green"))
        else:
            print(colored("[!]WARNING! CUDA IS NOT ACTIVE", "red"))
            print(colored(
                "[!] Expect low performance", "red"))

        # Modelin confidence ve intersection over union thresholdları belirlenir.
        self.model.conf = 0.45
        self.model.iou = 0.45  # Non-maximum suppression IoU (0-1)
        # Kullanıcıya programın kontrolü için basılması gereken tuşların bilgisi verilir.
        print("\n[INFO] PRESS 'F1' TO TOGGLE AUTO AIM"
              "\n[INFO] PRESS 'F2' TO QUIT PROGRAM"
              "\n[INFO] PRESS 'F3' TO TOGGLE MOVEMENT CORRECTION"
              "\n[INFO] PRESS 'F4' TO CHANGE PLAYER TEAM (DEFAULT IS TERRORIST)"
              "\n[INFO] PRESS 'F5' TO TOGGLE IFF")
    # Otomatik nişan almanın açılıp kapatılması.
    def toggle_autoaim():
        if Bot.auto_aim_status == colored("ON", 'green'):
            Bot.auto_aim_status = colored("OFF", 'red')
        else:
            Bot.auto_aim_status = colored("ON", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] AIMBOT IS [{Bot.auto_aim_status}]", end="\r")
    # Sol click
    def l_click():
        ctypes.windll.user32.mouse_event(0x0002)  # left mouse down
        time.sleep(0.00015)
        ctypes.windll.user32.mouse_event(0x0004)  # left mouse up

    # Otomatik nişan almanın açık olup olmadığını kontrol et.
    def is_autoaim_on():
        if Bot.auto_aim_status == colored("ON", 'green'):
            return True
        else:
            return False

    # Nişangahın hedefin kafa bölgesi üzerinde olup olmadığını kontrol et.
    def is_on_target(self, x, y):
        # Hedef noktasının piksel cinsinden genişliği.
        acceptable_radius = 5
        if self.screen_width_halved - acceptable_radius <= x <= self.screen_width_halved + acceptable_radius:
            if self.screen_height_halved - acceptable_radius <= y <= self.screen_height_halved + acceptable_radius:
                return True
        else:
            return False

    # Fare'yi verilen koordinatlara göre hareket ettir.
    def move_mouse(self, x, y):
        scale = Bot.sensitivity_config["mouse_sens"]
        dx, dy = Bot.calculate_distance_from_crosshair(self, x, y)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

    # Hedefin x ve y eksenlerinde nişangaha olan uzaklığını hesapla.
    def calculate_distance_from_crosshair(self, x, y):
        dx = int(x - self.screen_width_halved)
        dy = int(y - self.screen_height_halved)
        return dx, dy

    # Hareketli hedefler için düzeltme özelliğinin açılıp kapatılması.
    def toggle_moving_targets():
        if Bot.moving_targets_status == colored("ENABLED", 'green'):
            Bot.moving_targets_status = colored("DISABLED", 'red')
        else:
            Bot.moving_targets_status = colored("ENABLED", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] MOVING TARGET TRACKING IS [{Bot.moving_targets_status}]", end="\r")

    # Kullanıcının girmiş olduğu mouse hassasiyetini program denenirken kullanılan hassasiyet değeriyle ölçeklendirilip hareket eden hedefler için düzeltme yap.
    def deviate_to_moving_target(self, deviation, x, y):
        scale = Bot.sensitivity_config["mouse_sens"]
        scaled_deviation = int(deviation * 2.5 / scale * 1.5)
        Bot.move_mouse(self, x + scaled_deviation, y)
        return scaled_deviation

    # Hareketli hedef takibinin açık olup olmadığını kontrol et.
    def is_moving_targets_enabled():
        return True if Bot.moving_targets_status == colored("ENABLED", 'green') else False

    # Oyuncu takımını değiştir.
    def change_player_team():
        if Bot.player_team == colored("Terrorist", 'yellow'):
            Bot.player_team = colored("Counter-Terrorist", 'blue')
        else:
            Bot.player_team = colored("Terrorist", 'yellow')
        sys.stdout.write("\033[K")
        print(f"[!] PLAYER TEAM IS CHANGED TO [{Bot.player_team}]", end="\r")

    # Dost düşman ayırt etmeyi aç/kapa.
    def toggle_iff():
        if Bot.iff_status == colored("ON", 'green'):
            Bot.iff_status = colored("OFF", 'red')
        else:
            Bot.iff_status = colored("ON", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] IFF IS  [{Bot.iff_status}]", end="\r")

    # Dost düşman ayırt etmenin açık olup olmadığını kontrol et.
    def is_iff_on():
        return True if Bot.iff_status == colored("ON", 'green') else False
        sys.stdout.write("\033[K")

    # Mainden çağrılan başlangıç fonksiyonu.
    def start(self):
        print("[INFO] Beginning screen capture")
        detection_box = {'left': int(self.screen_width_halved - self.detection_box_size // 2),  # Algılama yapılacak kutunun sol üst köşesinin x koordinatını hesaplar. X min
                          'top': int(self.screen_height_halved - self.detection_box_size // 2),  # Algılama yapılacak kutunun sol üst köşesinin y koordinatını hesaplar Y min
                          'width': int(self.detection_box_size),  # Kutunun genişliği
                          'height': int(self.detection_box_size)} # Kutunun yüksekliği

        # Hedefin hareketini takip etmek için kullanılan değişkenlerin ilk değerleri verilir.
        last_x = 0
        m_counter = 0
        deviation = 0
        while True:
            time_s = time.perf_counter() # Frame rate hesaplanması için başlangıç süresi tutulur.
            screenshot = np.array(Bot.screenshot_window.grab(detection_box)) # Oluşturulan mss objesiyle verilen çerçevenin ekran görüntüsü alınıp numpy array haline getirilir.
            results = self.model(screenshot) # Görüntü modelden geçirilir.
            least_target_dist = closest_target = False
            if len(results.xyxy[0]) != 0: # Hedef algılandı.
                for *box, conf, cls in results.xyxy[0]: # Algılanan tüm hedefler için tekrar et.
                    x1y1 = [int(x.item()) for x in box[:2]] # Algılanan hedeflerin çerçevelerinin sağ üst köşe koordinatları.
                    x2y2 = [int(x.item()) for x in box[2:]] # Algılanan hedeflerin çerçevelerinin sol alt köşe koordinatları.
                    x1, y1, x2, y2, conf, class_name = *x1y1, *x2y2, conf.item(), results.names[int(cls.item())]
                    height = y2 - y1
                    # Verilen hedef çerçevesinde kafanın vücuda olan oranı kullanılarak kafanın bulunduğu yerin kabaca tahmin edilmesi
                    est_head_coordinates_X, est_head_coordinates_Y = int((x1 + x2)/2), int((y1 + y2)/2 - height/2.5)

                    # Nişangah ile kafa arasındaki mesafenin hesaplanması
                    target_dist = math.dist((est_head_coordinates_X, est_head_coordinates_Y), (self.detection_box_size / 2, self.detection_box_size / 2))

                    if not least_target_dist: least_target_dist = target_dist # En yakın hedefin tespit edilmesi için least_target_dist değişkeninin ilk değerinin verilmesi.

                    if target_dist <= least_target_dist:
                        least_target_dist = target_dist
                        if Bot.is_iff_on(): # Dost düşman ayırımı açık olduğu durumda en yakın hedefi karşı takım olarak tanınan en yakın hedef olarak algıla.
                            if Bot.player_team == colored("Terrorist", 'yellow'):
                                if class_name == "counter":
                                    closest_target = {"x1y1": x1y1, "x2y2": x2y2, "est_head_coordinates_X": est_head_coordinates_X,
                                                         "est_head_coordinates_Y": est_head_coordinates_Y, "conf": conf,
                                                         "class": class_name}
                            elif Bot.player_team == colored("Counter-Terrorist", 'blue'):
                                if class_name == "terrorist":
                                    closest_target = {"x1y1": x1y1, "x2y2": x2y2, "est_head_coordinates_X": est_head_coordinates_X,
                                                         "est_head_coordinates_Y": est_head_coordinates_Y, "conf": conf,
                                                         "class": class_name}
                        else:
                            closest_target = {"x1y1": x1y1, "x2y2": x2y2, "est_head_coordinates_X": est_head_coordinates_X,
                                                 "est_head_coordinates_Y": est_head_coordinates_Y, "conf": conf,
                                                 "class": class_name}
                        cv2.rectangle(screenshot, x1y1, x2y2, (244, 113, 115), 2) # Tanınan tüm hedeflerin etrafına sınırlayıcı çerçeve çiz.
                        # Sınırlayıcı çerçeve üzerine confidence değeri ve tanınan sınıf ismini yazdır.
                        if Bot.is_iff_on():
                            cv2.putText(screenshot, f"{int(conf * 100)}% {class_name}", x1y1, cv2.FONT_HERSHEY_DUPLEX, 0.5,
                                        (244, 113, 116), 2)
                        else:
                            cv2.putText(screenshot, f"{int(conf * 100)}%", x1y1, cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                        (245, 112, 115), 2)

                if closest_target: # Geçerli bir tespit varsa.
                    cv2.circle(screenshot, (closest_target["est_head_coordinates_X"], closest_target["est_head_coordinates_Y"]), 5, (115, 244, 113), -1) # Kafa üzerinde bir yuvarlak oluştur.

                    # Nişangah ile kafa bölgesi arasında bir çizgi oluştur.
                    cv2.line(screenshot, (closest_target["est_head_coordinates_X"], closest_target["est_head_coordinates_Y"]), (self.detection_box_size // 2, self.detection_box_size // 2), (244, 242, 113), 2)
                    # Fare hareketlerinde kullanılacak kafa koordinatlarını ata.
                    head_exact_X, head_exact_Y = detection_box['left'] + closest_target["est_head_coordinates_X"], detection_box['top'] + closest_target["est_head_coordinates_Y"]

                    x1, y1 = closest_target["x1y1"]
                    if Bot.is_on_target(self, head_exact_X, head_exact_Y): # Nişangah hedefin kafa bölgesi üzerine geldiğinde "ON TARGET" mesajını görüntü ekranına bas.
                        Bot.l_click() # Ateş et
                        cv2.putText(screenshot, "ON TARGET", (x1 + 40, y1+40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (116, 245, 114), 2)
                        # Hareketli hedef düzeltmesi yapıldığını varsayarak hareket takibi parametrelerini sıfırla.
                        m_counter = 0
                        deviation = 0
                        last_x = 0
                    else: # Nişangah hedef üzerinde değilse en yakın hedef üzerine "TARGETING" yazısını bastır.
                        cv2.putText(screenshot, "TARGETING", (x1 + 40, y1+40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (116, 114, 245), 2)

                    if Bot.is_autoaim_on(): # Otomatik nişan alma açık ise en yakın hedefin kafa koordinatlarını kullanarak fare hareket metodlarını çağır.
                        if Bot.is_moving_targets_enabled(): # Hareketli hedef takibi açıksa hareket yönünü ve derecesini hesaplayarak sapma fonksiyonlarını çağır.
                            if -20 < head_exact_X - last_x < 20 and not (-1 < head_exact_X - last_x < 1):
                                deviation += head_exact_X - last_x
                                m_counter += 1
                            if m_counter >= 3:
                                scaled_deviation = Bot.deviate_to_moving_target(self, deviation, head_exact_X, head_exact_Y)
                                last_x = head_exact_X - scaled_deviation + deviation
                                deviation = 0
                                m_counter = 0
                                Bot.l_click()

                            else:
                                Bot.move_mouse(self, head_exact_X, head_exact_Y)
                                last_x = head_exact_X
                        else:
                            Bot.move_mouse(self, head_exact_X, head_exact_Y)
            # Başlangıç zamanını kullanarak FPS değerini hesaplayarak görüntü penceresinin sol üst köşesine bastır.
            cv2.putText(screenshot, f"FPS: {int(1/(time.perf_counter() - time_s))}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (114, 115, 245), 2)
            cv2.imshow("Monitor", screenshot)  # Görüntünün basılacağı "Monitör" penceresini başlat.
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break

    def exit_program(): # F2 ye basıldığında çağırılarak programı sonlandırır.
        print("\n[INFO] QUITTING PROGRAM!")
        Bot.screenshot_window.close()
        os._exit(0)
