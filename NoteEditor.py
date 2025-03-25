import markdown2
from bs4 import BeautifulSoup

from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout


class NoteEditor(BoxLayout):
    note_content = StringProperty('')
    preview_content = StringProperty('')
    current_file = StringProperty('')
    edit_mode = BooleanProperty(True)

    def reset_scroll_positions(self):
        # Сбрасываем позицию скролла для обоих режимов
        self.ids.editor_scroll.scroll_y = 1
        self.ids.preview_scroll.scroll_y = 1

    def save_note(self):
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.note_content)

    def update_preview(self):
        markdown_text = self.ids.editor.text
        self.note_content = markdown_text

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

        self.preview_content = text