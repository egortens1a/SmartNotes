from kivy.uix.popup import Popup


class InputDialog(Popup):
    def __init__(self, title, hint_text, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.ids.input.hint_text = hint_text
        self.callback = callback

    def on_ok(self):
        self.callback(self.ids.input.text)
        self.dismiss()