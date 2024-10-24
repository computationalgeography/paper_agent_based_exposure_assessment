import enum
import sqlite3


class EnumBase(enum.Enum):
    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.name


class ActivityType(EnumBase):
    """  """
    unknown = None
    point = 1
    buffer = 2
    route = 3


class ActivityDescription(EnumBase):
    """  """
    unknown = None
    home = 1
    work = 2
    commute_home_to_work = 3
    commute_work_to_home = 4
    leisure = 5


class CommuteType(EnumBase):
    """  """
    unknown = -1
    car = 0
    bike = 1
    foot = 2
    train = 3
    public_transport = 4


class BufferCalculation(EnumBase):
    """  """
    unknown = 0
    sum = 1
    mean = 2
