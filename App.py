import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
import markdown2
from bs4 import BeautifulSoup
import time

Builder.load_string('''
<MarkdownPreview>:
    text: ''
    ScrollView:
        Label:
            text: root.text
            markup: True
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            padding: 10, 10

<NoteEditor>:
    orientation: 'vertical'
    TextInput:
        id: editor
        text: root.note_content
        size_hint_y: 0.7
        font_name: 'data/fonts/RobotoMono-Regular.ttf'
        background_color: (0.1, 0.1, 0.1, 1)
        foreground_color: (1, 1, 1, 1)
        cursor_color: (1, 1, 1, 1)
        on_text: root.update_preview()
    Button:
        text: 'Save'
        size_hint_y: 0.1
        on_press: root.save_note()
    MarkdownPreview:
        id: preview
        size_hint_y: 0.2

<InputDialog>:
    size_hint: (0.8, 0.4)
    title: ''
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        TextInput:
            id: input
            hint_text: ''
            size_hint_y: 0.6
        BoxLayout:
            size_hint_y: 0.4
            spacing: 10
            Button:
                text: 'Cancel'
                on_press: root.dismiss()
            Button:
                text: 'OK'
                on_press: root.on_ok()

<MainPanel>:
    orientation: 'horizontal'
    BoxLayout:
        size_hint_x: 0.2
        orientation: 'vertical'
        Button:
            text: 'New Note'
            size_hint_y: 0.1
            on_press: root.show_new_note_dialog()
        Button:
            text: 'New Folder'
            size_hint_y: 0.1
            on_press: root.show_new_folder_dialog()
        FileChooserListView:
            id: file_chooser
            size_hint_y: 0.8
            filters: ['*.md']
            on_selection: root.load_note(file_chooser.selection)
    NoteEditor:
        id: note_editor
        size_hint_x: 0.8
''')


class InputDialog(Popup):
    def __init__(self, title, hint_text, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.ids.input.hint_text = hint_text
        self.callback = callback

    def on_ok(self):
        self.callback(self.ids.input.text)
        self.dismiss()  # Добавлено закрытие окна после выполнения callback


class MarkdownPreview(BoxLayout):
    text = StringProperty('')


class NoteEditor(BoxLayout):
    note_content = StringProperty('')
    current_file = StringProperty('')

    def save_note(self):
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.ids.editor.text)

    def update_preview(self):
        markdown_text = self.ids.editor.text
        html = markdown2.markdown(markdown_text)

        soup = BeautifulSoup(html, 'html.parser')

        text = str(soup)
        text = text.replace('<h1>', '[size=24][b]').replace('</h1>', '[/b][/size]')
        text = text.replace('<h2>', '[size=20][b]').replace('</h2>', '[/b][/size]')
        text = text.replace('<h3>', '[size=18][b]').replace('</h3>', '[/b][/size]')
        text = text.replace('<strong>', '[b]').replace('</strong>', '[/b]')
        text = text.replace('<em>', '[i]').replace('</em>', '[/i]')
        text = text.replace('<code>', '[font=RobotoMono-Regular][color=00ff00]').replace('</code>', '[/color][/font]')
        text = text.replace('<pre>', '[font=RobotoMono-Regular]').replace('</pre>', '[/font]')
        text = text.replace('<li>', '• ').replace('</li>', '')
        text = text.replace('<ul>', '').replace('</ul>', '')
        text = text.replace('<ol>', '').replace('</ol>', '')
        text = text.replace('<p>', '').replace('</p>', '')
        text = text.replace('<br/>', '')

        text = ''.join(BeautifulSoup(text, 'html.parser').find_all(text=True))

        self.ids.preview.text = text


class MainPanel(BoxLayout):
    vault_dir = 'my_vault'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        self.refresh_file_chooser()

    def refresh_file_chooser(self):
        self.ids.file_chooser.path = self.vault_dir
        self.ids.file_chooser._update_files()

    def load_note(self, selection):
        if selection:
            self.ids.note_editor.current_file = selection[0]
            try:
                with open(selection[0], 'r', encoding='utf-8') as f:
                    self.ids.note_editor.note_content = f.read()
                self.ids.note_editor.update_preview()
            except Exception as e:
                print(f"Error loading note: {e}")

    def show_new_note_dialog(self):
        def create_note(filename):
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
                self.refresh_file_chooser()
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
        def create_folder(foldername):
            if not foldername:
                return
            new_folder_path = os.path.join(self.vault_dir, foldername)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                self.refresh_file_chooser()
            except Exception as e:
                print(f"Error creating folder: {e}")

        dialog = InputDialog(
            title="New Folder",
            hint_text="Enter folder name",
            callback=create_folder
        )
        dialog.open()


class ObsidianApp(App):
    def build(self):
        Window.size = (1200, 800)
        return MainPanel()


if __name__ == '__main__':
    ObsidianApp().run()