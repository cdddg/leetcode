from datetime import date
from time import sleep
from typing import Union

from .adapter import LeetcodeAdapter
from .db import get_session, transaction
from .repository import markdown_repo, question_repo, \
    question_similarity_repo, question_tag_repo


@transaction()
def upsert_question(no: int, commited_at: Union[str, None]):
    commited_at = (
        commited_at if commited_at else date.today().strftime('%Y/%m/%d')
    )
    question = question_repo.get_by_no(no)
    question_id = (
        question.id if question else LeetcodeAdapter().get_question_id(no)
    )

    # insert question
    data = LeetcodeAdapter().get_question_data(question_id)
    if not question:
        kwargs = data.to_dict()
        kwargs.pop('tags')
        kwargs.pop('similarities')
        question = question_repo.insert(**kwargs)
    else:
        question.acceptance = data.acceptance
        question.like = data.like
        question.dislike = data.dislike

    # insert or delete similarities
    if not question.is_paid_only:
        raw = set(
            row.similarity_id
            for row in question_similarity_repo.list(question_id)
        )
        for similarity_id in data.similarities:
            if similarity_id in raw:
                raw.remove(similarity_id)
                continue
            if not question_repo.get_by_id(similarity_id):
                kwargs = (
                    LeetcodeAdapter().get_question_data(similarity_id).to_dict()
                )
                kwargs.pop('tags')
                kwargs.pop('similarities')
                question_repo.insert(**kwargs)
            question_similarity_repo.insert(
                question_id=question.id, similarity_id=similarity_id
            )
        for similarity_id in raw:
            question_similarity_repo.delete(
                question_id=question.id, similarity_id=similarity_id
            )

    # insert or delete tags
    if data.tags:
        raw = set(row.tag for row in question_tag_repo.list(question_id))
        for tag in data.tags:
            if tag in raw:
                raw.remove(tag)
                continue
            question_tag_repo.insert(question_id=question_id, tag=tag)
        for tag in raw:
            question_tag_repo.delete(question_id=question_id, tag=tag)

    get_session().flush()
    question = question_repo.get_by_no(no)
    if not markdown_repo.is_existed_md(no):
        markdown_repo.create_question_md(no, question, commited_at)
    else:
        markdown_repo.add_commited_at(no, question, commited_at)


def upsert_markdowns_to_db():
    for no in markdown_repo.get_md_numbers():
        print('--no', no)
        upsert_question(no, markdown_repo.get_last_commited_at(no))
        sleep(10)


def upsert_readme_md():
    markdown_repo.create_readme_md()
