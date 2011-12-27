#!/usr/bin/python

import shapely.wkb
import psycopg2
import sys

import interp

X, Y = 500, 250

db = psycopg2.connect("host=localhost")

def print_robinson_path(f=None):
  c = db.cursor()
  try:
    c.execute("""
      select ST_AsBinary(ST_Transform(ST_Segmentize(ST_GeomFromText(
        'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))', 4326), 5), 954030))
    """)
    path_bin = c.fetchone()[0]
  finally:
    c.close()
  
  p = shapely.wkb.loads(str(path_bin))
  if f is None:
    print '<path id="robinson" d="{path}"/>'.format(path=polygon_as_svg(p))
  else:
    original_path = polygon_as_svg(p)
    morphed_path = polygon_as_svg(p, f)
    print """<path id="robinson" d="{original}">
      <animate dur="10s" repeatCount="indefinite" attributeName="d" 
         values="{original};{morphed};{morphed};{original};{original}"/>
    </path>""".format(original=original_path, morphed=morphed_path)

def print_country_paths(f=None):
  c = db.cursor()
  try:
    c.execute("""
      select country.iso2
           , ST_AsBinary(ST_Simplify(ST_Transform(the_geom,954030), 10000)) g
           , exists(select * from carbon_reserves where carbon_reserves.country_gid = country.gid) has_data
      from "tm_world_borders-0" country
    """)

    for iso2, g, has_data in c.fetchall():
      classes = "has-data" if has_data else "no-data"
      p = shapely.wkb.loads(str(g))
      if f is None:
        path = multipolygon_as_svg(p)
        if path:
          print '<path id="{iso2}" d="{path}" class="{classes}"/>'.format(iso2=iso2, path=path, classes=classes)
      else:
        original_path = multipolygon_as_svg(p)
        if original_path:
          morphed_path = multipolygon_as_svg(p, f)
          print """<path id="{iso2}" d="{original}" class="{classes}">
            <animate dur="10s" repeatCount="indefinite" attributeName="d" 
                values="{original};{morphed};{morphed};{original};{original}"/>
          </path>""".format(iso2=iso2, original=original_path, morphed=morphed_path, classes=classes)
          
  finally:
    c.close()


def polygon_ring_as_svg(ring, f=None):
    poly_arr = ["M"]
    first = True
    for x, y in ring.coords:
      if f:
        x, y = f(x, y)
      poly_arr.append("%.0f" % x)
      poly_arr.append("%.0f" % -y)
      if first:
        poly_arr.append("L")
        first = False
    poly_arr.pop(); poly_arr.pop() # Remove the last point
    poly_arr.append("Z")
    return poly_arr

def polygon_as_svg(polygon, f=None):
  return " ".join(polygon_ring_as_svg(polygon.exterior, f))

def multipolygon_as_svg(multipolygon, f=None):
  path_arr = []
  for g in multipolygon.geoms:
    path_arr.append(polygon_ring_as_svg(g.exterior, f))
    for interior in g.interiors:
      path_arr.append(polygon_ring_as_svg(interior, f))
  
  return " ".join(sum(path_arr, []))


def main():
  interpolator = interp.Interpolator(X, Y, sys.argv[1])
  print """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" height="600" width="1000" viewBox="-17005833.3305252 -8625154.47184994 34011666.6610504 17250308.94369988">
  <defs />
  <style type="text/css">
    svg { background: #eee; }
    #robinson { fill: #9ec7f3; stroke: #999; stroke-width: 40000; }
    path { fill: #f7d3aa; stroke: #a08070; stroke-width: 20000; }
    path.no-data { fill: white; }
  </style>"""
  print_robinson_path(interpolator)
  print_country_paths(interpolator)
  print "</svg>"

main()
