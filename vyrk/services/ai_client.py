# -*- coding: utf-8 -*-
"""AI client: обращается к внешнему AI API или использует локальный fallback."""

from __future__ import annotations  # Включает современную запись type hints.

from collections import Counter  # Counter нужен, чтобы считать жанры избранных фильмов.
from typing import Any  # Any используется для словарей с разными полями фильма.

import requests  # requests отправляет HTTP-запросы во внешний AI API.


class AiClient:
    """Класс для блока AI client из схемы: AI client -> AI API."""

    DEFAULT_QUERIES = ["sci-fi", "drama", "adventure"]  # Стартовые подсказки, пока избранного нет.

    def __init__(self, api_key: str = "", api_url: str = "", model: str = "") -> None:
        self.api_key = api_key  # Сохраняем ключ AI API.
        self.api_url = api_url  # Сохраняем адрес AI API.
        self.model = model  # Сохраняем название модели.

    @property
    def live_mode(self) -> bool:
        return bool(self.api_key and self.api_url and self.model)  # True означает, что внешний AI API настроен.

    def suggest_queries(self, favorites: list[dict[str, Any]]) -> dict[str, Any]:
        fallback = self._local_suggestions(favorites)  # Сначала готовим локальный запасной вариант.
        if not favorites:  # Без избранных фильмов нечего отправлять в AI API.
            return fallback  # Возвращаем стартовые подсказки.
        if not self.live_mode:  # Если ключи AI API не настроены.
            return fallback  # Возвращаем локальную рекомендацию по жанрам.
        try:
            ai_text = self._request_ai(favorites)  # Запрашиваем рекомендации у внешнего AI API.
            queries = self._parse_queries(ai_text)  # Превращаем ответ AI в список поисковых запросов.
        except requests.RequestException:  # Если сеть или AI API дали ошибку.
            return fallback  # Не ломаем сайт и возвращаем локальные рекомендации.
        if not queries:  # AI может вернуть пустой или неудобный ответ.
            return fallback  # В таком случае снова используем fallback.
        return {
            "title": "AI API подсказка",  # Заголовок блока рекомендаций.
            "text": "Внешний AI API предложил похожие направления для поиска.",  # Текст-объяснение.
            "queries": queries[:3],  # На экран выводим максимум три подсказки.
            "source": "ai_api",  # Помечаем, что источник рекомендаций — внешний AI API.
        }

    def _request_ai(self, favorites: list[dict[str, Any]]) -> str:
        movie_lines = [
            f"- {movie.get('Title', 'Unknown')} ({movie.get('Year', 'N/A')}), genres: {movie.get('Genre', 'N/A')}"
            for movie in favorites[:8]
        ]  # Берем не больше восьми фильмов, чтобы prompt был коротким.
        prompt = (
            "Suggest three short movie search queries based on these favorites. "
            "Return only comma-separated queries, no explanations.\n" + "\n".join(movie_lines)
        )  # Просим AI вернуть простой формат, который легко разобрать.
        payload = {
            "model": self.model,  # Передаем название модели.
            "messages": [
                {"role": "system", "content": "You recommend concise movie search queries."},
                {"role": "user", "content": prompt},
            ],  # Формируем сообщения для chat completions API.
            "temperature": 0.4,  # Низкая температура делает ответы стабильнее.
            "max_tokens": 80,  # Ответ должен быть коротким.
        }  # Тело запроса для OpenAI-compatible API.
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}  # Авторизация.
        response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)  # Отправляем запрос.
        response.raise_for_status()  # Превращаем HTTP-ошибки в исключения.
        data = response.json()  # Читаем JSON-ответ.
        return data["choices"][0]["message"]["content"]  # Достаем текст из ответа AI.

    def _local_suggestions(self, favorites: list[dict[str, Any]]) -> dict[str, Any]:
        if not favorites:  # Если избранных фильмов нет.
            return {
                "title": "Начните с поиска",  # Заголовок блока.
                "text": "Сохраните несколько фильмов, и программа предложит новые запросы по жанрам.",  # Подсказка.
                "queries": self.DEFAULT_QUERIES,  # Начальные поисковые идеи.
                "source": "local_demo",  # Источник — локальная логика.
            }
        genres = Counter()  # Создаем счетчик жанров.
        for movie in favorites:  # Перебираем избранные фильмы.
            for genre in movie.get("Genre", "").split(","):  # Разделяем строку жанров через запятую.
                clean = genre.strip().lower()  # Убираем пробелы и приводим жанр к нижнему регистру.
                if clean and clean != "n/a":  # Пропускаем пустые и неизвестные значения.
                    genres[clean] += 1  # Увеличиваем счетчик жанра.
        top_genres = [genre for genre, _count in genres.most_common(3)]  # Берем три самых частых жанра.
        if not top_genres:  # Если жанры не удалось извлечь.
            top_genres = self.DEFAULT_QUERIES  # Используем стартовые подсказки.
        return {
            "title": "Персональная подсказка",  # Заголовок блока.
            "text": "Чаще всего в избранном встречаются эти жанры.",  # Объяснение рекомендации.
            "queries": top_genres,  # Быстрые ссылки для нового поиска.
            "source": "local_demo",  # Источник — локальная логика.
        }

    def _parse_queries(self, text: str) -> list[str]:
        normalized = text.replace("\n", ",")  # Считаем переносы строк разделителями.
        raw_items = normalized.split(",")  # Делим ответ на отдельные варианты.
        cleaned = [item.strip(" -0123456789.").strip().lower() for item in raw_items]  # Чистим нумерацию.
        return [item for item in cleaned if item][:3]  # Возвращаем до трех непустых запросов.
