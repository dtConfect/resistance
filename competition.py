#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import importlib
import random
import math
import sys

from player import Bot
from game import Game
from util import Variable

statistics = {}


class CompetitionStatistics:
    def __init__(self):
        self.resWins = Variable()
        self.spyWins = Variable()
        self.resVotesRes = Variable()
        self.resVotesSpy = Variable()
        self.spyVotesRes = Variable()
        self.spyVotesSpy = Variable()
        self.spyVoted = Variable()
        self.resVoted = Variable()
        self.spySelected = Variable()
        self.resSelected = Variable()
        self.spySelection = Variable()
        self.resSelection = Variable()

    def total(self):
        return Variable(
            self.resWins.total + self.spyWins.total,
            self.resWins.samples + self.spyWins.samples
            )


class CompetitionRound(Game):

    def onPlayerVoted(self, player, vote, leader, team):
        global statistics
        statistics.setdefault(player.name, CompetitionStatistics())
        s = statistics[player.name]

        spies = [t for t in team if t.spy]
        if player.spy:
            # When there are spies, we expect support.
            if spies:    
                s.spyVotesRes.sample(int(vote))
            # For missions without spies, we expect down vote.
            else:
                s.spyVotesSpy.sample(int(not vote))
            return

        # When there are no spies, we expect support.
        if not spies:    
            s.resVotesRes.sample(int(vote))
        # For missions with spies, we expect down vote.
        else:
            s.resVotesSpy.sample(int(not vote))

        # Everyone on the mission hopes to be approved.
        for p in team:
            statistics.setdefault(p.name, CompetitionStatistics())
            s = statistics[p.name]
            if p.spy:
                s.spyVoted.sample(int(vote))
            else:
                s.resVoted.sample(int(vote))
   
    def onPlayerSelected(self, player, team):
        # TODO: Detailed statistics indicating selection by each other
        # player, and whether or not the other is playing as spy.
        global statistics
        spies = [t for t in team if t.spy]

        statistics.setdefault(player.name, CompetitionStatistics())
        if player.spy:
            statistics[player.name].spySelection.sample(int(len(spies) > 0))
        else:
            statistics[player.name].resSelection.sample(int(len(spies) == 0))

        for bot in self.bots:
            statistics.setdefault(bot.name, CompetitionStatistics())
            s = statistics[bot.name]
            if bot.spy:
                s.spySelected.sample(int(bot in team))
            else:
                s.resSelected.sample(int(bot in team))


