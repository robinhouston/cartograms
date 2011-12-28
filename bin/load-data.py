#!/usr/bin/python
# -*- encoding: utf-8 -*-

import csv
import sys
import psycopg2


"""
create table dataset (
   id serial primary key,
   name varchar not null unique
);

create table data_value (
    country_gid integer not null references country (gid),
    dataset_id integer not null references dataset(id),
    value numeric(16,1)
);
"""

def each(filename):
    f = open(filename, 'r')
    r = csv.reader(f)
    
    header = r.next()
    for row in r:
        yield dict(zip(header, [x.decode("utf-8") for x in row]))
    
    f.close()

db = psycopg2.connect("host=localhost")
def as_seq(gen, dataset_id, *cols):
    for d in gen:
        yield (dataset_id,) + tuple((
            d[col] for col in cols
        ))

dataset_name, csv_filename, country_col, value_col = sys.argv[1:]

c = db.cursor()
c.execute("""
    insert into dataset (name) values (%s)
""", (dataset_name,))
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
            country_gid,
            value
        ) (
            select %s, gid, %s
            from country
            where iso2 = %s
        )
    """,
    as_seq(each(csv_filename), dataset_id, value_col, country_col)
)
c.close()
db.commit()
