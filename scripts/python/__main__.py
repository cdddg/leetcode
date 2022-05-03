import argparse

from src import facade
from src.db import get_engine
from src.model import Base

if __name__ == "__main__":
    Base.metadata.create_all(get_engine())

    parser = argparse.ArgumentParser()
    g1 = parser.add_argument_group()
    g1.add_argument("--no", type=int)
    g1.add_argument("--commited-at")
    args = parser.parse_args()
    if args.no:
        facade.upsert_question(args.no, args.commited_at)
        facade.upsert_readme_md()
    else:
        facade.upsert_markdowns_to_db()
