import math 


def getHeading(x1, y1, x2, y2):
   heading = math.atan2(y2 - y1, x2 - x1)
   heading = heading * (180.0 / math.pi)
   heading = (heading + 360) % 360
   heading = 360 - heading
   return abs(heading)


