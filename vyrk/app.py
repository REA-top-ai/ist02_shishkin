# -*- coding: utf-8 -*-
"""Flask-сайт для поиска фильмов через OMDb и сохранения избранного."""

from __future__ import annotations  # Включает современную запись type hints.

from authlib.integrations.flask_client import OAuth  # OAuth подключает вход через Google.
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for  # Основные функции Flask.

from config import Config  # Config хранит настройки из .env.
from services.ai_client import AiClient  # AiClient соответствует блоку AI client на схеме.
from services.google_auth import create_auth_blueprint, current_user, login_required  # Помощники авторизации.
from services.json_db import JsonDb  # JsonDb работает с JSON-базой данных.
from services.omdb_client import OmdbClient  # OmdbClient отправляет запросы на сайт OMDb API.


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)  # Создаем объект Flask-приложения.
    app.config.from_object(Config)  # Загружаем основные настройки.
    if test_config:  # Тесты могут передать свои настройки.
        app.config.update(test_config)  # Подменяем настройки только для тестового запуска.

    db = JsonDb(app.config["DATABASE_PATH"])  # Подключаем JSON-базу.
    omdb = OmdbClient(app.config["OMDB_API_KEY"])  # Подключаем реальный OMDb API.
    ai_client = AiClient(app.config["AI_API_KEY"], app.config["AI_API_URL"], app.config["AI_MODEL"])  # AI client.
    oauth = OAuth(app)  # Создаем менеджер OAuth для Google Auth.

    app.register_blueprint(create_auth_blueprint(oauth, db))  # Добавляем маршруты /login, /logout и callback.

    @app.context_processor
    def inject_globals() -> dict:
        user = current_user()  # Берем текущего пользователя из сессии.
        favorites = db.list_favorites(user.get("email") if user else None)  # Загружаем избранное для счетчика.
        return {
            "current_user": user,  # Передаем пользователя во все HTML-шаблоны.
            "favorite_count": len(favorites),  # Передаем количество избранных фильмов.
            "demo_mode": omdb.demo_mode,  # Передаем признак локального демо-режима.
            "ai_live_mode": ai_client.live_mode,  # Передаем признак реального AI API.
        }

    @app.route("/")
    def index():
        query = request.args.get("q", "")  # Читаем поисковую строку из URL.
        year = request.args.get("year", "")  # Читаем необязательный год из URL.
        result = {"ok": True, "error": "", "movies": [], "demo": omdb.demo_mode}  # Пустой результат до поиска.
        if query:  # Если пользователь ввел название фильма.
            result = omdb.search(query, year)  # Ищем фильмы через OMDb API.
        user = current_user()  # Читаем пользователя из сессии.
        favorites = db.list_favorites(user.get("email") if user else None)  # Загружаем избранные фильмы.
        advice = ai_client.suggest_queries(favorites)  # Получаем рекомендации через AI client.
        return render_template(
            "index.html",  # Отдаем главный HTML-шаблон.
            query=query,  # Возвращаем введенный поисковый текст в input.
            year=year,  # Возвращаем введенный год в input.
            result=result,  # Передаем результаты поиска.
            favorites=favorites,  # Передаем список избранного.
            advice=advice,  # Передаем рекомендации.
        )

    @app.route("/movie/<imdb_id>")
    def movie_detail(imdb_id: str):
        movie = db.get_cached_movie(imdb_id) or omdb.get_by_id(imdb_id)  # Берем фильм из кэша или OMDb API.
        if not movie:  # Если фильм не найден.
            flash("Фильм не найден.", "warning")  # Показываем сообщение пользователю.
            return redirect(url_for("index"))  # Возвращаемся на главную страницу.
        db.cache_movie(movie)  # Сохраняем успешный ответ OMDb в кэш.
        user = current_user()  # Читаем текущего пользователя.
        favorites = db.list_favorites(user.get("email") if user else None)  # Загружаем избранное пользователя.
        saved_ids = {item.get("imdbID") for item in favorites}  # Собираем id избранных фильмов.
        return render_template("movie.html", movie=movie, is_saved=imdb_id in saved_ids)  # Рендерим карточку.

    @app.post("/favorites/add")
    @login_required
    def add_favorite():
        imdb_id = request.form["imdb_id"]  # Читаем imdbID из отправленной формы.
        movie = db.get_cached_movie(imdb_id) or omdb.get_by_id(imdb_id)  # Получаем полные данные фильма.
        if not movie:  # Если фильм нельзя загрузить.
            flash("Не удалось сохранить фильм.", "danger")  # Сообщаем об ошибке.
            return redirect(request.referrer or url_for("index"))  # Возвращаем пользователя назад.
        db.add_favorite(current_user()["email"], movie)  # Сохраняем фильм в избранное текущего пользователя.
        flash(f"Фильм «{movie['Title']}» добавлен в избранное.", "success")  # Показываем подтверждение.
        return redirect(request.referrer or url_for("movie_detail", imdb_id=imdb_id))  # Возвращаем текущий экран.

    @app.post("/favorites/remove")
    @login_required
    def remove_favorite():
        imdb_id = request.form["imdb_id"]  # Читаем imdbID из формы удаления.
        db.remove_favorite(current_user()["email"], imdb_id)  # Удаляем фильм из JSON-базы.
        flash("Фильм удален из избранного.", "info")  # Показываем сообщение об удалении.
        return redirect(request.referrer or url_for("index"))  # Возвращаем пользователя назад.

    @app.get("/api/search")
    def api_search():
        query = request.args.get("q", "")  # Читаем параметр q для поиска.
        year = request.args.get("year", "")  # Читаем необязательный год.
        return jsonify(omdb.search(query, year))  # Возвращаем JSON-ответ поиска.

    @app.get("/api/movie/<imdb_id>")
    def api_movie(imdb_id: str):
        movie = db.get_cached_movie(imdb_id) or omdb.get_by_id(imdb_id)  # Загружаем фильм по imdbID.
        if not movie:  # Если фильм отсутствует.
            return jsonify({"ok": False, "error": "Movie not found"}), 404  # Возвращаем API-ошибку 404.
        db.cache_movie(movie)  # Кэшируем успешный ответ.
        return jsonify({"ok": True, "movie": movie})  # Возвращаем фильм как JSON.

    @app.get("/api/title")
    def api_title():
        title = request.args.get("t", "")  # Читаем параметр t из документации OMDb.
        year = request.args.get("year", "") or request.args.get("y", "")  # Читаем год как year или y.
        movie = omdb.get_by_title(title, year)  # Загружаем фильм через OMDb-параметр t.
        if not movie:  # Если фильм по названию не найден.
            return jsonify({"ok": False, "error": "Movie not found"}), 404  # Возвращаем API-ошибку 404.
        db.cache_movie(movie)  # Сохраняем фильм в кэш.
        return jsonify({"ok": True, "movie": movie, "demo": omdb.demo_mode})  # Возвращаем JSON.

    @app.get("/api/favorites")
    @login_required
    def api_favorites():
        favorites = db.list_favorites(current_user()["email"])  # Загружаем избранное текущего пользователя.
        return jsonify({"ok": True, "favorites": favorites})  # Возвращаем избранное как JSON.

    @app.get("/api/recommendations")
    @login_required
    def api_recommendations():
        favorites = db.list_favorites(current_user()["email"])  # Загружаем избранное для рекомендаций.
        return jsonify({"ok": True, "advice": ai_client.suggest_queries(favorites)})  # Возвращаем подсказки.

    @app.route("/favicon.ico")
    def favicon():
        return "", 204  # Отдаем пустой favicon, чтобы в консоли браузера не было 404.

    return app  # Возвращаем полностью настроенное Flask-приложение.


app = create_app()  # Создаем приложение для команды flask и хостинга.


if __name__ == "__main__":  # Этот блок выполняется только при запуске python app.py.
    app.run(debug=True)  # Запускаем локальный сервер разработки.
