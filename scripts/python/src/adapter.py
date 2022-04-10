import copy
import json
import random
import time
from typing import List, TYPE_CHECKING

import browsercookie
import requests

from .enum import LevelEnum

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass


user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'


@dataclass
class QuestionNode:
    id: str
    no: int
    level: LevelEnum
    like: int
    dislike: int
    acceptance: float
    title: str
    content: str
    is_paid_only: bool
    tags: List[str]
    similarities: List[str]

    def to_dict(self) -> dict:
        dict_ = copy.deepcopy(vars(self))
        dict_.pop('__initialised__', None)

        return dict_


class LeetcodeAdapter:
    base_url = 'https://leetcode.com'

    def __init__(self):
        self.session = requests.Session()
        self.csrftoken = self.get_csrftoken()

    def get_csrftoken(self):
        url = self.base_url
        cookies = self.session.get(
            url, cookies=self.get_chrome_cookies()
        ).cookies
        for cookie in cookies:
            if cookie.name == 'csrftoken':
                return cookie.value

    def get_chrome_cookies(self):
        return browsercookie.chrome()

    def get_question_id(self, no: int) -> str:
        url = f'{self.base_url}/api/problems/all/'
        resp = self.session.get(
            url,
            headers={'User-Agent': user_agent, 'Connection': 'keep-alive'},
            timeout=10,
        )
        data = json.loads(resp.content.decode('utf-8'))
        question_no_to_id_map = {}
        for row in data['stat_status_pairs'][::-1]:
            stat = row['stat']
            question_no_to_id_map[int(stat['frontend_question_id'])] = stat[
                'question__title_slug'
            ]

        return question_no_to_id_map[no]

    def get_question_data(self, id_: str) -> QuestionNode:
        time.sleep(random.randint(1, 3))
        params = {
            'operationName': 'getQuestionDetail',
            'variables': {'titleSlug': id_},
            'query': """
                query getQuestionDetail($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        questionId
                        questionFrontendId
                        questionTitle
                        questionTitleSlug
                        content
                        stats
                        difficulty
                        likes
                        dislikes
                        similarQuestions
                        categoryTitle
                        isPaidOnly
                        topicTags {
                            name
                            slug
                        }

                    }
                }
            """,
        }
        resp = self.session.post(
            url='https://leetcode.com/graphql',
            data=json.dumps(params).encode('utf8'),
            headers={
                'User-Agent': user_agent,
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Referer': f'https://leetcode.com/problems/{id_}',
            },
            timeout=10,
        )
        data = resp.json()['data']
        stats = json.loads(data['question']['stats'])

        return QuestionNode(
            id=data['question']['questionTitleSlug'],
            no=data['question']['questionFrontendId'],
            level=LevelEnum(data['question']['difficulty'].upper()),
            like=data['question']['likes'],
            dislike=data['question']['dislikes'],
            acceptance=round(
                stats['totalAcceptedRaw'] / stats['totalSubmissionRaw'], 2
            ),
            title=data['question']['questionTitle'],
            content=data['question']['content'] or '',
            is_paid_only=data['question']['isPaidOnly'],
            tags=[tag['slug'] for tag in data['question']['topicTags']],
            similarities=[
                q['titleSlug']
                for q in json.loads(data['question']['similarQuestions'])
            ],
        )
