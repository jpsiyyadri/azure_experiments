from sqlalchemy.orm import joinedload, sessionmaker

from db import SessionLocal as Session
from models import Person


def get_persons():
    with Session() as session:
        persons = session.query(Person).all()
    return persons


def get_person_by_id(person_id: int):
    with Session() as session:
        person = session.query(Person).filter(Person.id == person_id).first()
    return person


def add_person(name: str, age: int, email: str):
    with Session() as session:
        person = Person(name=name, age=age, email=email)
        session.add(person)
        session.commit()
        session.refresh(person)
    return person


def update_person(person_id: int, name: str, age: int, email: str):
    print("update_person")
    with Session() as session:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            person.name = name
            person.age = age
            person.email = email
            session.commit()
            session.refresh(person)
    print("completed update_person")
    return person


def delete_person(person_id: int):
    with Session() as session:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            session.delete(person)
            session.commit()
    return person


if __name__ == "__main__":
    # persons = get_persons()
    # print(persons)

    # person = get_person_by_id(1)
    # print(person)

    # Uncomment to add a person
    new_person = add_person("John", 30, "email@gmail.com")
    print(new_person)

    updated_person = update_person(2, "John Doe", 33, "google@gmail.com")
    print(updated_person)

    # Uncomment to delete a person
    deleted_person = delete_person(1)
    print(deleted_person)

    # person = get_person_by_id(1)
    # print(person)

    print("Done!")

    persons = get_persons()
    print(persons)
