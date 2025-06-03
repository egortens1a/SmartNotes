import json
import datetime
import zlib
import base64
import os
import shutil

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle

import summarizer_model
from Dialogs import SummaryPopup
from utils import preprocess_to_html


class NoteEditor(BoxLayout):
    note_content = StringProperty('')
    preview_content = StringProperty('')
    current_file = StringProperty('')  # Изменено: пустая строка вместо None
    edit_mode = BooleanProperty(True)
    drawing_active = BooleanProperty(False)
    brush_color = ListProperty([201 / 256, 115 / 256, 155 / 256, 1])
    brush_width = NumericProperty(5)
    drawing_data = ListProperty([])

    def __init__(self, **kwargs):
        self._last_canvas_pos = (0, 0)
        self._erase_mode = 'point'  # режим стирания ('point' или 'line')
        super().__init__(**kwargs)
        self.current_line = None
        self.bind(drawing_data=self.update_canvas)
        self.autosave_trigger = Clock.create_trigger(self.autosave, 30)
        self._last_right_click_time = 0  # Для отслеживания двойного клика
        self.brush_settings_popup = None  # Add this line
        self._red = 1.0
        self._green = 1.0
        self._blue = 1.0
        self._brightness = 1.0

        self.summarizator = summarizer_model.TextSummarizer("ML/model")


    def toggle_mode(self):
        self.edit_mode = not self.edit_mode

        if hasattr(self, '_last_scroll_y'):
            target_scroll = self._last_scroll_y
        else:
            target_scroll = 1.0

        self.ids.editor.height = self.height
        self.ids.preview.height = self.height

        self.update_preview(force=True)
        # Анимация переключения
        anim_editor = Animation(
            height=max(self.ids.editor.minimum_height, self.height) if self.edit_mode else 0,
            duration=0.2
        )
        anim_preview = Animation(
            height=max(self.ids.preview.texture_size[1], self.height) if not self.edit_mode else 0,
            duration=0.2
        )
        anim_editor.start(self.ids.editor)
        anim_preview.start(self.ids.preview)

        Clock.schedule_once(
            lambda dt: setattr(self.ids.editor, 'scroll_y', target_scroll),
            0.21
        )
        Clock.schedule_once(lambda dt: self.update_canvas(), 0.22)

    def update_preview(self, force=False):
        """
        Обработка текста для красивого отображения
        """
        if not self.edit_mode or force:
            text = preprocess_to_html(self.ids.editor.text)
            self.preview_content = '[color=000000]' + text + '[/color]'

    def on_text_change(self, instance, value):
        """
        Обработчик изменения текста для автосохранения
        """
        self.autosave_trigger()

    def autosave(self, dt):
        """
        Автоматическое сохранение заметки
        """
        if self.current_file and self.ids.editor.text:
            self.save_note()

    def create_backup(self):
        """
        Создание резервной копии файла
        """
        if not self.current_file:
            return

        backup_dir = os.path.join(os.path.dirname(self.current_file), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(self.current_file)}_{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_name)

        shutil.copy2(self.current_file, backup_path)

    def compress_data(self, data):
        """
        Сжатие JSON данных
        """
        json_str = json.dumps(data)
        return base64.b64encode(zlib.compress(json_str.encode('utf-8'))).decode('utf-8')

    def decompress_data(self, compressed):
        """
        Распаковка данных
        """
        return json.loads(zlib.decompress(base64.b64decode(compressed)).decode('utf-8'))

    def serialize_drawing(self, drawing):
        """
        Оптимизированная сериализация одного рисунка
        """
        return {
            'color': [round(c, 3) for c in drawing['color']],  # Уменьшаем точность
            'width': round(drawing['width'], 1),
            'points': [round(p, 1) for p in drawing['points']]  # Уменьшаем точность координат
        }

    def deserialize_drawing(self, data):
        print(f"Deserializing drawing: input data = {data}")
        try:
            result = {
                'color': data.get('color', [1, 0, 0, 1]),
                'width': data.get('width', 2.0),
                'points': data.get('points', [])
            }
            print(f"Deserialization result: {result}")
            return result
        except Exception as e:
            print(f"DESERIALIZATION ERROR: {str(e)}")
            return {
                'color': [1, 0, 0, 1],
                'width': 2.0,
                'points': []
            }

    def save_note(self):
        if not self.current_file:
            return

        note_data = {
            "version": 1.3,
            "text": self.ids.editor.text,
            "drawings": []
        }

        # Сохраняем каждый рисунок отдельно с метаданными
        for drawing in self.drawing_data:
            note_data["drawings"].append({
                "points": [round(p, 1) for p in drawing['points']],
                "color": [round(c, 3) for c in drawing['color']],
                "width": round(drawing['width'], 1),
                "is_new": True
            })

        if not self.current_file.endswith('.json'):
            self.current_file = os.path.splitext(self.current_file)[0] + '.json'

        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(note_data, f, indent=2)

    def load_note(self, selection):
        if not selection:
            return

        filepath = selection[0]
        print(f"Загрузка файла: {filepath}")
        self.note_editor.current_file = filepath

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()

                if filepath.endswith('.json'):
                    try:
                        data = json.loads(content)
                        # Проверяем обязательные поля
                        if not isinstance(data, dict):
                            raise ValueError("Неверный формат JSON")

                        self.note_editor.ids.editor.text = data.get("text", "")
                        self.note_editor.drawing_data = data.get("drawings", [])
                        print(
                            f"Успешно загружен JSON: text={len(data.get('text', ''))} chars, drawings={len(data.get('drawings', []))}")
                    except json.JSONDecodeError as e:
                        print(f"Ошибка парсинга JSON: {e}")
                        self.note_editor.ids.editor.text = content  # Показываем сырой текст как fallback
                else:
                    self.note_editor.ids.editor.text = content

            self.note_editor.update_preview(force=True)
        except Exception as e:
            print(f"Критическая ошибка загрузки: {e}")
            self.note_editor.ids.editor.text = f"Ошибка загрузки: {str(e)}"

    def update_color_preview(self, *args):
        """Обновляет превью цвета в popup настроек кисти"""
        if hasattr(self, 'brush_settings_popup') and self.brush_settings_popup:
            if hasattr(self.brush_settings_popup, 'ids'):
                # Получаем слайдер и превью из ids
                alpha_slider = self.brush_settings_popup.ids.get('alpha_slider')
                color_preview = self.brush_settings_popup.ids.get('color_preview')

                if color_preview:
                    color_preview.canvas.before.clear()
                    with color_preview.canvas.before:
                        Color(*self.brush_color)
                        Rectangle(pos=color_preview.pos, size=color_preview.size)

                # Обновляем значение слайдера, если он есть
                if alpha_slider:
                    alpha_slider.value = self.brush_color[3]

    def toggle_drawing_mode(self, *args):
        """Переключение режима рисования - работает ТОЛЬКО в режиме просмотра"""
        if not self.edit_mode:  # Только в режиме просмотра
            self.drawing_active = not self.drawing_active  # Переключаем состояние

            # Show/hide brush settings popup
            if self.drawing_active:
                self.show_brush_settings()
            elif self.brush_settings_popup:
                self.brush_settings_popup.dismiss()
                self.brush_settings_popup = None

            # Блокируем/разблокируем другие кнопки, кроме этой
            self.ids.main_scroll.do_scroll = not self.drawing_active

            # Если выходим из режима рисования - завершаем текущую линию
            if not self.drawing_active:
                self.current_line = None

            self.update_canvas()
        else:
            # В режиме редактора просто мигаем кнопкой
            anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
            anim.start(self.ids.exit_drawing_btn)

    def clear_editor(self):
        """Очищает редактор и сбрасывает все данные"""
        self.current_file = ''  # Пустая строка вместо None
        self.ids.editor.text = ""
        self.drawing_data = []
        self.update_canvas()

    def on_touch_down(self, touch):
        if self.ids.exit_drawing_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if not self.edit_mode and self.ids.preview.collide_point(*touch.pos):
            local_pos = self.ids.preview.to_widget(touch.x, touch.y, relative=True)
            local_x = max(0, min(self.ids.preview.width, local_pos[0]))
            local_y = max(0, min(self.ids.preview.height, local_pos[1]))

            if 'right' in touch.button and self.drawing_active:
                current_time = touch.time_start
                if current_time - self._last_right_click_time < 0.3:
                    self._erase_mode = 'line' if self._erase_mode == 'point' else 'point'
                    self.show_popup("Режим стирания", f"Режим: {'линия' if self._erase_mode == 'line' else 'точка'}")
                self._last_right_click_time = current_time
                self.erase_at_point(local_x, local_y)
                return True

            elif 'left' in touch.button and self.drawing_active:
                self.current_line = None
                self.current_line = {
                    'points': [local_x, local_y],
                    'color': list(self.brush_color),
                    'width': self.brush_width,
                    'is_new': True
                }
                self.drawing_data.append(self.current_line)
                return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.edit_mode and self.drawing_active and self.ids.preview.collide_point(*touch.pos):
            local_pos = self.ids.preview.to_widget(touch.x, touch.y, relative=True)
            local_x = max(0, min(self.ids.preview.width, local_pos[0]))
            local_y = max(0, min(self.ids.preview.height, local_pos[1]))

            if 'right' in touch.button:
                if self._erase_mode == 'line' and hasattr(self, '_last_erase_pos'):
                    self.erase_along_line(self._last_erase_pos[0], self._last_erase_pos[1], local_x, local_y)
                else:
                    self.erase_at_point(local_x, local_y)
                self._last_erase_pos = (local_x, local_y)
                return True
            elif 'left' in touch.button and self.current_line:
                self.current_line['points'].extend([local_x, local_y])
                self.update_canvas()
                return True

        return super().on_touch_move(touch)

    def erase_along_line(self, x1, y1, x2, y2, radius=5):
        """Стирает рисунки вдоль линии между точками (x1,y1) и (x2,y2)"""
        steps = max(3, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 2))
        changed = False

        for i in range(steps):
            t = i / (steps - 1)
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)

            new_drawing_data = []
            for drawing in self.drawing_data:
                points = drawing['points']
                remove_drawing = False

                for j in range(0, len(points) - 1, 2):
                    px, py = points[j], points[j + 1]
                    distance = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
                    if distance < radius:
                        remove_drawing = True
                        changed = True
                        break

                if not remove_drawing:
                    new_drawing_data.append(drawing)

            self.drawing_data = new_drawing_data

        if changed:
            self.update_canvas()
        return changed

    def erase_at_point(self, x, y, radius=10):
        """
        Точно стирает под курсором, разрывая линии в месте пересечения
        """
        if not self.drawing_data:
            return False

        changed = False
        new_drawings = []

        for drawing in self.drawing_data:
            points = drawing['points']
            if len(points) < 4:
                continue

            new_segments = []
            current_segment = [points[0], points[1]]

            for i in range(2, len(points) - 1, 2):
                x1, y1 = points[i - 2], points[i - 1]
                x2, y2 = points[i], points[i + 1]

                if x1 == x2 and y1 == y2:
                    continue

                if self.line_intersects_circle(x1, y1, x2, y2, x, y, radius):
                    changed = True
                    if len(current_segment) >= 2:
                        new_segments.append(current_segment.copy())
                    current_segment = []
                else:
                    if not current_segment:
                        current_segment.extend([x1, y1])
                    current_segment.extend([x2, y2])

            if current_segment:
                new_segments.append(current_segment)

            for segment in new_segments:
                if len(segment) >= 4:
                    new_drawing = drawing.copy()
                    new_drawing['points'] = segment
                    new_drawings.append(new_drawing)

        if changed:
            self.drawing_data = new_drawings
            self.update_canvas()
            return True
        return False

    def line_intersects_circle(self, x1, y1, x2, y2, cx, cy, r):
        """
        Проверяет, пересекает ли отрезок окружность
        """
        # Переносим координаты так, чтобы окружность была в центре
        x1 -= cx
        y1 -= cy
        x2 -= cx
        y2 -= cy

        dx = x2 - x1
        dy = y2 - y1
        a = dx * dx + dy * dy

        if a == 0:
            return x1 * x1 + y1 * y1 <= r * r

        b = 2 * (x1 * dx + y1 * dy)
        c = x1 * x1 + y1 * y1 - r * r

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return False  # Нет пересечения

        t1 = (-b + discriminant ** 0.5) / (2 * a)
        t2 = (-b - discriminant ** 0.5) / (2 * a)

        # Проверяем, что хотя бы один корень в пределах отрезка [0,1]
        return (0 <= t1 <= 1) or (0 <= t2 <= 1)

    def smooth_edges(self, smoothing_radius=10):
        """
        Добавляет промежуточные точки на концах линий для сглаживания
        """
        for drawing in self.drawing_data:
            points = drawing['points']
            if len(points) < 4:  # Нечего сглаживать
                continue

            # Сглаживаем начало линии
            x1, y1 = points[0], points[1]
            x2, y2 = points[2], points[3]
            if ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 < smoothing_radius:
                # Добавляем промежуточную точку
                points.insert(0, (x1 + x2) / 2)
                points.insert(1, (y1 + y2) / 2)

            # Сглаживаем конец линии
            x_end1, y_end1 = points[-2], points[-1]
            x_end2, y_end2 = points[-4], points[-3]
            if ((x_end1 - x_end2) ** 2 + (y_end1 - y_end2) ** 2) ** 0.5 < smoothing_radius:
                # Добавляем промежуточную точку
                points.append((x_end1 + x_end2) / 2)
                points.append((y_end1 + y_end2) / 2)

    def show_popup(self, title, message):
        """
        Вспомогательный метод для уведомлений
        """
        Popup(title=title,
              content=Label(text=message),
              size_hint=(0.4, 0.2)).open()

    def update_canvas(self, *args):
        if not hasattr(self, 'ids'):
            return

        self.ids.preview.canvas.after.clear()

        if not self.drawing_data:
            return

        # Рисуем ТОЛЬКО в превью
        with self.ids.preview.canvas.after:
            for drawing in self.drawing_data:
                try:
                    Color(*drawing['color'])
                    if len(drawing['points']) >= 2:
                        Line(
                            points=drawing['points'],
                            width=drawing['width'],
                            cap='round',
                            joint='round'
                        )
                except Exception as e:
                    print(f"Error drawing: {e}")

    def normalize_coordinates(self, points, width, height):
        """
        Нормализует координаты относительно размера редактора
        """
        normalized = []
        for i in range(0, len(points), 2):
            x = points[i] / width if width > 0 else 0
            y = points[i + 1] / height if height > 0 else 0
            normalized.extend([x, y])
        return normalized

    def show_brush_menu(self):
        """
        Переключает режим рисования
        """
        self.drawing_active = not self.drawing_active
        self.ids.editor.disabled = self.drawing_active
        self.ids.exit_drawing_btn.opacity = 1 if self.drawing_active else 0

        if not self.drawing_active:
            self.current_line = None

        self.update_canvas()

    def save_color_settings(self, r, g, b):
        """
        Сохраняет базовые RGB компоненты (без учета яркости)
        """
        self.red = r
        self.green = g
        self.blue = b
        self.update_brush_settings()

    def get_red(self):
        return self.red

    def get_green(self):
        return self.green

    def get_blue(self):
        return self.blue

    def get_brightness(self):
        return self.brightness

    # Добавляем методы для работы с цветом
    def get_rgb(self):
        """
        Возвращает текущие RGB значения
        """
        return self._red, self._green, self._blue

    def set_rgb(self, r, g, b):
        """
        Устанавливает RGB значения
        """
        self._red = max(0.0, min(1.0, float(r)))
        self._green = max(0.0, min(1.0, float(g)))
        self._blue = max(0.0, min(1.0, float(b)))
        self.update_brush_settings()

    def set_brightness(self, value):
        """
        Устанавливает яркость
        """
        self._brightness = max(0.1, min(2.0, float(value)))
        self.update_brush_settings()

    def update_brush_settings(self):
        """
        Обновляет все параметры кисти
        """
        self.brush_color = [
            min(1.0, self._red * self._brightness),
            min(1.0, self._green * self._brightness),
            min(1.0, self._blue * self._brightness),
            self.brush_color[3]  # Сохраняем текущую прозрачность
        ]
        self.update_thickness_preview()
        self.update_canvas()

    def set_alpha(self, value):
        """
        Устанавливает прозрачность
        """
        self.brush_color[3] = max(0.1, min(1.0, float(value)))
        self.update_thickness_preview()
        self.update_canvas()


    def on_brush_color(self, instance, value):
        """
        Автоматически вызывается при изменении brush_color
        """
        self.update_thickness_preview()

    def set_alpha(self, value):
        """
        Устанавливает прозрачность и сразу обновляет превью
        """
        self.brush_color[3] = max(0.1, min(1.0, float(value)))
        self.update_thickness_preview()
        self.update_canvas()

    def update_thickness_preview(self):
        """
        Мгновенное обновление превью толщины
        """
        if hasattr(self, 'brush_settings_popup') and self.brush_settings_popup:
            if hasattr(self.brush_settings_popup.ids, 'thickness_preview'):
                preview = self.brush_settings_popup.ids.thickness_preview.ids.line_preview
                preview.canvas.after.clear()
                with preview.canvas.after:
                    Color(*self.brush_color)
                    Line(
                        points=[preview.x, preview.center_y, preview.right, preview.center_y],
                        width=self.brush_width,
                        cap='round'
                    )


    def show_brush_settings(self):
        if not hasattr(self, 'brush_settings_popup') or self.brush_settings_popup is None:
            from kivy.factory import Factory
            self.brush_settings_popup = Factory.BrushSettingsPopup()

            def init_values(dt):
                if hasattr(self.brush_settings_popup, 'ids'):
                    ids = self.brush_settings_popup.ids
                    ids.red_slider.value = self._red
                    ids.green_slider.value = self._green
                    ids.blue_slider.value = self._blue
                    ids.width_slider.value = self.brush_width
                    self.update_thickness_preview()

            Clock.schedule_once(init_values)

        self.brush_settings_popup.open()

    def apply_color(self, r, g, b, brightness=1.0, alpha=1.0):
        """
        Применяет цвет и обновляет слайдеры
        """
        self._red = r
        self._green = g
        self._blue = b
        self._brightness = brightness

        # Обновляем brush_color (учитывая яркость)
        self.brush_color = [
            min(1.0, r * brightness),
            min(1.0, g * brightness),
            min(1.0, b * brightness),
            alpha
        ]

        # Если popup открыт - обновляем слайдеры
        if hasattr(self, 'brush_settings_popup') and self.brush_settings_popup:
            if hasattr(self.brush_settings_popup, 'ids'):
                ids = self.brush_settings_popup.ids
                ids.red_slider.value = r
                ids.green_slider.value = g
                ids.blue_slider.value = b
                ids.brightness_slider.value = brightness
                ids.alpha_slider.value = alpha

        self.update_canvas()

    def set_brush_width(self, value):
        """
        Устанавливает толщину кисти с обновлением превью
        """
        self.brush_width = max(1, min(50, value))
        self.update_canvas()
        self.update_thickness_preview()

    def summarize(self):
        """
        Суммаризация с индикатором загрузки
        """
        if not self.ids.editor.text:
            self._show_summary_popup("Нет текста для суммаризации")
            return

        popup = Popup(
            title="Суммаризация",
            size_hint=(0.6, 0.4),
            separator_color=[179 / 256, 179 / 256, 179 / 256, 1]
        )
        popup.content = Label(text="Обработка текста...")
        popup.open()

        def summary_callback(summary):
            popup.dismiss()
            self._show_summary_popup(summary)

        summary = self.summarizator.summarize(self.ids.editor.text)
        summary_callback(summary)

    def _show_summary_popup(self, text):
        """
        Показывает попап с суммаризацией, используя KV-шаблон
        """
        popup = SummaryPopup()
        popup.ids.summary_text.text = preprocess_to_html(text)
        popup.open()
