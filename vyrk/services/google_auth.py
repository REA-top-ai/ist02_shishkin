# -*- coding: utf-8 -*-
"""Маршруты Google OAuth и функции авторизации."""

from __future__ import annotations  # Включает современную запись type hints.

from functools import wraps  # wraps сохраняет имя и метаданные декорируемой функции.
from typing import Any, Callable  # Any и Callable нужны для type hints.

from flask import Blueprint, current_app, flash, redirect, request, session, url_for  # Инструменты Flask.


DEMO_USER = {
    "email": "demo@example.com",  # Email демо-пользователя для локальной проверки без Google credentials.
    "name": "Demo User",  # Имя демо-пользователя.
    "picture": "",  # Пустая картинка означает, что UI покажет первую букву имени.
}  # Демо-вход нужен только если Google OAuth ключи не заданы.


def google_auth_configured() -> bool:
    return bool(current_app.config["GOOGLE_CLIENT_ID"] and current_app.config["GOOGLE_CLIENT_SECRET"])  # Проверка.


def current_user() -> dict[str, Any] | None:
    return session.get("user")  # Пользователь хранится в браузерной сессии Flask.


def safe_next_url(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):  # Разрешаем только локальные ссылки.
        return value  # Возвращаем безопасный путь внутри сайта.
    return url_for("index")  # Для внешних ссылок возвращаем главную страницу.


def login_required(route: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(route)  # Сохраняем Flask-метаданные исходного маршрута.
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_user():  # Если пользователь не вошел.
            flash("Сначала войдите через Google.", "warning")  # Показываем предупреждение.
            return redirect(url_for("auth.login", next=request.full_path))  # Отправляем на вход.
        return route(*args, **kwargs)  # Если вход есть, запускаем исходный маршрут.

    return wrapper  # Возвращаем защищенную функцию.


def create_auth_blueprint(oauth: Any, db: Any) -> Blueprint:
    bp = Blueprint("auth", __name__)  # Создаем группу маршрутов авторизации.

    @bp.record_once
    def register_oauth(state: Any) -> None:
        app = state.app  # Flask передает приложение при регистрации blueprint.
        if app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]:  # Регистрируем Google только с ключами.
            oauth.register(
                name="google",  # Внутреннее имя провайдера.
                client_id=app.config["GOOGLE_CLIENT_ID"],  # Google Client ID из .env.
                client_secret=app.config["GOOGLE_CLIENT_SECRET"],  # Google Client Secret из .env.
                server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],  # OpenID metadata Google.
                client_kwargs={"scope": "openid email profile"},  # Запрашиваем только профиль и email.
            )

    @bp.route("/login")
    def login() -> Any:
        next_url = safe_next_url(request.args.get("next"))  # Запоминаем безопасный URL возврата.
        session["next_url"] = next_url  # Сохраняем URL возврата в сессии.
        if not google_auth_configured():  # Если Google OAuth не настроен.
            db.upsert_user(DEMO_USER)  # Создаем демо-пользователя в JSON-базе.
            session["user"] = DEMO_USER  # Сохраняем демо-пользователя в сессии.
            flash("Google OAuth не настроен, поэтому включен демо-вход.", "info")  # Объясняем режим.
            return redirect(next_url)  # Возвращаем пользователя туда, куда он шел.
        redirect_uri = url_for("auth.callback", _external=True)  # URL, куда Google вернет пользователя.
        return oauth.google.authorize_redirect(redirect_uri)  # Запускаем OAuth-переход на Google.

    @bp.route("/auth/callback")
    def callback() -> Any:
        token = oauth.google.authorize_access_token()  # Меняем временный код Google на токены.
        user_info = token.get("userinfo")  # Authlib может вернуть профиль прямо в token.
        if not user_info:  # Если профиля в token нет.
            user_info = oauth.google.parse_id_token(token)  # Читаем профиль из id_token.
        user = {
            "email": user_info["email"],  # Email будет id пользователя.
            "name": user_info.get("name", user_info["email"]),  # Берем имя или email.
            "picture": user_info.get("picture", ""),  # Берем аватар, если он есть.
        }
        db.upsert_user(user)  # Сохраняем или обновляем пользователя в JSON-базе.
        session["user"] = user  # Сохраняем минимальный профиль в сессии.
        flash("Вход через Google выполнен.", "success")  # Показываем успешный вход.
        return redirect(safe_next_url(session.pop("next_url", None)))  # Возвращаем на исходную страницу.

    @bp.route("/logout")
    def logout() -> Any:
        session.clear()  # Очищаем сессию пользователя.
        flash("Вы вышли из аккаунта.", "info")  # Показываем сообщение о выходе.
        return redirect(url_for("index"))  # Возвращаем на главную.

    return bp  # Возвращаем готовый blueprint.
