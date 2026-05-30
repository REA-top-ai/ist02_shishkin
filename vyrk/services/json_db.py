# -*- coding: utf-8 -*-
"""Простая JSON-база вместо отдельного SQL-сервера."""

from __future__ import annotations  # Включает современную запись type hints.

import json  # json преобразует словари Python в JSON-файл и обратно.
from pathlib import Path  # Path удобно работает с путями к файлам.
from threading import Lock  # Lock защищает файл от одновременной записи.
from typing import Any  # Any используется для произвольных JSON-словарей.


class JsonDb:
    """Класс для хранения пользователей, избранного и кэша фильмов в JSON."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)  # Сохраняем путь к JSON-файлу.
        self.lock = Lock()  # Создаем блокировку для операций чтения и записи.
        self.path.parent.mkdir(parents=True, exist_ok=True)  # Создаем папку data, если ее нет.
        if not self.path.exists():  # Если файла базы еще нет.
            self._write({"users": {}, "cache": {}})  # Создаем пустую структуру базы.

    def _read(self) -> dict[str, Any]:
        with self.lock:  # Не даем нескольким запросам читать/писать файл одновременно.
            with self.path.open("r", encoding="utf-8") as file:  # Открываем JSON в UTF-8.
                return json.load(file)  # Превращаем JSON-текст в словарь Python.

    def _write(self, data: dict[str, Any]) -> None:
        with self.lock:  # Защищаем запись от одновременного доступа.
            with self.path.open("w", encoding="utf-8") as file:  # Открываем файл для записи в UTF-8.
                json.dump(data, file, ensure_ascii=False, indent=2)  # Сохраняем читаемый JSON.

    def all_data(self) -> dict[str, Any]:
        return self._read()  # Возвращаем все содержимое базы.

    def upsert_user(self, user: dict[str, str]) -> dict[str, Any]:
        data = self._read()  # Загружаем текущее состояние базы.
        email = user["email"]  # Email из Google используется как id пользователя.
        existing = data["users"].get(email, {})  # Берем существующего пользователя, если он уже есть.
        favorites = existing.get("favorites", [])  # Сохраняем старое избранное.
        data["users"][email] = {**existing, **user, "favorites": favorites}  # Обновляем профиль пользователя.
        self._write(data)  # Записываем изменения в файл.
        return data["users"][email]  # Возвращаем сохраненный профиль.

    def get_user(self, email: str | None) -> dict[str, Any] | None:
        if not email:  # У гостя нет email.
            return None  # Возвращаем None для неавторизованного пользователя.
        data = self._read()  # Читаем базу.
        return data["users"].get(email)  # Возвращаем пользователя или None.

    def list_favorites(self, email: str | None) -> list[dict[str, Any]]:
        user = self.get_user(email)  # Ищем пользователя по email.
        if not user:  # Если пользователя нет.
            return []  # Избранное тоже пустое.
        return user.get("favorites", [])  # Возвращаем список избранных фильмов.

    def add_favorite(self, email: str, movie: dict[str, Any]) -> list[dict[str, Any]]:
        data = self._read()  # Читаем текущее состояние базы.
        user = data["users"].setdefault(email, {"email": email, "name": email, "favorites": []})  # Создаем юзера.
        favorites = user.setdefault("favorites", [])  # Создаем список избранного, если его нет.
        imdb_id = movie["imdbID"]  # imdbID уникально определяет фильм.
        favorites[:] = [item for item in favorites if item.get("imdbID") != imdb_id]  # Убираем дубликат.
        favorites.insert(0, movie)  # Добавляем фильм в начало списка.
        data["cache"][imdb_id] = movie  # Кэшируем данные фильма.
        self._write(data)  # Сохраняем базу.
        return favorites  # Возвращаем обновленное избранное.

    def remove_favorite(self, email: str, imdb_id: str) -> list[dict[str, Any]]:
        data = self._read()  # Читаем базу.
        user = data["users"].get(email)  # Ищем пользователя.
        if not user:  # Если пользователь не найден.
            return []  # Возвращаем пустой список.
        user["favorites"] = [item for item in user.get("favorites", []) if item.get("imdbID") != imdb_id]  # Фильтруем.
        self._write(data)  # Сохраняем изменения.
        return user["favorites"]  # Возвращаем оставшееся избранное.

    def cache_movie(self, movie: dict[str, Any]) -> None:
        if not movie.get("imdbID"):  # Без imdbID фильм нельзя безопасно кэшировать.
            return  # Просто выходим.
        data = self._read()  # Читаем базу.
        data["cache"][movie["imdbID"]] = movie  # Записываем фильм в кэш.
        self._write(data)  # Сохраняем файл.

    def get_cached_movie(self, imdb_id: str) -> dict[str, Any] | None:
        data = self._read()  # Читаем базу.
        return data.get("cache", {}).get(imdb_id)  # Возвращаем фильм из кэша или None.
