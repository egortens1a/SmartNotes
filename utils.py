
import math
from collections import defaultdict
import os
import re


def compute_tfidf(target_text, corpus):
    """
    Вычисляет TF-IDF для слов в целевом тексте относительно корпуса документов.

    Аргументы:
    ----------
    target_text : str
        Текст, для которого вычисляется TF-IDF (разбивается на слова по пробелам).
    corpus : list of str
        Список текстов (каждый текст разбивается на слова по пробелам).

    Возвращает:
    -----------
    dict
        Словарь {слово: tfidf_вес} для слов в `target_text`.
    """

    # Разбиваем тексты на слова (можно улучшить токенизацию)
    target_words = target_text.lower().split()
    corpus_words = [doc.lower().split() for doc in corpus]

    # === 1. Вычисляем TF (Term Frequency) для целевого текста ===
    tf = defaultdict(float)
    total_words = len(target_words)
    for word in target_words:
        tf[word] += 1.0 / total_words

    # === 2. Вычисляем IDF (Inverse Document Frequency) ===
    idf = defaultdict(float)
    total_docs = len(corpus_words) + 1  # +1 чтобы учесть сам target_text

    # Считаем, в скольких документах встречается слово
    doc_freq = defaultdict(int)
    # Учитываем слова из корпуса
    for doc in corpus_words:
        for word in set(doc):  # set() чтобы учитывать слово только 1 раз в документе
            doc_freq[word] += 1
    # Учитываем слова из target_text (как отдельный документ)
    for word in set(target_words):
        doc_freq[word] += 1

    # Вычисляем IDF: log(общее_число_документов / число_документов_со_словом)
    for word, count in doc_freq.items():
        idf[word] = math.log(total_docs / count)

    # === 3. Вычисляем TF-IDF (только для слов из target_text) ===
    tfidf = {}
    for word in set(target_words):  # Убираем дубликаты
        tfidf[word] = tf[word] * idf.get(word, 0)

    top10 = sorted(tfidf, key=lambda x: tfidf[x])[-10:]
    return tfidf

def preprocess_markdown(text):
    """
    Очищает текст от Markdown разметки и приводит к нижнему регистру.
    Удаляет:
    - заголовки (#, ## и т.д.)
    - ссылки
    - изображения
    - жирный/курсив
    - код
    - списки
    """
    # Удаляем Markdown разметку
    text = re.sub(r'#{1,6}\s*', '', text)  # Заголовки
    text = re.sub(r'\!?\[.*?\]\(.*?\)', '', text)  # Ссылки и изображения
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)  # Жирный/курсив
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)  # Код
    text = re.sub(r'[\-\*\+]\s+', '', text)  # Маркеры списков
    text = re.sub(r'\d+\.\s+', '', text)  # Нумерованные списки

    # Оставляем только буквы, цифры и пробелы
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()

    return text


def compute_tfidf_for_search(query, documents):
    """
    Вычисляет TF-IDF для поискового запроса относительно документов.

    Аргументы:
    ----------
    query : str
        Поисковый запрос (разбивается на слова по пробелам).
    documents : list of tuple (filepath, text)
        Список документов, где каждый документ - это (путь к файлу, текст).

    Возвращает:
    -----------
    list of tuple
        Отсортированный список (путь к файлу, оценка релевантности) по убыванию.
    """
    # Обрабатываем запрос
    query_words = preprocess_markdown(query).split()

    # Обрабатываем документы
    processed_docs = []
    for filepath, text in documents:
        processed_text = preprocess_markdown(text)
        processed_docs.append((filepath, processed_text.split()))

    # === 1. Вычисляем TF (Term Frequency) для запроса ===
    query_tf = defaultdict(float)
    total_words = len(query_words)
    for word in query_words:
        query_tf[word] += 1.0 / total_words

    # === 2. Вычисляем IDF (Inverse Document Frequency) ===
    idf = defaultdict(float)
    total_docs = len(processed_docs) + 1  # +1 для самого запроса

    # Считаем, в скольких документах встречается слово
    doc_freq = defaultdict(int)

    # Учитываем слова из документов
    for _, words in processed_docs:
        for word in set(words):
            doc_freq[word] += 1

    # Учитываем слова из запроса
    for word in set(query_words):
        doc_freq[word] += 1

    # Вычисляем IDF
    for word, count in doc_freq.items():
        idf[word] = math.log(total_docs / count)

    # === 3. Вычисляем релевантность документов ===
    results = []

    for filepath, doc_words in processed_docs:
        # Вычисляем TF для документа
        doc_tf = defaultdict(float)
        doc_length = len(doc_words)
        for word in doc_words:
            doc_tf[word] += 1.0 / doc_length

        # Вычисляем оценку релевантности
        score = 0.0
        for word in set(query_words):
            if word in doc_tf:
                score += query_tf[word] * doc_tf[word] * idf[word]

        if score > 0:
            results.append((filepath, score))

    # Сортируем по убыванию релевантности
    results.sort(key=lambda x: -x[1])

    return results