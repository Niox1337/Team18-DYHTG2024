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