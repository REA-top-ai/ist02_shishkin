# -*- coding: utf-8 -*-
"""Клиент для реального сайта OMDb API: https://www.omdbapi.com/."""

from __future__ import annotations  # Включает современную запись type hints.

from typing import Any  # Any используется для словарей с ответами API.

import requests  # requests отправляет HTTP-запросы на OMDb.


class OmdbClient:
    """Обертка над OMDb API без локальной подмены фильмов."""

    API_URL = "https://www.omdbapi.com/"  # HTTPS-версия API из документации OMDb.

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key  # Сохраняем OMDb API key из .env.

    @property
    def demo_mode(self) -> bool:
        return False  # В финальной версии локальный demo для OMDb не используется.

    def search(self, query: str, year: str = "") -> dict[str, Any]:
        query = query.strip()  # Убираем лишние пробелы из поискового текста.
        year = year.strip()  # Убираем лишние пробелы из года.
        if not query:  # Параметр OMDb "s" не может быть пустым.
            return {"ok": False, "error": "Введите название фильма.", "movies": [], "demo": False}
        if not self.api_key:  # Без ключа нельзя обращаться к OMDb.
            return self._missing_key_response()  # Возвращаем ошибку настройки ключа.
        params = self._search_params(query, year)  # Собираем параметры OMDb для поиска через "s".
        try:
            payload = self._get_json(params)  # Отправляем запрос и читаем JSON.
        except requests.RequestException as error:  # Обрабатываем сетевую ошибку.
            return {"ok": False, "error": f"Ошибка соединения с OMDb: {error}", "movies": [], "demo": False}
        if payload.get("Response") == "False":  # OMDb так сообщает о неудачном поиске.
            return {"ok": False, "error": payload.get("Error", "Фильм не найден."), "movies": [], "demo": False}
        movies = [self._short_movie(item) for item in payload.get("Search", [])]  # Нормализуем карточки.
        return {"ok": True, "error": "", "movies": movies, "demo": False}  # Возвращаем результат для UI/API.

    def get_by_id(self, imdb_id: str) -> dict[str, Any] | None:
        imdb_id = imdb_id.strip()  # Убираем пробелы из imdbID.
        if not self.api_key:  # Без ключа нельзя обращаться к OMDb.
            return None  # Роут покажет ошибку.
        params = self._id_params(imdb_id)  # Собираем параметры OMDb для поиска через "i".
        try:
            payload = self._get_json(params)  # Получаем один фильм по IMDb ID.
        except requests.RequestException:  # Если OMDb недоступен.
            return None  # Возвращаем None вместо падения сайта.
        if payload.get("Response") == "False":  # OMDb сообщает, что фильм не найден.
            return None  # Возвращаем None для отсутствующего фильма.
        return self._detail_movie(payload)  # Нормализуем подробную карточку.

    def get_by_title(self, title: str, year: str = "") -> dict[str, Any] | None:
        title = title.strip()  # Убираем пробелы из названия.
        year = year.strip()  # Убираем пробелы из года.
        if not title:  # Параметр OMDb "t" не может быть пустым.
            return None  # Пустой запрос не отправляем.
        if not self.api_key:  # Без ключа нельзя обращаться к OMDb.
            return None  # Роут вернет ошибку.
        params = self._title_params(title, year)  # Собираем параметры OMDb для поиска через "t".
        try:
            payload = self._get_json(params)  # Получаем фильм по названию.
        except requests.RequestException:  # Если OMDb недоступен.
            return None  # Возвращаем None вместо падения сайта.
        if payload.get("Response") == "False":  # OMDb сообщает, что фильм не найден.
            return None  # Возвращаем None для отсутствующего фильма.
        return self._detail_movie(payload)  # Нормализуем подробную карточку.

    def _search_params(self, query: str, year: str = "") -> dict[str, str]:
        params = {"apikey": self.api_key, "s": query, "type": "movie", "r": "json"}  # Параметры OMDb By Search.
        if year:  # Год является необязательным параметром.
            params["y"] = year  # Добавляем параметр y только при вводе года.
        return params  # Возвращаем точные параметры HTTP-запроса.

    def _id_params(self, imdb_id: str) -> dict[str, str]:
        return {"apikey": self.api_key, "i": imdb_id, "plot": "full", "r": "json"}  # Параметры OMDb By ID.

    def _title_params(self, title: str, year: str = "") -> dict[str, str]:
        params = {"apikey": self.api_key, "t": title, "type": "movie", "plot": "full", "r": "json"}  # By Title.
        if year:  # Год является необязательным параметром.
            params["y"] = year  # Добавляем параметр y только при вводе года.
        return params  # Возвращаем точные параметры HTTP-запроса.

    def _get_json(self, params: dict[str, str]) -> dict[str, Any]:
        response = requests.get(self.API_URL, params=params, timeout=8)  # Отправляем запрос на www.omdbapi.com.
        response.raise_for_status()  # Если HTTP-статус плохой, вызываем исключение.
        return response.json()  # Преобразуем JSON-ответ OMDb в словарь Python.

    def _missing_key_response(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "OMDb API key не настроен. Получите ключ на https://www.omdbapi.com/apikey.aspx и вставьте его в .env как OMDB_API_KEY.",
            "movies": [],
            "demo": False,
        }  # Без ключа не возвращаем локальные фильмы.

    def _short_movie(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "Title": item.get("Title", "Без названия"),  # Название фильма.
            "Year": item.get("Year", "N/A"),  # Год выпуска.
            "Poster": self._poster(item.get("Poster")),  # Ссылка на постер или пустая строка.
            "imdbID": item.get("imdbID", ""),  # Уникальный IMDb ID.
            "Type": item.get("Type", "movie"),  # Тип результата, обычно movie.
        }

    def _detail_movie(self, item: dict[str, Any]) -> dict[str, Any]:
        movie = self._short_movie(item)  # Начинаем с коротких полей карточки.
        movie.update(
            {
                "Rated": item.get("Rated", "N/A"),  # Возрастной рейтинг.
                "Released": item.get("Released", "N/A"),  # Дата выхода.
                "Runtime": item.get("Runtime", "N/A"),  # Длительность.
                "Genre": item.get("Genre", "N/A"),  # Жанры.
                "Director": item.get("Director", "N/A"),  # Режиссер.
                "Writer": item.get("Writer", "N/A"),  # Сценаристы.
                "Actors": item.get("Actors", "N/A"),  # Актеры.
                "Plot": item.get("Plot", "Описание отсутствует."),  # Описание фильма.
                "Language": item.get("Language", "N/A"),  # Язык.
                "Country": item.get("Country", "N/A"),  # Страна.
                "imdbRating": item.get("imdbRating", "N/A"),  # Рейтинг IMDb.
            }
        )
        return movie  # Возвращаем полную карточку фильма.

    def _poster(self, poster: str | None) -> str:
        if not poster or poster == "N/A":  # OMDb пишет N/A, когда постера нет.
            return ""  # Пустая строка включает placeholder в шаблоне.
        return poster  # Возвращаем настоящую ссылку на постер.
