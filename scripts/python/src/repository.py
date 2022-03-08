from .db import get_session
from .model import Question, QuestionSimilarity, QuestionTag


class BaseRepository:
    MODEL_CLS = None

    @property
    def _session(self):
        return get_session()

    def add(self, entity):
        self._session.add(entity)
        self._session.flush()

        return entity

    def insert(self, **kwargs):
        return self.add(self.MODEL_CLS(**kwargs))  # type: ignore

    def update(self, no, **kwargs):
        self._session.query(self.MODEL_CLS).filter_by(no=no).update(**kwargs)


class QuestionRepository(BaseRepository):
    MODEL_CLS = Question

    def get_by_id(self, id_: str):
        return (
            self._session.query(self.MODEL_CLS).filter_by(id=id_).one_or_none()
        )

    def get_by_no(self, no: int):
        return (
            self._session.query(self.MODEL_CLS).filter_by(no=no).one_or_none()
        )


class QuestionSimilarity(BaseRepository):
    MODEL_CLS = QuestionSimilarity

    def get(self, question_id: str):
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(question_id=question_id)
            .all()
        )


class QuestionTagRepository(BaseRepository):
    MODEL_CLS = QuestionTag

    def get(self, question_id: int):
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(question_id=question_id)
            .all()
        )


question_repo = QuestionRepository()
question_similarity_repo = QuestionSimilarity()
question_tag_repo = QuestionTagRepository()
