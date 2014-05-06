import logging
import logging.handlers
import re
import filecmp
import sys
import os

from player import Player

# From url: http://stackoverflow.com/questions/4703390/how-to-extract-a-floating-number-from-a-string-in-python
float_pattern = r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"

# Confect suspicion accuracy classes:

# Suspicion accuracies
class AccuracyAfterMission:
    def __init__(self, suspicion, spy):
        self.suspicion = suspicion
        self.spy = spy
        self.inaccuracy = suspicion if not spy else 1-suspicion

class AccuracyAfterMissions:
    def __init__(self, spy):
        self.missions = []
        self.missionCount = 0;
        self.spy = spy

    def logMission(self, accuracy):
        self.missions.append(accuracy)
        self.missionCount = len(self.missions)

class AccuraciesAfterMissions:
    def __init__(self, others, spies):
        self.accuracyAfterMissions = {}
        self.others = others
        self.spies = spies
        for o in others:
            wasSpy = o in spies
            self.accuracyAfterMissions[o.name] = AccuracyAfterMissions(wasSpy)

    def logMission(accuracies):
        for o in self.others:
            self.accuracyAfterMissions[o.name].logMission(accuracies[o.name])

    def printAccuracies(self):
        for o in self.others:
            print ("\t%s:" % (o.name))
            isSpyString = "Yes" if self.accuracyAfterMissions[o.name].spy else "No"
            mCount = self.accuracyAfterMissions[o.name].missionCount
            for m in range(0, mCount):
                suspicionThisMission = self.accuracyAfterMissions[o.name].missions[m].suspicion
                inaccuracyThisMission = self.accuracyAfterMissions[o.name].missions[m].inaccuracy

                print("\t\tMission %d: Suspicion = %f : Was spy = %s : Guess inaccuracy = %f" % (m, suspicionThisMission, isSpyString, inaccuracyThisMission))

    #def copy(self):
        #copyOfMe = AccuraciesAfterMissions([Player(p.name, p.index) for p in self.others],
                                           #[Player(p.name, p.index) for p in self.spies])


# Suspicion scores
class SuspicionAfterMissions:
    def __init__(self):
        self.missions = []
        self.missionCount = 0
    
    def logMission(self,suspicion):
        self.missions.append(suspicion)
        self.missionCount = len(self.missions)

    def toAccuracyAfterMissions(self, wasSpy):
        ret = AccuracyAfterMissions(wasSpy)

        for m in range(0, self.missionCount):
           ret.logMission(AccuracyAfterMission(self.missions[m], wasSpy))

        return ret

class SuspicionsAfterMissions:
    def __init__(self, others):
        self.suspicionAfterMissions = {}
        self.others = others
        for o in others:
            self.suspicionAfterMissions[o.name] = SuspicionAfterMissions()

    def logMission(self, suspicions):
        for o in self.others:
            self.suspicionAfterMissions[o.name].logMission(suspicions[o.name])

    def toAccuraciesAfterMissions(self, spies):
        ret = AccuraciesAfterMissions(self.others, spies)

        for o in self.others:
            wasSpy = o in spies
            curToAdd = self.suspicionAfterMissions[o.name].toAccuracyAfterMissions(wasSpy)
            ret.accuracyAfterMissions[o.name] = curToAdd

        return ret



