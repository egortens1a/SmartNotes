from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.lang import Builder

import time
import os

from kivy.uix.popup import Popup

import NoteEditor
import InputDialog


Builder.load_file("SmartNotesRefactor.kv")

class SearchDialog(Popup):
    def do_search(self, query):
        self.ids.search_results.text = f"Результаты поиска по запросу '{query}':\n\n(функция поиска в разработке)"

class MainPanel(BoxLayout):
    vault_dir = 'my_vault'
    file_chooser = ObjectProperty(None)
    note_editor = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        self.file_chooser.path = self.vault_dir
        self.file_chooser._update_files()

    def show_search_dialog(self):
        dialog = SearchDialog()
        dialog.open()

    def load_note(self, selection):
        if selection:
            self.note_editor.current_file = selection[0]
            try:
                with open(selection[0], 'r', encoding='utf-8') as f:
                    self.note_editor.note_content = f.read()
                self.note_editor.update_preview(force=True)
            except Exception as e:
                print(f"Error loading note: {e}")

    def show_new_note_dialog(self):
        def create_note(filename):
            if not filename:
                return
            if not filename.endswith('.md'):
                filename += '.md'
            new_note_path = os.path.join(self.file_chooser.path, filename)

            if os.path.exists(new_note_path):
                base, ext = os.path.splitext(filename)
                timestamp = str(int(time.time()))
                new_note_path = os.path.join(self.file_chooser.path, f"{base}_{timestamp}{ext}")

            try:
                with open(new_note_path, 'w', encoding='utf-8') as f:
                    f.write(f'# {os.path.splitext(filename)[0]}\n\nStart writing here...')
                self.file_chooser._update_files()
                self.load_note([new_note_path])
            except Exception as e:
                print(f"Error creating note: {e}")

        dialog = InputDialog.InputDialog(
            title="Новая заметка",
            hint_text="Введите название заметки (без .md)",
            callback=create_note
        )
        dialog.open()

    def show_new_folder_dialog(self):
        def create_folder(foldername):
            if not foldername:
                return
            new_folder_path = os.path.join(self.file_chooser.path, foldername)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.file_chooser._update_files()
            except Exception as e:
                print(f"Error creating folder: {e}")

        dialog = InputDialog.InputDialog(
            title="Новая папка",
            hint_text="Введите название папки",
            callback=create_folder
        )
        dialog.open()


class SmartNotes(App):
    def build(self):
        Window.size = (1200, 800)
        return MainPanel()


if __name__ == '__main__':
    SmartNotes().run()