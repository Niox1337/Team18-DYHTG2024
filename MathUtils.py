import math 
import numpy as np

def getHeading2(x1, y1, x2, y2):
    vector1=  np.array([70-x1, -y1])
    vector2 = np.array([x2-x1, y2-y1])
    dot_product = np.dot(vector1, vector2)
    vector1_magnitude = math.sqrt( vector1[0]**2 + vector1[1]**2)
    vector2_magnitude = math.sqrt( vector2[0]**2 + vector2[1]**2)
    return math.degrees(math.acos(dot_product/(vector1_magnitude * vector2_magnitude)))

def getHeading(x1, y1, x2, y2):
   heading = math.atan2(y2 - y1, x2 - x1)
   heading = heading * (180.0 / math.pi)
   heading = (heading + 360) % 360
   heading = 360 - heading
   return abs(heading)


