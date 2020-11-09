#! python3
#
# Test drawn form IEEE 1115-2014 "sizing of nickel-cadmium batteries used in standby operation"
# It takes a battery definition: capacity, amps per duration, aging factor, design margin
# and an angine starter profile in terms of repeated start attemps and helps sizing this battery
#
# Author: Gerard Gauthier
# Date: 2020/11
# Python semantic version: ^3.9.0
#

import datetime
import json
import numpy as np
import os.path as osPath
import pandas
import sys

from scipy import interpolate

class IEEE1115FileNames:
    def __init__(obj, d):
        obj.startingCycles = d["startingCycles"]
        obj.ampsByDurationFileName = d["ampsByDurationFileName"]

class IEEE1115:
    def __init__(obj, jsonFileName):
        f = open(jsonFileName, "r")
        d = json.loads(f.read())
        obj.title = d["title"]
        obj.nominalCapacity = d["nominalCapacity"]
        obj.numberOfSections = int(d["numberOfSections"])
        obj.verbose = d["verbose"]
        obj.deratingFactorOnTemp = d["deratingFactorOnTemp"]
        obj.randomSize = d["randomSize"]
        obj.designMargin = d["designMargin"]
        obj.agingFactor = d["agingFactor"]
        obj.finalTolerance = d["finalTolerance"]
        obj.csvFileNames = IEEE1115FileNames(d["csvFileNames"])

def getSec(timeStr):
    """get seconds from HH:MM:SS (two integers and a float)"""
    h, m, s = timeStr.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def csvAsNp(fileName):
    """take csv data file name and returns an numpy array
    assumes first column is always of format HH:MM:SS[.S] and transforms it into seconds
    """
    arr = pandas.read_csv(fileName, header=0).values
    for x in arr:
        x[0] = getSec(x[0])
    return np.array(arr)

if len(sys.argv) != 2:
    raise Exception("needs json definition file name as argument to start")

jsonDefFileName = sys.argv[1]

if not osPath.isfile(jsonDefFileName):
    raise FileNotFoundError(f"with file name \"{jsonDefFileName}\"")

# main object which contains every parameter used in this test
testParams = IEEE1115(jsonDefFileName)

for k in testParams.csvFileNames.__dict__.keys():
    fn = getattr(testParams.csvFileNames, k)
    if not osPath.isfile(fn):
        raise FileNotFoundError(f"with \"{k} = {fn}\"")

print(f"{testParams.title}\n defined in \"{jsonDefFileName}\"")
print(f" IEEE 1125-2014 simulation started on {datetime.datetime.now().strftime('%Y/%m/%d')}")
print(f" Starting data file: \"{testParams.csvFileNames.startingCycles}\"")
print(f" Battery current data file: \"{testParams.csvFileNames.ampsByDurationFileName}\"")
print("")

ampsByDurationData = csvAsNp(testParams.csvFileNames.ampsByDurationFileName)
ampsByDurationData = (np.array([xi for xi in ampsByDurationData[:, 0]]),
                      np.array([yi for yi in ampsByDurationData[:, 1]]))

# defines a function which takes a duration in seconds and return Amps
ampsByDurationFunction = interpolate.interp1d(ampsByDurationData[0], ampsByDurationData[1], kind="cubic", fill_value='extrapolate')

def secToHMS(sec):
    intSec = int(sec)
    h = int(intSec/3600)
    intSec %= 3600
    m = int(intSec/60)
    s = sec - 3600*h - 60*m
    return f"{h:02.0f}:{m:02.0f}:{s:04.1f}"

def ktFactorFunction(duration):
    """takes a duration in seconds and return the kt factor (nominal capacity divided by Amps for that duration)"""
    return testParams.nominalCapacity / ampsByDurationFunction(duration)

# array made of sub array with three fields:
#  0: section duration, 1: current in Amps, 2: starting cycle number (1-based)
startingSequence = csvAsNp(testParams.csvFileNames.startingCycles)
startingSequenceLength = startingSequence.shape[0]

