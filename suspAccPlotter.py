from suspAcc import *

import argparse
import ast
import matplotlib.pyplot as plt

# Confect suspicion accuracy plotter
# Contains various functionality for plotting suspicion accuracy graphs given data
# logged from a competition or burstcompetition by the suspAcc SuspicionStatsLogger
# Note: Currently only designed to work with competitions held with g=p
#   where g = number of players per game and p = competition entrants

# Switches
switch_filepath = 'filepath'
switch_gamesToAverageOver = "--avovr"
switch_playerAverageGroups = "--pavg"
switch_forceIncludeAllAverage = "--fiaa"
switch_graphOnlySpiesGroupIndices = "--gosgi"
switch_graphOnlyResistanceGroupIndices = "--gorgi"

# Enums
class PlotType:
    MissionsSep = range(1, 2)

# We use a class for this to avoid parameter spam  in functions.
# Just set variables to the class. We can re-use them for mutliple
# functions and stuff.
class GenericPlotter:
    def __init__(self):
        self.gamesToAverageOver = 100
        self.playerAverageGroups = []
        self.forceIncludeAllAverage = False
        self.graphOnlySpiesGroupIndices = []
        self.graphOnlyResistanceGroupIndices = []

        pass

    # Functions
    def plot_MissionSep_getEmptyDataPoint(self):
        return [ [] for mission in range(0,5)]
    def plot_MissionsSep_getEmptyDataPointsList(self):
        dataPoints = [ self.plot_MissionSep_getEmptyDataPoint() for pavg in self.playerAverageGroups] 
        # If no groups are supplied, add a group for the all-average  
        if self.forceIncludeAllAverage or not len(self.playerAverageGroups): 
            dataPoints.append(self.plot_MissionSep_getEmptyDataPoint())  
        return dataPoints
    def plot_MissionsSep(self, fullCompData):

        gamesCount = len(fullCompData.games)

        if not gamesCount:
            print("Error: Zero games in data")
            return False

        if not ((gamesCount % self.gamesToAverageOver) == 0):
            print("Error: Number of games in data not divisible by gamesToAverageOver (%d)" % (self.gamesToAverageOver))
            print("Please supply custom value for \"%s\"" % (switch_gamesToAverageOver))
            return False

        if any(index in self.graphOnlyResistanceGroupIndices for index in self.graphOnlySpiesGroupIndices):
            print("Error: Index passed with %s also passed with %s" %(switch_graphOnlySpiesGroupIndices, switch_graphOnlyResistanceGroupIndices))
            return False

        pavgCount = len(self.playerAverageGroups)
        allAvIndex = pavgCount

        # Data points (inaccuracy, gameCount) indexed by:
        #   1. playerAverageGroups index (plus one additional average across all)
        #   2. mission index (zero to four)
        #   3. data point index (suspicion inaccuracy averages over gamesToAverageOver games)
        dataPoints = self.plot_MissionsSep_getEmptyDataPointsList()             

        # Values to be averaged for the current data points, indexed by:
        #   1. playerAverageGroups index (plus one additional average across all)
        #   2. mission index (zero to four)
        #   3. sub data point index (individual suspicion inaccuracies averaged for all players grouping)
        subDataPoints = self.plot_MissionsSep_getEmptyDataPointsList()
        # Loop over games and collate the averages
        for gameIndex, game in zip(range(0, gamesCount), fullCompData.games):
            
            # Skip spy games
            if not game.observerWasSpy:
                # Find out how many missions were undertaken in the current game
                curGameMissionCount = game.accuracyAfterMissions.values()[0].missionCount

                # Collate inaccuracies for this game
                for missionIndex in range(0, curGameMissionCount):
                    for groupIndex in range(0, len(subDataPoints)):
                        # Grab the player average grouping
                        currentGroup = []
                        if groupIndex == allAvIndex:
                            # Make grouping of all others
                            currentGroup = [o.name for o in game.others]
                        else:
                            # Grab current grouping
                            currentGroup = self.playerAverageGroups[groupIndex]

                        if groupIndex in self.graphOnlySpiesGroupIndices:
                            # Grab only players in the group who are spies in this mission
                            #print("Spies!")
                            currentGroup = [player for player in currentGroup if player in [o.name for o in game.spies]]
                        elif groupIndex in self.graphOnlyResistanceGroupIndices:
                            # Grab only players in the group who are not spies in this mission
                            #print("Resistance!")
                            currentGroup = [player for player in currentGroup if player not in [o.name for o in game.spies]]
                        else:
                            #print("All!")
                            pass

                        # Check that there aren't no players left in the group
                        if len(currentGroup):
                            # Grab inaccuracies for current mission and group
                            if all(player in [o.name for o in game.others] for player in currentGroup):
                                groupInaccAv = 0.0
                                for player in currentGroup:
                                    curInacc = game.accuracyAfterMissions[player].missions[missionIndex].inaccuracy
                                    curInaccContrib = curInacc/float(len(currentGroup))
                                    groupInaccAv += curInaccContrib
                                    pass
                                subDataPoints[groupIndex][missionIndex].append(groupInaccAv)

                        pass # End accumulate current game groupings
                    pass # End accumulate current game missions
                pass # End if not game.observerWasSpy

            # If this was the last in a set of games to average over, work that out now
            if (((gameIndex+1) % self.gamesToAverageOver) == 0):
                for groupIndex in range(0, len(subDataPoints)):
                    for missionIndex in range(0, len(subDataPoints[groupIndex])):
                        # The data point appended includes the average inaccuracy, and the games passed thus far.
                        # If, in this set, no games were played to the current mission number (incredibly unlikely), simply ommit the point.
                        # We can decide elsewhere whether to break the line or connect our neighbours.
                        if len(subDataPoints[groupIndex][missionIndex]):
                            dataPoints[groupIndex][missionIndex].append(
                                                                        (sum(subDataPoints[groupIndex][missionIndex])/float(len(subDataPoints[groupIndex][missionIndex])), gameIndex+1)
                                                                       )
                            pass
                        pass # End subDataPoints missions
                    pass # End subDataPoints groupings
                
                # And clear the sub data points
                subDataPoints = self.plot_MissionsSep_getEmptyDataPointsList()

                pass # End save current set
            pass # End For games 

        # Plot lines
        plotColors = ['r','g','b','c','p','m','y']
        plotMarkers = ['o','s','d','^','x']
        usedColors = []
        lineLabels = []
        markerLabels = ["Mission %d" % (m) for m in range(1, 6) ]
        
        for groupIndex in range(0, len(dataPoints)):
            # Set color for opponent group
            curColor=plotColors[groupIndex]
            # Make sure the all group is always black
            if(groupIndex == allAvIndex):
                curColor = 'k'

            for missionIndex in range(0, len(dataPoints[groupIndex])):
                curMarker = plotMarkers[missionIndex]
                # Grab the player average grouping
                currentGroup = []
                if groupIndex == allAvIndex:
                    # Make grouping of all others
                    currentGroup = [o.name for o in game.others]
                else:
                    # Grab current grouping
                    currentGroup = self.playerAverageGroups[groupIndex]
                newPlot, = plt.plot([p[1]-(self.gamesToAverageOver/2.0) for p in dataPoints[groupIndex][missionIndex]], [p[0] for p in dataPoints[groupIndex][missionIndex]],
                         marker=curMarker,
                         color=curColor)
            lineLabels.append("%s%s"
                              % (','.join(map(str, currentGroup)),
                                 (' (Spies Only)' if groupIndex in self.graphOnlySpiesGroupIndices else
                                  ' (Resistance Only)' if groupIndex in self.graphOnlyResistanceGroupIndices else
                                  '')))
            usedColors.append(curColor)
            
        # Set labels
        plt.title("%s Suspicion Inaccuracy After Missions" %(fullCompData.observerName))
        plt.xlabel("Games (averaged over every %d)" %(self.gamesToAverageOver))
        plt.ylabel("Inaccuracy")

        # Set up legend
        # Leave some space at the bottom for the line colors
        ymin,ymax = plt.ylim()
        yHeight = (ymax-ymin)*0.7
        #plt.ylim(ymin, ymin+yHeight)
        # We need to render some dummy lines to get the information we really want
        #markerFig, markerAx = plt.subplots(1,1)
        plt.hold(True)
        legend1Plots = []
        for m,l in zip(plotMarkers,markerLabels):
            curPlot, = plt.plot(None,None,marker=m,color='k',label=l)
            legend1Plots.append(curPlot)
        legend1 = plt.legend(legend1Plots, markerLabels, loc=1)

        legend2Plots = []
        for c,l in zip(usedColors,lineLabels):
            curPlot, = plt.plot(None,None,color=c,label=l)
            legend2Plots.append(curPlot)
        legend2 = plt.legend(legend2Plots, lineLabels, bbox_to_anchor=(0.5, -0.05), loc='upper center', ncol=3)

        plt.gca().add_artist(legend1)
        #plt.legend(plots, plotLabels, loc='upper right', borderpad=2)

        # Set display limits
        plt.xlim([0, gamesCount])
        plt.ylim([-0.1, 1.0])

        # Set up grid
        plt.grid(True)

        ## Success
        return True
        pass

    def display(self):
        plt.show()
        pass



