"""
@name: test001
@author: Dan Taylor
@license: GNU Public License (GPL) version 3.0
@about: 2013 dissertation project for BScH (Hons) Computer Games Programming, University of Derby.
"""


# ---------------
# PACKAGES
# ---------------
import random
import itertools
import logging
import collections
import logging
import logging.handlers

from player import Bot
from game import State, Game
# ---------------


# ---------------
# MODUS OPERANDI:
# ---------------
# Only selects and approves teams containing itself.
# Doesn't care who else is on the team.
# Always sabotages if playing a spy.
# Special cases:
# 1.	On the last voting opportunity:
# 			If playing as a spy, rejects the mission.
# 			If playing as resistance, approves the mission.
# ---------------


# ---------------
# MAIN CLASS
# ---------------
class test001(Bot):
	# Called when we are the leader to allow selection of a team.
	def select(self, players, count):
		"""Pick a sub-group of players to go on the next mission."""
		# Select self and (count-1) others to go on the mission
		return [self] + random.sample(self.others(), count - 1)
	
	# Called when a team has been selected to allow us to vote.
	def vote(self, team):
		"""Given a selected team, deicde whether the mission should proceed."""
		# Special case #1: Spies will always reject the last vote, resistance will approve
		if self.game.tries == 5:
			return not self.spy
		
		# Only approve missions that we're going on!
		if self in self.game.team:
			return True
		else:
			return False
		
	# Called when we are on a mission as a spy, to allow us to sabotage it.
	def sabotage(self):
		"""Decide what to do on the mission once it has been approved."""
		# Always sabotage missions we're on.
		return True
		
		
		
# ---------------


