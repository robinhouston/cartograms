import csv
import sys

iso3_by_iso2 = {}
with open("data/iso-3166-alpha-3.csv", 'r') as f:
    r = csv.reader(f)
    for row in r:
        iso3, iso2 = row[0:2]
        iso3_by_iso2[iso2] = iso3


with open("data/iso-country-codes.ssv", 'r') as f:
    for line in f:
        row = line.split(';')
        try:
            row[1:1] = [iso3_by_iso2[row[0]]]
        except KeyError:
            print >>sys.stderr, "Code '%s' not found" % (row[0],)
        print ';'.join(row),