# Logger
class SuspicionStatsLogger:
    def __init__(self, name, customFilepath=None, mangler=None):
        self.logname = name + '-suspicionStats'
        self.filename = customFilepath if customFilepath else 'logs/' + self.logname + '.log'

        # Double check whether we need the mangler, or bad things could happen:
        self.mangler = None
        if SuspicionStatsLogger.requiresBotnameMangler:
            self.mangler = mangler

        self.log = logging.getLogger(self.filename)
        if not self.log.handlers:
            # Clear existing log file
            with open(self.filename, 'w'):
                pass

            try:
                output = logging.FileHandler(filename=self.filename)
                self.log.addHandler(output)
                self.log.setLevel(logging.DEBUG)

                self.log.info("!")
                self.log.info("%s suspicion inaccuracy log" % (name))

            except IOError:
                pass

    def logGame(self, accuraciesAfterMissions, observerIsSpy):
        self.log.info("-")
        # Some data redundancy here, but it's easier to read, and I'm a noob at Python

        # Unmangle names if required
        #if self.mangler:
            #accCopy = accuraciesAfterMissions.copyWithNewNames()

        # Unmangle names if required
        if self.mangler:
            othersWithRealNames = [Player(self.mangler.getRealName(p.name), p.index) for p in accuraciesAfterMissions.others]
            spiesWithRealNames = [Player(self.mangler.getRealName(p.name), p.index) for p in accuraciesAfterMissions.spies]
            self.log.info("others: %s" % '.'.join(map(str, othersWithRealNames)))
            self.log.info("spies: %s" % '.'.join(map(str, spiesWithRealNames)))
        else:
            self.log.info("others: %s" % '.'.join(map(str, accuraciesAfterMissions.others)))
            self.log.info("spies: %s" % '.'.join(map(str, accuraciesAfterMissions.spies)))

        if observerIsSpy:
            self.log.info("SPYGAME")
        else:
            firstOpponent = True
            for o in accuraciesAfterMissions.others:
                if not firstOpponent:
                    self.log.info(",")
                firstOpponent = False

                firstMission = True
                for m in range(0, accuraciesAfterMissions.accuracyAfterMissions[o.name].missionCount):
                    self.log.info("n:%s;s:%f;r:%d;i:%f;"
                                  % ( self.mangler.getRealName(o.name) if self.mangler else o.name,
                                     accuraciesAfterMissions.accuracyAfterMissions[o.name].missions[m].suspicion,
                                     1 if accuraciesAfterMissions.accuracyAfterMissions[o.name].spy else 0,
                                     accuraciesAfterMissions.accuracyAfterMissions[o.name].missions[m].inaccuracy))
        pass

    @classmethod
    def requiresBotnameMangler(cls):
        """Check whether a mangler is required.
        This is achieved by examining the name of the script that was called originally.
        """
        return os.path.basename(sys.argv[0]).lower() == 'burstcompetition.py'.lower()
        pass
    # End DPT

# Deserializer
class FullCompetitionAccuracies:
    def __init__(self):
        self.games = []
        self.observerName = ""

        pass

    def saveToFile(self, filename=None):
        logger = SuspicionStatsLogger(self.observerName, filename)

        # Iterate over the games one by one and log each as if we had just played it
        # This should reproduce them in the correct order...
        for g in self.games:
            logger.logGame(g, g.observerWasSpy)

        pass

    def loadFromFile(self, filename):
        try:
            with open(filename, 'r') as f:
                self.games = []
                self.observerName = ""

                exclCount = 0

                # Manually iterate over the lines, for better control
                repeatLine = False
                line = None
                while True:
                    if not repeatLine:
                        line = next(f, None)
                    if line is None:
                        break

                    #self.games[curGameIndex] = AccuraciesAfterMissions

                    observerNameMatch = re.search('(.+) suspicion inaccuracy log', line)

                    if line[0] == '!':
                        # New competition
                        exclCount += 1
                        if exclCount > 1:
                            raise Exception('Multiple competition breakers (!) encountered. Terminating')
                        pass
                    elif observerNameMatch:
                        # Observer name
                        self.observerName = observerNameMatch.group(1)
                        pass
                    elif line[0] == '-':
                        # New game
                        # Next line should list other players and their indices
                        othersLine = next(f, None)
                        othersMatch = re.search('others: (.+)', othersLine)
                        if not othersMatch:
                            raise Exception('Expected \"others: \"')
                        # Next line should list spies in this game
                        spiesLine = next(f, None)
                        spiesMatch = re.search('spies: (.+)', spiesLine)
                        if not spiesMatch:
                            raise Exception('Expected \"spies: \"')
                        # Create the game
                        othersList = re.findall('(\d+)\-([^.]+)', othersMatch.group(1))
                        others = [Player(nom, int(id)) for id, nom in othersList]
                        spiesList = re.findall('(\d+)\-([^.]+)', spiesMatch.group(1))
                        spies = [Player(nom, int(id)) for id, nom in spiesList]
                        accsAfterMissions = AccuraciesAfterMissions(others, spies)
                        observerWasSpy = False
                        # Consume lines as mission stats for individual opponents until we reach
                        # something we don't recognise, then throw it back to the main loop:
                        while True:
                            missionLine = next(f, None)
                            repeat = False

                            if not missionLine:
                                repeat = True
                                pass
                            else:
                                spyGameMatch = re.match('SPYGAME', missionLine)
                                missionStatMatch = re.search('n:(.+);s:(.+);r:([01]);i:(.+);', missionLine)

                                if spyGameMatch:
                                    # SPYGAME
                                    observerWasSpy = True
                                    pass
                                elif missionLine[0] == ',':
                                    # New opponent
                                    pass
                                elif missionStatMatch:
                                    # Mission
                                    oppName = missionStatMatch.group(1)
                                    susp = float(re.findall(float_pattern, missionStatMatch.group(2))[0][0])
                                    wasSpy = missionStatMatch.group(3) == '1'
                                    # This one is actually recalculated from the other two...
                                    inacc = float(re.findall(float_pattern, missionStatMatch.group(4))[0][0])

                                    # Add this mission
                                    accsAfterMissions.accuracyAfterMissions[oppName].logMission( AccuracyAfterMission(susp, wasSpy) )
                                    pass
                                else:
                                    repeat = True
                                    pass

                                pass

                            # If the line was not recognised, terminate this game and throw the
                            # line back to the main loop
                            # It'll probably be a '-' separating games, or the eof (None)
                            if repeat:
                                repeatLine = True
                                line = missionLine
                                break

                            pass # End single game line parsing

                        # Add the game to our collection
                        self.games.append(accsAfterMissions)
                        self.games[-1].observerWasSpy = observerWasSpy
                        pass
                    elif line[0] == ',':
                        # New opponent
                        pass

                    pass # End full file line parsing

                pass # File closed: filename
            pass
        except IOError as ex:
            print(ex.message)
            pass
        except Exception as ex:
            print(ex.message)
            pass

        curGameIndex = 0

        


        pass


