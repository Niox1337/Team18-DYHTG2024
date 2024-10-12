from PolynomialRegression import *

enemies = {
}

class Enemy():

    def __init__(self, id):
        self.id = id
        self.message_queue = []
        self.NUM_MESSAGES = 5
    def add_message(self, message):
        self.message_queue.append(message)
        self.message_queue = self.message_queue[-self.NUM_MESSAGES:] # trim old messages
    def last_positions(self):
        get_xy = lambda v: (v["X"], v["Y"])
        return[get_xy(x) for x in self.message_queue]

def predict_new_position(positions):
    ROUNDING = 5
    
    x = [round(v[0], ROUNDING) for v in positions]
    y = [round(v[1], ROUNDING) for v in positions]

    diff_x = [x[i+1] - x[i] for i in range(0, len(x)-1)]
    diff_y = [y[i+1] - y[i] for i in range(0, len(y)-1)]
    avg_x = sum(diff_x)/len(diff_x)
    avg_y = sum(diff_y)/len(diff_y)
    new_x = x[-1] + avg_x
    new_y = y[-1] + avg_y

    return (new_x, new_y)

def track_enemy(message):

    # naive filter
    if message["messageType"] == 18: # need import server message types
        name = message["Name"]
        if "Random" in name in name:
            return # current tanks we don't want to track
        
        if message["Type"] != "Tank":
            return # ignore health items
    else:
        return # ignore other messages
                        
    id = message["Id"]
    if not id in enemies.keys():
        enemies[id] = Enemy(id)
    enemies[id].add_message(message)

    enemy = enemies[id]
    if len(enemy.message_queue) == enemy.NUM_MESSAGES:
        print("LAST POSITIONS:")
        print(enemy.last_positions())
        print("PREDICTING POSITION:")
        print(predict_new_position(enemy.last_positions()))