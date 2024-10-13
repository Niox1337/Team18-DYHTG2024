#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import math
import numpy as np


class ServerMessageTypes(object):
	TEST = 0
	CREATETANK = 1
	DESPAWNTANK = 2
	FIRE = 3
	TOGGLEFORWARD = 4
	TOGGLEREVERSE = 5
	TOGGLELEFT = 6
	TOGGLERIGHT = 7
	TOGGLETURRETLEFT = 8
	TOGGLETURRETRIGHT = 9
	TURNTURRETTOHEADING = 10
	TURNTOHEADING = 11
	MOVEFORWARDDISTANCE = 12
	MOVEBACKWARSDISTANCE = 13
	STOPALL = 14
	STOPTURN = 15
	STOPMOVE = 16
	STOPTURRET = 17
	OBJECTUPDATE = 18
	HEALTHPICKUP = 19
	AMMOPICKUP = 20
	SNITCHPICKUP = 21
	DESTROYED = 22
	ENTEREDGOAL = 23
	KILL = 24
	SNITCHAPPEARED = 25
	GAMETIMEUPDATE = 26
	HITDETECTED = 27
	SUCCESSFULLHIT = 28
    
	strings = {
		TEST: "TEST",
		CREATETANK: "CREATETANK",
		DESPAWNTANK: "DESPAWNTANK",
		FIRE: "FIRE",
		TOGGLEFORWARD: "TOGGLEFORWARD",
		TOGGLEREVERSE: "TOGGLEREVERSE",
		TOGGLELEFT: "TOGGLELEFT",
		TOGGLERIGHT: "TOGGLERIGHT",
		TOGGLETURRETLEFT: "TOGGLETURRETLEFT",
		TOGGLETURRETRIGHT: "TOGGLETURRENTRIGHT",
		TURNTURRETTOHEADING: "TURNTURRETTOHEADING",
		TURNTOHEADING: "TURNTOHEADING",
		MOVEFORWARDDISTANCE: "MOVEFORWARDDISTANCE",
		MOVEBACKWARSDISTANCE: "MOVEBACKWARDSDISTANCE",
		STOPALL: "STOPALL",
		STOPTURN: "STOPTURN",
		STOPMOVE: "STOPMOVE",
		STOPTURRET: "STOPTURRET",
		OBJECTUPDATE: "OBJECTUPDATE",
		HEALTHPICKUP: "HEALTHPICKUP",
		AMMOPICKUP: "AMMOPICKUP",
		SNITCHPICKUP: "SNITCHPICKUP",
		DESTROYED: "DESTROYED",
		ENTEREDGOAL: "ENTEREDGOAL",
		KILL: "KILL",
		SNITCHAPPEARED: "SNITCHAPPEARED",
		GAMETIMEUPDATE: "GAMETIMEUPDATE",
		HITDETECTED: "HITDETECTED",
		SUCCESSFULLHIT: "SUCCESSFULLHIT"
	}
    
	def toString(self, id):
		if id in self.strings.keys():
			return self.strings[id]
		else:
			return "??UNKNOWN??"


class ServerComms(object):
	'''
	TCP comms handler
	
	Server protocol is simple:
	
	* 1st byte is the message type - see ServerMessageTypes
	* 2nd byte is the length in bytes of the payload (so max 255 byte payload)
	* 3rd byte onwards is the payload encoded in JSON
	'''
	ServerSocket = None
	MessageTypes = ServerMessageTypes()
	
	
	def __init__(self, hostname, port):
		self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ServerSocket.connect((hostname, port))

	def readTolength(self, length):
		messageData = self.ServerSocket.recv(length)
		while len(messageData) < length:
			buffData = self.ServerSocket.recv(length - len(messageData))
			if buffData:
				messageData += buffData
		return messageData

	def readMessage(self):
		'''
		Read a message from the server
		'''
		messageTypeRaw = self.ServerSocket.recv(1)
		messageLenRaw = self.ServerSocket.recv(1)
		messageType = struct.unpack('>B', messageTypeRaw)[0]
		messageLen = struct.unpack('>B', messageLenRaw)[0]
		
		if messageLen == 0:
			messageData = bytearray()
			messagePayload = {'messageType': messageType}
		else:
			messageData = self.readTolength(messageLen)
			logging.debug("*** {}".format(messageData))
			messagePayload = json.loads(messageData.decode('utf-8'))
			messagePayload['messageType'] = messageType
			
		logging.debug('Turned message {} into type {} payload {}'.format(
			binascii.hexlify(messageData),
			self.MessageTypes.toString(messageType),
			messagePayload))
		return messagePayload
		
	def sendMessage(self, messageType=None, messagePayload=None):
		'''
		Send a message to the server
		'''
		message = bytearray()
		
		if messageType is not None:
			message.append(messageType)
		else:
			message.append(0)
		
		if messagePayload is not None:
			messageString = json.dumps(messagePayload)
			message.append(len(messageString))
			message.extend(str.encode(messageString))
			    
		else:
			message.append(0)
		
		logging.debug('Turned message type {} payload {} into {}'.format(
			self.MessageTypes.toString(messageType),
			messagePayload,
			binascii.hexlify(message)))
		return self.ServerSocket.send(message)

