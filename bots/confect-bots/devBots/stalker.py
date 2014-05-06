"""
@name: stalker
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

import player
from suspAcc import *

from game import State, Game

import ruru
# ---------------


# ---------------
# MODUS OPERANDI:
# ---------------
# Bot that maintains suspicion scores based solely on opponent modelling.
# This is just for the sake of seeing how pure OM fares in identifying spies via logging inaccuracy.
# Leaves its decision making up to Ruru.
# ---------------


# ---------------
# CONSTANTS
# ---------------
k_byRoleStatsKey = 'ByRole'

# Perfect information behaviours
k_behaviour_general_selectsTeamFeaturingSelf = 'selectsTeamFeaturingSelf'
k_behaviour_general_votesForTeamFeaturingSelf = 'votesForTeamFeaturingSelf'
k_behaviour_general_votesForTeamNotFeaturingSelf = 'votesForTeamNotFeaturingSelf'
k_behaviour_general_votesForTeam3NotFeaturingSelf = 'votesForTeam3NotFeaturingSelf'
k_behaviour_general_votesAgainstTeamOnFifthAttempt = 'votesAgainstTeamOnFifthAttempt'

# Sketchy behaviours`
# We can't really be sure these are significant because they may vary based on competence of resistance play and pure chance
k_behaviour_general_selectsSuccessfulTeam = 'selectsSuccessfulTeam'
k_behaviour_general_votesForSuccessfulTeam = 'votesForSuccessfulTeam'
k_behaviour_general_votesForUnsuccsessfulTeam = 'votesForUnsuccessfulTeam'
k_behaviour_general_votesForTeamWithTwoSabotages = 'votesForTeamWithTwoSabotages'   # We suspect spies will have a slight bias against this behaviour
k_behaviour_general_teamOnIsUnsuccessful = 'teamOnIsUnsuccessful'                       # This might allow us to 'learn' correct suspicion to allocate for presence on failed missions (graphs indicate poor performance)

# ---------------
# ENUMS
# ---------------
class MissionOutcome:
    NotExecuted = 0
    Failed = 1
    Successful = 2

# ---------------

# ---------------
# SUPPORTING CLASSES
# ---------------
# MISC
class Variable(object):
    """Variable to track the frequency of an action.
    Coppied from aigd.py"""

    def __init__(self):
        self.total = 0
        self.samples = 0

    def sample(self, value):
        self.total += value
        self.samples += 1

    def estimate(self):
        if self.samples > 0:
            return float(self.total) / float(self.samples)
        else:
            return 0.5

    def combine(self, variable):
        self.total += variable.total
        self.samples += variable.samples

    def __repr__(self):
        if self.samples:
            return "%0.2f%% (%i)" % ((100.0 * float(self.total) / float(self.samples)), self.samples)
        else:
            return "UNKNOWN"


# BEHAVIOUR STATISTIC SCRAPERS
# Hopefully these classes will let us nicely group together the rules that maintain frequencies and calculate
# how well a player in the current game fits a particular model
class BehaviourStatisticScraper:
    """Base class for behaviour statistic scrapers"""

    def __init__(self):

        pass

    def calculateFrequency(self, player, localStats):
        
        raise Exception('Exception: Unimplemented')
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):

        raise Exception('Exception: Unimplemented')
        pass

    def sampleComplimentary(self, variable, modelFreq):

        variable.sample(modelFreq)
        pass

    def sampleContradictory(self, variable, modelFreq):
        
        variable.sample(1.0-modelFreq)
        pass

# Perfect information behaviours
class Behaviour_General_SelectsTeamFeaturingSelf(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if a.leader == player:
                    if player in a.team:
                        freq.sample(1.0)
                    else:
                        freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if a.leader == player:
                    if player in a.team:
                        self.sampleComplimentary(freq, modelFreq)
                    else:
                        self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForTeamFeaturingSelf(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if player in a.team:
                    if a.votes[player.index-1]:
                        freq.sample(1.0)
                    else:
                        freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if player in a.team:
                    if a.votes[player.index-1]:
                        self.sampleComplimentary(freq, modelFreq)
                    else:
                        self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForTeamNotFeaturingSelf(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if not player in a.team:
                    if a.votes[player.index-1]:
                        freq.sample(1.0)
                    else:
                        freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if not player in a.team:
                    if a.votes[player.index-1]:
                        self.sampleComplimentary(freq, modelFreq)
                    else:
                        self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForTeam3NotFeaturingSelf(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if len(a.team) == 3:
                    if not player in a.team:
                        if a.votes[player.index-1]:
                            freq.sample(1.0)
                        else:
                            freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            for a in m.attempts:
                if len(a.team) == 3:
                    if not player in a.team:
                        if a.votes[player.index-1]:
                            self.sampleComplimentary(freq, modelFreq)
                        else:
                            self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesAgainstTeamOnFifthAttempt(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            if len(m.attempts) == 5:
                a = m.attempts[4]
                if not a.votes[player.index-1]:
                    freq.sample(1.0)
                else:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            if len(m.attempts) == 5:
                a = m.attempts[4]
                if not a.votes[player.index-1]:
                    self.sampleComplimentary(freq, modelFreq)
                else:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

# Sketchy behaviours
# We can't really be sure these are significant because they may vary based on competence of resistance play and pure chance
# Other bots use them, or measures similar to them, however, and a few seem to have worked well during early development...
class Behaviour_General_SelectsSuccessfulTeam(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            a = m.attempts[-1]
            if a.leader == player:
                if m.outcome == MissionOutcome.Successful:
                    freq.sample(1.0)
                elif m.outcome == MissionOutcome.Failed:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            a = m.attempts[-1]
            if a.leader == player:
                if m.outcome == MissionOutcome.Successful:
                    self.sampleComplimentary(freq, modelFreq)
                elif m.outcome == MissionOutcome.Failed:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForSuccessfulTeam(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            if m.outcome == MissionOutcome.Successful:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    freq.sample(1.0)
                else:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            if m.outcome == MissionOutcome.Successful:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    self.sampleComplimentary(freq, modelFreq)
                else:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForUnsuccessfulTeam(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            if m.outcome == MissionOutcome.Failed:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    freq.sample(1.0)
                else:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            if m.outcome == MissionOutcome.Failed:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    self.sampleComplimentary(freq, modelFreq)
                else:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_VotesForTeamWithTwoSabotages(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            if m.sabotages == 2:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    freq.sample(1.0)
                else:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            if m.sabotages == 2:
                a = m.attempts[-1]
                if a.votes[player.index-1]:
                    self.sampleComplimentary(freq, modelFreq)
                else:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

class Behaviour_General_TeamOnIsUnsuccessful(BehaviourStatisticScraper):
    def calculateFrequency(self, player, localStats):
        freq = Variable()
        for m in localStats.missions:
            a = m.attempts[-1]
            if player in a.team:
                if m.outcome == MissionOutcome.Successful:
                    freq.sample(1.0)
                elif m.outcome == MissionOutcome.Failed:
                    freq.sample(0.0)
        return freq
        pass

    def calculateModelFitting(self, player, localStats, modelFreq):
        freq = Variable()
        for m in localStats.missions:
            a = m.attempts[-1]
            if player in a.team:
                if m.outcome == MissionOutcome.Successful:
                    self.sampleComplimentary(freq, modelFreq)
                elif m.outcome == MissionOutcome.Failed:
                    self.sampleContradictory(freq, modelFreq)
        return freq
        pass

# LOCAL STATISTICS
class PlayerModelFittings:
    """Class to represent how well the current spy and resistance models for a player fit him."""

    def __init__(self):
        self.resFitting = Variable()
        self.spyFitting = Variable()

    def getOverallFitting(self):
        return (self.resFitting.estimate()*0.5) + (self.spyFitting.estimate()*0.5)

    def getSuspicion(self):
        return ((1.0-self.resFitting.estimate())*0.5) + (self.spyFitting.estimate()*0.5)

class AttemptRecord(object):
    """Class to represent a single voting attempt in our history ofthe current game."""

    def __init__(self, leader, team, votes):

        self.leader = leader
        self.team = [t for t in team]
        self.votes = [v for v in votes]

        pass

class MissionRecord(object):
    """Class to represent a single mission in our history of the current game."""

    def __init__(self):

        self.attempts = []
        self.sabotages = 0
        self.saboteurs = []
        self.certainSpies = []
        self.outcome = MissionOutcome.NotExecuted

        pass

    def logAttempt(self, attemptRecord):
        self.attempts.append(attemptRecord)

    def logSabotages(self, sabotages, saboteurs):
        self.sabotages = sabotages
        self.saboteurs = saboteurs
        self.outcome = MissionOutcome.Failed if sabotages else MissionOutcome.Successful

    def logCertainSpies(self, spies):
        self.certainSpies = spies

class LocalStatistics(object):
    """Class to record the history of the current game, including team selections, leaders, voting, sabotages.
    These will be used to update GlobalStatistics for each player at the end of the game"""
    
    def __init__(self, observer):

        self.resistance = []
        self.spies = []
        self.missions = []
        self.observer = observer

        pass

    def logIdentities(self, resistance ,spies):

        self.resistance = [r for r in resistance]
        self.spies = [s for s in spies]

        pass

    def logMission(self, mission):

        self.missions.append(mission)

        pass


# GLOBAL STATISTICS
class GlobalStatistics(object):
    """Class to represent the likelihood of a player to take certain actions in certain circumstances."""

    def __init__(self):

        self.generalFrequencies = {}
        self.generalBehaviours = {}

        # set up general statistics to track
        # -
        col = [
               # Perfect information behaviours
               #(k_behaviour_general_selectsTeamFeaturingSelf, Behaviour_General_SelectsTeamFeaturingSelf),
               #(k_behaviour_general_votesForTeamFeaturingSelf, Behaviour_General_VotesForTeamFeaturingSelf),
               #(k_behaviour_general_votesForTeamNotFeaturingSelf, Behaviour_General_VotesForTeamNotFeaturingSelf),
               #(k_behaviour_general_votesForTeam3NotFeaturingSelf, Behaviour_General_VotesForTeam3NotFeaturingSelf),
               #(k_behaviour_general_votesAgainstTeamOnFifthAttempt, Behaviour_General_VotesAgainstTeamOnFifthAttempt),
               ## Sketchy behaviours
               #(k_behaviour_general_selectsSuccessfulTeam, Behaviour_General_SelectsSuccessfulTeam),
               #(k_behaviour_general_votesForSuccessfulTeam, Behaviour_General_VotesForSuccessfulTeam),
               #(k_behaviour_general_votesForUnsuccsessfulTeam, Behaviour_General_VotesForUnsuccessfulTeam),
               #(k_behaviour_general_votesForTeamWithTwoSabotages, Behaviour_General_VotesForTeamWithTwoSabotages),
               (k_behaviour_general_teamOnIsUnsuccessful, Behaviour_General_TeamOnIsUnsuccessful),
               ]
        for c in col:
            self.generalFrequencies.setdefault(c[0], Variable())
            self.generalBehaviours.setdefault(c[0], c[1]())
 
        pass

    def update(self, player, localStats):
        
        # Process the given game history
        for k in self.generalFrequencies.keys():
            self.generalFrequencies[k].combine(self.generalBehaviours[k].calculateFrequency(player, localStats))
            pass

        pass

    def getModelFittings(self, player, localStats):

        # Calculate how well the player fits this model, given the current game history in localStats
        fitting = Variable()

        for k in self.generalFrequencies.keys():
            fitting.combine(self.generalBehaviours[k].calculateModelFitting(player, localStats, self.generalFrequencies.setdefault(k, Variable()).estimate()))
            pass

        return fitting

        pass

class GlobalStatisticsRes(GlobalStatistics):
    """Class to represent the likelihood of a player to take certain actions in certain circumstances.
    Contains resistance-specific stats"""

    def __init__(self):

        GlobalStatistics.__init__(self)
        self.resistanceFrequencies = {}
        self.resistanceBehaviours = {}

        # Set up resistance statistics to track

        pass

    def update(self, player, localStats):
        
        GlobalStatistics.update(self, player, localStats)
        # Process the given game history
        for k in self.resistanceFrequencies.keys():
            self.resistanceFrequencies[k].combine(self.resistanceBehaviours[k].calculateFrequency(player, localStats))
            pass

        pass

    def getModelFittings(self, player, localStats):

        fitting = GlobalStatistics.getModelFittings(self, player, localStats)
        # Calculate how well the player fits this model, given the current game history in localStats

        for k in self.resistanceFrequencies.keys():
            fitting.combine(self.resistanceBehaviours[k].calculateModelFitting(player, localStats, self.resistanceFrequencies.setdefault(k, Variable()).estimate()))
            pass

        return fitting

        pass

class GlobalStatisticsSpy(GlobalStatistics):
    """Class to represent the likelihood of a player to take certain actions in certain circumstances.
    Contains spy-specific stats"""

    def __init__(self):

        GlobalStatistics.__init__(self)
        self.spyFrequencies = {}
        self.spyBehaviours = {}

        # Set up spy statistics to track

        pass

    def update(self, player, localStats):
        
        GlobalStatistics.update(self, player, localStats)
        # Process the given game history
        for sb in self.spyFrequencies.keys():
            self.spyFrequencies[k].combine(self.spyBehaviours[k].calculateFrequency(player, localStats))
            pass

        pass

    def getModelFittings(self, player, localStats):

        fitting = GlobalStatistics.getModelFittings(self, player, localStats)
        # Calculate how well the player fits this model, given the current game history in localStats

        for k in self.spyFrequencies.keys():
            fitting.combine(self.spyBehaviours[k].calculateModelFitting(player, localStats, self.spyFrequencies.setdefault(k, Variable().estimate())))
            pass

        return fitting

        pass

class GlobalStatisticsPair(object):
    """Class to represent the likelihood of a player to take certain actions in certain circumstances.
    Maintains a separate record for each role, spy or resistance."""

    def __init__(self):

        self.res = GlobalStatisticsRes()
        self.spy = GlobalStatisticsSpy()

        pass

    def update(self, player, localStats):

        if player in localStats.resistance:
            stats = self.res 
        elif player in localStats.spies:
            stats = self.spy
        else:
            stats = None

        if stats:
            stats.update(player, localStats)

        pass

    def getModelFittings(self, player, localStats):

        fittings = PlayerModelFittings()
        fittings.resFitting = self.res.getModelFittings(player, localStats)
        fittings.spyFitting = self.spy.getModelFittings(player, localStats)
        return fittings

        pass

class GlobalStatisticsCollection(object):
    """Class to represent the likelihood of a player to take certain actions in certain circumstances.
    May be set to track each player independantly, or maintain one record for each role, spy or resistance,
    across all players."""

    def __init__(self, trackByRole=False):

        self.collection = {}
        self.trackByRole = trackByRole

        pass

    def getStatsFor(self, player):

        name = k_byRoleStatsKey if self.trackByRole else player.name
        return self.collection.setdefault(name, GlobalStatisticsPair())

        pass

    def updateStats(self, localStats):

        [self.updateStatsFor(p, localStats) for p in localStats.resistance if not p == localStats.observer]
        [self.updateStatsFor(p, localStats) for p in localStats.spies if not p == localStats.observer]

        pass

    def updateStatsFor(self, player, localStats):

        stats = self.getStatsFor(player)
        stats.update(player, localStats)

        pass

    def getModelFittings(self, players, localStats):

        fittings = {}

        for p in players:
            stats = self.getStatsFor(p)
            fittings[p.name] = stats.getModelFittings(p, localStats)

        return fittings

        pass

# ---------------


# ---------------
# MAIN CLASS
# ---------------
class Stalker(ruru.Ruru):

    globalStatisticsCollection = GlobalStatisticsCollection(False)

    def onGameRevealed(self, players, spies):
        """This function will be called to list all the players, and if you're
        a spy, the spies too -- including others and yourself.
        """
        ruru.Ruru.onGameRevealed(self, players, spies)

        self.localStatistics = LocalStatistics(player.Player(self.name, self.index))
        self.playerModelFittings = self.globalStatisticsCollection.getModelFittings(self.otherPlayers, self.localStatistics)
        self.currentMission = None
        self.iSabotaged = False

        # DPT - Inaccuracy Stuff
        self.suspicionsAfterMissions = SuspicionsAfterMissions(self.otherPlayers)
        nameMangler = self.game._mangler if SuspicionStatsLogger.requiresBotnameMangler() else None
        self.suspicionLogger = SuspicionStatsLogger(self.name, mangler=nameMangler)

        pass

    def onMissionAttempt(self, mission, tries, leader):
        """Callback function when a new turn begins, before the
        players are selected.
        """
        ruru.Ruru.onMissionAttempt(self, mission, tries, leader)

        self.currentMission = MissionRecord()
        self.iSabotaged = False

        pass

    # Called when we are the leader to allow selection of a team.
    def select(self, players, count):
        """Pick a sub-group of players to go on the next mission.
        """
        return ruru.Ruru.select(self, players, count)

        pass
    
    def onTeamSelected(self, leader, team):
        """Called immediately after the team is selected to go on a mission,
        and before the voting happens.
        @param leader   The leader in charge for this mission.
        @param team     The team that was selected by the current leader.
        """
        ruru.Ruru.onTeamSelected(self, leader ,team)

        pass

    # Called when a team has been selected to allow us to vote.
    def vote(self, team):
        """Given a selected team, deicde whether the mission should proceed.
        """
        return ruru.Ruru.vote(self, team)

        pass
       
    def onVoteComplete(self, votes):
        """Callback once the whole team has voted.
        @param votes        Boolean votes for each player (ordered).
        """
        ruru.Ruru.onVoteComplete(self, votes)

        # Log the voting attempt
        self.currentMission.logAttempt(AttemptRecord(self.game.leader, self.game.team, votes))

        pass

    # Called when we are on a mission as a spy, to allow us to sabotage it.
    def sabotage(self):
        """Decide what to do on the mission once it has been approved.  This
        function is only called if you're a spy, otherwise you have no choice.
        """
        sabotage =  ruru.Ruru.sabotage(self)
        self.iSabotaged = sabotage
        return sabotage

        pass
        
    def onMissionComplete(self, sabotaged):
        """Callback once the players have been chosen.
        """
        ruru.Ruru.onMissionComplete(self, sabotaged)

        # If we are a spy and were on the mission, we should know who did what:
        saboteurs = []
        if self.spy:
            if self.iSabotaged:
                saboteurs.append(player.Player(self.name, self.index))
            if (sabotaged == 1 and not self.iSabotaged) or (sabotaged == 2):
                # Other spy must have sabotaged
                saboteurs.append([player.Player(o.name, o.index) for o in self.spies if not o == self][0]) 

        # Log the mission result
        self.currentMission.logSabotages(sabotaged, saboteurs)
        # Ruru only has very simple logic for identifying players who're definately spies
        # (Only when both sabotage on a two-man mission - I think it's reasonable to expect
        # any bot to pick up on that, so it shouldn't be impacted too much by bot competance)
        self.currentMission.logCertainSpies(self.spies)
        # Log the mission to localStats
        self.localStatistics.logMission(self.currentMission)

        # Update model fittings (from which we can calculate suspicion scores):
        self.playerModelFittings = self.globalStatisticsCollection.getModelFittings(self.otherPlayers, self.localStatistics)

        # DPT - Inaccuracy Stuff
        # Track suspicion after each mission
        currentSuspicions = self.calculateCurrentPlayerSuspicions()
        self.suspicionsAfterMissions.logMission(currentSuspicions)

        pass
    
    # DPT - Inaccuracy Stuff
    def calculateCurrentPlayerSuspicions(self):
        currentSuspicions = {}

        for o in self.otherPlayers:
            currentSuspicions[o.name] = self.playerModelFittings[o.name].getSuspicion()

        return currentSuspicions
      
    def onGameComplete(self, win, spies):
        """Callback once the game is complete, and everything is revealed.
        """
        ruru.Ruru.onGameComplete(self, win, spies)

        # Note spy and resistance identities in local statistics
        resistance = [r for r in self.otherPlayers if r not in spies]
        self.localStatistics.logIdentities(resistance, spies)

        # Update global statistics
        self.globalStatisticsCollection.updateStats(self.localStatistics)

        # DPT - Inaccuracy Stuff
        # Record accuracy of spy identification
        #print("Stalker suspicion statistics: ")
        accuraciesAfterMissions = self.suspicionsAfterMissions.toAccuraciesAfterMissions(spies)
        #accuraciesAfterMissions.printAccuracies()
        # Log to file
        self.suspicionLogger.logGame(accuraciesAfterMissions, self.spy)

        pass


    @classmethod
    def onCompetitionEnd(cls):
        """Callback once a program executing a series of games has completed.
        This allows bots to throw up some useful statistics and info for debugging.
        """
        ruru.Ruru.onCompetitionEnd()

        pass



# ---------------
