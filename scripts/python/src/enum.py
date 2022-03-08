import enum


@enum.unique
class LevelEnum(enum.Enum):
    easy = 'Easy'
    medium = 'Medium'
    hard = 'Hard'
