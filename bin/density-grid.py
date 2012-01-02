#!/usr/bin/python
# -*- encoding: utf-8 -*-

import sys
import psycopg2

"""
Generate a density grid that can be fed to cart.
"""

db = psycopg2.connect("host=localhost")

dataset_name = sys.argv[1]
map_name = sys.argv[2]
if len(sys.argv) > 3:
  multiplier = int(sys.argv[3])
else:
  multiplier = 1

c = db.cursor()
c.execute("""
  select id, division_id, srid,
         width, height
  from map
  where name = %s
""", (map_name,))
map_id, division_id, srid, X, Y = c.fetchone()
c.close()

def region_at_position(x, y):
  c = db.cursor()
  try:
    c.execute("""
      select id from region
      where ST_Contains(the_geom, ST_Transform(ST_SetSRID(ST_MakePoint(%s, -%s), %s), 4326))
      and region.division_id = %s
    """, (x, y, srid, division_id))
    r = c.fetchone()
    return r[0] if r else None
  finally:
    c.close()

def get_global_density():
    c = db.cursor()
    try:
        c.execute("""
            select sum(data_value.value) / sum(region.area)
            from region
            join data_value on region.id = data_value.region_id
            join dataset on data_value.dataset_id = dataset.id
            where dataset.name = %s and region.division_id = %s
        """, (dataset_name, division_id))
        return c.fetchone()[0]
    finally:
        c.close()

def get_local_densities():
  c = db.cursor()
  try:
    c.execute("""
      select y, x, data_value.value / region.area density
         , grid.region_id
      from grid
      left join (
         select region_id, value
         from data_value
         join dataset on data_value.dataset_id = dataset.id
         where dataset.name = %s
      ) data_value using (region_id)
      left join region on data_value.region_id = region.id
      where grid.map_id = %s
      and region.division_id = %s
      order by y, x
    """, (dataset_name, map_id, division_id))
    
    a = [ [None for i in range(X)] for j in range(Y) ]
    for r in c.fetchall():
      y, x, v, region_id = r
      # if region_id is not None and v is None:
      #   v = 1e-5 / multiplier
      a[y][x] = v
    
    return a
    
  finally:
    c.close()

global_density = get_global_density()
local_densities = get_local_densities()
def carbon_reserve_density_at_position(x, y):
  return multiplier * (local_densities[y][x] or global_density)

padding = " ".join(["%.5f" % (multiplier * global_density)] * X)
for y in range(Y):
  print padding, padding, padding
for y in range(Y):
  print padding, (" ".join(["%.5f"] * X)) % tuple((
    carbon_reserve_density_at_position(x, y) for x in range(X)
  )), padding
for y in range(Y):
  print padding, padding, padding

