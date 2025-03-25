from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

import time
import os

import NoteEditor
from InputDialog import InputDialog


Builder.load_file("SmartNotes.kv")

class MarkdownPreview(BoxLayout):
    text = StringProperty('')


class MainPanel(BoxLayout):
    """Главная панель приложения с файловым менеджером и редактором"""

    vault_dir = 'my_vault'
    file_chooser = ObjectProperty(None)
    note_editor = ObjectProperty(None)

    def __init__(self, **kwargs):
        """
        Инициализирует главную панель
        Создаёт папку для заметок если её нет
        """
        super().__init__(**kwargs)
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        self.file_chooser.path = self.vault_dir
        self.file_chooser._update_files()

    def load_note(self, selection):
        """
        Загружает заметку из файла
        Args:
            selection: список выбранных файлов
        """
        if selection:
            self.note_editor.current_file = selection[0]
            try:
                with open(selection[0], 'r', encoding='utf-8') as f:
                    self.note_editor.note_content = f.read()
                self.note_editor.update_preview()
            except Exception as e:
                print(f"Error loading note: {e}")

    def show_new_note_dialog(self):
        """
        Показывает диалог создания новой заметки
        """

        def create_note(filename):
            """Создаёт новую заметку с указанным именем"""
            if not filename:
                return
            if not filename.endswith('.md'):
                filename += '.md'
            new_note_path = os.path.join(self.vault_dir, filename)

            if os.path.exists(new_note_path):
                base, ext = os.path.splitext(filename)
                timestamp = str(int(time.time()))
                new_note_path = os.path.join(self.vault_dir, f"{base}_{timestamp}{ext}")

            try:
                with open(new_note_path, 'w', encoding='utf-8') as f:
                    f.write(f'# {os.path.splitext(filename)[0]}\n\nStart writing here...')
                self.file_chooser._update_files()
                self.load_note([new_note_path])
            except Exception as e:
                print(f"Error creating note: {e}")

        dialog = InputDialog(
            title="New Note",
            hint_text="Enter note name (without .md)",
            callback=create_note
        )
        dialog.open()

    def show_new_folder_dialog(self):
        """
        Показывает диалог создания новой папки
        """

        def create_folder(foldername):
            """Создаёт новую папку с указанным именем"""
            if not foldername:
                return
            new_folder_path = os.path.join(self.vault_dir, foldername)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.file_chooser._update_files()
            except Exception as e:
                print(f"Error creating folder: {e}")

        dialog = InputDialog(
            title="New Folder",
            hint_text="Enter folder name",
            callback=create_folder
        )
        dialog.open()


class ObsidianApp(App):
    """Главный класс приложения"""

    def build(self):
        """
        Создаёт и возвращает главный виджет приложения
        return: экземпляр MainPanel
        """
        Window.size = (1200, 800)
        return MainPanel()


if __name__ == '__main__':
    ObsidianApp().run()