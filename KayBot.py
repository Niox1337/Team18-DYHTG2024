#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random

from time import time

from MessageFilter import *
from MathUtils import * 

BLUE_GOAL = (0, 100)
BLUE_PENALTY = (0, 75)
RED_GOAL = (0, -100)
RED_PENALTY = (0, -75) 
CENTER = (0, 0)

def in_goal(x, y):
	return y > 100 or y < -100 or x > 100 or x < -100

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

my_name = args.name
my_team = args.name.split(":")[0]
my_ammo = 1000 # nonsense default arguments
my_health = 1000
my_x = 100
my_y = 100 
my_id = 1000
my_heading = 0
my_turret_heading = 0

# Main loop - read game messages, ignore them and randomly perform actions
i=0

# this is going to get very annoying to handle very fast
CHASING_SNITCH = False
HAVE_SNITCH = False
HAVE_KILL = False
ROAMING = True
SEARCHING_HEALTH = False
SEARCHING_AMMO = False

# how long did we last see these things?
TIME_SINCE_LAST_SNITCH = 1000
TIME_SINCE_LAST_HEALTH = 1000
TIME_SINCE_LAST_AMMO = 1000
TIME_SINCE_LAST_RANDOM = 1000

def goToRandomPlace():
	new_x = random.randint(-90, 90)
	new_y = random.randint(-90, 90)
	new_goal = getHeading(my_x, my_y, new_x, new_y)
	GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": new_goal})

message = GameServer.readMessage()

while True:

	GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)

	message = GameServer.readMessage()
	messageType = message["messageType"]

	# this updates our stats so it NEEDS to be at the top
	if messageType == ServerMessageTypes.OBJECTUPDATE:

		if message["Type"] == "Tank":
			their_name = message["Name"]
			if their_name == my_name:
				my_ammo = message["Ammo"]
				my_health = message["Health"]
				my_x = message["X"]
				my_y = message["Y"]
				my_id = message["Id"]
				my_heading = message["Heading"]
				my_turret_heading = message["TurretHeading"]
			elif my_team in their_name:
				#ally
				pass
			else:
				#track_enemy(message)
				pass


# REGION: SNITCH ACQUIRED
	if messageType == ServerMessageTypes.SNITCHPICKUP:
			if message["Id"] == my_id:
				HAVE_SNITCH = True
				ROAMING = False

	# in before i forget to reset one of these as i add new ones
	if messageType == ServerMessageTypes.DESTROYED:
		HAVE_SNITCH = False
		CHASING_SNITCH = False
		HAVE_KILL = False
		SEARCHING_HEALTH = False
		SEARCHING_AMMO = False
		ROAMING = True

	if HAVE_SNITCH:
		print("RUNNING WITH SNITCH")
		to_goal = getHeading(my_x, my_y, BLUE_GOAL[0], BLUE_GOAL[1])
		GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
		if in_goal(my_x, my_y):
			HAVE_SNITCH = False
			ROAMING = True
			to_goal = getHeading(my_x, my_y, CENTER[0], CENTER[1])
			GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
		continue

# REGION: HANDLE KILL
	if HAVE_KILL:
		if in_goal(my_x, my_y):
			HAVE_KILL = False
			ROAMING = True
			# TODO : set to roaming, not just return to center
			to_goal = getHeading(my_x, my_y, CENTER[0], CENTER[1])
			GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
		else:
			to_goal = getHeading(my_x, my_y, BLUE_GOAL[0], BLUE_GOAL[1])
			GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
		continue

	if my_ammo == 0:
		SEARCHING_AMMO = True
		ROAMING = False

	if my_health == 1:
		SEARCHING_HEALTH = True
		ROAMING = False

	if messageType == ServerMessageTypes.OBJECTUPDATE:

		if message["Type"] == "Tank":
			their_name = message["Name"]
			if their_name == my_name:
				my_ammo = message["Ammo"]
				my_health = message["Health"]
				my_x = message["X"]
				my_y = message["Y"]
				my_id = message["Id"]
				my_heading = message["Heading"]
				my_turret_heading = message["TurretHeading"]
			elif my_team in their_name:
				#ally
				pass
			else:
				track_enemy(message)
				#pass

# # REGION: SEARCHING HEALTH (these need messages in, unlike have kill and have snitch which don't)
		if SEARCHING_HEALTH:
			GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_turret_heading + 70})
			if my_health > 1:
				SEARCHING_HEALTH = False 
				ROAMING = True
			if message["Type"] == "HealthPickup":
				to_health = getHeading(my_x, my_y, message["X"], message["Y"])
				GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_health})
				GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": to_health})
				TIME_SINCE_LAST_HEALTH = time()
			else:
				if time() - TIME_SINCE_LAST_HEALTH > 2:
					goToRandomPlace()
			continue

# REGION: SEARCHING AMMO
		if SEARCHING_AMMO:
			GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_turret_heading + 70})
			if my_ammo > 0:
				SEARCHING_AMMO = False 
				ROAMING = True
			if message["Type"] == "AmmoPickup":
				to_ammo = getHeading(my_x, my_y, message["X"], message["Y"])
				GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_ammo})
				GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": to_ammo})
				TIME_SINCE_LAST_AMMO = time()
			else:
				if time() - TIME_SINCE_LAST_AMMO > 2:
					goToRandomPlace()

			continue

			if their_name == "ManualTankd" or False:
				print("gottem")
		
				#to_goal = getHeading(my_x, my_y, message["X"], message["Y"])
				to_goal = getHeading(my_x, my_y, BLUE_GOAL[0], BLUE_GOAL[1])
				#GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
				print(to_goal)
				GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": to_goal})
				GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_goal})
		
		#if not CHASING_SNITCH: GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {"Amount": 2})

		if ROAMING and message["Type"] == "Snitch":
			print("IT'S THE  SNITCH")
			
			print("CHASE THE SNITCH!!!")
			CHASING_SNITCH = True
			to_snitch = getHeading(my_x, my_y, message["X"], message["Y"])
			GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": to_snitch})
			GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": to_snitch})

	if messageType == ServerMessageTypes.KILL:
		HAVE_KILL = True
		GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)

# REGION: ROAMING

	if ROAMING and not CHASING_SNITCH:
			print("ROAM")
			if time() - TIME_SINCE_LAST_RANDOM > 4:
				TIME_SINCE_LAST_RANDOM = time()
				goToRandomPlace()
			GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_turret_heading + 70})


	

	


	#track_enemy(message)
    
	if i == 5 or i == 10 or True:
		if random.randint(0, 10) > 5 or True:
			logging.info("Firing")
			GameServer.sendMessage(ServerMessageTypes.FIRE)
	elif i == 10:
		pass
		#logging.info("Turning randomly")
		#GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})
	elif i == 15:
		pass
		#logging.info("Moving randomly")
		#GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': random.randint(0, 10)})
	i = i + 1
	if i > 20:
		i = 0

