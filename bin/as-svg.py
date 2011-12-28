#!/usr/bin/python

import shapely.wkb
import psycopg2
import sys

import interp

#SIMPLIFICATION = 10000
SIMPLIFICATION = 1000

# STROKE_WIDTH = 20000
STROKE_WIDTH = 2000

db = psycopg2.connect("host=localhost")

dataset_name = sys.argv[1]
map_name = sys.argv[2]

c = db.cursor()
c.execute("""
  select id, division_id, srid,
         width, height,
         x_min, x_max,
         y_min, y_max
  from map
  where name = %s
""", (map_name,))
map_id, division_id, srid, width, height, x_min, x_max, y_min, y_max = c.fetchone()
c.close()


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

def print_region_paths(f=None):
  c = db.cursor()
  try:
    c.execute("""
      select region.name
           , ST_AsBinary(ST_Simplify(ST_Transform(region.the_geom, %s), %s)) g
           , exists(
              select *
              from data_value
              join dataset on data_value.dataset_id = dataset.id
              where dataset.name = %s
              and data_value.region_id = region.id) has_data
      from region
      where region.division_id = %s
    """, (srid, SIMPLIFICATION, dataset_name, division_id))

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
  interpolator = interp.Interpolator(sys.argv[3], width, height, x_min, y_min, x_max, y_max)
  print """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%d" height="%d" viewBox="%.5f %.5f %.5f %.5f">
  <defs />
  <style type="text/css">
    svg { background: #eee; }
    #robinson { fill: #9ec7f3; stroke: #999; stroke-width: 40000; }
    path { fill: #f7d3aa; stroke: #a08070; stroke-width: %d; }
    path.no-data { fill: white; }
  </style>""" % (width, height, x_min, -y_max, x_max-x_min, y_max-y_min, STROKE_WIDTH)
  #print_robinson_path(interpolator)
  print_region_paths(interpolator)
  print "</svg>"

main()
