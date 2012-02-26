#!/usr/bin/python

import csv
import re
import sys

def normalise(country_name):
  s = country_name.upper()
  return re.sub(r'[^A-Z]|\bAND\b|\bTHE\b', '', s)

# Read in the list of country codes
code_by_name = {}
for line in open("data/iso-country-codes.ssv", 'r'):
    split_line = line.strip().split(";")
    code = split_line[0]
    names = split_line[1:]
    for name in names:
      norm = normalise(name)
      if norm in code_by_name:
        raise Exception("Normalised name '%s' already seen" % (norm))
      code_by_name[norm] = code

# Now read in the data file
f = open(sys.argv[1], 'r')
r = csv.reader(f)
w = csv.writer(sys.stdout)
header = r.next()
header[1:1] = ["Country code"]
w.writerow(header)
for row in r:
    country = row[0]
    norm = normalise(country)
    if norm in code_by_name:
        code = code_by_name[norm]
        row[1:1] = [code]
        w.writerow(row)
    else:
        print >>sys.stderr, "Failed to recognise '{country}'".format(country=country)
