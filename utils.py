
import math
from collections import defaultdict
import re

import markdown2
from bs4 import BeautifulSoup

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
    text = re.sub(r'\s+', ' ', text).strip()

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
    total_docs = len(processed_docs) + 1

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

def preprocess_to_html(text):
    '''
    Конвертирует исходный текст с Markdown-разметкой в html верстку
    :param text: исходный текст
    :return: html-верстка
    '''
    html = markdown2.markdown(text)
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
    return text