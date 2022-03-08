import argparse

from src import facade
from src.db import get_engine
from src.model import Base

if __name__ == "__main__":
    Base.metadata.create_all(get_engine())

    parser = argparse.ArgumentParser()
    g1 = parser.add_argument_group()
    g1.add_argument("--no", type=int)
    g1.add_argument("--commit-at")
    g2 = parser.add_argument_group()
    g2.add_argument("--update")
    args = parser.parse_args()

    if args.no and not args.commit_at:
        facade.get_or_insert_question(args.no)
        facade.generate_question_md(args.no)
        facade.generate_readme_md()

    elif args.no and args.commit_at:
        facade.get_or_insert_question(args.no)
        facade.generate_question_md(args.no, args.commit_at)
        facade.add_commit_at(args.no, args.commit_at)
        facade.generate_readme_md()

    else:
        facade.generate_readme_md()
