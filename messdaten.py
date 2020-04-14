import random
import math
import time


class Report:
    def __init__(self):
        # dummy pos in x and y coordinates
        self.x_pos = 0
        self.y_pos = 0
        self.pos = ()
        self.speed = 0
        self.direction = ''
        self.report = {}
        self.freq = 100  # interval of two positions in ms

    def _get_pos(self):
        self.x_pos = random.randrange(1, 30)
        self.y_pos = random.randrange(1, 30)
        return self.x_pos, self.y_pos

    def _get_two_pos(self):
        # dummy
        # get current pos with UWB System
        x1, y1 = self._get_pos()
        pos1 = x1, y1
        # wait freq in millisecond
        time.sleep(self.freq / 1000)
        # get current pos with UWB System
        x2, y2 = self._get_pos()
        pos2 = x2, y2
        return pos1, pos2

    def _get_speed(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        # calc speed with pos difference
        self.y_res = y2 - y1
        self.x_res = x2 - x1
        # distance between two positions
        self.dist = math.sqrt(self.x_res ** 2 + self.y_res ** 2)
        self.speed = self.dist / (self.freq / 1000)  # speed in m/s, freq in millisecond
        return self.speed

    def _get_direction(self, pos1, pos2):
        #  calc direction: left, right, straight forward
        #  compare angel phi of two pos: if greater than right/left and if smaller than left/rigt
        #  if equal than straight forward
        # dummy
        # get current pos with UWB System
        x1, y1 = pos1
        x2, y2 = pos2
        self.phi_1 = math.atan(x1 / y1)
        self.phi_2 = math.atan(x2 / y2)
        # if (diff_angel < 0) = "left", if (diff_angel > 0) = "right", if (diff_angel == 0) = "forward"
        self.diff_angel = self.phi_2 - self.phi_1
        if self.diff_angel < 0:
            self.direction = "left"
        elif self.diff_angel == 0:
            self.direction = "forward"
        elif self.diff_angel > 0:
            self.direction = "right"
        return self.direction

    def create_report(self):
        pos1, pos2 = self._get_two_pos()
        self.speed = round(self._get_speed(pos1, pos2), 2)
        self.direction = self._get_direction(pos1, pos2)
        self.pos = self._get_pos()
        timestamp = int(time.time())
        self.report = {"position": self.pos, "speed": self.speed, "direction": self.direction, "timestamp": timestamp}
        return self.report