def getHeading(x1, y1, x2, y2):
	heading = math.atan2(y2 - y1, x2 - x1)
	heading = heading * (180.0 / math.pi)
	heading = (heading + 360) % 360
	heading = 360 - heading
	return abs(heading)

def calculate_distance(x1, y1, x2, y2):
    X = abs(x1-x2)
    Y = abs(y1-y2)
    return math.sqrt(X**2 + Y**2)

def get_current_state(name): 
    while(True):
        message = GameServer.readMessage()
        if message["messageType"] != 18:
            continue
        if message["Name"] == name:
            return message

def goToPoint(x1,y1,x2,y2):
    heading = getHeading(x1,y1,x2,y2)
    for i in range(20):
        if i == 5:
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,{"Amount": heading})
        if i == 15:
            distance = calculate_distance(x1,y1,x2,y2)
            GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {"Amount": distance})
            
def go_to_bank(x1,y1):
    if abs(x1) > 50:
        goToPoint(x1, y1, 0, y1)
    
    if calculate_distance(currentX, currentY, 0, 100) < calculate_distance(currentX, currentY, 0, 100):
        goToPoint(currentState['X'], currentState['Y'], 0, 100)
    else:
        goToPoint(currentState['X'], currentState['Y'], 0, 100)

def attack(tank, enemy):
	x1,y1 = tank['X'], tank['Y']
	x2,y2 = enemy['X'], enemy['Y']
	GameServer.sendMessage(ServerMessageTypes.STOPALL)
	heading = getHeading(x1,y1,x2,y2)
	while True:
		tank = get_current_state(tank['Name'])
		enemy = get_current_state(enemy['Name'])
		if enemy['Health'] == 0:
			go_to_bank(tank['X'], tank['Y'])
			break
		for i in range(10):
			if i == 0:
				GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": heading})
			if i == 3:
				GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": heading})
			if i == 7:
				distance = calculate_distance(x1, y1, x2, y2) - 10
				GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {"Amount": distance})
			elif i == 5 or i == 10:
				GameServer.sendMessage(ServerMessageTypes.FIRE)
	GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETRIGHT)

 
def findRandomLocation(currentX, currentY):
	GameServer.sendMessage(ServerMessageTypes.STOPMOVE)
	GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": random.randint(90,270)})
	pointX, pointY =  random.randint(-50, 50), random.randint( -80, 80)
	heading = getHeading(currentX,currentY, pointX, pointY)
	for i in range(11):
		if i == 5: 
			GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,	{"Amount": heading} )
		if i == 10:
			GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD, {"Amount": heading})

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='TeamA:RandomBot', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)


# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

# Spawn our tank
logging.info("Creating tank with name '{}'".format(args.name))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})

# Main loop - read game messages, ignore them and randomly perform actions
i=0
message = GameServer.readMessage()
GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETRIGHT)
GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)

currentState = get_current_state(args.name)
findRandomLocation(currentState['X'], currentState['Y'])

i = 0
while True:
	message = GameServer.readMessage()
	currentState = get_current_state(args.name)
	currentX = currentState['X']
	currentY = currentState['Y']
    
	if abs(currentX >= 50) or abs(currentY) >= 80:
		findRandomLocation(currentX, currentY)
    
	if message["messageType"] == 18:
		if message['Type'] == 'Tank' and message['Name'] != args.name and message['Health'] > 0:
			if currentState["Ammo"] < 3:
				continue
			GameServer.sendMessage(ServerMessageTypes.STOPALL)
			attack(currentState, message)
			GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)
			GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETRIGHT)
		elif message['Type'] == 'HealthPickup' and currentState['Health'] <= 2:
			goToPoint(currentX, currentY, message['X'], message['Y'])
		elif message['Type'] == 'AmmoPickup' and currentState['Ammo'] <= 5:
			goToPoint(currentX, currentY, message['X'], message['Y'])
            
	if message["messageType"] == 24:
		go_to_bank(currentX,currentY)
		if i == 10:
			GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)
	
	i += 1
	if i== 20:
		findRandomLocation(currentX, currentY)
	

