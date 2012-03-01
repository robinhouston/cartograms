#!/usr/bin/python

import sys
import psycopg2

dataset_name = sys.argv[1]

db = psycopg2.connect("host=localhost")

c = db.cursor()
c.execute("""
  delete from data_value where dataset_id in (
    select id from dataset where name = %s
  )
""", (dataset_name,))
c.close()

c = db.cursor()
c.execute("""
  delete from dataset where name = %s
""", (dataset_name,))
c.close()

db.commit()
