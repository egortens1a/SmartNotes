import markdown2
from bs4 import BeautifulSoup

from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

class NoteEditor(BoxLayout):
    note_content = StringProperty('')
    preview_content = StringProperty('')
    current_file = StringProperty(None)
    edit_mode = BooleanProperty(True)

    def toggle_mode(self):
        """
        Переключатель режимов (редактирование/просмотр)
        :return: None
        """
        self.edit_mode = not self.edit_mode
        self.update_preview(force=True)
        self.ids.editor.height = max(self.ids.editor.minimum_height, self.height * 0.7) if self.edit_mode else 0
        self.ids.preview.height = max(self.ids.preview.texture_size[1], self.height * 0.7) if not self.edit_mode else 0

    def show_brush_menu(self):
        """
        открывает окно с кистями
        :return: ?
        """
        popup = Popup(title="Инструменты рисования",
                      size_hint=(0.4, 0.4))
        popup.content = Label(text="Инструменты рисования в разработке")
        popup.open()

    def summarize(self):
        """
        Выводит суммированный текст
        :return:
        """
        popup = Popup(title="Суммаризация текста",
                      size_hint=(0.6, 0.6))
        popup.content = Label(text="Суммаризация текста в разработке")
        popup.open()

    def extract_keywords(self):
        """
        выделение ключевых слов
        :return:
        """
        popup = Popup(title="Ключевые слова",
                      size_hint=(0.5, 0.5))
        popup.content = Label(text="Извлечение ключевых слов в разработке")
        popup.open()

    def save_note(self):
        """
        Сохранение записи
        :return: None
        """
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.note_content)
            popup = Popup(title="Сохранено",
                          size_hint=(0.3, 0.2))
            popup.content = Label(text="Файл успешно сохранен")
            popup.open()

    def update_preview(self, force=False):
        """
        Обработка текста для красивого отображения
        :param force:
        :return: None
        """
        if not self.edit_mode or force:
            markdown_text = self.ids.editor.text
            html = markdown2.markdown(markdown_text)
            soup = BeautifulSoup(html, 'html.parser')

            text = str(soup)
            text = text.replace('<h1>', '[size=24][b]').replace('</h1>', '[/b][/size]')
            text = text.replace('<h2>', '[size=20][b]').replace('</h2>', '[/b][/size]')
            text = text.replace('<h3>', '[size=18][b]').replace('</h3>', '[/b][/size]')
            text = text.replace('<strong>', '[b]').replace('</strong>', '[/b]')
            text = text.replace('<em>', '[i]').replace('</em>', '[/i]')
            text = text.replace('<code>', '[font=RobotoMono-Regular][color=00ff00]').replace('</code>',
                                                                                             '[/color][/font]')
            text = text.replace('<pre>', '[font=RobotoMono-Regular]').replace('</pre>', '[/font]')
            text = text.replace('<li>', '• ').replace('</li>', '')
            text = text.replace('<ul>', '').replace('</ul>', '')
            text = text.replace('<ol>', '').replace('</ol>', '')
            text = text.replace('<p>', '').replace('</p>', '')
            text = text.replace('<br/>', '')

            text = ''.join(BeautifulSoup(text, 'html.parser').find_all(string=True))

            self.preview_content = '[color=000000]' + text +  '[/color]'