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
    # g2 = parser.add_argument_group()
    # g2.add_argument("--update")
    args = parser.parse_args()

    if args.no:
        facade.insert_or_update_question(args.no, args.commit_at)
