#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import importlib
import random
import math
import sys

# Import the whole competition module so we can access the original, mutable global statistics
import competition
from competition import *
from player import *

import pseudonymgen


class NameMangler:
    """Class to maintain a collection of real names, mangled names, and the relations
    between them."""
    __nextNameUUID = 0

    def __init__(self):
        self._namesR2M = {} # Names - real to mangled
        self._namesM2R = {} # Names - mangled to real

    def setNames(self, newNames):
        """Take a set of real names, discard our old dictionaries and create new ones for
        the given set of real names, and freshly generated, unique, and historically
        unique mangled names"""
        self._namesR2M.clear()
        self._namesM2R.clear()
        #print("")
        for r in newNames:
            #textName = 'bot'
            textName = pseudonymgen.getName()
            m = "%s-%i" % (textName, self.__nextNameUUID)
            #print >>sys.stderr, '%s will be known as %s' %(r, m)
            self.__nextNameUUID += 1
            self._namesR2M.setdefault(r, m)

        self._namesM2R = {m:r for r, m in self._namesR2M.items()}

    def getRealName(self, mangledName):
        return self._namesM2R[mangledName]

    def getMangledName(self, realName):
        return self._namesR2M[realName]


class BurstCompetitionRound(CompetitionRound):
    def __init__(self, bots, roles, mangler):
        # Store a reference to the mangler
        # May change this to just a dictionary of manglings later... but that seems too open
        self._mangler = mangler

        # Call the CompetitionRound __init__
        # Hopefully it'll still call through to our createBots override (like C++ wouldn't)
        # - Confirmed - this works nicely :D
        CompetitionRound.__init__(self, bots, roles)

        # Allow access to the name mangler through the state so that our suspicion accuracy logging
        # can unmangle names easily, but damned shall thy house be if thou exploits this in a bot!
        self.state._mangler = self._mangler

    def createBots(self, bots, roles):
        """Override CompetitionRound's createBots function to use the given name mangler"""
        # Create Bot instances based on the constructor passed in.
        self.bots = [p[1](self.state, i, r, p[0]) for p, r, i in zip(bots, roles, range(1, len(bots)+1))]
        
        # Maintain a copy of players that includes minimal data, for passing to other bots.
        #self.state.players = [Player(p.name, p.index) for p in self.bots]
        self.state.players = [Player(self._mangler.getMangledName(p.name), p.index) for p in self.bots]
        #print("Confirm called burst/mangler version of createBots!!!")


