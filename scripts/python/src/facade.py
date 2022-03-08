from datetime import date
import os
import re

import html2text
from pytablewriter import MarkdownTableWriter

from .adapter import LeetcodeAdapter
from .db import transaction
from .repository import question_repo, question_similarity_repo, \
    question_tag_repo


@transaction()
def get_or_insert_question(no: int):
    question = question_repo.get_by_no(no)
    if not question:
        id_ = LeetcodeAdapter().get_questions()[no]
        question = insert_question(id_)

    if not question.is_paid_only and not question_similarity_repo.get(
        question.id
    ):
        q = LeetcodeAdapter().get_question(question.id)
        for similarity_id in q.similarities:
            if not question_similarity_repo.get(question.id):
                question_similarity_repo.insert(question_id=question.id, similaroty_id=similarity_id)

    return question


def insert_question(id_: str, _save_similarity_question=True):
    question = question_repo.get_by_id(id_)
    if not question:
        q = LeetcodeAdapter().get_question(id_)
        question = question_repo.insert(
            id=q.id,
            no=q.no,
            level=q.level,
            acceptance=q.acceptance,
            like=q.like,
            dislike=q.dislike,
            title=q.title,
            content=q.content,
            is_paid_only=q.is_paid_only,
        )

        for tag in q.tags:
            question_tag_repo.insert(question_id=id_, tag=tag)
        for similarity_id in (
            q.similarities if _save_similarity_question else []
        ):
            question_similarity_repo.insert(
                question_id=id_, similaroty_id=similarity_id
            )
            if not question_repo.get_by_id(similarity_id):
                insert_question(similarity_id, _save_similarity_question=False)

    return question


def generate_question_md(no: int, date_=None):

    path = f"{os.path.abspath(__file__ + 4 * '/..')}/docs/{no:04}.md"
    if os.path.isfile(path):
        return

    with open(path, 'w', encoding='utf-8') as f:
        q = question_repo.get_by_no(no)
        f.write(
            f'# [{q.no}. {q.title}]({LeetcodeAdapter().base_url}/problems/{q.id})\n'
        )
        f.write(
            html2text.html2text(q.content, bodywidth=0)
            .replace('    **Input:**', ' \n    Input:')
            .replace('**Output:**', 'Output:')
            .replace('**Explanation:**', 'Explanation:')
            .replace('\n    \n    ', '')
            .replace('**Follow-up:  **', '**Follow-up:** ')
            .replace('\n`', '` ')
        )
        f.write(f'\n\n')
        f.write(
            f'**Related Topics:** '
            + ' '.join(f'`{row.tag}`' for row in question_tag_repo.get(q.id))
        )
        f.write(f'\n\n')
        f.write('<br>\n\n')
        f.write('## Solutions [^1]:\n\n')
        f.write('```python\n```\n\n')
        f.write('<br>\n\n')
        f.write(f'[^1]: `{date_ or date.today().strftime("%Y/%m/%d")}`\n')


def generate_readme_md():
    root = os.path.abspath(__file__ + 4 * '/..')
    rows = []
    for _, _, files in os.walk(f'{root}/docs/'):
        for file in sorted(files):
            name, ext = os.path.splitext(file)
            if ext == '.md':
                no = int(name)
                get_or_insert_question(no)
                q = question_repo.get_by_no(no)
                rows.append(
                    [
                        q.no,
                        f'[{q.title}](docs/{q.no:04}.md)',
                        q.level.value,
                        '{:.1%}'.format(q.like / (q.like + q.dislike)),
                        get_last_commit_at(q.no).group(2),
                    ]
                )

    writer = MarkdownTableWriter(
        table_name='',
        headers=['#', 'Title', 'Difficulty', 'Like', 'Last Commit at'],
        value_matrix=rows,
        margin=1,  # add a whitespace for both sides of each cell
    )
    writer.write_table()
    writer.dump(f'{root}/README.md')


def get_last_commit_at(no: int) -> re.Match:
    with open(f"{os.path.abspath(__file__ + 4 * '/..')}/docs/{no:04}.md") as f:
        text = f.read()
        commits_at = re.findall(r'\[\^[0-9]*\]: [0-9`/]*', text)

        if commits_at and (
            last := re.search(r'\[\^(\d+)\]: `(\S+)`', commits_at[-1])
        ):
            return last

        raise ValueError


def get_solution_title(no: int) -> re.Match:
    with open(f"{os.path.abspath(__file__ + 4 * '/..')}/docs/{no:04}.md") as f:
        text = f.read()
        if match := re.search(r'## Solutions \[\^[0-9]*\]:', text):
            return match

        raise ValueError


def add_commit_at(no: int, date_: str):
    path = f"{os.path.abspath(__file__ + 4 * '/..')}/docs/{no:04}.md"
    with open(path) as _:
        last_commit_at = get_last_commit_at(no)
        solution_title = get_solution_title(no).group()
        text = (
            _.read()
            .replace(
                solution_title,
                f'## Solutions [^{int(last_commit_at.group(1)) + 1}]:',
            )
            .replace(
                last_commit_at.group(0),
                f'{last_commit_at.group(0)}\n[^{int(last_commit_at.group(1)) + 1}]: `{date_}`\n',
            )
        )

        if last_commit_at.group(2) != date_:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