# Unit test stuff
if __name__ == '__main__':
    print("Running Unit Test for suspAcc serialization/deserialization:")

    # File paths
    loggerOutPath = 'logs/suspAccUnitTest-01LoggerOutput.log'
    fullCompOutPath = 'logs/suspAccUnitTest-02FullCompAccOutput.log'

    # Create original log
    observerName = "suspAccUnitTester"
    logger = SuspicionStatsLogger(observerName, loggerOutPath)

    # Create games
    players01 = [Player("PlayerOne", 5), Player("PlayerTwo", 1), Player("PlayerThree", 4), Player("Player4", 3)]
    spies01 = [players01[0], players01[1]]
    gameAcc01 = AccuraciesAfterMissions(players01, spies01)
    players02 = [Player("Player4", 5), Player("PlayerTwo", 3), Player("PlayerOne", 2), Player("PlayerThree", 1)]
    spies02 = [players02[2], players02[1]]
    gameAcc02 = AccuraciesAfterMissions(players02, spies02)
    players03 = [Player("Player4", 5), Player("PlayerTwo", 3), Player("PlayerOne", 2), Player("PlayerThree", 1)]
    spies03 = [Player(observerName, 4), players02[1]]
    gameAcc03 = AccuraciesAfterMissions(players03, spies03)

    # Create game01 missions
    # players[0]
    gameAcc01.accuracyAfterMissions[players01[0].name].logMission(AccuracyAfterMission(0.824792, True))
    gameAcc01.accuracyAfterMissions[players01[0].name].logMission(AccuracyAfterMission(0.999978, True))
    gameAcc01.accuracyAfterMissions[players01[0].name].logMission(AccuracyAfterMission(1.000000, True))
    gameAcc01.accuracyAfterMissions[players01[0].name].logMission(AccuracyAfterMission(1.000000, True))
    # players[1]
    gameAcc01.accuracyAfterMissions[players01[1].name].logMission(AccuracyAfterMission(0.915221, True))
    gameAcc01.accuracyAfterMissions[players01[1].name].logMission(AccuracyAfterMission(0.999800, True))
    gameAcc01.accuracyAfterMissions[players01[1].name].logMission(AccuracyAfterMission(0.999877, True))
    gameAcc01.accuracyAfterMissions[players01[1].name].logMission(AccuracyAfterMission(0.999990, True))
    # players[2]
    gameAcc01.accuracyAfterMissions[players01[2].name].logMission(AccuracyAfterMission(0.000769, False))
    gameAcc01.accuracyAfterMissions[players01[2].name].logMission(AccuracyAfterMission(0.000001, False))
    gameAcc01.accuracyAfterMissions[players01[2].name].logMission(AccuracyAfterMission(0.000000, False))
    gameAcc01.accuracyAfterMissions[players01[2].name].logMission(AccuracyAfterMission(0.000000, False))
    # players[3]
    gameAcc01.accuracyAfterMissions[players01[3].name].logMission(AccuracyAfterMission(0.259218, False))
    gameAcc01.accuracyAfterMissions[players01[3].name].logMission(AccuracyAfterMission(0.000221, False))
    gameAcc01.accuracyAfterMissions[players01[3].name].logMission(AccuracyAfterMission(0.000123, False))
    gameAcc01.accuracyAfterMissions[players01[3].name].logMission(AccuracyAfterMission(0.000010, False))

    # Create game02 missions
    # players[0]
    gameAcc02.accuracyAfterMissions[players02[0].name].logMission(AccuracyAfterMission(0.514770, False))
    gameAcc02.accuracyAfterMissions[players02[0].name].logMission(AccuracyAfterMission(0.044391, False))
    gameAcc02.accuracyAfterMissions[players02[0].name].logMission(AccuracyAfterMission(0.000034, False))
    gameAcc02.accuracyAfterMissions[players02[0].name].logMission(AccuracyAfterMission(0.000000, False))
    # players[1]
    gameAcc02.accuracyAfterMissions[players02[1].name].logMission(AccuracyAfterMission(0.479231, True))
    gameAcc02.accuracyAfterMissions[players02[1].name].logMission(AccuracyAfterMission(0.955608, True))
    gameAcc02.accuracyAfterMissions[players02[1].name].logMission(AccuracyAfterMission(0.999966, True))
    gameAcc02.accuracyAfterMissions[players02[1].name].logMission(AccuracyAfterMission(1.000000, True))
    # players[2]
    gameAcc02.accuracyAfterMissions[players02[2].name].logMission(AccuracyAfterMission(0.576428, True))
    gameAcc02.accuracyAfterMissions[players02[2].name].logMission(AccuracyAfterMission(0.955626, True))
    gameAcc02.accuracyAfterMissions[players02[2].name].logMission(AccuracyAfterMission(0.999957, True))
    gameAcc02.accuracyAfterMissions[players02[2].name].logMission(AccuracyAfterMission(1.000000, True))
    # players[3]
    gameAcc02.accuracyAfterMissions[players02[3].name].logMission(AccuracyAfterMission(0.429571, False))
    gameAcc02.accuracyAfterMissions[players02[3].name].logMission(AccuracyAfterMission(0.044374, False))
    gameAcc02.accuracyAfterMissions[players02[3].name].logMission(AccuracyAfterMission(0.000043, False))
    gameAcc02.accuracyAfterMissions[players02[3].name].logMission(AccuracyAfterMission(0.000000, False))

    # Create game03 missions
    # These don't actually matter, because its a spy game
    # players[0]
    gameAcc03.accuracyAfterMissions[players03[0].name].logMission(AccuracyAfterMission(0.514770, False))
    gameAcc03.accuracyAfterMissions[players03[0].name].logMission(AccuracyAfterMission(0.044391, False))
    gameAcc03.accuracyAfterMissions[players03[0].name].logMission(AccuracyAfterMission(0.000034, False))
    gameAcc03.accuracyAfterMissions[players03[0].name].logMission(AccuracyAfterMission(0.000000, False))
    # players[1]
    gameAcc03.accuracyAfterMissions[players03[1].name].logMission(AccuracyAfterMission(0.479231, False))
    gameAcc03.accuracyAfterMissions[players03[1].name].logMission(AccuracyAfterMission(0.955608, False))
    gameAcc03.accuracyAfterMissions[players03[1].name].logMission(AccuracyAfterMission(0.999966, False))
    gameAcc03.accuracyAfterMissions[players03[1].name].logMission(AccuracyAfterMission(1.000000, False))
    # players[2]
    gameAcc03.accuracyAfterMissions[players03[2].name].logMission(AccuracyAfterMission(0.576428, True))
    gameAcc03.accuracyAfterMissions[players03[2].name].logMission(AccuracyAfterMission(0.955626, True))
    gameAcc03.accuracyAfterMissions[players03[2].name].logMission(AccuracyAfterMission(0.999957, True))
    gameAcc03.accuracyAfterMissions[players03[2].name].logMission(AccuracyAfterMission(1.000000, True))
    # players[3]
    gameAcc03.accuracyAfterMissions[players03[3].name].logMission(AccuracyAfterMission(0.429571, False))
    gameAcc03.accuracyAfterMissions[players03[3].name].logMission(AccuracyAfterMission(0.044374, False))
    gameAcc03.accuracyAfterMissions[players03[3].name].logMission(AccuracyAfterMission(0.000043, False))
    gameAcc03.accuracyAfterMissions[players03[3].name].logMission(AccuracyAfterMission(0.000000, False))

    # Write to original log
    logger.logGame(gameAcc01, False)
    logger.logGame(gameAcc03, True)
    logger.logGame(gameAcc02, False)

    # Read original log
    fullCompAcc = FullCompetitionAccuracies()
    fullCompAcc.loadFromFile(loggerOutPath)

    # Recreate log
    fullCompAcc.saveToFile(fullCompOutPath)

    # Compare log files
    filesMatch = filecmp.cmp(loggerOutPath, fullCompOutPath)

    if filesMatch:
        print("Files match byte for byte.")
    else:
        print("Files do not match byte for byte.")

    pass
