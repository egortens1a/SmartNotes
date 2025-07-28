from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.lang import Builder

import time
import os

import NoteEditor # он нужен, хоть и неявно
import Dialogs

import os
os.environ['KIVY_NO_ARGS'] = '1'  # Отключает аргументы Kivy

class MainPanel(BoxLayout):
    vault_dir = 'my_vault'
    file_chooser = ObjectProperty(None)
    note_editor = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        self.file_chooser.path = self.vault_dir
        # Разрешаем отображать .json
        self.file_chooser.filters = ['*.json']
        self.file_chooser._update_files()

    def show_search_dialog(self):
        """Вывод окна поиска"""
        def on_file_selected(filepath):
            self.load_note([filepath])
            self.file_chooser.path = os.path.dirname(filepath)
            self.file_chooser._update_files()
            self.file_chooser.selection = [filepath]

        dialog = Dialogs.SearchDialog(
            vault_dir=self.vault_dir,
            on_file_select_callback=on_file_selected
        )
        dialog.open()

    def update_file_list(self):
        """
        Обновляет список файлов с учетом дубликатов
        """
        # Получаем текущий путь
        current_path = self.file_chooser.path

        # Собираем все файлы
        all_files = []
        for root, dirs, files in os.walk(current_path):
            for f in files:
                if f.endswith(('.json')):
                    all_files.append(os.path.join(root, f))

        self.file_chooser.path = ''
        self.file_chooser.path = current_path

    def load_note(self, selection):
        if not selection:
            self.note_editor.clear_editor()
            return

        filepath = selection[0]
        self.note_editor.current_file = filepath
        self.note_editor.drawing_data = []

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                if filepath.endswith('.json'):
                    try:
                        data = json.load(f)
                        if isinstance(data, dict) and 'text' in data:
                            self.note_editor.ids.editor.text = data['text']
                            if 'drawings' in data:
                                for drawing in data['drawings']:
                                    if 'is_new' not in drawing:
                                        drawing['is_new'] = True
                                    self.note_editor.drawing_data.append(drawing)
                    except Exception as e:
                        print(f"Invalid JSON: {e}")
                else:
                    self.note_editor.ids.editor.text = f.read()

            self.note_editor.update_preview(force=True)
        except Exception as e:
            print(f"Load error: {e}")

    def show_new_note_dialog(self):
        def create_note(filename):
            if not filename:
                return

            self.note_editor.current_file = ''
            self.note_editor.ids.editor.text = ""
            self.note_editor.drawing_data = []

            if not filename.lower().endswith('.json'):
                filename += '.json'

            new_note_path = os.path.join(self.file_chooser.path, filename)

            # Обработка существующих файлов
            if os.path.exists(new_note_path):
                base, ext = os.path.splitext(filename)
                new_note_path = os.path.join(
                    self.file_chooser.path,
                    f"{base}_{int(time.time())}{ext}"
                )

            try:
                note_data = {
                    "version": 1.3,
                    "text": f"# {os.path.splitext(filename)[0]}\n\n",
                    "drawings": []
                }

                with open(new_note_path, 'w', encoding='utf-8') as f:
                    json.dump(note_data, f, indent=2)

                self.update_file_list()
                self.load_note([new_note_path])
            except Exception as e:
                print(f"Ошибка создания: {e}")
                self.show_popup("Ошибка", f"Не удалось создать заметку: {str(e)}")

        dialog = Dialogs.InputDialog(
            title="Новая заметка",
            hint_text="Введите название (можно без .json)",
            callback=create_note
        )
        dialog.open()

    def show_new_folder_dialog(self):
        """
        Создание новой папки (открытие окна)
        :return:
        """
        def create_folder(foldername):
            """
            Создание новой папки
            :param foldername: название папки
            :return: None
            """
            if not foldername:
                return
            new_folder_path = os.path.join(self.file_chooser.path, foldername)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.file_chooser._update_files()
            except Exception as e:
                print(f"Error creating folder: {e}")

        dialog = Dialogs.InputDialog(
            title="Новая папка",
            hint_text="Введите название папки",
            callback=create_folder
        )
        dialog.open()


"""
    Загрузка верстки
"""
Builder.load_file("SmartNotes.kv")


class SmartNote(App):
    def build(self):
        Window.size = (1200, 800)
        Window.clearcolor = (1, 1, 1, 1)  # RGBA значения (от 0 до 1)
        return MainPanel()


if __name__ == '__main__':
    SmartNote().run()