class CompetitionRunner(object):

    def __init__(self, competitors, rounds, quiet = False):
        self.rounds = rounds
        self.quiet = quiet
        self.games = [] 

        # Make sure there are sufficient entrants if necessary.
        # WARNING: Results in multiple bot instances per game!
        self.competitors = competitors
        # DPT - 28-Jan-2014 - Let's let the user know what they're getting:
        if competitors and len(self.competitors) < 5:
            if not self.quiet:
                print("")
                print >>sys.stderr, 'Not enough competitors for a single game.'
                print >>sys.stderr, 'Competitors will be entered multiple times.'
        # End DPT
        while competitors and len(self.competitors) < 5:
            self.competitors.extend(competitors)

        # DPT - 04-Feb-2014 - Print extra debug information?
        self.loud = True
        # End DPT

    def listGameSelections(self):
        """Evaluate all bots in all possible permutations!  If there are more
        games requested, randomly fill up from a next round of permutations."""
        if not self.competitors: raise StopIteration 

        p = []
        r = set(itertools.permutations([True, True, False, False, False]))
        for players in itertools.permutations(self.competitors, 5):
            for roles in r:
                p.append((players, roles))

        permutations = []
        while len(permutations) < self.rounds:
            random.shuffle(p)
            permutations.extend(p)
        
        # DPT - 28-Jan-2014 - Let's let the user know what they're getting:
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
        # End DPT
        
        print("")

        for players, roles in permutations[:self.rounds]:
            yield (players, roles)

    def main(self):
        global statistics
        statistics = {}

        names = [bot.__name__ for bot in self.competitors]
        for bot in self.competitors:
            if hasattr(bot, 'onCompetitionStarting'):
                bot.onCompetitionStarting(names)

        # DPT - 29-Jan-2014 - Seperate this into a function so it's easier for subclasses:
        self.run()
        # End DPT

    # DPT - 29-Jan-2014 - Seperate this into a function so it's easier for subclasses:
    def run(self):
        print >>sys.stderr, "Running competition with %i bots." % (len(self.competitors))
        for i, (players, roles) in enumerate(self.listGameSelections()):
            if not self.quiet:
                if (i+1) % 500 == 0: print >>sys.stderr, '(%02i%%)' % (100*(i+1)/self.rounds)
                elif (i+1) % 100 == 0: print >>sys.stderr, 'o',
                elif (i+1) % 25 == 0: print >>sys.stderr, '.',

            self.play(CompetitionRound, players, roles)

        print("")
    # End DPT

    # DPT - 04-Feb-2014 - Callback for competition end:
    def onCompetitionEnd(self):
        if not self.quiet and self.loud:
            print >>sys.stderr, 'Debug upchuck for each competitor:'
            for k in self.competitors:
                print("")
                print >>sys.stderr, '%s:' % (k.__name__)
                k.onCompetitionEnd() 
    # End DPT

    def play(self, GameType, players, roles = None, channel = None):
        g = GameType(players, roles)
        g.channel = channel
        self.games.append(g)
        g.run()
        self.games.remove(g)

        # Gather statistics for this game, for each bot involved
        for b in g.bots:
            statistics.setdefault(b.name, CompetitionStatistics())
            s = statistics.get(b.name)
            if b.spy:
                s.spyWins.sample(int(not g.won))
            else:
                s.resWins.sample(int(g.won))
        return g

    def echo(self, *args):
        print(' '.join([str(a) for a in args]))

    def score(self, name):
        return (statistics[name].spyWins.estimate(),
                statistics[name].resWins.estimate(),
                statistics[name].total())

    def rank(self, name):
        results = sorted(statistics.items(), key = lambda x: x[1].total().estimate(), reverse = True)
        for i in range(len(results)):
            if results[i][0] == name:
                return i
        return None

    def last(self):
        results = sorted(statistics, key = lambda x: statistics[x].total().estimate(), reverse = True)
        bot = [c for c in self.competitors if c.__name__ == results[-1]][0]
        other = [c for c in self.competitors if c.__name__ == results[-2]][0]
        return (bot, statistics[results[-1]].total()),                  \
               (other, statistics[results[-2]].total())

    def show(self, summary = False):
        global statistics

        print("")
        for bot in self.competitors:
            if hasattr(bot, 'onCompetitionFinished'):
                bot.onCompetitionFinished()

        if len(statistics) == 0:
            return

        if not summary:
            self.echo("SPIES\t\t\t\t(vote,\t\t voted,\t\t selected,\t selection)")
            for s in sorted(statistics.items(), key = lambda x: x[1].spyWins.estimate(), reverse = True):
                self.echo(" ", '{0:<16s}'.format(s[0]), s[1].spyWins, "\t", s[1].spyVotesRes, s[1].spyVotesSpy, "\t", s[1].spyVoted, "\t\t", s[1].spySelected, "\t\t", s[1].spySelection)

            self.echo("RESISTANCE\t\t\t(vote,\t\t voted,\t\t selected,\t selection)")
            for s in sorted(statistics.items(), key = lambda x: x[1].resWins.estimate(), reverse = True):
                self.echo(" ", '{0:<16s}'.format(s[0]), s[1].resWins, "\t", s[1].resVotesRes, s[1].resVotesSpy, "\t", s[1].resVoted, "\t\t", s[1].resSelected, "\t\t", s[1].resSelection)
            self.echo("TOTAL")

        for s in sorted(statistics.items(), key = lambda x: x[1].total().estimate(), reverse = True):
            self.echo(" ", '{0:<16s}'.format(s[0]), s[1].total().detail())
        self.echo("")

# DPT - 2013 - Moved path append stuff into getCompetitors and expanded to
# deal with Windows-style backslashes for folders.
def getCompetitors(argv):
    competitors = []
    for request in argv:
        if '/' in request or '\\' in request:
            # The argument is an additional search path
            sys.path.append(request)
            somethingToAdd = False;
        elif '.' in request:
            # The argument is a bot to add as a competitor
            filename, classname = request.split('.')
            somethingToAdd = True;
        else:
            # The argument may be a module or directory to add competitors from
            filename, classname = request, None
            somethingToAdd = True;

        # Try to add the requested bots
        if somethingToAdd:
            module = importlib.import_module(filename)
            if classname:
                competitors.append(getattr(module, classname))
            else:
                for b in dir(module):
                    if hasattr(module, '__all__') and not b in module.__all__: continue
                    if b.startswith('__') or b == 'Bot': continue
                    cls = getattr(module, b)
                    try:
                        if issubclass(cls, Bot):
                            competitors.append(cls)
                    except TypeError:
                        pass
    return competitors

if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print('USAGE: competition.py 10000 file.BotName [...]')
        sys.exit(-1)

    # DPT - 2013 - Moved path append stuff into getCompetitors and expanded
    # to deal with Windows-style backslashes for folers.

    competitors = getCompetitors(sys.argv[2:])
    runner = CompetitionRunner(competitors, int(sys.argv[1]))
    try:
        runner.main()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        runner.show()
        # DPT - 04-Feb-2014 - Callback for competition end:
        runner.onCompetitionEnd()
        # End DPT

