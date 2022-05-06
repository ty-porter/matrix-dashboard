from enum import Enum

class InputStatusEnum(Enum):
    NOTHING = 1
    SINGLE_PRESS = 2
    DOUBLE_PRESS = 3
    TRIPLE_PRESS = 4
    LONG_PRESS = 5
    ENCODER_INCREASE = 6
    ENCODER_DECREASE = 7
