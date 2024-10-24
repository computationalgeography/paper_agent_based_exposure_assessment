from .config import ActivityType, ActivityDescription, CommuteType, BufferCalculation


class Activity(object):
    def __init__(self):

        self._time_delta = None
        self._end_time = None

        self._activity_type = ActivityType.unknown
        self._activity_description = ActivityDescription.unknown

        self._activity_id = None
        self._travel_mode = CommuteType.unknown

        self._activity_start = None
        self._activity_end = None

        self._agenda_start = None
        self._agenda_end = None

        self._position = None

    def activity(self, current_time):
        raise NotImplementedError

    @property
    def activity_type(self):
        return self._activity_type

    @property
    def activity_id(self):
        return self._activity_id

    @property
    def description(self):
        assert self._activity_description
        return self._activity_description

    @property
    def mode(self):
        assert self._travel_mode
        return self._travel_mode


class PointActivity(Activity):
    def __init__(self, act_desc):
        super().__init__()
        self._activity_type = ActivityType.point
        self._activity_description = act_desc

        self.xcoord = None
        self.ycoord = None


class BufferActivity(Activity):
    def __init__(self, act_desc):
        super().__init__()
        self._activity_type = ActivityType.buffer
        self._activity_description = act_desc

        self.xcoord = None
        self.ycoord = None
        self.buffersize = None
        self.buffer_method = BufferCalculation.unknown


class Point_Final(PointActivity):
    def __init__(self, act_desc, xcoord, ycoord):
        super().__init__(act_desc)

        self.xcoord = xcoord
        self.ycoord = ycoord

    def activity(self, current_time):

        assert self._agenda_start
        assert self._agenda_end

        self._activity_start = current_time
        self._activity_end = self._agenda_end


class Point_Fixed(PointActivity):
    def __init__(self, act_desc, xcoord, ycoord, delta):
        super().__init__(act_desc)

        self.xcoord = xcoord
        self.ycoord = ycoord
        self._activity_delta = delta

    def activity(self, current_time):
        assert self._agenda_start
        assert self._agenda_end

        self._activity_start = current_time
        self._activity_end = self._activity_start + self._activity_delta


class Buffer_Fixed(BufferActivity):
    def __init__(self, act_desc, xcoord, ycoord, delta, buffersize, method=BufferCalculation.mean):
        super().__init__(act_desc)

        self.xcoord = xcoord
        self.ycoord = ycoord
        self._activity_delta = delta
        self.buffersize = buffersize
        self.buffer_method = method

    def activity(self, current_time):
        assert self._agenda_start
        assert self._agenda_end

        self._activity_start = current_time
        self._activity_end = self._activity_start + self._activity_delta


class Buffer_Final(BufferActivity):
    def __init__(self, act_desc, xcoord, ycoord, delta, buffersize, method=BufferCalculation.mean):
        super().__init__(act_desc)

        self.xcoord = xcoord
        self.ycoord = ycoord
        self._activity_delta = delta
        self.buffersize = buffersize
        self.buffer_method = method

    def activity(self, current_time):
        assert self._agenda_start
        assert self._agenda_end

        self._activity_start = current_time
        self._activity_end = self._agenda_end


class Commute(Activity):
    def __init__(self, act_desc, home_x, home_y, work_x, work_y, travel_mode, duration):
        super().__init__()
        self._activity_type = ActivityType.route
        self._activity_description = act_desc

        self.start_x = home_x
        self.start_y = home_y
        self.dest_x = work_x
        self.dest_y = work_y

        self.travel_mode = travel_mode
        self.duration = duration

    def activity(self, current_time):
        assert self._agenda_start
        assert self._agenda_end
        assert self.duration > 0

        self._activity_start = current_time
        self._activity_end = self._activity_start + self.duration * self._time_delta
