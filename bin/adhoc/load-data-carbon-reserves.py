#!/usr/bin/python
# -*- encoding: utf-8 -*-

import csv
import sys
import psycopg2


"""
create table carbon_reserves (
    country_gid integer not null references country (gid),
    oil_carbon numeric(8,1),
    gas_carbon numeric(8,1),
    coal_carbon numeric(8,1)
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
def as_seq(gen):
    for country in gen:
        yield (
            country["Oil carbon"] or 0,
            country["Gas carbon"] or 0,
            country["Coal carbon"] or 0, 
            country["Code"]
        )

c = db.cursor()
c.executemany("""
        insert into carbon_reserves (
            country_gid,
            oil_carbon, gas_carbon, coal_carbon
        ) (
            select gid,
                   %s, %s, %s
            from country
            where iso2 = %s
        )
    """,
    as_seq(each("data/carbon-reserves.csv"))
)
c.close()
db.commit()
