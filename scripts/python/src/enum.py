import enum


@enum.unique
class LevelEnum(enum.Enum):
    easy = 'EASY'
    medium = 'MEDIUM'
    hard = 'HARD'

    def to_color_str(self):
        return {
            'EASY': '<span style="color:green">`Easy`</span>',
            'MEDIUM': '<span style="color:orange">`Medium`</span>',
            'HARD': '<span style="color:red">`Hard`</span>',
        }[self.value]
