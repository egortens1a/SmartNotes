import torch
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
from threading import Thread
from queue import Queue


class TextSummarizer:
    def __init__(self, model_path):
        print("[Summarizer] Инициализация модели...")
        #0odel_path = r"alan-turing-institute/mt5-small-finetuned-mnli-xtreme-xnli"
        self.model_path = model_path
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.ready = False
        self.stop_flag = False  # Флаг для остановки потока

        # Запуск потока для инициализации модели
        self.init_thread = Thread(target=self._initialize_in_thread, daemon=True)
        self.init_thread.start()

        # Поток для обработки задач
        self.process_thread = Thread(target=self._process_in_thread, daemon=True)
        self.process_thread.start()

    def _initialize_in_thread(self):
        """
        Инициализация модели в потоке
        """
        try:
            self.tokenizer = MT5Tokenizer.from_pretrained(self.model_path)
            self.model = MT5ForConditionalGeneration.from_pretrained(self.model_path)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model = self.model.to(self.device)
            self.ready = True

            print("[Summarizer] Модель загружена и готова к работе!")
        except Exception as e:
            print("[Summarizer] Ошибка загрузки модели: 1")
            self.ready = False

    def summarize(self, text):
        """
        Публичный метод для запроса суммаризации
        """
        if not self.ready:
            return "[Ошибка] Модель еще не загружена!"

        print("[Summarizer] Добавление задачи в очередь")
        self.task_queue.put(text)
        return self.result_queue.get()  # Блокируется, пока не получит результат

    def _process_in_thread(self):
        """
        Основной цикл обработки задач.
        """
        while not self.stop_flag:
            try:
                text = self.task_queue.get()
                if text is None:  # Сигнал остановки
                    break

                print("[Summarizer] Обработка текста длиной символов")

                # Разбивка текста на части (~500 токенов)
                chunks = self._split_text(text)
                summaries = []

                for i, chunk in enumerate(chunks):
                    print("[Summarizer] Обработка части")
                    summary = self._summarize_chunk(chunk)
                    summaries.append(summary)

                full_summary = " ".join(summaries)
                self.result_queue.put(full_summary)

            except Exception as e:
                print("[Summarizer] Ошибка обработки 2")
                self.result_queue.put(f"[Ошибка] {str(e)}")

    def _split_text(self, text, max_tokens=1024):
        """
        Разбивает текст на части по предложениям
        """
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sent in sentences:
            if len(current_chunk.split()) + len(sent.split()) <= max_tokens:
                current_chunk += sent + ". "
            else:
                chunks.append(current_chunk)
                current_chunk = sent + ". "

        if current_chunk:
            chunks.append(current_chunk)

        print("[Summarizer] Текст разбит на {len(chunks)} частей")
        return chunks

    def _summarize_chunk(self, text):
        """
        Суммаризация одной части текста
        """
        inputs = self.tokenizer(
            "simplify |" + text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        summary_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=256,
            min_length=128,
            num_beams=4,
            length_penalty=0.7,
            no_repeat_ngram_size=3,
            early_stopping=True
        )
        print("[Summarizer] Задача выполнена")
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    def shutdown(self):
        """
        Корректное завершение работы
        """
        self.stop_flag = True
        self.task_queue.put(None)  # Сигнал остановки