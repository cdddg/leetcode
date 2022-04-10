"""
    enum
     └――――――┐
    db      ┆
     └――――――┐
    model   ┆
     └――――――┤
            ┆
            └―> repository
                 └―――――――――┐
                           ┆
                 adapter   ┆
                  └――――――――┤
                           ┆
                           └―> facade
"""

import os

ROOT = os.path.abspath(__file__ + 4 * '/..')
DOC_PATH = os.path.join(ROOT, 'docs')
