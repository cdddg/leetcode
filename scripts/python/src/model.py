from datetime import datetime
from uuid import uuid4 as _uuid4

from sqlalchemy import BOOLEAN, Column, DateTime, Enum, Float, ForeignKey, \
    Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from .enum import LevelEnum

Base = declarative_base()
uuid4 = lambda: _uuid4().hex


class Question(Base):
    __tablename__ = 'question'

    id = Column(String(32), primary_key=True, default=uuid4)
    no = Column(
        Integer, index=True, unique=True, nullable=False, comment='number'
    )
    level = Column(Enum(LevelEnum))
    acceptance = Column(Float)
    like = Column(Integer)
    dislike = Column(Integer)
    title = Column(String)
    content = Column(Text)
    is_paid_only = Column(BOOLEAN)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)


class QuestionSimilarity(Base):
    __tablename__ = 'question_similarity'

    id = Column(Integer, primary_key=True)
    question_id = Column(String(32), ForeignKey(Question.id), nullable=True)
    similaroty_id = Column(String(32), ForeignKey(Question.id), nullable=True)


class QuestionTag(Base):
    __tablename__ = 'question_tag'

    id = Column(Integer, primary_key=True)
    question_id = Column(String(32), ForeignKey(Question.id), nullable=True)
    tag = Column(String)