class BurstCompetitionRunner(CompetitionRunner):
    def __init__(self, competitors, rounds, burstSize = 10, quiet = False):
        # Store burst size
        self.burstSize = burstSize
        # Create a name mangler to use
        self._nameMangler = NameMangler()
        # Call super initialization and pass required variables through
        CompetitionRunner.__init__(self, competitors, rounds, quiet)
        # Store unique identifiers for each competitor
        self.competitorIds = [getUniqueCompetitorName(i, c) for i, c in zip(range(0, len(self.competitors)), self.competitors)]
        # Print extra debug information?
        self.loud = True

    def listGameSelections(self):
        """Evaluate all bots in all possible permutations! If there are more games requested,
        randomly fill up from a next round of permutations.
        Overridden to group permutations of the same bots (in different
        roles and seats) so that names can be mangled at a set interval."""
        if not self.competitors: raise StopIteration
        
        if not self.burstSize == 0:
            bursts = []

            # Get each unique permutation of roles, where True is Spy and False is Resistance
            roleP = set(itertools.permutations([True, True, False, False, False]))
            # Get each order-independent combination of competitors
            for players in itertools.combinations(zip(self.competitorIds, self.competitors), 5):
                thesePlayersP = []
                # Get each seating permutation of these competitors
                for seating in itertools.permutations(players, 5):
                    for roles in roleP:
                        thesePlayersP.append((players, roles))

                # We should be able to make even bursts
                if not ((len(thesePlayersP) % self.burstSize) == 0):
                    if not self.quiet:
                        print("")
                        print >>sys.stderr, 'Error: Number of permutations per player combination is not divisible by the burstSize: %i / %i = %f' \
                                            % (len(thesePlayersP), self.burstSize, (len(thesePlayersP)/float(self.burstSize)))

                    raise StopIteration

                # thesePlayersP should now represent every possible game that could be played
                # with the current combination of players.
                # Now we shuffle them to make sure there's no pattern in each 'burst', and
                # divide them up into groups of the burstSize
                currentBurst = []
                i = 0
                random.shuffle(thesePlayersP)
                for p in thesePlayersP:
                    currentBurst.append(p)
                    i += 1
                    if i == self.burstSize:
                        bursts.append(currentBurst)
                        currentBurst = []
                        i = 0

                # We shouldn't have any bots left in currentBurst when this terminates
                if len(currentBurst) > 0:
                    if not self.quiet:
                        print("")
                        print >>sys.stderr, 'Error: Some permutations were not added to the collection of bursts. This shouldn\'t fire unless (len(thesePlayersP) %% self.burstSize) != 0'
                    raise StopIteration

            # bursts should now contain random groupings of permutations, each for a particular
            # combination of players, covering every possible game.
            # We shuffle them up again, then spit out individual games from each burst in turn.
            permutations = []
            while len(permutations) < self.rounds:
                random.shuffle(bursts)
                for b in bursts:
                    random.shuffle(b)
                    permutations.extend(b)

            if not self.quiet:
                compr = len(bursts)*self.burstSize
                burstsPlayed = self.rounds/float(self.burstSize)
                print("")
                print >>sys.stderr, 'Requested games: %i' % (self.rounds)
                print >>sys.stderr, 'Comprehensive size: %i' % (compr)
                if not (self.rounds == compr):
                    print >>sys.stderr, 'Comprehensive sets played: %f' % (self.rounds/float(compr))
                if not ((self.rounds % compr) == 0):
                    print("")
                    print >>sys.stderr, 'Requested games is not divisible by comprehensive size.'
                    print >>sys.stderr, 'Some bots will not compete in an equal number of games.'
                print("")
                print >>sys.stderr, 'Requested burst size: %i' % (self.burstSize)
                print >>sys.stderr, 'Comprehensive burst size: %i (%i! * 10)' % (1200, 5) # Factorial(5)*10 or 5!*10 - It'll always be this
                print >>sys.stderr, 'Comprehensive count for requested size: %i' % (len(bursts))
                print >>sys.stderr, 'Bursts played count: %i' % (burstsPlayed)
                if not (len(bursts) == burstsPlayed):
                    print >>sys.stderr, 'Comprehensive  burst sets played: %f' % (burstsPlayed/len(bursts))

            print("")

            for players, roles in permutations[:self.rounds]:
                yield (players, roles)
        else:
            # If a burstSize of 0 (zero) was supplied, assume we want one big batch with the same name per bot.
            # We can fall back on the old enumeration for this, but we need another zero check in run below.
            # This is mostly just for debug purposes - so I can compare results to competition.py
            print("")
            print >>sys.stderr, 'A burstSize of 0 (zero) was supplied. Assuming consistent names and one burst desired.'
            p = []
            r = set(itertools.permutations([True, True, False, False, False]))
            for players in itertools.permutations(zip(self.competitorIds, self.competitors), 5):
                for roles in r:
                    p.append((players, roles))

            permutations = []
            while len(permutations) < self.rounds:
                random.shuffle(p)
                permutations.extend(p)
        
            if not self.quiet:
                compr = len(p)
                print("")
                print >>sys.stderr, 'Requested games: %i' % (self.rounds)
                print >>sys.stderr, 'Comprehensive size: %i' % (compr)
                if not (self.rounds == compr):
                    print >>sys.stderr, 'Comprehensive sets played: %f' % (self.rounds/float(compr))
                if not ((self.rounds % compr) == 0):
                    print("")
                    print >>sys.stderr, 'Requested games is not divisible by comprehensive size.'
                    print >>sys.stderr, 'Some bots will not compete in an equal number of games.'
        
            print("")

            for players, roles in permutations[:self.rounds]:
                yield (players, roles)

    def run(self):
        """Override CompetitionRunner's run function to allow us to manage name mangling and such"""

        print("")
        print >>sys.stderr, "Running competition with %i bots:" % (len(self.competitors))
        for id in self.competitorIds:
            print >>sys.stderr, '%s' % (id)

        # Initialise random name generation
        pseudonymgen.loadNames('pseudonyms\\tolkienParts.txt')

        # If burstSize is 0 (zero), generate names just the once, for ALL bots
        if self.burstSize == 0:
            self._nameMangler.setNames(self.competitorIds)

        # This printing can probably be made more informative for our purposes
        for i, (players, roles) in enumerate(self.listGameSelections()):
            if not self.quiet:
                if (i+1) % 500 == 0: print >>sys.stderr, '(%02i%%)' % (100*(i+1)/self.rounds)
                elif (i+1) % 100 == 0: print >>sys.stderr, 'o',
                elif (i+1) % 25 == 0: print >>sys.stderr, '.',

            if self.burstSize != 0 and \
                (i % self.burstSize) == 0:
                # i.e. On rounds 0, burstSize, burstSize*2, burstSize*3, ...
                # Every time we start a new burst, we should refresh the names used.
                # If our version of listGameSelections is working correctly, each
                # contiguous [burstSize] games should feature the same five bots...
                self._nameMangler.setNames(self.competitorIds)

            self.play(BurstCompetitionRound, players, roles)

        print("")

    def onCompetitionEnd(self):
        if not self.quiet and self.loud:
            print >>sys.stderr, 'Debug upchuck for each competitor:'
            for k, id in zip(self.competitors, self.competitorIds):
                print("")
                print >>sys.stderr, '%s:' % (id)
                k.onCompetitionEnd() 

    def play(self, GameType, players, roles = None, channel = None):
        """Override CompetitionRunner's play function to allow us to initialise a different GameType
        and un-mangle names for our statistics"""
        g = GameType(players, roles, self._nameMangler)
        g.channel = channel
        self.games.append(g)
        g.run()
        self.games.remove(g)

        # Gather statistics for this game, for each bot involved
        for b in g.bots:
            competition.statistics.setdefault(b.name, CompetitionStatistics())
            s = competition.statistics.get(b.name)
            if b.spy:
                s.spyWins.sample(int(not g.won))
            else:
                s.resWins.sample(int(g.won))
        return g

def getUniqueCompetitorName(index, competitor):
    return '%s-%d' % (getattr(competitor, '__name__'), index)

if __name__ == '__main__':
    botArgsStart = 3

    try:
        rounds = int(sys.argv[2])
    except ValueError:
        botArgsStart = 2

    if (len(sys.argv)-1) < botArgsStart:
        # Not enough arguments to have included any bots...
        print('USAGE:')
        print('burstcompetition.py 10000 20 file.BotName [...]')
        print('or')
        print('burstcompetition.py 10000 file.BotName [...]')
        sys.exit(-1)

    competitors = getCompetitors(sys.argv[botArgsStart:])
    if botArgsStart > 2:
        runner = BurstCompetitionRunner(competitors, int(sys.argv[1]), int(sys.argv[2]))
    else:
        runner = BurstCompetitionRunner(competitors, int(sys.argv[1]))

    try:
        runner.main()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        runner.show()
        runner.onCompetitionEnd()