def checkPeriod(period, periodName="period"):
    """raises an exception if period is not acceptable as a 1-based value"""
    if period < 1 or period > startingSequenceLength:
        raise IndexError(f"{periodName}={period} unfit (not in [1, {startingSequenceLength}] range)")

checkPeriod(testParams.numberOfSections, "testParams.numberOfSections")

def durationBetweenPeriods(firstPeriod, lastPeriod):
    """calculates cumulated duration between firstPeriod and lastPeriod (both inclusive and 1-based)"""
    checkPeriod(firstPeriod, "durationBetweenPeriods::firstPeriod")
    checkPeriod(lastPeriod, "durationBetweenPeriods::lastPeriod")
    if firstPeriod>lastPeriod:
        raise IndexError(f"durationBetweenPeriods: firstPeriod ({firstPeriod}) > lastPeriod ({lastPeriod})")
    return np.array([time for time in startingSequence[(firstPeriod-1):lastPeriod, 0]]).sum()

def ampsAtPeriod(period):
    """current in Amps for a given (1-based) period"""
    checkPeriod(period, "ampsAtPeriod::period")
    return startingSequence[period-1][1]

def cycleAtPeriod(period):
    """cycle for a given (1-based) period"""
    checkPeriod(period, "cycleAtPeriod::period")
    return startingSequence[period-1][2]

requiredSizesPerSection = np.array([])
for section in range(1, testParams.numberOfSections+1):
    if section < startingSequenceLength and ampsAtPeriod(section) < ampsAtPeriod(section+1):
        if testParams.verbose:
            print(f"Section {section} skipped\n")
    else:
        if testParams.verbose:
            print(f"Section {section}")
            print("Period,Load,Change,Duration,Remaining,Kt,Temp Derating,Size")
        previousLoad = 0.0
        requiredSectionSizes = np.array([])
        for period in range(1, section+1):
            load = ampsAtPeriod(period)
            changeInLoad = load - previousLoad
            previousLoad = load
            duration = startingSequence[period-1, 0]
            durationToSectionEnd = durationBetweenPeriods(period, section)
            kt = ktFactorFunction(durationToSectionEnd)
            tempDeratingFactor = testParams.deratingFactorOnTemp
            requiredSectionSize = changeInLoad * kt * tempDeratingFactor
            if testParams.verbose:
                print(f"{period},{load:.2f},{changeInLoad:.2f},{secToHMS(duration)},{secToHMS(durationToSectionEnd)},{kt:.4f},{tempDeratingFactor:.2f},{requiredSectionSize:.2f}")
            requiredSectionSizes= np.append(requiredSectionSizes, requiredSectionSize)
        maxRequiredSectionSize = requiredSectionSizes.sum()
        if testParams.verbose:
            print(f"Total: {maxRequiredSectionSize:.2f} Ah\n")
        requiredSizesPerSection= np.append(requiredSizesPerSection, maxRequiredSectionSize)
cycleNb = cycleAtPeriod(testParams.numberOfSections)
print(f"Result testing {cycleNb} cycle{'s' if cycleNb!=1 else ''}")
maximumSectionSize = requiredSizesPerSection.max()
uncorrectedSize = maximumSectionSize + testParams.randomSize
print(f"Maximum section size: {maximumSectionSize:.2f} + Random size: {testParams.randomSize:.2f}")
print(f" = Uncorrected size: {uncorrectedSize:.2f} Ah")
size = uncorrectedSize * testParams.designMargin * testParams.agingFactor
print(f"Uncorrected size: {uncorrectedSize:.2f} x Design margin: {testParams.designMargin:.2f} x Aging factor: {testParams.agingFactor:.2f}")
print(f" = Size: {size:.2f} Ah")
numberOfBatteriesRequired = int((size*testParams.finalTolerance+testParams.nominalCapacity)/testParams.nominalCapacity)
print(f"Number of batteries required: {numberOfBatteriesRequired} (with a {100*(1-testParams.finalTolerance):.1f}% tolerance)")

