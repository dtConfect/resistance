"""
@name: nosey
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

import stalker
# ---------------


# ---------------
# MODUS OPERANDI:
# ---------------
# Like Stalker (stalker.py), but tracks a single spy and resistance model sampled
# from all players.
# ---------------


# ---------------
# MAIN CLASS
# ---------------
class Nosey(stalker.Stalker):

    def onGameRevealed(self, players, spies):
        """This function will be called to list all the players, and if you're
        a spy, the spies too -- including others and yourself.
        """

        # Change the tracking model before it's used for anything.
        self.globalStatisticsCollection.trackByRole = True
        stalker.Stalker.onGameRevealed(self, players, spies)

        pass

    def onMissionAttempt(self, mission, tries, leader):
        """Callback function when a new turn begins, before the
        players are selected.
        """
        stalker.Stalker.onMissionAttempt(self, mission, tries, leader)

        pass

    # Called when we are the leader to allow selection of a team.
    def select(self, players, count):
        """Pick a sub-group of players to go on the next mission.
        """
        return stalker.Stalker.select(self, players, count)

        pass
    
    def onTeamSelected(self, leader, team):
        """Called immediately after the team is selected to go on a mission,
        and before the voting happens.
        @param leader   The leader in charge for this mission.
        @param team     The team that was selected by the current leader.
        """
        stalker.Stalker.onTeamSelected(self, leader ,team)

        pass

    # Called when a team has been selected to allow us to vote.
    def vote(self, team):
        """Given a selected team, deicde whether the mission should proceed.
        """
        return stalker.Stalker.vote(self, team)

        pass
       
    def onVoteComplete(self, votes):
        """Callback once the whole team has voted.
        @param votes        Boolean votes for each player (ordered).
        """
        stalker.Stalker.onVoteComplete(self, votes)

        pass

    # Called when we are on a mission as a spy, to allow us to sabotage it.
    def sabotage(self):
        """Decide what to do on the mission once it has been approved.  This
        function is only called if you're a spy, otherwise you have no choice.
        """
        return stalker.Stalker.sabotage(self)

        pass
        
    def onMissionComplete(self, sabotaged):
        """Callback once the players have been chosen.
        """
        stalker.Stalker.onMissionComplete(self, sabotaged)

        pass
      
    def onGameComplete(self, win, spies):
        """Callback once the game is complete, and everything is revealed.
        """
        stalker.Stalker.onGameComplete(self, win, spies)

        pass

    @classmethod
    def onCompetitionEnd(cls):
        """Callback once a program executing a series of games has completed.
        This allows bots to throw up some useful statistics and info for debugging.
        """
        stalker.Stalker.onCompetitionEnd()

        pass



# ---------------
