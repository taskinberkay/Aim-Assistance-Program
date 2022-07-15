from pynput import keyboard
from termcolor import colored
import json
import os
import sys
import threading


def listener_input(key):
    try:
        # F1'e basıldığında otomatik nişan almayı aç
        if key == keyboard.Key.f1:
            Bot.toggle_autoaim()
        # F2'ye basıldığında konsolu temizleyerek programı kapat
        if key == keyboard.Key.f2:
            Bot.exit_program()
        # F3'e basıldığında hareketli hedef düzeltmesini aç
        if key == keyboard.Key.f3:
            Bot.toggle_moving_targets()
        # F4'e basıldığında dost düşman ayırt edilmesi için oyuncu takımını değiştir.
        if key == keyboard.Key.f4:
            Bot.change_player_team()
        # F5'e basıldığında dost düşman ayırt etmeyi çalıştır
        if key == keyboard.Key.f5:
            Bot.toggle_iff()
    except NameError:
        pass

# Bot objesi oluşturup başlatır.
def main():
    global bot
    bot = Bot()
    bot.start()

# Hali hazırda yoksa ve ya program metod çağırılarak çalıştırılırsa kullanıcıdan x, y hassasiyeti ve mouse hassasiyeti girdilerini alarak config dosyası oluşturulur.
def setup():
    path = "lib/conf"
    if not os.path.exists(path):
        os.makedirs(path)

    print("[INFO] X/Y axis sensitivity must be set to same value")
    def grab_setup_input(str):
        is_valid = False
        while not is_valid:
            try:
                val = float(input(str))
                is_valid = True
            except ValueError:
                print("[!] Invalid Input. Enter only one value")
        return val

    axes_sens = grab_setup_input("Enter your X/Y axis sensitivity (Default value is 0.2 for CS:GO if you havent manualy changed it through in game console): ")
    mouse_sens = grab_setup_input("Enter your in game mouse sensitivity: ")
    sensitivity_settings = {"axes_sens": axes_sens, "mouse_sens": mouse_sens}

    with open('lib/conf/config.json', 'w') as outfile:
        json.dump(sensitivity_settings, outfile)
    print("[INFO] Sensitivity configuration has been successfully saved.")

if __name__ == "__main__":
    # Program başlatıldığında konsol temizlenir.
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    # Programın logosu ekrana yazılır.
    print(colored('''
 __     ______  _      ____        _____               
 \ \   / / __ \| |    / __ \      | ____|              
  \ \_/ / |  | | |   | |  | |_   _| |__                
   \   /| |  | | |   | |  | \ \ / /___ \               
    | | | |__| | |___| |__| |\ V / ___) |              
    |_|  \____/|______\____/  \_/ |____/        _____  
              |__   __|  __ \   /\        /\   |  __ \ 
                 | |  | |  | | /  \      /  \  | |__) |
                 | |  | |  | |/ /\ \    / /\ \ |  ___/ 
                 | |  | |__| / ____ \  / ____ \| |     
                 |_|  |_____/_/    \_\/_/    \_\_|     
                 
(Neural Network Target Detection and Aim Assistance Program)''', "cyan"))
    # Config dosyasının olup olmadığı kontrol edilir. Yoksa config oluşturulan setup metodu çağrılır.
    if not os.path.exists("lib/conf/config.json"):
        print("[!] Sensitivity configuration could not be found! Starting configuration...")
        setup()
    if "setup" in sys.argv:
        print("[INFO] Starting sensitivity configuration...")
        setup()
    # Çalıştırılacak olan ana sınıf olan Bot import edilir.
    from lib.tdaap import Bot
    # Kullanıcıdan input almak için beklenir.
    listener = keyboard.Listener(on_release=listener_input)
    listener.start()
    # Aimbot'un çalıştırıldığı main fonksiyonuna gidilir.
    main()
