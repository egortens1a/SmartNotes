from kivy.graphics import Rectangle, Color
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import os
import utils

from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label


class InputDialog(Popup):
    """
    Создание файла
    """
    def __init__(self, title, hint_text, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.ids.input.hint_text = hint_text
        self.callback = callback

    def on_ok(self):
        self.callback(self.ids.input.text)
        self.dismiss()


class ClickableLabel(ButtonBehavior, Label):
    """Лейбл с возможностью клика и красивым оформлением"""

    """Лейбл с возможностью клика и улучшенным отображением текста"""

    def __init__(self, **kwargs):
        self.background_color = kwargs.pop('background_color', [0.95, 0.95, 0.95, 1])
        super().__init__(**kwargs)

        # Настройки внешнего вида
        self.background_normal = ''
        self.background_color = [0.85, 0.85, 0.85, 1]
        self.font_size = '16sp'  # Базовый размер шрифта
        self.halign = 'left'  # Выравнивание по левому краю
        self.valign = 'top'  # Выравнивание по верхнему краю
        self.padding = [20, 15]  # Стандартные отступы

        # Создаем элементы canvas
        with self.canvas.before:
            self.bg_color = Color(*self.background_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.border_color = Color(0.8, 0.8, 0.8, 1)
            self.border_rect = Rectangle(pos=self.pos, size=(self.width, 1))

        self.bind(
            pos=self._update_graphics,
            size=self._update_graphics,
            width=lambda *x: setattr(self, 'text_size', (self.width, None))
        )

    def _update_graphics(self, *args):
        """Обновляем графические элементы при изменении размера/позиции"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.pos = self.pos
        self.border_rect.size = (self.width, 1)

    def on_state(self, instance, value):
        """Изменяем цвет фона при нажатии"""
        if value == 'down':
            self.bg_color.rgba = self.background_color
        else:
            self.bg_color.rgba = self.background_color

class SearchDialog(Popup):
    def __init__(self, vault_dir, on_file_select_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.vault_dir = vault_dir
        self.on_file_select_callback = on_file_select_callback
        self.empty_label = Label(
            text="Ничего не найдено :(",
            font_size=dp(18),
            color=(0.6, 0.6, 0.6, 1),
            halign='center',
            valign='middle'
        )

    def do_search(self, query):
        if not query.strip():
            self._show_empty_state("Введите поисковый запрос")
            return

        # Очищаем предыдущие результаты
        self.ids.results_container.clear_widgets()

        # Загружаем все заметки из хранилища
        documents = []
        for root, _, files in os.walk(self.vault_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            documents.append((filepath, content))
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")

        # Выполняем поиск
        results = utils.compute_tfidf_for_search(query, documents)

        if not results:
            self._show_empty_state("Ничего не найдено :(")
            return

        # Отображаем результаты в виде карточек
        for filepath, score in results[:5]:  # Показываем топ-5 результатов
            card = self._create_result_card(filepath, score)
            self.ids.results_container.add_widget(card)

    def _create_result_card(self, filepath, score):
        """Создает карточку результата поиска с крупным текстом названий"""
        filename = os.path.splitext(os.path.basename(filepath))[0]
        rel_path = os.path.relpath(filepath, self.vault_dir)

        card = ClickableLabel(
            text=f"[size=25][b]{filename}[/b][/size]\n[size=12]{rel_path}[/size]",
            markup=True,
            size_hint_y=None,
            height=dp(90),  # Увеличиваем высоту для крупного текста
            halign='left',
            valign='top',
            color=(0.2, 0.2, 0.2, 1),
            padding=(dp(20), dp(15)),
            background_color=(0.95, 0.95, 0.95, 1)
        )

        # Гарантируем перенос текста по ширине
        card.text_size = (card.width, None)
        card.bind(width=lambda *x: setattr(card, 'text_size', (card.width, None)))

        card.filepath = filepath
        card.bind(on_press=self._on_file_selected)
        return card

    def _show_empty_state(self, message):
        """Показывает состояние пустых результатов"""
        self.ids.results_container.clear_widgets()
        self.empty_label.text = message
        self.ids.results_container.add_widget(self.empty_label)

    def _on_file_selected(self, instance):
        """Обработчик выбора файла"""
        if self.on_file_select_callback:
            self.on_file_select_callback(instance.filepath)
        self.dismiss()