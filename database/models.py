from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, TIMESTAMP, ForeignKey, BigInteger

from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)


class Template(Base):
    __tablename__ = 'templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)


class TemplateExercise(Base):
    __tablename__ = 'template_exercises'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey('templates.id', ondelete='CASCADE'))
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    sets_and_reps: Mapped[str] = mapped_column(String, nullable=False)
    weight_or_rubber: Mapped[str] = mapped_column(String, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class BodyParameter(Base):
    __tablename__ = 'body_parameters'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    parameters: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)


class Workout(Base):
    __tablename__ = 'workouts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey('templates.id', ondelete='SET NULL'), nullable=True)
    date: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    notes: Mapped[str] = mapped_column(String, nullable=True)


class WorkoutExercise(Base):
    __tablename__ = 'workout_exercises'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(Integer, ForeignKey('workouts.id', ondelete='CASCADE'))
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    sets_and_reps: Mapped[str] = mapped_column(String, nullable=False)
    weight_or_rubber: Mapped[str] = mapped_column(String, nullable=True)