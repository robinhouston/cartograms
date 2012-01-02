#!/usr/bin/python

from __future__ import division

import optparse
import sys

import cairo
import shapely.wkb
import psycopg2

import utils

FILL_COLOUR = (0xf7 / 0xff, 0xd3 / 0xff, 0xaa / 0xff)
STROKE_COLOUR = (0xa0 / 0xff, 0x80 / 0xff, 0x70 / 0xff)

class AsPNG(object):
  def __init__(self, options):
    self.options = options
    self.db = psycopg2.connect("host=localhost")
    self.m = utils.Map(self.db, options.map)
    if options.cart:
      self.f = utils.Interpolator(options.cart, self.m)
    else:
      self.f = None
    
    if options.output:
      self.out = open(options.output, 'w')
    else:
      self.out = sys.stdout

  def render_region_paths(self):
    c = self.db.cursor()
    try:
      if self.options.dataset:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), %(simplification)s)) g
               , exists(
                  select *
                  from data_value
                  join dataset on data_value.dataset_id = dataset.id
                  where dataset.name = %(dataset_name)s
                  and data_value.region_id = region.id) has_data
          from region
          where region.division_id = %(division_id)s
        """, {
          "srid": self.m.srid,
          "simplification": self.options.simplification,
          "datset_name": self.options.dataset,
          "division_id": self.m.division_id
        })
      else:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), %(simplification)s)) g
               , false
          from region
          where region.division_id = %(division_id)s
        """, {
          "srid": self.m.srid,
          "simplification": self.options.simplification,
          "division_id": self.m.division_id
        })
      for iso2, g, has_data in c.fetchall():
        classes = "has-data" if has_data else "no-data"
        p = shapely.wkb.loads(str(g))
        self.render_multipolygon(p)
          
    finally:
      c.close()

  def render_polygon_ring(self, ring):
      poly_arr = ["M"]
      first = True
      for x, y in ring.coords:
        if self.f:
          x, y = self.f(x, y)
        if first:
          self.c.move_to(x, y)
          first = False
        else:
          self.c.line_to(x, y)
      
      self.c.close_path()
      if FILL_COLOUR:
        self.c.set_source_rgb(*FILL_COLOUR)
        if STROKE_COLOUR:
          self.c.fill_preserve()
        else:
          self.c.fill()
      if STROKE_COLOUR:
        self.c.set_source_rgb(*STROKE_COLOUR)
        self.c.stroke()

  def render_polygon(self, polygon):
    for ring in polygon.exterior:
      self.render_polygon_ring(ring)

  def render_multipolygon(self, multipolygon):
    path_arr = []
    for g in multipolygon.geoms:
      self.render_polygon_ring(g.exterior)
      
      for interior in g.interiors: # XXXX NO
        self.render_polygon_ring(interior)
  
    return " ".join(sum(path_arr, []))

  def render_map(self):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.m.width, self.m.height)
    self.c = cairo.Context(surface)
    
    self.c.rectangle(0,0, self.m.width, self.m.height)
    self.c.set_source_rgb(0x9e/0xff, 0xc7/0xff, 0xf3/0xff)
    self.c.fill()

    self.c.transform(cairo.Matrix(
      self.m.width / (self.m.x_max - self.m.x_min), 0,
      0, - self.m.height / (self.m.y_max - self.m.y_min),
      -self.m.x_min * self.m.width / (self.m.x_max - self.m.x_min),
      self.m.y_max * self.m.height / (self.m.y_max - self.m.y_min),
    ))
    self.c.set_line_width(self.options.stroke_width)

    self.render_region_paths()

    surface.write_to_png(self.out)
    surface.finish()

def main():
  global options
  parser = optparse.OptionParser()
  parser.add_option("", "--map",
                    action="store",
                    help="the name of the map to use")
  parser.add_option("", "--cart",
                    action="store",
                    help="the name of the file containing the cartogram grid")
  parser.add_option("", "--dataset",
                    action="store",
                    help="the name of the dataset (used to mark which regions have data)")
  
  parser.add_option("-o", "--output",
                    action="store",
                    help="the name of the output file (defaults to stdout)")
  
  parser.add_option("", "--simplification",
                    action="store", default=1000,
                    help="how much to simplify the paths (default %default)")
  parser.add_option("", "--stroke-width",
                    action="store", default=2000, type="int",
                    help="width of SVG strokes (default %default)")

  parser.add_option("", "--static",
                    action="store_true", default=False,
                    help="Do not animate")
  
  parser.add_option("", "--circles",
                    action="store",
                    help="the name of the table containing data points to plot")
  parser.add_option("", "--circle-radius",
                    action="store", default=500, type="int",
                    help="radius of circles (default %default)")
  parser.add_option("", "--circle-opacity",
                    action="store", default=0.1, type="float",
                    help="opacity of circles (default %default)")
  
  (options, args) = parser.parse_args()
  if args:
    parser.error("Unexpected non-option arguments")
  
  if not options.map:
    parser.error("Missing option --map")
  
  AsPNG(options=options).render_map()

main()
