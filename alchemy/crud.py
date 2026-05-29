from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Journalist, Publication, Feedback
from datetime import datetime


def create_journalist(session: Session, username: str, email_address: str) -> Journalist:
    new_journalist = Journalist(username=username, email_address=email_address)
    session.add(new_journalist)
    session.commit()
    session.refresh(new_journalist)
    return new_journalist


def get_journalist_by_email(session: Session, email_address: str) -> Journalist | None:
    return session.query(Journalist).filter(Journalist.email_address == email_address).first()


def create_publication(session: Session, caption: str, description: str, journalist_id: int, is_published: bool = False) -> Publication:
    new_publication = Publication(caption=caption, description=description, journalist_id=journalist_id, is_published=is_published)
    session.add(new_publication)
    session.commit()
    session.refresh(new_publication)
    return new_publication


def get_published_publications(session: Session, limit: int = 10) -> list[Publication]:
    return session.query(Publication).filter(Publication.is_published == True).limit(limit).all()


def get_publications_by_journalist(session: Session, journalist_id: int, limit: int = 10) -> list[Publication]:
    return session.query(Publication).filter(Publication.journalist_id == journalist_id).limit(limit).all()


def update_publication_status(session: Session, publication_id: int, is_published: bool) -> bool:
    publication = session.query(Publication).filter(Publication.id == publication_id).first()
    if publication is None:
        return False
    publication.is_published = is_published
    session.commit()
    return True


def add_feedback(session: Session, publication_id: int, sender_name: str, message: str) -> Feedback:
    new_feedback = Feedback(publication_id=publication_id, sender_name=sender_name, message=message)
    session.add(new_feedback)
    session.commit()
    session.refresh(new_feedback)
    return new_feedback


def get_top_journalists_by_publications(session: Session, limit: int = 3) -> list[tuple[str, int]]:
    result = (session.query(Journalist.username, func.count(Publication.id).label("pub_count"))
              .join(Publication)
              .group_by(Journalist.id)
              .order_by(desc("pub_count"))
              .limit(limit)
              .all())
    return result


def get_journalist_by_username(session: Session, username: str) -> Journalist | None:
    return session.query(Journalist).filter(Journalist.username == username).first()


def get_published_publications_by_date(session: Session, date: datetime, limit: int = 10) -> list[Publication]:
    return (session.query(Publication)
            .filter(Publication.is_published == True,
                    func.date(Publication.created_at) == date.date())
            .limit(limit)
            .all())


def create_journalists_bulk(session: Session, journalists_data: list[dict]) -> list[Journalist]:
    journalists = [Journalist(username=data["username"], email_address=data["email_address"]) for data in journalists_data]
    session.add_all(journalists)
    session.commit()
    for journalist in journalists:
        session.refresh(journalist)
    return journalists


def get_publication_with_feedbacks(session: Session, publication_id: int) -> dict | None:
    publication = session.query(Publication).filter(Publication.id == publication_id).first()
    if publication is None:
        return None
    return {"publication": publication, "feedbacks": publication.feedbacks}
