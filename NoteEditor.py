import markdown2
from bs4 import BeautifulSoup

from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout


class NoteEditor(BoxLayout):
    """Основной редактор с Markdown-разметкой и превью"""

    note_content = StringProperty('')
    preview_content = StringProperty('')
    current_file = StringProperty(None)
    edit_mode = BooleanProperty(True)

    def on_edit_mode(self, instance, value):
        """
        Обработчик изменения режима редактирования/просмотра
        Args:
            instance: экземпляр виджета
            value: новое значение режима (True - редактирование)
        """
        self.ids.editor.height = max(self.ids.editor.minimum_height, self.height * 0.4) if value else 0
        self.ids.preview.height = max(self.ids.preview.texture_size[1], self.height * 0.4) if not value else 0
        self.ids.main_scroll.scroll_y = 1

    def save_note(self):
        """
        Сохраняет текущую заметку в файл
        """
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.note_content)

    def update_preview(self):
        """
        Обновляет превью Markdown-разметки
        Преобразует Markdown в форматированный текст для отображения
        """
        markdown_text = self.ids.editor.text
        self.note_content = markdown_text

        if not self.edit_mode:
            html = markdown2.markdown(markdown_text)
            soup = BeautifulSoup(html, 'html.parser')

            text = str(soup)
            text = text.replace('<h1>', '[size=24][b]').replace('</h1>', '[/b][/size]\\n')
            text = text.replace('<h2>', '[size=20][b]').replace('</h2>', '[/b][/size]\\n')
            text = text.replace('<h3>', '[size=18][b]').replace('</h3>', '[/b][/size]\\n')
            text = text.replace('<strong>', '[b]').replace('</strong>', '[/b]')
            text = text.replace('<em>', '[i]').replace('</em>', '[/i]')
            text = text.replace('<code>', '[font=RobotoMono-Regular][color=00ff00]').replace('</code>',
                                                                                             '[/color][/font]')
            text = text.replace('<pre>', '[font=RobotoMono-Regular]\\n').replace('</pre>', '\\n[/font]')
            text = text.replace('<li>', '• ').replace('</li>', '\\n')
            text = text.replace('<ul>', '').replace('</ul>', '')
            text = text.replace('<ol>', '').replace('</ol>', '')
            text = text.replace('<p>', '').replace('</p>', '\\n')
            text = text.replace('<br/>', '\\n')

            text = ''.join(BeautifulSoup(text, 'html.parser').find_all(text=True))

            self.preview_content = text
            self.ids.preview.height = max(self.ids.preview.texture_size[1], self.height * 0.4)