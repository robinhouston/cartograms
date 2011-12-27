#!/usr/bin/python
# -*- encoding: utf-8 -*-

import psycopg2

"""

"""

XMAX, YMAX = 17005833.3305252, 8625154.47184994
X, Y = 500, 250


db = psycopg2.connect("host=localhost")
def country_at_position(x, y):
  c = db.cursor()
  try:
    c.execute("""
      select gid from "tm_world_borders-0"
      where ST_Contains(the_geom, ST_Transform(ST_GeomFromText('POINT(%d %d)', 954030), 4326))
    """ % (x, -y))
    r = c.fetchone()
    return r[0] if r else None
  finally:
    c.close()

def get_global_density():
    c = db.cursor()
    try:
        c.execute("""
            select 10000 * sum(oil_carbon + gas_carbon + coal_carbon) / sum(area)
            from "tm_world_borders-0"
            join carbon_reserves on "tm_world_borders-0".gid = carbon_reserves.country_gid
        """)
        return c.fetchone()[0]
    finally:
        c.close()

def get_local_densities():
  c = db.cursor()
  try:
    c.execute("""
      select y, x, 10000 * (
                carbon_reserves.oil_carbon +
                carbon_reserves.gas_carbon +
                carbon_reserves.coal_carbon
             ) / country.area
             carbon_reserve_density
      from grid
      left join carbon_reserves using (country_gid)
      left join "tm_world_borders-0" country on grid.country_gid = country.gid
      order by y, x
    """)
    
    a = [ [None for i in range(X)] for j in range(Y) ]
    for r in c.fetchall():
      y, x, v = r
      a[y][x] = v
    
    return a
    
  finally:
    c.close()

global_density = get_global_density()
local_densities = get_local_densities()
def carbon_reserve_density_at_position(x, y):
  return local_densities[y][x] or global_density

padding = " ".join(["%.5f" % global_density] * X)
for y in range(Y):
  print padding, padding, padding
for y in range(Y):
  print padding, (" ".join(["%.5f"] * X)) % tuple((
    carbon_reserve_density_at_position(x, y) for x in range(X)
  )), padding
for y in range(Y):
  print padding, padding, padding

