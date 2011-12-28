#!/usr/bin/python
# -*- encoding: utf-8 -*-

import csv
import sys
import psycopg2


def each(filename):
    f = open(filename, 'r')
    r = csv.reader(f)
    
    header = r.next()
    for row in r:
        yield dict(zip(header, [x.decode("utf-8") for x in row]))
    
    f.close()

db = psycopg2.connect("host=localhost")
class Col(str):
  """A column name, as opposed to a constant string.
  """
def as_seq(gen, *cols):
    for d in gen:
        yield tuple((
            d[col] if isinstance(col, Col) else col for col in cols
        ))

dataset_name, csv_filename, division_name, region_col, value_col = sys.argv[1:]

c = db.cursor()
c.execute("""
    insert into dataset (name, division_id) (select %s, division.id from division where name = %s)
""", (dataset_name, division_name))
c.close()

c = db.cursor()
c.execute("""
    select currval('dataset_id_seq'::regclass)
""")
dataset_id = c.fetchone()[0]
c.close()

c = db.cursor()
c.executemany("""
        insert into data_value (
            dataset_id,
            division_id,
            region_id,
            value
        ) (
            select %s, division.id, region.id, %s
            from region
            join division on region.division_id = division.id
            where division.name = %s and region.name = %s
        )
    """,
    as_seq(each(csv_filename), dataset_id, Col(value_col), division_name, Col(region_col))
)
c.close()
db.commit()
