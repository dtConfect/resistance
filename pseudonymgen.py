#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Implementation based on: http://stackoverflow.com/questions/5731670/simple-random-name-generator-in-python

import random

parts = {}

def clearNames():
    parts.clear()

def loadNames(fileName = 'pseudonyms\defaultParts.txt'):
    with open(fileName, 'r') as f:
        currentList = []
        for line in f.readlines():
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                currentList = []
                parts[line[1:-1]] = currentList
            else:
                currentList.append(line.strip())

def getName():
    return ''.join(random.choice(parts[partName]) for partName in sorted(parts))