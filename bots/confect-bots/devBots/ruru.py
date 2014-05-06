"""
@name: ruru
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
# As many expert rules as we can throw together.
# Minimal/no logical deduction or opponent modelling.
# ---------------


# ---------------
# MAIN CLASS
# ---------------
class Ruru(Bot):

    def onGameRevealed(self, players, spies):
        """This function will be called to list all the players, and if you're
        a spy, the spies too -- including others and yourself.
        """
        self.all = [p for p in players]
        self.spies = [s for s in spies]
        self.resistance = [r for r in players if r not in spies]
        self.otherPlayers = [o for o in players if not o == self]
        

        pass

    def onMissionAttempt(self, mission, tries, leader):
        """Callback function when a new turn begins, before the
        players are selected.
        """
        pass

    # Called when we are the leader to allow selection of a team.
    def select(self, players, count):
        """Pick a sub-group of players to go on the next mission.
        """

        selection = []
        requirement = count

        # Always make sure to select yourself for missions with a team size of 3.
        if count == 3:
            selection += [self]
            requirement = count - len(selection)

        # If we're a spy, always make sure there's a spy on the team
        if self.spy:
            if not len([s for s in selection if s in self.spies]):
                selection += random.sample([s for s in self.spies if s not in selection], 1)
                requirement = count - len(selection)

        # Make up remaining numbers with a random sample of non-spies (for resistancem this is all players)
        selection += random.sample([r for r in self.resistance if r not in selection], requirement)
        requirement = count - len(selection)

        # In case we don't have enough somehow, make up remaining numbers via random selection
        selection += random.sample([o for o in self.otherPlayers if o not in selection], requirement)
        requirement = count - len(selection)

        return selection
    
    def onTeamSelected(self, leader, team):
        """Called immediately after the team is selected to go on a mission,
        and before the voting happens.
        @param leader   The leader in charge for this mission.
        @param team     The team that was selected by the current leader.
        """
        pass

    # Called when a team has been selected to allow us to vote.
    def vote(self, team):
        """Given a selected team, deicde whether the mission should proceed.
        """
        spiesOnMission = [s for s in self.spies if s in self.game.team]

        # Voting against the last voting attempt for a mission is a damn giveaway that you're
        # a spy, or you don't know the rules of the game. If all of the resistance members
        # know what they're doing the spies can never win this way, so don't even try.
        if self.game.tries == 5:
            return True
        
        # Is there really any point in voting against teams for the first mission?
        if self.game.turn == 1:
            return True

        # Approve teams that we are the leader of 
        # This is a sticky one if you don't have a strong selection policy, I think.
        # Not approving it might appear strange, but why have confidence in your own, weak selection?
        if self.game.leader == self:
            return True

        # As a spy, if only one more mission is required for spy victory, approve any team
        # with at least one spy on it
        if self.spy:
            if self.game.losses == 2:
                if len(spiesOnMission) > 0:
                    return True

        # The only reason a resistance member might sensibly approve a team of size three which
        # does not feature himself is if we are on the fifth voting attempt. Such a team is
        # garunteed to feature at least one spy.
        if len(team) == 3 and not self.index in [p.index for p in team]:
            return False

        # If we are a spy, reject teams that are entirely composed of spies
        if self.spy:
            if len(spiesOnMission) == len(team):
                return False

        # If we are a spy, reject teams that have zero or more than one spy on them
        if self.spy:
            if not len(spiesOnMission) == 1:
                return False
                pass

        # If we are a spy, accept any team with at least one spy on
        if self.spy:
            if len(spiesOnMission) > 0:
                return True

        # Reject teams with known spies on them
        if len(spiesOnMission):
            return False

        # Otherwise, approve the mission
        return True

        # Fallback case. Should probably make sure we can't make it to this.
        return random.choice([True, False])
       
    def onVoteComplete(self, votes):
        """Callback once the whole team has voted.
        @param votes        Boolean votes for each player (ordered).
        """
        pass

    # Called when we are on a mission as a spy, to allow us to sabotage it.
    def sabotage(self):
        """Decide what to do on the mission once it has been approved.  This
        function is only called if you're a spy, otherwise you have no choice.
        """

        spiesOnMission = [s for s in self.spies if s in self.game.team]

        # We don't need to worry about revealing ourselves at this point in the game; we won.
        if self.game.losses == 2:
            return True;

        # Don't sabotage if every player on the team is a spy. We consider this too risky.
        if len(spiesOnMission) == len(self.game.team):
            return False

        # If we are the leader on a team of three with one other spy, however, assume the other spy
        # on the team won't sabotage (some bots have this policy, others depend on strange things like
        # table index...).
        if self.game.leader == self:
            return True

        # Finally, if we're the only spy on the team, sabotage!
        if len(spiesOnMission) == 1:
            return True

        return False
        
    def onMissionComplete(self, sabotaged):
        """Callback once the players have been chosen.
        """

        # As resistance, make a note of who the spies are when they give themselves away
        if not self.spy:
            if len(self.game.team) == sabotaged:
                self.spies += [s for s in self.game.team if s not in self.spies]
                self.resistance = [r for r in self.resistance if r not in self.game.team]

        pass
        
    def onGameComplete(self, win, spies):
        """Callback once the game is complete, and everything is revealed.
        """
        pass


    @classmethod
    def onCompetitionEnd(cls):
        """Callback once a program executing a series of games has completed.
        This allows bots to throw up some useful statistics and info for debugging.
        """
        pass



# ---------------
