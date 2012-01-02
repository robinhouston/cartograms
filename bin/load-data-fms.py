#!/usr/bin/python

import psycopg2

"""
create table fms_problem (
  id serial primary key,
  created timestamp not null,
  category varchar not null
);
SELECT AddGeometryColumn('','fms_problem','location','4326','POINT',2);
"""

db = psycopg2.connect("host=localhost")
c = db.cursor()
c.executemany("""
insert into fms_problem (
  created, location, category
) values (
  %(t)s ::timestamp, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326), %(cat)s
)
""", (
  dict(zip(("t", "lat", "lon", "cat"), line.split("\t")))
  for line in open("data/fms.txt", 'r')
))
c.close()

db.commit()
