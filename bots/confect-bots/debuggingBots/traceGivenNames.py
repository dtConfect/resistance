import random
import sys

from player import Bot 


class TraceGivenNames(Bot):
    """Bot which squeels the names of all the bots it's given in callbacks. This is so that I could identify where bots
    were being passed the bots collection or items from it, rather than the players collection and its items.
    From RandomBot: An AI bot that's perhaps never played before and doesn't understand the rules very well!"""

    def onGameRevealed(self, players, spies):
        print("")
        print >>sys.stderr, "In onGameRevealed..."
        for p in players:
            print >>sys.stderr, "I was passed: '%s'" % (p.name)

        # Time to make this bot super slow by checking for known names!
        self.notMangledNames = ('Deceiver', 'Hippie', 'RuleFollower', 'RandomBot', 'TraceGivenNames')

    def onMissionAttempt(self, mission, tries, leader):
        print("")
        print >>sys.stderr, "In onMissionAttempt..."
        print >>sys.stderr, "I was passed: '%s'" % (leader.name)

    def select(self, players, count):
        print("")
        print >>sys.stderr, "In select..."
        for p in players:
            print >>sys.stderr, "I was passed: '%s'" % (p.name)

        self.log.info("A completely random selection.")
        return random.sample(self.game.players, count)

    def onTeamSelected(self, leader, team):
        print("")
        print >>sys.stderr, "In onTeamSelected..."
        print >>sys.stderr, "I was passed: (leader) '%s'" % (leader.name)
        for p in team:
            print >>sys.stderr, "I was passed: (member) '%s'" % (p.name)

            if p.name in self.notMangledNames:
                print("Unmangled name detected!")

    def vote(self, team):
        print("")
        print >>sys.stderr, "In vote..."
        for p in team:
            print >>sys.stderr, "I was passed: '%s'" % (p.name)

            if p.name in self.notMangledNames:
                print("Unmangled name detected!")

        self.log.info("A completely random vote.")
        return random.choice([True, False])

    def onVoteComplete(self, votes):
        print("")
        print >>sys.stderr, "In onVoteComplete..."

    def sabotage(self):
        print("")
        print >>sys.stderr, "In sabotage..."

        self.log.info("A completely random sabotage.")
        return random.choice([True, False])

    def onMissionComplete(self, sabotaged):
        print("")
        print >>sys.stderr, "In onMissionComplete..."

    def onGameComplete(self, win, spies):
        print("")
        print >>sys.stderr, "In onGameComplete..."