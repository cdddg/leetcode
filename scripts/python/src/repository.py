import os
import re
from typing import List

from html2text import html2text
from pytablewriter import MarkdownTableWriter
from sqlalchemy.orm import selectinload

from . import DOC_PATH, ROOT
from .adapter import LeetcodeAdapter
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

    def delete(self, **kwargs):
        self._session.query(self.MODEL_CLS).filter_by(**kwargs).delete()


class QuestionRepository(BaseRepository):
    MODEL_CLS = Question

    def get_by_id(self, id_: str):
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(id=id_)
            .options(
                selectinload(self.MODEL_CLS.similarities).joinedload(
                    'similarity'
                ),
                selectinload(self.MODEL_CLS.tags),
            )
            .one_or_none()
        )

    def get_by_no(self, no: int):
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(no=no)
            .options(
                selectinload(self.MODEL_CLS.similarities),
                selectinload(self.MODEL_CLS.tags),
            )
            .populate_existing()
            .one_or_none()
        )


class QuestionSimilarityRepository(BaseRepository):
    MODEL_CLS = QuestionSimilarity

    def list(self, question_id: str) -> List[QuestionSimilarity]:
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(question_id=question_id)
            .options(selectinload(QuestionSimilarity.similarity))
            .all()
        )


class QuestionTagRepository(BaseRepository):
    MODEL_CLS = QuestionTag

    def list(self, question_id: str):
        return (
            self._session.query(self.MODEL_CLS)
            .filter_by(question_id=question_id)
            .all()
        )


class MarkdownRepository:
    @staticmethod
    def _get_md_solution_title(content: str) -> re.Match:
        if match := re.search(r'## Solutions \[\^[0-9]*\]:', content):
            return match

        raise ValueError

    @staticmethod
    def _get_md_last_commited_at(content: str) -> re.Match:
        commited_at_list = re.findall(r'\[\^[0-9]*\]: [0-9`/]*', content)
        if not commited_at_list:
            raise ValueError('Commited_at is empty')
        if not (
            last := re.search(r'\[\^(\d+)\]: `(\S+)`', commited_at_list[-1])
        ):
            raise ValueError('Last commited_at not found')

        return last

    @staticmethod
    def _get_md_paths() -> List[str]:
        root, _, files = list(os.walk(DOC_PATH))[0]

        return sorted(
            [
                os.path.join(root, f)
                for f in files
                if os.path.splitext(f)[1] == '.md'
            ]
        )

    @staticmethod
    def _build_md_name(no: int):
        return f'{no:04}.md'

    @staticmethod
    def get_md_numbers() -> List[int]:
        _, _, files = list(os.walk(DOC_PATH))[0]

        return sorted(
            [
                int(os.path.splitext(f)[0])
                for f in files
                if os.path.splitext(f)[1] == '.md'
            ]
        )

    def _get_md_content(self, no: int) -> str:
        with open(self._build_md_path(no)) as f:
            content = f.read()

        return content

    def _build_md_path(self, no: int):
        return os.path.join(DOC_PATH, self._build_md_name(no))

    def is_existed_md(self, no: int):
        return os.path.exists(self._build_md_path(no))

    def get_last_commited_at(self, no: int) -> str:
        with open(self._build_md_path(no)) as f:
            return self._get_md_last_commited_at(f.read()).group(2)

    def create_question_md(self, no: int, question: Question, commited_at: str):
        with open(self._build_md_path(no), 'w', encoding='utf-8') as f:
            f.write(
                f'# [{question.no}. {question.title}]({LeetcodeAdapter().base_url}/problems/{question.id})\n'
            )
            f.write(f'{question.level.to_color_str()}\n\n')
            f.write(
                html2text(
                    question.content.replace('<p>&nbsp;</p>', ''), bodywidth=0
                )
                .replace('    \n    \n    **Input:**', '\n    Input:')
                .replace('**Output:**', 'Output:')
                .replace('**Explanation:**', 'Explanation:')
                .replace('**Follow-up:  **', '**Follow-up:** ')
                .replace('\n`', '` ')
                .replace('\n\n\n\n', '\n\n\n')
                .strip()
            )
            f.write('\n\n')
            f.write(
                '**Related Topics:** '
                + ' '.join(f'`{row.tag}`' for row in question.tags)
                + '\n\n'
            )
            f.write('**Similar Questions:**\n\n\n\n')
            f.write('<br>\n\n')
            f.write('## Solutions [^1]:\n\n')
            f.write('```python\n```\n\n')
            f.write('<br>\n\n')
            f.write(f'[^1]: `{commited_at}`')

        self.update_similarity_link(question)
        for row in question.similarities:
            similarity = row.similarity
            if self.is_existed_md(similarity.no):
                self.update_similarity_link(similarity)

    def create_readme_md(self):
        rows = []
        for p in self._get_md_paths():
            name = os.path.basename(p)
            no = int(os.path.splitext(name)[0])
            question = QuestionRepository().get_by_no(no)
            rows.append(
                [
                    question.no,
                    f'[{question.title}](docs/{question.no:04}.md)',
                    question.level.to_color_str(),
                    '{:.1%}'.format(
                        question.like / (question.like + question.dislike)
                    ),
                    self._get_md_last_commited_at(
                        self._get_md_content(question.no)
                    ).group(2),
                ]
            )
        writer = MarkdownTableWriter(
            table_name='',
            headers=['#', 'Title', 'Difficulty', 'Like', 'Last Commit at'],
            value_matrix=rows,
            margin=1,  # add a whitespace for both sides of each cell
        )
        writer.write_table()
        writer.dump(f'{ROOT}/README.md')

    def add_commited_at(self, no: int, question: Question, commited_at: str):
        if not self.is_existed_md(no):
            raise FileNotFoundError(self._build_md_path(no))

        with open(self._build_md_path(no)) as f:
            content = f.read()
            last_commit_at = self._get_md_last_commited_at(content)
            if last_commit_at.group(2) == commited_at:
                return

            title = self._get_md_solution_title(content).group()
            content = content.replace(
                title, f'## Solutions [^{int(last_commit_at.group(1)) + 1}]:'
            ).replace(
                last_commit_at.group(0),
                f'{last_commit_at.group(0)}\n[^{int(last_commit_at.group(1)) + 1}]: `{commited_at}`\n',
            )
        with open(self._build_md_path(no), 'w', encoding='utf-8') as f:
            f.write(content)

    def update_similarity_link(self, question: Question):
        path = self._build_md_path(question.no)
        with open(path) as f:
            content = f.read()
            text = re.findall(
                r'(?<=\*\*Similar Questions:\*\*\n)[^<]+', content
            )
            if len(text) != 1:
                raise ValueError

            text = text[0]
            similarities = []
            for row in question.similarities:
                similarity = row.similarity
                similarities.append(
                    [
                        similarity.no,
                        similarity.title,
                        similarity.level.value.capitalize(),
                    ]
                )
                if self.is_existed_md(similarity.no):
                    similarities[-1][
                        1
                    ] = f'[{similarity.title}](./{self._build_md_name(similarity.no)})'
            tb = MarkdownTableWriter(
                table_name='',
                headers=['No', 'Title', 'Difficulty'],
                value_matrix=similarities,
                margin=1,  # add a whitespace for both sides of each cell
            )
            content = content.replace(
                f'**Similar Questions:**\n{text}<br>',
                f'**Similar Questions:**\n\n{tb.dumps()}\n<br>',
            )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


question_repo = QuestionRepository()
question_similarity_repo = QuestionSimilarityRepository()
question_tag_repo = QuestionTagRepository()
markdown_repo = MarkdownRepository()
