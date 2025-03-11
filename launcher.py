#!/usr/bin/env python3
"""
StarLabs-Monad Launcher

"""

import os
import sys
import platform
import random
import asyncio
import importlib.util
import tkinter as tk
from tkinter import messagebox, ttk
import yaml
import subprocess
import re
from datetime import datetime, timedelta
import signal
import json

def handle_exit(signum, frame):
    """Обработчик сигнала для корректного завершения приложения"""
    print("\nЗавершение работы лаунчера...")
    try:
        if 'root' in globals() and hasattr(globals()['root'], 'quit'):
            globals()['root'].quit()
    except Exception:
        pass
    sys.exit(0)

# Регистрируем обработчик сигнала
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Проверяем наличие необходимых библиотек
try:
    import customtkinter as ctk
except ImportError:
    print("Установка необходимых библиотек...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

# Определяем цветовую схему
COLORS = {
    "bg": "#121212",  # Слегка светлее черного фона
    "frame_bg": "#1e1e1e",  # Слегка светлее фона фрейма
    "accent": "#B8860B",  # Приглушенный золотой/желтый (DarkGoldenrod)
    "text": "#ffffff",  # Белый текст
    "entry_bg": "#1e1e1e",  # Темный фон ввода
    "hover": "#8B6914",  # Более темный приглушенный желтый для наведения
}

class StarLabsLauncher:
    def __init__(self):
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создание главного окна
        self.root = ctk.CTk()
        self.root.title("StarLabs Monad Launcher")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.configure(fg_color=COLORS["bg"])
        
        # Путь к файлу настроек
        self.settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_settings.json")
        
        # Проверка и исправление файла tasks.py
        self.check_tasks_file()
        
        # Загрузка доступных модулей
        self.modules = self.load_available_modules()
        
        # Инициализация настроек рандомизации с дефолтными значениями
        self.init_default_settings()
        
        # Загрузка сохраненных настроек (перезаписывает дефолтные значения)
        self.load_settings()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Обновление интерфейса в соответствии с загруженными настройками
        self.update_ui_from_settings()
        
        # Привязка обработчика закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            if os.path.exists(self.settings_path):
                print(f"Загрузка настроек из {self.settings_path}")
                with open(self.settings_path, "r", encoding="utf-8") as file:
                    settings = json.load(file)
                    
                # Загрузка настроек для начальных модулей
                if "initial" in settings:
                    self.initial_modules = settings["initial"].get("modules", self.initial_modules)
                
                # Загрузка настроек для SWAPS
                if "swaps" in settings:
                    self.swaps_count_min = settings["swaps"].get("min", self.swaps_count_min)
                    self.swaps_count_max = settings["swaps"].get("max", self.swaps_count_max)
                    self.swaps_modules = settings["swaps"].get("modules", self.swaps_modules)
                
                # Загрузка настроек для STAKES
                if "stakes" in settings:
                    self.stakes_count_min = settings["stakes"].get("min", self.stakes_count_min)
                    self.stakes_count_max = settings["stakes"].get("max", self.stakes_count_max)
                    self.stakes_modules = settings["stakes"].get("modules", self.stakes_modules)
                
                # Загрузка настроек для MINT
                if "mint" in settings:
                    self.mint_count_min = settings["mint"].get("min", self.mint_count_min)
                    self.mint_count_max = settings["mint"].get("max", self.mint_count_max)
                    self.mint_modules = settings["mint"].get("modules", self.mint_modules)
                    
                if "games" in settings:
                    self.games_modules = settings["games"].get("modules", self.games_modules)
                
                # Загрузка настроек для OTHER
                if "other" in settings:
                    self.other_probability = settings["other"].get("probability", self.other_probability)
                    self.other_modules = settings["other"].get("modules", self.other_modules)
                
                # Загрузка настроек для collect_all_to_monad
                if "collect" in settings:
                    self.collect_probability = settings["collect"].get("probability", self.collect_probability)
                
                # Загрузка флага для генерации рандомных задач для каждого аккаунта
                self.random_for_each_account = settings.get("random_for_each_account", self.random_for_each_account)
                
                # Загрузка состояния чекбоксов
                self.random_modules_enabled = settings.get("random_modules_enabled", False)
                self.schedule_enabled = settings.get("schedule_enabled", False)
                
                # Загрузка значения часов для расписания
                self.hours_value = settings.get("hours_value", "24")
                
                print("Настройки успешно загружены")
                return True
            else:
                print(f"Файл настроек {self.settings_path} не найден")
                return False
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def save_settings(self):
        """Сохранение настроек в файл"""
        try:
            settings = {
                "initial": {  # Добавляем секцию для начальных модулей
                    "modules": self.initial_modules
                },
                "swaps": {
                    "min": self.swaps_count_min,
                    "max": self.swaps_count_max,
                    "modules": self.swaps_modules
                },
                "stakes": {
                    "min": self.stakes_count_min,
                    "max": self.stakes_count_max,
                    "modules": self.stakes_modules
                },
                "mint": {
                    "min": self.mint_count_min,
                    "max": self.mint_count_max,
                    "modules": self.mint_modules
                },
                "other": {
                    "probability": self.other_probability,
                    "modules": self.other_modules
                },
                
                "games": {
                    "modules": self.games_modules
                },
                "collect": {
                    "probability": self.collect_probability
                },
                "random_for_each_account": self.random_for_each_account,
                "random_modules_enabled": self.random_modules_var.get(),
                "schedule_enabled": self.schedule_var.get(),
                "hours_value": self.hours_entry.get()
            }
            
            with open(self.settings_path, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4)
            
            print("Настройки успешно сохранены")
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {str(e)}")
    
    def update_ui_from_settings(self):
        """Обновление интерфейса в соответствии с загруженными настройками"""
        try:
            # Установка состояния чекбоксов
            self.random_modules_var.set(self.random_modules_enabled)
            self.toggle_random_modules()
            
            self.schedule_var.set(self.schedule_enabled)
            self.toggle_schedule()
            
            # Установка значения часов для расписания
            self.hours_entry.delete(0, "end")
            self.hours_entry.insert(0, self.hours_value)
            
            # Выводим информацию о загруженных настройках
            print(f"Интерфейс обновлен: random_modules={self.random_modules_enabled}, schedule={self.schedule_enabled}")
            
        except Exception as e:
            print(f"Ошибка при обновлении интерфейса: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        self.save_settings()
        self.root.destroy()
    
    def check_tasks_file(self):
        """Проверка и исправление файла tasks.py"""
        try:
            # Путь к файлу tasks.py
            tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.py")
            
            # Проверяем существование файла
            if not os.path.exists(tasks_path):
                print("Предупреждение: Файл tasks.py не найден.")
                return
            
            # Читаем текущее содержимое файла
            with open(tasks_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Проверяем наличие синтаксических ошибок в TASKS
            tasks_pattern = r"TASKS = \[([\s\S]*?)\]"
            tasks_match = re.search(tasks_pattern, content)
            if tasks_match:
                tasks_content = tasks_match.group(1)
                
                # Проверяем наличие лишних запятых
                if ",," in tasks_content:
                    # Исправляем лишние запятые
                    tasks_content = re.sub(r",\s*,", ",", tasks_content)
                    
                    # Заменяем содержимое TASKS
                    new_tasks_content = "TASKS = [" + tasks_content + "]"
                    content = re.sub(tasks_pattern, new_tasks_content, content)
                    
                    # Записываем исправленное содержимое
                    with open(tasks_path, "w", encoding="utf-8") as file:
                        file.write(content)
                    
                    print("Исправлены синтаксические ошибки в файле tasks.py")
        
        except Exception as e:
            print(f"Ошибка при проверке файла tasks.py: {str(e)}")
        
    def load_available_modules(self):
        """Загрузка доступных модулей"""
        modules = {
            "INITIAL": [
                "faucet",     
                "memebridge",
                "dusted"      
            ],
            "SWAPS": [
                "collect_all_to_monad",
                "swaps",
                "bean",
                "ambient",
                "izumi"
            ],
            "STAKES": [
                "apriori",
                "magma",
                "shmonad",
                "kintsu"
            ],
            "MINT": [
                "monadverse",
                "magiceden",
                "accountable",
                "owlto",
                "lilchogstars",
                "demask",
                "monadking",
                "monadking_unlocked"
            ],
            "GAMES": [ 
                "frontrunner"  
            ],
            "OTHER": [
                "logs",
                "nad_domains",
                "aircraft"
            ]
        }
        return modules
        
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Создание фрейма для кнопок
        button_frame = ctk.CTkFrame(self.root, fg_color=COLORS["frame_bg"])
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Кнопка исправления бага с SelectorEventLoop
        self.fix_button = ctk.CTkButton(
            button_frame,
            text="Исправить баг с SelectorEventLoop",
            command=self.fix_selector_event_loop,
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.fix_button.pack(fill="x", padx=10, pady=10)
        
        # Кнопка открытия конфигурации
        self.config_button = ctk.CTkButton(
            button_frame,
            text="Открыть конфигурацию",
            command=self.open_config,
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.config_button.pack(fill="x", padx=10, pady=10)
        
        # Фрейм для настроек запуска
        launch_frame = ctk.CTkFrame(self.root, fg_color=COLORS["frame_bg"])
        launch_frame.pack(fill="x", padx=20, pady=10)
        
        # Чекбокс для рандомных модулей
        self.random_modules_var = ctk.BooleanVar(value=False)
        self.random_modules_check = ctk.CTkCheckBox(
            launch_frame,
            text="Использовать рандомные модули",
            variable=self.random_modules_var,
            font=("Helvetica", 12, "bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            border_color=COLORS["accent"],
            command=self.toggle_random_modules
        )
        self.random_modules_check.pack(anchor="w", padx=10, pady=10)
        
        # Кнопка настройки рандомных модулей
        self.random_settings_button = ctk.CTkButton(
            launch_frame,
            text="Настройка рандомных модулей",
            command=self.open_random_settings,
            font=("Helvetica", 12),
            height=30,
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text"],
            corner_radius=8
        )
        self.random_settings_button.pack(anchor="w", padx=30, pady=5)
        
        # Чекбокс для генерации расписания
        self.schedule_var = ctk.BooleanVar(value=False)
        self.schedule_check = ctk.CTkCheckBox(
            launch_frame,
            text="Сгенерировать расписание",
            variable=self.schedule_var,
            font=("Helvetica", 12, "bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            border_color=COLORS["accent"],
            command=self.toggle_schedule
        )
        self.schedule_check.pack(anchor="w", padx=10, pady=10)
        
        # Фрейм для настройки часов (скрыт по умолчанию)
        self.hours_frame = ctk.CTkFrame(launch_frame, fg_color=COLORS["frame_bg"])
        
        # Метка и поле для ввода часов
        hours_label = ctk.CTkLabel(
            self.hours_frame,
            text="Количество часов:",
            font=("Helvetica", 12),
            text_color=COLORS["text"]
        )
        hours_label.pack(side="left", padx=10)
        
        self.hours_entry = ctk.CTkEntry(
            self.hours_frame,
            width=60,
            font=("Helvetica", 12),
            fg_color=COLORS["entry_bg"],
            text_color=COLORS["text"],
            border_color=COLORS["accent"]
        )
        self.hours_entry.pack(side="left", padx=10)
        self.hours_entry.insert(0, "24")
        
        # Кнопка запуска
        self.launch_button = ctk.CTkButton(
            self.root,
            text="Запустить",
            command=self.launch_app,
            font=("Helvetica", 16, "bold"),
            height=50,
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        self.launch_button.pack(fill="x", padx=20, pady=20)
        
        # Текстовое поле для вывода информации
        self.info_text = ctk.CTkTextbox(
            self.root,
            font=("Consolas", 12),
            fg_color=COLORS["entry_bg"],
            text_color=COLORS["text"],
            border_color=COLORS["accent"],
            wrap="word"
        )
        self.info_text.pack(fill="both", expand=True, padx=20, pady=10)
        self.info_text.insert("1.0", "StarLabs Monad Launcher готов к работе.\n")
        
        # Добавляем контекстное меню для копирования
        self.create_context_menu()
    

    def create_context_menu(self):
        """Создание контекстного меню для текстового поля"""
        if platform.system() == "Windows":
            self.info_text.bind("<Button-3>", self.show_context_menu)
        else:
            self.info_text.bind("<Button-2>", self.show_context_menu)
        
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Выделить всё", command=self.select_all_text)
    
    def show_context_menu(self, event):
        """Показать контекстное меню"""
        self.context_menu.post(event.x_root, event.y_root)

    def copy_text(self):
        """Копировать выделенный текст"""
        try:
            selected_text = self.info_text.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            # Если ничего не выделено
            pass

    def select_all_text(self):
        """Выделить весь текст"""
        self.info_text.tag_add("sel", "1.0", "end")
        return "break"
    
    def init_default_settings(self):
        """Инициализация настроек рандомизации с дефолтными значениями"""
        self.initial_modules = {
            "faucet": True,      # По умолчанию включен
            "memebridge": False,  # По умолчанию выключен
            "dusted": False      # Добавляем новый модуль, по умолчанию выключен
        }
        # Настройки для SWAPS
        self.swaps_count_min = 1
        self.swaps_count_max = 3
        self.swaps_modules = {module: True for module in self.modules.get("SWAPS", []) if module != "collect_all_to_monad"}
        
        # Отдельная настройка для collect_all_to_monad
        if "SWAPS" in self.modules and "collect_all_to_monad" in self.modules["SWAPS"]:
            self.collect_probability = 50
        else:
            self.collect_probability = 0
        
        # Настройки для STAKES
        self.stakes_count_min = 1
        self.stakes_count_max = 3
        self.stakes_modules = {module: True for module in self.modules.get("STAKES", [])}
        
        # Настройки для MINT
        self.mint_count_min = 2
        self.mint_count_max = 4
        self.mint_modules = {module: True for module in self.modules.get("MINT", [])}
        
        self.games_modules = {module: True for module in self.modules.get("GAMES", [])}
        
        # Настройки для OTHER
        self.other_probability = 30
        self.other_modules = {module: True for module in self.modules.get("OTHER", []) if module != "logs"}
        
        # Флаг для генерации рандомных задач для каждого аккаунта
        self.random_for_each_account = True
        
        # Флаги для чекбоксов
        self.random_modules_enabled = False
        self.schedule_enabled = False
        
        # Значение часов для расписания
        self.hours_value = "24"
    
    def toggle_random_modules(self):
        """Переключение видимости настроек рандомных модулей"""
        if self.random_modules_var.get():
            self.random_settings_button.configure(state="normal")
        else:
            self.random_settings_button.configure(state="disabled")
    
    def toggle_schedule(self):
        """Переключение видимости настроек расписания"""
        if self.schedule_var.get():
            self.hours_frame.pack(fill="x", padx=10, pady=10)
        else:
            self.hours_frame.pack_forget()
    
    def open_random_settings(self):
        """Открытие окна настроек рандомизации"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Настройки рандомизации")
        settings_window.geometry("600x700")
        settings_window.minsize(600, 700)
        settings_window.configure(fg_color=COLORS["bg"])
        settings_window.grab_set()  # Делаем окно модальным
        
        # Создаем прокручиваемый фрейм
        scroll_frame = ctk.CTkScrollableFrame(settings_window, fg_color=COLORS["bg"])
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # НОВАЯ СЕКЦИЯ: Начальные модули
        initial_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
        initial_frame.pack(fill="x", padx=10, pady=10)
        
        initial_label = ctk.CTkLabel(
            initial_frame,
            text="Начальные модули:",
            font=("Helvetica", 14, "bold"),
            text_color=COLORS["text"]
        )
        initial_label.pack(anchor="w", padx=10, pady=5)
        
        # Чекбоксы для начальных модулей
        self.initial_vars = {}
        for module in self.modules["INITIAL"]:
            var = ctk.BooleanVar(value=self.initial_modules.get(module, False))
            checkbox = ctk.CTkCheckBox(
                initial_frame,
                text=module,
                variable=var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                fg_color=COLORS["accent"],
                hover_color=COLORS["hover"],
                border_color=COLORS["accent"]
            )
            checkbox.pack(anchor="w", padx=30, pady=2)
            self.initial_vars[module] = var

        # Настройки для SWAPS
        if "SWAPS" in self.modules:
            swaps_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            swaps_frame.pack(fill="x", padx=10, pady=10)
            
            swaps_label = ctk.CTkLabel(
                swaps_frame,
                text="SWAPS (выбрать от-до):",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            swaps_label.pack(anchor="w", padx=10, pady=5)
            
            # Подсчитываем количество доступных модулей SWAPS (без collect_all_to_monad)
            swaps_count = len([module for module in self.modules["SWAPS"] if module != "collect_all_to_monad"])
            
            # Слайдеры для выбора диапазона
            swaps_range_frame = ctk.CTkFrame(swaps_frame, fg_color=COLORS["frame_bg"])
            swaps_range_frame.pack(fill="x", padx=10, pady=5)
            
            swaps_min_label = ctk.CTkLabel(
                swaps_range_frame,
                text="Минимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            swaps_min_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.swaps_min_var = ctk.IntVar(value=self.swaps_count_min)
            swaps_min_slider = ctk.CTkSlider(
                swaps_range_frame,
                from_=0,
                to=swaps_count,
                number_of_steps=swaps_count,
                variable=self.swaps_min_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            swaps_min_slider.pack(side="left", padx=5)
            
            swaps_min_value = ctk.CTkLabel(
                swaps_range_frame,
                textvariable=self.swaps_min_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            swaps_min_value.pack(side="left", padx=5)
            
            swaps_max_label = ctk.CTkLabel(
                swaps_range_frame,
                text="Максимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            swaps_max_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.swaps_max_var = ctk.IntVar(value=self.swaps_count_max)
            swaps_max_slider = ctk.CTkSlider(
                swaps_range_frame,
                from_=0,
                to=swaps_count,
                number_of_steps=swaps_count,
                variable=self.swaps_max_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            swaps_max_slider.pack(side="left", padx=5)
            
            swaps_max_value = ctk.CTkLabel(
                swaps_range_frame,
                textvariable=self.swaps_max_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            swaps_max_value.pack(side="left", padx=5)
            
            # Чекбоксы для модулей
            self.swaps_vars = {}
            for module in self.modules["SWAPS"]:
                if module != "collect_all_to_monad":  # Этот модуль обрабатывается отдельно
                    # Используем текущее значение из класса
                    var = ctk.BooleanVar(value=self.swaps_modules.get(module, True))
                    checkbox = ctk.CTkCheckBox(
                        swaps_frame,
                        text=module,
                        variable=var,
                        font=("Helvetica", 12),
                        text_color=COLORS["text"],
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["hover"],
                        border_color=COLORS["accent"]
                    )
                    checkbox.pack(anchor="w", padx=30, pady=2)
                    self.swaps_vars[module] = var
        
        # Настройки для STAKES
        if "STAKES" in self.modules:
            stakes_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            stakes_frame.pack(fill="x", padx=10, pady=10)
            
            stakes_label = ctk.CTkLabel(
                stakes_frame,
                text="STAKES (выбрать от-до):",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            stakes_label.pack(anchor="w", padx=10, pady=5)
            
            # Подсчитываем количество доступных модулей STAKES
            stakes_count = len(self.modules["STAKES"])
            
            # Слайдеры для выбора диапазона
            stakes_range_frame = ctk.CTkFrame(stakes_frame, fg_color=COLORS["frame_bg"])
            stakes_range_frame.pack(fill="x", padx=10, pady=5)
            
            stakes_min_label = ctk.CTkLabel(
                stakes_range_frame,
                text="Минимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            stakes_min_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.stakes_min_var = ctk.IntVar(value=self.stakes_count_min)
            stakes_min_slider = ctk.CTkSlider(
                stakes_range_frame,
                from_=0,
                to=stakes_count,
                number_of_steps=stakes_count,
                variable=self.stakes_min_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            stakes_min_slider.pack(side="left", padx=5)
            
            stakes_min_value = ctk.CTkLabel(
                stakes_range_frame,
                textvariable=self.stakes_min_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            stakes_min_value.pack(side="left", padx=5)
            
            stakes_max_label = ctk.CTkLabel(
                stakes_range_frame,
                text="Максимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            stakes_max_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.stakes_max_var = ctk.IntVar(value=self.stakes_count_max)
            stakes_max_slider = ctk.CTkSlider(
                stakes_range_frame,
                from_=0,
                to=stakes_count,
                number_of_steps=stakes_count,
                variable=self.stakes_max_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            stakes_max_slider.pack(side="left", padx=5)
            
            stakes_max_value = ctk.CTkLabel(
                stakes_range_frame,
                textvariable=self.stakes_max_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            stakes_max_value.pack(side="left", padx=5)
            
            # Чекбоксы для модулей
            self.stakes_vars = {}
            for module in self.modules["STAKES"]:
                # Используем текущее значение из класса
                var = ctk.BooleanVar(value=self.stakes_modules.get(module, True))
                checkbox = ctk.CTkCheckBox(
                    stakes_frame,
                    text=module,
                    variable=var,
                    font=("Helvetica", 12),
                    text_color=COLORS["text"],
                    fg_color=COLORS["accent"],
                    hover_color=COLORS["hover"],
                    border_color=COLORS["accent"]
                )
                checkbox.pack(anchor="w", padx=30, pady=2)
                self.stakes_vars[module] = var
        
        # Настройки для MINT
        if "MINT" in self.modules:
            mint_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            mint_frame.pack(fill="x", padx=10, pady=10)
            
            mint_label = ctk.CTkLabel(
                mint_frame,
                text="MINT (выбрать от-до):",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            mint_label.pack(anchor="w", padx=10, pady=5)
            
            # Подсчитываем количество доступных модулей MINT
            mint_count = len(self.modules["MINT"])
            
            # Слайдеры для выбора диапазона
            mint_range_frame = ctk.CTkFrame(mint_frame, fg_color=COLORS["frame_bg"])
            mint_range_frame.pack(fill="x", padx=10, pady=5)
            
            mint_min_label = ctk.CTkLabel(
                mint_range_frame,
                text="Минимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            mint_min_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.mint_min_var = ctk.IntVar(value=self.mint_count_min)
            mint_min_slider = ctk.CTkSlider(
                mint_range_frame,
                from_=0,
                to=mint_count,
                number_of_steps=mint_count,
                variable=self.mint_min_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            mint_min_slider.pack(side="left", padx=5)
            
            mint_min_value = ctk.CTkLabel(
                mint_range_frame,
                textvariable=self.mint_min_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            mint_min_value.pack(side="left", padx=5)
            
            mint_max_label = ctk.CTkLabel(
                mint_range_frame,
                text="Максимум:",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            mint_max_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.mint_max_var = ctk.IntVar(value=self.mint_count_max)
            mint_max_slider = ctk.CTkSlider(
                mint_range_frame,
                from_=0,
                to=mint_count,
                number_of_steps=mint_count,
                variable=self.mint_max_var,
                width=100,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            mint_max_slider.pack(side="left", padx=5)
            
            mint_max_value = ctk.CTkLabel(
                mint_range_frame,
                textvariable=self.mint_max_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=20
            )
            mint_max_value.pack(side="left", padx=5)
            
            # Чекбоксы для модулей
            self.mint_vars = {}
            for module in self.modules["MINT"]:
                # Используем текущее значение из класса
                var = ctk.BooleanVar(value=self.mint_modules.get(module, True))
                checkbox = ctk.CTkCheckBox(
                    mint_frame,
                    text=module,
                    variable=var,
                    font=("Helvetica", 12),
                    text_color=COLORS["text"],
                    fg_color=COLORS["accent"],
                    hover_color=COLORS["hover"],
                    border_color=COLORS["accent"]
                )
                checkbox.pack(anchor="w", padx=30, pady=2)
                self.mint_vars[module] = var
                
        if "GAMES" in self.modules:
            games_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            games_frame.pack(fill="x", padx=10, pady=10)
            
            games_label = ctk.CTkLabel(
                games_frame,
                text="Игровые модули:",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            games_label.pack(anchor="w", padx=10, pady=5)
            
            # Чекбоксы для модулей
            self.games_vars = {}
            for module in self.modules["GAMES"]:
                var = ctk.BooleanVar(value=self.games_modules.get(module, True))
                checkbox = ctk.CTkCheckBox(
                    games_frame,
                    text=module,
                    variable=var,
                    font=("Helvetica", 12),
                    text_color=COLORS["text"],
                    fg_color=COLORS["accent"],
                    hover_color=COLORS["hover"],
                    border_color=COLORS["accent"]
                )
                checkbox.pack(anchor="w", padx=30, pady=2)
                self.games_vars[module] = var
        
        # Настройка для OTHER с вероятностью
        if "OTHER" in self.modules:
            other_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            other_frame.pack(fill="x", padx=10, pady=10)
            
            other_label = ctk.CTkLabel(
                other_frame,
                text="Другие модули:",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            other_label.pack(anchor="w", padx=10, pady=5)
            
            # Слайдер для вероятности
            other_prob_frame = ctk.CTkFrame(other_frame, fg_color=COLORS["frame_bg"])
            other_prob_frame.pack(fill="x", padx=10, pady=5)
            
            other_prob_label = ctk.CTkLabel(
                other_prob_frame,
                text="Вероятность (%):",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            other_prob_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.other_prob_var = ctk.IntVar(value=self.other_probability)
            other_prob_slider = ctk.CTkSlider(
                other_prob_frame,
                from_=0,
                to=100,
                number_of_steps=10,
                variable=self.other_prob_var,
                width=200,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            other_prob_slider.pack(side="left", padx=5)
            
            other_prob_value = ctk.CTkLabel(
                other_prob_frame,
                textvariable=self.other_prob_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=30
            )
            other_prob_value.pack(side="left", padx=5)
            
            # Чекбоксы для модулей
            self.other_vars = {}
            for module in self.modules["OTHER"]:
                if module != "logs":  # logs всегда будет в конце
                    # Используем текущее значение из класса
                    var = ctk.BooleanVar(value=self.other_modules.get(module, True))
                    checkbox = ctk.CTkCheckBox(
                        other_frame,
                        text=module,
                        variable=var,
                        font=("Helvetica", 12),
                        text_color=COLORS["text"],
                        fg_color=COLORS["accent"],
                        hover_color=COLORS["hover"],
                        border_color=COLORS["accent"]
                    )
                    checkbox.pack(anchor="w", padx=30, pady=2)
                    self.other_vars[module] = var
                    
        # Настройка для collect_all_to_monad с вероятностью
        if "SWAPS" in self.modules and "collect_all_to_monad" in self.modules["SWAPS"]:
            collect_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
            collect_frame.pack(fill="x", padx=10, pady=10)
            
            collect_label = ctk.CTkLabel(
                collect_frame,
                text="Использовать collect_all_to_monad:",
                font=("Helvetica", 14, "bold"),
                text_color=COLORS["text"]
            )
            collect_label.pack(anchor="w", padx=10, pady=5)
            
            # Слайдер для вероятности
            collect_prob_frame = ctk.CTkFrame(collect_frame, fg_color=COLORS["frame_bg"])
            collect_prob_frame.pack(fill="x", padx=10, pady=5)
            
            collect_prob_label = ctk.CTkLabel(
                collect_prob_frame,
                text="Вероятность (%):",
                font=("Helvetica", 12),
                text_color=COLORS["text"]
            )
            collect_prob_label.pack(side="left", padx=5)
            
            # Используем текущее значение из класса
            self.collect_prob_var = ctk.IntVar(value=self.collect_probability)
            collect_prob_slider = ctk.CTkSlider(
                collect_prob_frame,
                from_=0,
                to=100,
                number_of_steps=10,
                variable=self.collect_prob_var,
                width=200,
                fg_color=COLORS["entry_bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["hover"],
                progress_color=COLORS["accent"]
            )
            collect_prob_slider.pack(side="left", padx=5)
            
            collect_prob_value = ctk.CTkLabel(
                collect_prob_frame,
                textvariable=self.collect_prob_var,
                font=("Helvetica", 12),
                text_color=COLORS["text"],
                width=30
            )
            collect_prob_value.pack(side="left", padx=5)
        
        # Настройка для генерации рандомных задач для каждого аккаунта
        account_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS["frame_bg"])
        account_frame.pack(fill="x", padx=10, pady=10)
        
        # Используем текущее значение из класса
        self.random_account_var = ctk.BooleanVar(value=self.random_for_each_account)
        random_account_check = ctk.CTkCheckBox(
            account_frame,
            text="Генерировать рандомные задачи для каждого аккаунта",
            variable=self.random_account_var,
            font=("Helvetica", 12, "bold"),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            border_color=COLORS["accent"]
        )
        random_account_check.pack(anchor="w", padx=10, pady=10)
        
        # Кнопка сохранения настроек
        save_button = ctk.CTkButton(
            settings_window,
            text="Сохранить настройки",
            command=lambda: self.save_random_settings(settings_window),
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text"],
            corner_radius=10
        )
        save_button.pack(fill="x", padx=20, pady=20)
    
    def save_random_settings(self, window):
        """Сохранение настроек рандомизации"""
        # Сохраняем настройки начальных модулей
        if hasattr(self, "initial_vars"):
            self.initial_modules = {module: var.get() for module, var in self.initial_vars.items()}
        # Сохраняем настройки SWAPS
        if hasattr(self, "swaps_min_var") and hasattr(self, "swaps_max_var"):
            self.swaps_count_min = self.swaps_min_var.get()
            self.swaps_count_max = self.swaps_max_var.get()
            
            # Проверяем, что минимум не больше максимума
            if self.swaps_count_min > self.swaps_count_max:
                self.swaps_count_min = self.swaps_count_max
        
        if hasattr(self, "swaps_vars"):
            self.swaps_modules = {module: var.get() for module, var in self.swaps_vars.items()}
        
        # Сохраняем настройки STAKES
        if hasattr(self, "stakes_min_var") and hasattr(self, "stakes_max_var"):
            self.stakes_count_min = self.stakes_min_var.get()
            self.stakes_count_max = self.stakes_max_var.get()
            
            # Проверяем, что минимум не больше максимума
            if self.stakes_count_min > self.stakes_count_max:
                self.stakes_count_min = self.stakes_count_max
        
        if hasattr(self, "stakes_vars"):
            self.stakes_modules = {module: var.get() for module, var in self.stakes_vars.items()}
        
        # Сохраняем настройки MINT
        if hasattr(self, "mint_min_var") and hasattr(self, "mint_max_var"):
            self.mint_count_min = self.mint_min_var.get()
            self.mint_count_max = self.mint_max_var.get()
            
            # Проверяем, что минимум не больше максимума
            if self.mint_count_min > self.mint_count_max:
                self.mint_count_min = self.mint_count_max
        
        if hasattr(self, "mint_vars"):
            self.mint_modules = {module: var.get() for module, var in self.mint_vars.items()}
        
        if hasattr(self, "games_vars"):
            self.games_modules = {module: var.get() for module, var in self.games_vars.items()}
        
        # Сохраняем настройки OTHER
        if hasattr(self, "other_prob_var"):
            self.other_probability = self.other_prob_var.get()
        
        if hasattr(self, "other_vars"):
            self.other_modules = {module: var.get() for module, var in self.other_vars.items()}
        
        # Сохраняем настройки collect_all_to_monad
        if hasattr(self, "collect_prob_var"):
            self.collect_probability = self.collect_prob_var.get()
        
        # Сохраняем настройку для генерации рандомных задач для каждого аккаунта
        if hasattr(self, "random_account_var"):
            self.random_for_each_account = self.random_account_var.get()
        
        # Закрываем окно настроек
        window.destroy()
        
        self.update_info("Настройки рандомизации сохранены.")
    
    def fix_selector_event_loop(self):
        """Исправление бага с SelectorEventLoop в main.py"""
        try:
            # Путь к файлу main.py
            main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            
            # Проверяем существование файла
            if not os.path.exists(main_path):
                self.update_info("Ошибка: Файл main.py не найден.")
                return
            
            # Читаем содержимое файла
            with open(main_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Проверяем, закомментирована ли строка с исправлением
            pattern = r"# if platform\.system\(\) == \"Windows\":"
            if re.search(pattern, content):
                # Раскомментируем строки
                content = content.replace(
                    "# if platform.system() == \"Windows\":",
                    "if platform.system() == \"Windows\":"
                )
                content = content.replace(
                    "#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())",
                    "    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())"
                )
                
                # Записываем изменения обратно в файл
                with open(main_path, "w", encoding="utf-8") as file:
                    file.write(content)
                
                self.update_info("Баг с SelectorEventLoop успешно исправлен.")
            else:
                # Проверяем, возможно строки уже раскомментированы
                pattern = r"if platform\.system\(\) == \"Windows\":"
                if re.search(pattern, content):
                    self.update_info("Баг с SelectorEventLoop уже исправлен.")
                else:
                    self.update_info("Не удалось найти строки для исправления бага.")
        
        except Exception as e:
            self.update_info(f"Ошибка при исправлении бага: {str(e)}")
    
    def open_config(self):
        """Открытие конфигурации через интерфейс"""
        try:
            # Импортируем ConfigUI
            spec = importlib.util.spec_from_file_location(
                "config_ui", 
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "utils", "config_ui.py")
            )
            config_ui_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_ui_module)
            
            # Создаем и запускаем интерфейс конфигурации
            self.update_info("Открываю интерфейс конфигурации...")
            
            # Сохраняем текущие обработчики after
            old_after_ids = self.root.tk.call('after', 'info')
            
            # Создаем и запускаем интерфейс конфигурации
            config_ui = config_ui_module.ConfigUI()
            config_ui.run()
            
            # Отменяем все новые обработчики after, которые могли быть созданы
            new_after_ids = self.root.tk.call('after', 'info')
            for after_id in new_after_ids:
                if after_id not in old_after_ids:
                    try:
                        self.root.after_cancel(after_id)
                    except Exception:
                        pass
            
            self.update_info("Конфигурация сохранена.")
        
        except Exception as e:
            self.update_info(f"Ошибка при открытии конфигурации: {str(e)}")
    
    def generate_random_tasks(self):
        """Генерация рандомных задач на основе настроек"""
        tasks = []
        other_tasks = []
        
        # Добавляем начальные модули, если они включены
        if "INITIAL" in self.modules:
            for module in self.modules["INITIAL"]:
                if self.initial_modules.get(module, False):
                    tasks.append(module)
        
        # Выбираем рандомные модули из SWAPS
        if "SWAPS" in self.modules:
            swaps_modules = [module for module, enabled in self.swaps_modules.items() if enabled and module != "collect_all_to_monad"]
            if swaps_modules:
                count = random.randint(self.swaps_count_min, self.swaps_count_max)
                count = min(count, len(swaps_modules))
                if count > 0:
                    selected_swaps = random.sample(swaps_modules, count)
                    # Добавляем каждый модуль отдельно
                    for module in selected_swaps:
                        other_tasks.append(module)
        
        # Выбираем рандомные модули из STAKES
        if "STAKES" in self.modules:
            stakes_modules = [module for module, enabled in self.stakes_modules.items() if enabled]
            if stakes_modules:
                count = random.randint(self.stakes_count_min, self.stakes_count_max)
                count = min(count, len(stakes_modules))
                if count > 0:
                    selected_stakes = random.sample(stakes_modules, count)
                    # Добавляем каждый модуль отдельно
                    for module in selected_stakes:
                        other_tasks.append(module)
        
        # Выбираем рандомные модули из MINT
        if "MINT" in self.modules:
            mint_modules = [module for module, enabled in self.mint_modules.items() if enabled]
            if mint_modules:
                count = random.randint(self.mint_count_min, self.mint_count_max)
                count = min(count, len(mint_modules))
                if count > 0:
                    selected_mint = random.sample(mint_modules, count)
                    # Добавляем каждый модуль отдельно
                    for module in selected_mint:
                        other_tasks.append(module)
                        
        if "GAMES" in self.modules:
            games_modules = [module for module, enabled in self.games_modules.items() if enabled]
            for module in games_modules:
                other_tasks.append(module)
        
        # Добавляем OTHER модули с заданной вероятностью
        if "OTHER" in self.modules:
            other_modules = [module for module, enabled in self.other_modules.items() if enabled]
            if other_modules and random.random() * 100 < self.other_probability:
                selected_other = random.choice(other_modules)
                other_tasks.append(selected_other)
        
        # Перемешиваем только остальные задачи
        random.shuffle(other_tasks)
        
        # Добавляем остальные задачи после начальных
        tasks.extend(other_tasks)
        
        # Добавляем collect_all_to_monad с заданной вероятностью
        if "SWAPS" in self.modules and "collect_all_to_monad" in self.modules["SWAPS"] and random.random() * 100 < self.collect_probability:
            tasks.append("collect_all_to_monad")
        
        # Всегда добавляем logs в конец
        if "OTHER" in self.modules and "logs" in self.modules["OTHER"]:
            tasks.append("logs")
        
        # Выводим сгенерированные задачи в лог
        self.update_info(f"Сгенерированы задачи:\n{tasks}")
        
        return tasks
    
    def update_tasks_file(self, tasks):
        """Обновление файла tasks.py с новыми задачами"""
        try:
            # Путь к файлу tasks.py
            tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.py")
            
            # Проверяем существование файла
            if not os.path.exists(tasks_path):
                self.update_info("Ошибка: Файл tasks.py не найден.")
                return False
            
            # Читаем текущее содержимое файла
            with open(tasks_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Отладка: выводим первые 500 символов содержимого
            self.update_info(f"Содержимое tasks.py (первые 500 символов):\n{content[:500]}")
            
            # Создаем строку с новыми задачами
            custom_task_content = "CUSTOM_TASK = [\n"
            
            for task in tasks:
                if isinstance(task, tuple) or isinstance(task, list):
                    # Если это список задач для рандома, используем квадратные скобки
                    task_str = "    [" + ", ".join(f'"{t}"' for t in task) + "],\n"
                else:
                    # Если это одиночная задача
                    task_str = f'    "{task}",\n'
                custom_task_content += task_str
            
            custom_task_content += "]"
            
            # Заменяем определение CUSTOM_TASK в файле
            pattern = r"CUSTOM_TASK = \[[\s\S]*?\]"
            match = re.search(pattern, content)
            
            if match:
                self.update_info(f"Найдено определение CUSTOM_TASK в позиции {match.start()}-{match.end()}")
                new_content = re.sub(pattern, custom_task_content, content)
                
                # Записываем изменения в файл
                with open(tasks_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                
                self.update_info("Файл tasks.py успешно обновлен с новыми задачами.")
                
                # Выводим содержимое обновленного файла для проверки
                self.update_info(f"Обновленное содержимое CUSTOM_TASK:\n{custom_task_content}")
                
                return True
            else:
                self.update_info("Ошибка: В файле tasks.py не найдено определение CUSTOM_TASK.")
                
                # Попробуем найти с другим шаблоном
                alt_pattern = r"CUSTOM_TASK\s*=\s*\["
                alt_match = re.search(alt_pattern, content)
                if alt_match:
                    self.update_info(f"Найдено начало CUSTOM_TASK с альтернативным шаблоном в позиции {alt_match.start()}")
                
                return False
            
        except Exception as e:
            self.update_info(f"Ошибка при обновлении файла tasks.py: {str(e)}")
            import traceback
            self.update_info(traceback.format_exc())
            return False
    
    def create_random_tasks_script(self):
        try:
            # Путь к временному скрипту
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "random_tasks_for_accounts.py")
            
            # Получаем только включенные модули для передачи в скрипт
            enabled_swaps_modules = {}
            for module in self.modules.get("SWAPS", []):
                if module != "collect_all_to_monad":
                    enabled_swaps_modules[module] = self.swaps_modules.get(module, True)
                    
            enabled_stakes_modules = {}
            for module in self.modules.get("STAKES", []):
                enabled_stakes_modules[module] = self.stakes_modules.get(module, True)
                    
            enabled_mint_modules = {}
            for module in self.modules.get("MINT", []):
                enabled_mint_modules[module] = self.mint_modules.get(module, True)
            
            # Добавляем игровые модули
            enabled_games_modules = {}
            for module in self.modules.get("GAMES", []):
                enabled_games_modules[module] = self.games_modules.get(module, True)
                    
            enabled_other_modules = {}
            for module in self.modules.get("OTHER", []):
                if module != "logs":
                    enabled_other_modules[module] = self.other_modules.get(module, True)
                
            # Создаем скрипт с использованием raw-строки (r-префикс)
            script_content = r"""#!/usr/bin/env python3
import os
import sys
import random
import importlib
import asyncio
import platform
import traceback
import re
import time
import shutil

# Настраиваем логирование
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("random_tasks_log.txt", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RandomTasks")

# Исправляем SelectorEventLoop на Windows
if platform.system() == "Windows":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Установлена политика WindowsSelectorEventLoopPolicy")
    except Exception as e:
        logger.error(f"Ошибка при установке политики WindowsSelectorEventLoopPolicy: {e}")

# Путь к директории проекта
project_dir = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Директория проекта: {project_dir}")

# Добавляем директорию проекта в sys.path
sys.path.insert(0, project_dir)
"""

            # Добавляем настройки модулей и рандомизации
            script_content += f"""
# Захардкоженные модули по категориям
INITIAL_MODULES = {self.initial_modules} 
SWAPS_MODULES = {enabled_swaps_modules}
STAKES_MODULES = {enabled_stakes_modules}
MINT_MODULES = {enabled_mint_modules}
GAMES_MODULES = {enabled_games_modules}
OTHER_MODULES = {enabled_other_modules}

# Настройки рандомизации
SWAPS_MIN = {self.swaps_count_min}
SWAPS_MAX = {self.swaps_count_max}
STAKES_MIN = {self.stakes_count_min}
STAKES_MAX = {self.stakes_count_max}
MINT_MIN = {self.mint_count_min}
MINT_MAX = {self.mint_count_max}
OTHER_PROBABILITY = {self.other_probability}
COLLECT_PROBABILITY = {self.collect_probability}

logger.info("Настройки рандомизации загружены")
"""

            # Добавляем остальную часть скрипта как raw-строку
            script_content += r"""
# Глобальный счетчик аккаунтов и словарь задач
account_index = 0
account_tasks = {}

# Функция для генерации рандомных задач
# Функция для генерации рандомных задач
def generate_random_tasks():
    tasks = []
    other_tasks = []
    
    # Добавляем начальные модули, если они включены
    for module, enabled in INITIAL_MODULES.items():
        if enabled:
            tasks.append(module)

    # Выбираем рандомные модули из SWAPS
    swaps_modules = [module for module in SWAPS_MODULES.keys() if SWAPS_MODULES[module] and module != "collect_all_to_monad"]
    if swaps_modules:
        max_swaps = min(SWAPS_MAX, len(swaps_modules))
        min_swaps = min(SWAPS_MIN, max_swaps)
        
        if max_swaps > 0 and min_swaps > 0:
            count = random.randint(min_swaps, max_swaps)
            if count > 0:
                selected_swaps = random.sample(swaps_modules, count)
                for module in selected_swaps:
                    other_tasks.append(module)
    
    # Выбираем рандомные модули из STAKES
    stakes_modules = [module for module in STAKES_MODULES.keys() if STAKES_MODULES[module]]
    if stakes_modules:
        max_stakes = min(STAKES_MAX, len(stakes_modules))
        min_stakes = min(STAKES_MIN, max_stakes)
        
        if max_stakes > 0 and min_stakes > 0:
            count = random.randint(min_stakes, max_stakes)
            if count > 0:
                selected_stakes = random.sample(stakes_modules, count)
                for module in selected_stakes:
                    other_tasks.append(module)
    
    # Выбираем рандомные модули из MINT
    mint_modules = [module for module in MINT_MODULES.keys() if MINT_MODULES[module]]
    if mint_modules:
        max_mint = min(MINT_MAX, len(mint_modules))
        min_mint = min(MINT_MIN, max_mint)
        
        if max_mint > 0 and min_mint > 0:
            count = random.randint(min_mint, max_mint)
            if count > 0:
                selected_mint = random.sample(mint_modules, count)
                for module in selected_mint:
                    other_tasks.append(module)
    
    # Добавляем GAMES модули, если они включены
    games_modules = [module for module in GAMES_MODULES.keys() if GAMES_MODULES[module]]
    for module in games_modules:
        other_tasks.append(module)
    
    # Добавляем OTHER модули с заданной вероятностью
    other_modules = [module for module in OTHER_MODULES.keys() if OTHER_MODULES[module]]
    if other_modules and random.random() * 100 < OTHER_PROBABILITY:
        selected_other = random.choice(other_modules)
        other_tasks.append(selected_other)
    
    # Перемешиваем только остальные задачи
    random.shuffle(other_tasks)
    
    # Добавляем остальные задачи после начальных
    tasks.extend(other_tasks)
    
    # Добавляем collect_all_to_monad с заданной вероятностью
    if random.random() * 100 < COLLECT_PROBABILITY:
        tasks.append("collect_all_to_monad")
    
    # Всегда добавляем logs в конец
    tasks.append("logs")
    
    return tasks

# Патчим модуль src.model.start для поддержки динамических задач
# Патчим модуль src.model.start для поддержки динамических задач
def patch_start_module():
    try:
        # Импортируем модуль start
        from src.model import start
        
        # Сохраняем оригинальный метод flow
        original_flow = start.Start.flow
        
        # Создаем патч для метода flow
        async def patched_flow(self):
            try:
                monad = start.MonadXYZ(
                    self.account_index,
                    self.proxy,
                    self.private_key,
                    self.discord_token,
                    self.config,
                    self.session,
                )

                if "farm_faucet" in self.config.FLOW.TASKS:
                    await monad.faucet()
                    return True
                
                # Если это первый вызов для этого аккаунта, генерируем задачи
                if self.account_index not in account_tasks:
                    tasks = generate_random_tasks()
                    account_tasks[self.account_index] = tasks
                    task_str = str(tasks)
                    formatted_tasks = task_str.replace("'", '"')
                    print(f"\nСгенерированы задачи для аккаунта {self.account_index}:\n{formatted_tasks}\n")
                    logger.info(f"Сгенерированы задачи для аккаунта {self.account_index}: {tasks}")
                else:
                    tasks = account_tasks[self.account_index]
                
                # Используем сгенерированные задачи вместо задач из конфигурации
                planned_tasks = []
                task_plan_msg = []
                task_index = 1

                for task in tasks:
                    planned_tasks.append((task_index, task, "single"))
                    task_plan_msg.append(f"{task_index}. {task}")
                    task_index += 1
                
                logger.info(
                    f"[{self.account_index}] Task execution plan: {' | '.join(task_plan_msg)}"
                )
                
                for i, task, task_type in planned_tasks:
                    logger.info(f"[{self.account_index}] Executing task {i}: {task}")
                    await self.execute_task(task, monad)
                    await self.sleep(task)

                return True
            except Exception as e:
                logger.error(f"[{self.account_index}] | Error: {e}")
                return False
        
        # Добавляем атрибут account_index в класс Start
        start.Start.account_index = 0
        
        # Сохраняем оригинальный метод __init__
        original_init = start.Start.__init__
        
        # Создаем патч для метода __init__
        def patched_init(self, *args, **kwargs):
            # Вызываем оригинальный метод
            original_init(self, *args, **kwargs)
            
            # Устанавливаем индекс аккаунта
            self.account_index = start.Start.account_index
            
            # Увеличиваем глобальный счетчик
            start.Start.account_index += 1
        
        # Заменяем методы на наши патчи
        start.Start.__init__ = patched_init
        start.Start.flow = patched_flow
        
        logger.info("Модуль start успешно пропатчен")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при патче модуля start: {e}")
        logger.error(traceback.format_exc())
        return False


# Патчим модуль src.utils.config для поддержки динамических задач
def patch_config_module():
    try:
        # Импортируем модуль config
        from src.utils import config
        
        # Проверяем, есть ли метод get_tasks
        if not hasattr(config.Config, 'get_tasks'):
            logger.error("Метод get_tasks не найден в классе Config")
            # Добавляем метод get_tasks, если его нет
            def get_tasks(self):
                return []
            config.Config.get_tasks = get_tasks
            logger.info("Добавлен метод get_tasks в класс Config")
        
        # Сохраняем оригинальный метод load
        original_load = config.Config.load
        
        # Создаем патч для метода load
        def patched_load(cls):
            try:
                # Пытаемся загрузить конфигурацию обычным способом
                return original_load.__func__(cls)
            except Exception as e:
                logger.info(f"Перехвачена ошибка при загрузке конфигурации: {e}")
                # Возвращаем конфигурацию с пустыми задачами
                config_obj = cls()
                config_obj.preset = "CUSTOM_TASK"
                return config_obj
        
        # Заменяем метод load на наш патч
        config.Config.load = classmethod(patched_load)
        
        # Патчим метод get_tasks, если он существует
        if hasattr(config.Config, 'get_tasks'):
            original_get_tasks = config.Config.get_tasks
            
            def patched_get_tasks(self):
                # Возвращаем пустой список задач, который будет заменен в методе flow
                return []
            
            # Заменяем метод get_tasks на наш патч
            config.Config.get_tasks = patched_get_tasks
        
        logger.info("Модуль config успешно пропатчен")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при патче модуля config: {e}")
        logger.error(traceback.format_exc())
        return False

# Функция для запуска процесса с рандомными задачами для каждого аккаунта
# Функция для запуска процесса с рандомными задачами для каждого аккаунта
def run_with_random_tasks():
    try:
        logger.info("Запуск с рандомными задачами для каждого аккаунта")
        
        # Патчим необходимые модули
        logger.info("Патчим модуль config...")
        if not patch_config_module():
            logger.error("Не удалось пропатчить модуль config")
            print("Не удалось пропатчить модуль config. Проверьте лог-файл.")
            return
        
        logger.info("Патчим модуль start...")
        if not patch_start_module():
            logger.error("Не удалось пропатчить модуль start")
            print("Не удалось пропатчить модуль start. Проверьте лог-файл.")
            return
        
        # Импортируем main и запускаем
        logger.info("Импорт main.py")
        try:
            import main
            logger.info("Запуск функции main")
            asyncio.run(main.main())
        except ImportError as e:
            logger.error(f"Ошибка импорта main.py: {e}")
            print(f"Ошибка импорта main.py: {e}")
        except Exception as e:
            logger.error(f"Ошибка при запуске main.py: {e}")
            logger.error(traceback.format_exc())
            print(f"Ошибка при запуске main.py: {e}")
            print(traceback.format_exc())
        
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        logger.error(traceback.format_exc())
        print(f"Ошибка при запуске: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        # Запускаем с рандомными задачами
        run_with_random_tasks()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        logger.critical(traceback.format_exc())
        print(f"Критическая ошибка: {e}")
        print(traceback.format_exc())
    finally:
        # Добавляем паузу, чтобы консоль не закрывалась
        print("\nНажмите Enter для выхода...")
        input()
"""
        
            # Записываем скрипт в файл
            with open(script_path, "w", encoding="utf-8") as file:
                file.write(script_content)
                    
            return script_path
        
        except Exception as e:
            self.update_info(f"Ошибка при создании скрипта для рандомных задач: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            self.update_info(f"Подробная информация об ошибке:\n{error_trace}")
            return None
        
        
    def reload_tasks_module(self):
        """Перезагрузка модуля tasks.py"""
        try:
            import importlib
            import sys
            
            # Удаляем модуль tasks из кэша, если он там есть
            if 'tasks' in sys.modules:
                del sys.modules['tasks']
            
            # Импортируем модуль заново
            import tasks
            
            self.update_info("Модуль tasks.py успешно перезагружен")
            return True
        except Exception as e:
            self.update_info(f"Ошибка при перезагрузке модуля tasks.py: {str(e)}")
            return False
        
    
    def create_temp_tasks_file(self, tasks):
        """Создание временного файла с задачами"""
        
        try:
            # Путь к временному файлу
            temp_tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_tasks.py")
            
            # Создаем содержимое файла
            content = "# Временный файл с задачами\n\n"
            content += "TASKS = [\n    \"CUSTOM_TASK\"\n]\n\n"
            
            # Добавляем CUSTOM_TASK
            content += "CUSTOM_TASK = [\n"
            for task in tasks:
                if isinstance(task, tuple):
                    # Если это кортеж задач
                    task_str = "    (" + ", ".join(f'"{t}"' for t in task) + "),\n"
                elif isinstance(task, list):
                    # Если это список задач
                    task_str = "    [" + ", ".join(f'"{t}"' for t in task) + "],\n"
                else:
                    # Если это одиночная задача
                    task_str = f'    "{task}",\n'
                content += task_str
            content += "]\n\n"
            
            # Добавляем функцию get_tasks
            content += "def get_tasks():\n    return CUSTOM_TASK\n"
            
            # Записываем в файл
            with open(temp_tasks_path, "w", encoding="utf-8") as file:
                file.write(content)
            
            self.update_info(f"Создан временный файл с задачами: {temp_tasks_path}")
            return temp_tasks_path
        except Exception as e:
            self.update_info(f"Ошибка при создании временного файла с задачами: {str(e)}")
            return None
        
    def generate_schedule(self, hours_str):
        """Генерация расписания запуска аккаунтов на указанное количество часов"""
        try:
            # Преобразуем строку с часами в число
            hours = int(hours_str)
            if hours <= 0:
                self.update_info("Ошибка: Количество часов должно быть положительным числом.")
                return False
            
            # Загружаем конфигурацию для определения количества аккаунтов
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
            if not os.path.exists(config_path):
                self.update_info("Ошибка: Файл конфигурации не найден.")
                return False
            
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file)
            
            # Получаем диапазон аккаунтов
            accounts_range = config_data["SETTINGS"]["ACCOUNTS_RANGE"]
            exact_accounts = config_data["SETTINGS"]["EXACT_ACCOUNTS_TO_USE"]
            
            # Определяем количество аккаунтов
            if accounts_range[0] == 0 and accounts_range[1] == 0:
                if exact_accounts:
                    # Используем конкретные аккаунты
                    num_accounts = len(exact_accounts)
                else:
                    # Используем все аккаунты
                    private_keys_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "private_keys.txt")
                    if not os.path.exists(private_keys_path):
                        self.update_info("Ошибка: Файл с приватными ключами не найден.")
                        return False
                    
                    with open(private_keys_path, "r", encoding="utf-8") as file:
                        private_keys = [line.strip() for line in file if line.strip()]
                    
                    num_accounts = len(private_keys)
            else:
                # Используем указанный диапазон
                start_idx = accounts_range[0]
                end_idx = accounts_range[1]
                num_accounts = end_idx - start_idx + 1
            
            if num_accounts <= 0:
                self.update_info("Ошибка: Не найдено аккаунтов для запуска.")
                return False
            
            # Преобразуем часы в минуты
            total_minutes = hours * 60
            
            # Определяем минимальный интервал между запусками
            # Если аккаунтов много, а времени мало, увеличиваем минимальный интервал
            min_interval = max(5, total_minutes // (num_accounts * 2))
            
            # Создаем список задержек для запуска аккаунтов (в секундах)
            # Первый аккаунт запускается сразу (задержка 0)
            delays = [0]  # Первый аккаунт без задержки
            
            # Распределяем оставшиеся аккаунты по времени
            remaining_accounts = num_accounts - 1
            if remaining_accounts > 0:
                # Распределяем оставшееся время между аккаунтами
                remaining_time = total_minutes * 60  # в секундах
                
                # Генерируем случайные задержки для оставшихся аккаунтов
                for i in range(remaining_accounts):
                    # Если это последний аккаунт, используем оставшееся время
                    if i == remaining_accounts - 1:
                        delay = remaining_time
                    else:
                        # Иначе выбираем случайную задержку в пределах оставшегося времени
                        max_delay = remaining_time // (remaining_accounts - i)
                        min_delay = min(min_interval * 60, max_delay)  # минимум 5 минут или максимально возможное
                        delay = random.randint(min_delay, max_delay)
                    
                    delays.append(delay)
                    remaining_time -= delay
            
            # Преобразуем задержки в абсолютное время от начала
            absolute_delays = [0]  # Первый аккаунт без задержки
            for i in range(1, len(delays)):
                absolute_delays.append(absolute_delays[i-1] + delays[i])
            
            # Создаем расписание запуска
            now = datetime.now()
            schedule = []
            
            for i, delay in enumerate(absolute_delays):
                launch_time = now + timedelta(seconds=delay)
                schedule.append((i+1, launch_time, delay))
            
            # Выводим расписание
            self.update_info("\n=== Расписание запуска аккаунтов ===")
            self.update_info(f"Всего аккаунтов: {num_accounts}")
            self.update_info(f"Период запуска: {hours} часов ({total_minutes} минут)")
            
            for account_idx, launch_time, delay in schedule:
                hours_from_now = delay // 3600
                mins_from_now = (delay % 3600) // 60
                secs_from_now = delay % 60
                
                if delay == 0:
                    time_str = "сразу"
                else:
                    time_str = f"через {hours_from_now}ч {mins_from_now}м {secs_from_now}с"
                    
                self.update_info(f"Аккаунт {account_idx}: {launch_time.strftime('%H:%M:%S')} ({time_str})")
            
            # Сохраняем расписание для использования в патч-скрипте
            schedule_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.json")
            import json
            with open(schedule_path, "w", encoding="utf-8") as file:
                # Сохраняем только задержки в секундах
                json.dump(absolute_delays, file)
            
            self.update_info(f"\nРасписание сохранено в файл: {schedule_path}")
            
            # Создаем патч-скрипт для запуска с расписанием
            self.create_schedule_launcher()
            
            return True
        
        except Exception as e:
            self.update_info(f"Ошибка при генерации расписания: {str(e)}")
            import traceback
            self.update_info(traceback.format_exc())
            return False
        
    def create_schedule_launcher(self):
        """Создание скрипта для запуска с расписанием"""
        try:
            # Путь к скрипту запуска по расписанию
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule_runner.py")
            self.update_info(f"Создаю скрипт: {script_path}")
            
            # Создаем содержимое скрипта
            script_content = """#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import platform
import traceback
import importlib.util
from datetime import datetime, timedelta

# Путь к директории проекта
project_dir = os.path.dirname(os.path.abspath(__file__))

# Исправляем SelectorEventLoop на Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Загружаем расписание
schedule_path = os.path.join(project_dir, "schedule.json")
try:
    with open(schedule_path, "r", encoding="utf-8") as file:
        schedule_delays = json.load(file)
    print(f"Загружено расписание с {len(schedule_delays)} задержками")
except Exception as e:
    print(f"Ошибка при загрузке расписания: {e}")
    print(traceback.format_exc())
    print("\\nНажмите Enter для выхода...")
    input()
    sys.exit(1)

# Определяем, нужно ли использовать рандомные модули
use_random_modules = {random_modules}

# Словарь для отслеживания запущенных аккаунтов
launched_accounts = set()
first_account_launched = False

# Патчим модуль process.py для поддержки расписания
def patch_process_module():
    try:
        # Импортируем модуль process
        import process
        
        # Сохраняем оригинальный метод account_flow
        original_account_flow = process.account_flow
        
        # Создаем патч для метода account_flow
        # В schedule_runner.py
        async def patched_account_flow(account_index, proxy, private_key, discord_token, twitter_token, email, config, lock, progress_tracker):
            global first_account_launched, launched_accounts
            
            # Если это первый запускаемый аккаунт (независимо от его индекса)
            if not first_account_launched:
                print(f"Запуск первого аккаунта {account_index} без задержки")
                first_account_launched = True
                launched_accounts.add(account_index)
            else:
                # Для всех последующих аккаунтов применяем задержку из расписания
                # Определяем порядковый номер запуска (1, 2, 3, ...)
                launch_order = len(launched_accounts)
                
                if launch_order < len(schedule_delays):
                    # Вычисляем время запуска
                    if launch_order == 0:
                        delay = schedule_delays[0]
                    else:
                        delay = schedule_delays[launch_order] - schedule_delays[launch_order-1]
                    
                    hours = delay // 3600
                    minutes = (delay % 3600) // 60
                    seconds = delay % 60
                    
                    print(f"Ожидание перед запуском аккаунта {account_index} (#{launch_order+1}): {hours}ч {minutes}м {seconds}с")
                    await asyncio.sleep(delay)
                
                launched_accounts.add(account_index)
            
            # Вызываем оригинальный метод со всеми параметрами
            return await original_account_flow(account_index, proxy, private_key, discord_token, twitter_token, email, config, lock, progress_tracker)
        
        # Заменяем методы на наши патчи
        process.account_flow = patched_account_flow
        
        print("Модуль process.py успешно пропатчен для работы с расписанием")
        return True
    except Exception as e:
        print(f"Ошибка при патче модуля process.py: {e}")
        print(traceback.format_exc())
        return False

# Главная функция
async def main():
    try:
        print("=== Запуск аккаунтов по расписанию ===")
        
        # Патчим необходимые модули
        if not patch_process_module():
            print("Ошибка при патче модуля process.py")
            return
        
        # Если нужно использовать рандомные модули
        if use_random_modules:
            # Запускаем скрипт с рандомными задачами
            print("Запуск с рандомными модулями...")
            
            # Путь к скрипту с рандомными задачами
            random_script_path = os.path.join(project_dir, "random_tasks_for_accounts.py")
            
            # Проверяем существование скрипта
            if not os.path.exists(random_script_path):
                print(f"Ошибка: Скрипт {random_script_path} не найден.")
                print("Создаем скрипт с рандомными задачами...")
                
                # Импортируем лаунчер и создаем скрипт
                launcher_path = os.path.join(project_dir, "launcher.py")
                spec = importlib.util.spec_from_file_location("launcher", launcher_path)
                launcher_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(launcher_module)
                
                # Создаем экземпляр лаунчера и вызываем метод создания скрипта
                launcher = launcher_module.StarLabsLauncher()
                random_script_path = launcher.create_random_tasks_script()
                
                if not random_script_path or not os.path.exists(random_script_path):
                    print("Ошибка при создании скрипта с рандомными задачами.")
                    return
            
            # Импортируем скрипт с рандомными задачами
            print("Импортируем скрипт с рандомными задачами...")
            spec = importlib.util.spec_from_file_location("random_tasks", random_script_path)
            random_tasks_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(random_tasks_module)
            
            # Патчим необходимые модули для рандомных задач
            print("Патчим модули для рандомных задач...")
            if hasattr(random_tasks_module, 'patch_config_module'):
                if not random_tasks_module.patch_config_module():
                    print("Ошибка при патче модуля config.py")
                    return
            
            if hasattr(random_tasks_module, 'patch_start_module'):
                if not random_tasks_module.patch_start_module():
                    print("Ошибка при патче модуля start.py")
                    return
        
        # Импортируем main.py и запускаем
        print("Импортируем main.py...")
        spec = importlib.util.spec_from_file_location("main", os.path.join(project_dir, "main.py"))
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # Запускаем main без указания аккаунта, чтобы использовать все аккаунты
        print("Запускаем main.py...")
        await main_module.main()
        
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        print("Скрипт запущен")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nПрограмма остановлена пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print(traceback.format_exc())
    finally:
        print("\\nНажмите Enter для выхода...")
        input()
"""

                
            # Заменяем переменные в скрипте
            script_content = script_content.replace("{random_modules}", str(self.random_modules_var.get()))
            
            # Записываем скрипт в файл
            with open(script_path, "w", encoding="utf-8") as file:
                file.write(script_content)
            
            self.update_info(f"Скрипт успешно записан: {script_path}")
            
            # Делаем скрипт исполняемым на Unix-системах
            if platform.system() != "Windows":
                os.chmod(script_path, 0o755)
            
            self.update_info(f"Создан скрипт для запуска с расписанием: {script_path}")
            
            # Если выбрана рандомизация модулей, создаем скрипт для рандомных задач
            if self.random_modules_var.get():
                random_script_path = self.create_random_tasks_script()
                if random_script_path:
                    self.update_info(f"Создан скрипт для рандомных задач: {random_script_path}")
            
            return True
        
        except Exception as e:
            self.update_info(f"Ошибка при создании скрипта для запуска с расписанием: {str(e)}")
            import traceback
            self.update_info(traceback.format_exc())
            return False
    
    
    def launch_app(self):
        """Запуск приложения"""
        try:
            # Проверяем содержимое tasks.py перед запуском
            tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.py")
            if os.path.exists(tasks_path):
                with open(tasks_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Ищем CUSTOM_TASK в файле
                custom_task_pattern = r"CUSTOM_TASK = \[([\s\S]*?)\]"
                custom_task_match = re.search(custom_task_pattern, content)
                if custom_task_match:
                    custom_task_content = custom_task_match.group(0)
                    self.update_info(f"Текущее содержимое CUSTOM_TASK:\n{custom_task_content}")
            
            # Создаем лог-файл для ошибок
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_log.txt")
            
            # Получаем текущую директорию
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Проверяем, нужно ли генерировать расписание
            if self.schedule_var.get():
                hours = self.hours_entry.get()
                if not self.generate_schedule(hours):
                    return
                
                # Запускаем с расписанием
                self.update_info("Запуск StarLabs Monad с расписанием...")
                
                # Создаем прямой запуск Python-скрипта вместо использования bat-файла
                schedule_runner_path = os.path.join(current_dir, "schedule_runner.py")
                
                if not os.path.exists(schedule_runner_path):
                    self.update_info(f"Ошибка: Файл {schedule_runner_path} не найден.")
                    return
                
                # Запускаем Python напрямую с указанием полного пути к интерпретатору и скрипту
                if platform.system() == "Windows":
                    # На Windows используем subprocess.Popen напрямую с Python
                    cmd = [sys.executable, schedule_runner_path]
                    process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    # На Unix-системах
                    cmd = [sys.executable, schedule_runner_path]
                    process = subprocess.Popen(cmd)
                
                self.update_info(f"Приложение запущено с расписанием (PID: {process.pid}).")
                return
            
            # Если расписание не используется, продолжаем обычный запуск
            # Проверяем, нужно ли использовать рандомные модули
            if self.random_modules_var.get():
                # Проверяем, нужно ли генерировать рандомные задачи для каждого аккаунта
                if self.random_for_each_account:
                    # Создаем скрипт для генерации рандомных задач для каждого аккаунта
                    script_path = self.create_random_tasks_script()
                    if not script_path:
                        return
                    
                    # Запускаем скрипт
                    self.update_info("Запуск StarLabs Monad с рандомными задачами для каждого аккаунта...")
                    
                    # На Windows запускаем в отдельном окне консоли
                    if platform.system() == "Windows":
                        # Запускаем Python напрямую
                        cmd = [sys.executable, script_path]
                        process = subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        # На Unix-системах
                        cmd = [sys.executable, script_path]
                        process = subprocess.Popen(cmd)
                    
                    self.update_info(f"Приложение запущено успешно (PID: {process.pid}).")
                else:
                    # Генерируем одинаковые рандомные задачи для всех аккаунтов
                    tasks = self.generate_random_tasks()
                    if not self.update_tasks_file(tasks):
                        return
                    
                    # Перезагружаем модуль tasks
                    self.reload_tasks_module()
                    
                    # Создаем временный файл с задачами
                    temp_tasks_path = self.create_temp_tasks_file(tasks)
                    if not temp_tasks_path:
                        return
                    
                    # Запускаем приложение обычным способом
                    self.update_info("Запуск StarLabs Monad с рандомными задачами...")
                    
                    # На Windows запускаем в отдельном окне консоли
                    if platform.system() == "Windows":
                        # Запускаем Python напрямую с импортом временного модуля
                        cmd = [sys.executable, "-c", 
                            f"import sys; sys.path.insert(0, '{current_dir}'); "
                            f"import importlib.util; "
                            f"spec = importlib.util.spec_from_file_location('tasks', '{temp_tasks_path}'); "
                            f"tasks = importlib.util.module_from_spec(spec); "
                            f"spec.loader.exec_module(tasks); "
                            f"from main import main; import asyncio; asyncio.run(main())"]
                        process = subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        # На Unix-системах
                        cmd = [sys.executable, "-c", 
                            f"import sys; sys.path.insert(0, '{current_dir}'); "
                            f"import importlib.util; "
                            f"spec = importlib.util.spec_from_file_location('tasks', '{temp_tasks_path}'); "
                            f"tasks = importlib.util.module_from_spec(spec); "
                            f"spec.loader.exec_module(tasks); "
                            f"from main import main; import asyncio; asyncio.run(main())"]
                        process = subprocess.Popen(cmd)
                    
                    self.update_info(f"Приложение запущено успешно (PID: {process.pid}).")
            else:
                # Запускаем приложение обычным способом
                self.update_info("Запуск StarLabs Monad...")
                
                # Запускаем main.py в отдельном процессе
                main_path = os.path.join(current_dir, "main.py")
                
                # На Windows запускаем в отдельном окне консоли
                if platform.system() == "Windows":
                    # Запускаем Python напрямую
                    cmd = [sys.executable, main_path]
                    process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    # На Unix-системах
                    cmd = [sys.executable, main_path]
                    process = subprocess.Popen(cmd)
                
                self.update_info(f"Приложение запущено успешно (PID: {process.pid}).")

        except Exception as e:
            self.update_info(f"Ошибка при запуске приложения: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            self.update_info(f"Подробная информация об ошибке:\n{error_trace}")
            
            # Сохраняем ошибку в лог-файл
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_error.txt")
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write(f"Ошибка при запуске приложения: {str(e)}\n\n")
                log_file.write(error_trace)
            
            self.update_info(f"Информация об ошибке сохранена в: {log_path}")
    
    def update_info(self, text):
        """Обновление текстового поля с информацией"""
        self.info_text.configure(state="normal")
        self.info_text.insert("end", f"\n{text}")
        self.info_text.see("end")
    
    def run(self):
        """Запуск лаунчера"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    launcher = StarLabsLauncher()
    launcher.run()