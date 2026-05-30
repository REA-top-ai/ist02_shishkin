# -*- coding: utf-8 -*-
"""Настройки приложения, которые читаются из переменных окружения и файла .env."""

import os  # Модуль os нужен, чтобы читать переменные окружения.
from pathlib import Path  # Path удобно собирает пути к файлам на Windows и Linux.

from dotenv import load_dotenv  # load_dotenv загружает переменные из локального файла .env.


BASE_DIR = Path(__file__).resolve().parent  # BASE_DIR хранит абсолютный путь к папке проекта.
load_dotenv(BASE_DIR / ".env")  # Загружаем .env, если он есть рядом с app.py.

PLACEHOLDER_VALUES = {
    "your-omdb-key",
    "your-google-client-id.apps.googleusercontent.com",
    "your-google-client-secret",
    "your-ai-api-key",
}  # Эти значения из примера не считаются настоящими ключами.


def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, default).strip()  # Читаем настройку и убираем пробелы по краям.
    if value in PLACEHOLDER_VALUES or value.startswith("your-"):  # Проверяем, не остался ли шаблон.
        return ""  # Пустая строка означает, что настройка не задана.
    return value  # Возвращаем реальное значение из окружения.


class Config:
    """Единый класс со всеми настройками Flask-приложения."""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")  # Ключ для подписи Flask-сессий.
    OMDB_API_KEY = env_value("OMDB_API_KEY")  # Реальный ключ OMDb с https://www.omdbapi.com/apikey.aspx.
    GOOGLE_CLIENT_ID = env_value("GOOGLE_CLIENT_ID")  # Client ID для Google OAuth.
    GOOGLE_CLIENT_SECRET = env_value("GOOGLE_CLIENT_SECRET")  # Client Secret для Google OAuth.
    AI_API_KEY = env_value("AI_API_KEY")  # Ключ для внешнего AI API.
    AI_API_URL = env_value("AI_API_URL", "https://api.openai.com/v1/chat/completions")  # Адрес AI API.
    AI_MODEL = env_value("AI_MODEL", "gpt-4o-mini")  # Название модели для AI API.
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/movies.json")  # Путь к JSON-базе.
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"  # Метаданные OAuth.