# Main
if __name__ == '__main__':
    # Create plotter instance
    plotter = GenericPlotter()

    # Parse Command line arguments
    argparser = argparse.ArgumentParser(description='Plot graph based on output from a suspAcc SuspicionStatsLogger.', formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument(switch_filepath,
                           metavar='F',
                           help='Filepath of the data to plot.')
    argparser.add_argument(switch_gamesToAverageOver,
                           dest='gamesToAverageOver',
                           type=int,
                           default=plotter.gamesToAverageOver,
                           help='Number of consecutive games to average values over for each point.')
    argparser.add_argument(switch_playerAverageGroups,
                           dest='playerAverageGroups',
                           default=plotter.playerAverageGroups,
                           help='Groups of players (by name) to produce average plots for.\n'
                                'If none are supplied all players will be averaged together to produce one plot.\n'
                                'e.g:\t[[\'Rebounder\',\'Invalidator\'],[\'Rebounder\'],[\'Invalidator\']]\n'
                                'Make sure there are no spaces.')
    argparser.add_argument(switch_forceIncludeAllAverage,
                           dest='forceIncludeAllAverage',
                           action='store_const',
                           const=True,
                           default=plotter.forceIncludeAllAverage,
                           help='Forces the plotting of an average over all players, even if %s is used.' %(switch_playerAverageGroups))
    argparser.add_argument(switch_graphOnlySpiesGroupIndices,
                           dest='graphOnlySpiesGroupIndices',
                           default=plotter.graphOnlySpiesGroupIndices,
                           help='Indices of player groups to produce average plots for of only the spies.\n'
                                'Each index corresponds to that of a group provided via %s.\n'
                                'For the average over all players, the index is 1 higher than the last provided group,\n'
                                'or zero, if no groups are provided.\n'
                                'e.g:\t[0,1,3,6,5]\n'
                                'Make sure there are no spaces.' %(switch_playerAverageGroups))
    argparser.add_argument(switch_graphOnlyResistanceGroupIndices,
                           dest='graphOnlyResistanceGroupIndices',
                           default=plotter.graphOnlyResistanceGroupIndices,
                           help='Indices of player groups to produce average plots for of only the spies.\n'
                                'Each index corresponds to that of a group provided via %s.\n'
                                'For the average over all players, the index is 1 higher than the last provided group,\n'
                                'or zero, if no groups are provided.\n'
                                'e.g:\t[0,1,3,6,5]\n'
                                'Make sure there are no spaces.' %(switch_playerAverageGroups))
    
    args = argparser.parse_args()

    # Load data
    fullCompData = FullCompetitionAccuracies()
    fullCompData.loadFromFile(args.filepath)

    # Set plotter values
    plotter.gamesToAverageOver = args.gamesToAverageOver
    if args.playerAverageGroups:
        plotter.playerAverageGroups = ast.literal_eval(args.playerAverageGroups)
    plotter.forceIncludeAllAverage = args.forceIncludeAllAverage
    if args.graphOnlySpiesGroupIndices:
        plotter.graphOnlySpiesGroupIndices = ast.literal_eval(args.graphOnlySpiesGroupIndices)
    if args.graphOnlyResistanceGroupIndices:
        plotter.graphOnlyResistanceGroupIndices = ast.literal_eval(args.graphOnlyResistanceGroupIndices)

    # Plot
    success = plotter.plot_MissionsSep(fullCompData)

    if success:
        # Display
        plotter.display()

    pass