#!/usr/bin/python

# Takes a CSV file whose first column is the country name,
# and adds a column for the ISO 3166-1 alpha-2 code, writing
# the augmented CSV file to stdout and reporting any failures
# to stderr.

import csv
import re
import sys

def normalise(country_name):
  s = country_name.upper()
  return re.sub(r'[^A-Z]|\bAND\b|\bTHE\b', '', s)

# Read in the list of country codes
class CountryNameEncoder(object):
    def __init__(self):
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
        
        self.code_by_name = code_by_name

    def process_file(self, csv_file_name,
        country_name_column=0,
        write_to=sys.stdout,
        input_delimiter=',', output_delimiter=',',
        has_header=True
    ):
        f = open(csv_file_name, 'r')
        r = csv.reader(f, delimiter=input_delimiter)
        if not isinstance(write_to, file):
            write_to = open(write_to, 'w')
        w = csv.writer(write_to, delimiter=output_delimiter)
        
        if has_header:
            header = r.next()
            try:
                # Try country_name_column as a column number
                country_name_column_number = int(country_name_column)
            except ValueError:
                # If that fails, try it as a column name
                country_name_column_number = header.index(country_name_column)
                # (If that fails, we get a ValueError)
        
            header[1:1] = ["Country code"]
            w.writerow(header)
        else:
            country_name_column_number = int(country_name_column)
        
        for row in r:
            country = row[country_name_column_number]
            norm = normalise(country)
            if norm in self.code_by_name:
                code = self.code_by_name[norm]
                row[1:1] = [code]
                w.writerow(row)
            else:
                print >>sys.stderr, "Failed to recognise '{country}'".format(country=country)

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("", "--country-col", default=0,
                      help="number or name of country name column")
    parser.add_option("", "--input-delimiter", default=',',
                      help="Field delimiter for input file (default %default)")
    parser.add_option("", "--output-delimiter", default=',',
                      help="Field delimiter for output file (default %default)")
    parser.add_option("", "--no-header", dest="has_header", action="store_false", default=True,
                      help="Input file has no header line")
    
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Wrong number of arguments (%d, expected 1)" % len(args))
    
    CountryNameEncoder().process_file(args[0],
        country_name_column=options.country_col,
        input_delimiter=options.input_delimiter,
        output_delimiter=options.output_delimiter,
        has_header=options.has_header)

if __name__ == "__main__":
    main()
