#!/usr/bin/python

from shapely import wkb
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import psycopg2

db = psycopg2.connect("host=localhost")
c = db.cursor()
c.execute("""
  select ST_AsEWKB(
      ST_Intersection(ST_Boundary(fr.the_geom), ST_Buffer(ch.the_geom, 0.001))
    ) fr_border
  , ST_AsEWKB(
      ST_Intersection(ST_Boundary(ch.the_geom), ST_Buffer(fr.the_geom, 0.001))
    ) ch_border
  , ST_XMin( ST_Intersection(ST_Buffer(fr.the_geom, 0.01), ST_Buffer(ch.the_geom, 0.01)) ) x_min
  , ST_XMax( ST_Intersection(ST_Buffer(fr.the_geom, 0.01), ST_Buffer(ch.the_geom, 0.01)) ) x_max
  , ST_YMin( ST_Intersection(ST_Buffer(fr.the_geom, 0.01), ST_Buffer(ch.the_geom, 0.01)) ) y_min
  , ST_YMax( ST_Intersection(ST_Buffer(fr.the_geom, 0.01), ST_Buffer(ch.the_geom, 0.01)) ) y_max
  from country fr
     , country ch
  where fr.iso2 = 'FR'
    and ch.iso2 = 'CH'
""")

fr_border_ewkb, ch_border_ewkb, x_min, x_max, y_min, y_max = c.fetchone()
fr_border = wkb.loads(str(fr_border_ewkb))
ch_border = wkb.loads(str(ch_border_ewkb))

def linestring_as_svg(name, linestring):
  path = "M"
  first_time = True
  for x, y in linestring.coords:
    print """<circle class="{name}" cx="{x}" cy="{y}" r="{r}" title="{x} {y}"/>""".format(name=name, x=x, y=-y, r=0.003)
    path += " %f %f" % (x, -y)
    if first_time:
      path += " L"
      first_time = False
  print """<path id="{name}" d="{path}"/>""".format(name=name, path=path)

print """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="{x_min:.5f} {minus_y_max:.5f} {x_extent:.5f} {y_extent:.5f}">""".format(
  width=500, height=500,
  x_min=x_min,
  minus_y_max=-y_max,
  x_extent=x_max-x_min,
  y_extent=y_max-y_min,
)
print """
<style>
  path { fill: none; stroke-width: 0.001; }
  circle.fr {fill: red;}
  circle.ch {fill: blue;}
  #fr { stroke: red; }
  #ch { stroke: blue; }
</style>
"""
linestring_as_svg("fr", fr_border)
linestring_as_svg("ch", ch_border)
print """</svg>"""

