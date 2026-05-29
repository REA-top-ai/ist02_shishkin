from database import SessionLocal, engine, Base
from models import Journalist, Publication, Feedback
from crud import *
from datetime import datetime


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        print("Начинаем тестирование...\n")

        print("Создаём журналистов...")
        journalist1 = create_journalist(session, "mikhail_ivanov", "mikhail@example.com")
        journalist2 = create_journalist(session, "natalia_sokolova", "natalia@example.com")
        print(f"{journalist1.username} (id={journalist1.id})")
        print(f"{journalist2.username} (id={journalist2.id})\n")

        print("Создаём публикации...")
        pub1 = create_publication(session, "Новости технологий 2026", "Обзор главных технологических событий текущего года.", journalist1.id, is_published=True)
        pub2 = create_publication(session, "Черновик: итоги квартала", "Материал ещё находится в разработке.", journalist1.id, is_published=False)
        pub3 = create_publication(session, "Интервью с разработчиком", "Эксклюзивное интервью с ведущим инженером.", journalist2.id, is_published=True)
        print(f"'{pub1.caption}' (опубликована)")
        print(f"'{pub2.caption}' (черновик)")
        print(f"'{pub3.caption}' (опубликована)\n")

        print("Добавляем отклики...")
        add_feedback(session, pub1.id, "Читатель_1", "Очень актуальная статья!")
        add_feedback(session, pub1.id, "Читатель_2", "Спасибо, было интересно читать.")
        add_feedback(session, pub1.id, "Гость_сайта", "Жду новых материалов на эту тему.")
        print("3 отклика добавлены к первой публикации\n")

        print("Публикуем черновик...")
        success = update_publication_status(session, pub2.id, is_published=True)
        if success:
            print(f"'{pub2.caption}' теперь опубликована\n")

        print("Все опубликованные публикации:")
        published = get_published_publications(session)
        for pub in published:
            print(f"'{pub.caption}' — автор: {pub.journalist.username}")
        print()

        print("Топ журналистов по количеству публикаций:")
        top_journalists = get_top_journalists_by_publications(session, limit=3)
        for rank, (username, count) in enumerate(top_journalists, 1):
            print(f"{rank}. {username}: {count} публикаций(и)")
        print()

        print("Поиск журналиста по email...")
        found = get_journalist_by_email(session, "mikhail@example.com")
        if found:
            print(f"Найдено: {found.username}\n")
        else:
            print("Журналист не найден\n")

        print("Поиск журналиста по имени пользователя...")
        found_by_username = get_journalist_by_username(session, "natalia_sokolova")
        if found_by_username:
            print(f"Найдено: {found_by_username.username}, email: {found_by_username.email_address}\n")
        else:
            print("Журналист не найден\n")

        print("Опубликованные публикации за сегодня:")
        pubs_today = get_published_publications_by_date(session, datetime.now())
        for pub in pubs_today:
            print(f"'{pub.caption}' — {pub.created_at}")
        print()

        print("Добавляем нескольких журналистов сразу...")
        new_journalists = create_journalists_bulk(session, [
            {"username": "alexey_zhukov", "email_address": "alexey@example.com"},
            {"username": "victoria_romanova", "email_address": "victoria@example.com"},
        ])
        for j in new_journalists:
            print(f"Создан: {j.username} (id={j.id})")
        print()

        print("Публикация с откликами:")
        result = get_publication_with_feedbacks(session, pub1.id)
        if result:
            print(f"Публикация: '{result['publication'].caption}'")
            for feedback in result["feedbacks"]:
                print(f"  — {feedback.sender_name}: {feedback.message}")
        print()

    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()
    finally:
        session.close()
        print("\nТестирование завершено. Сессия закрыта.")


if __name__ == "__main__":
    main()
