from kivy.uix.popup import Popup


class InputDialog(Popup):
    """Диалоговое окно для ввода текста"""

    def __init__(self, title, hint_text, callback, **kwargs):
        """
        Инициализирует диалоговое окно
        Args:
            title: заголовок окна
            hint_text: подсказка в поле ввода
            callback: функция обратного вызова при нажатии OK
        """
        super().__init__(**kwargs)
        self.title = title
        self.ids.input.hint_text = hint_text
        self.callback = callback

    def on_ok(self):
        """
        Обрабатывает нажатие кнопки OK
        Вызывает callback-функцию с введённым текстом и закрывает окно
        """
        self.callback(self.ids.input.text)
        self.dismiss()