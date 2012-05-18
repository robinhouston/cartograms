#!/usr/bin/python

from __future__ import division

import math
import optparse
import sys

import cairo
import PIL.Image, PIL.ImageDraw
import shapely.wkb
import psycopg2

import utils

FILL_COLOUR = (0xf7 / 0xff, 0xd3 / 0xff, 0xaa / 0xff)
FILL_COLOUR_NO_DATA = (1, 1, 1)
STROKE_COLOUR = (0xa0 / 0xff, 0x80 / 0xff, 0x70 / 0xff)

##
FILL_COLOUR = FILL_COLOUR_NO_DATA = None
STROKE_COLOUR = (0x33, 0x33, 0x33)
##

CIRCLE_FILL_COLOUR = (1, 0, 0)

class AsPNG(object):
  def __init__(self, options):
    self.options = options
    self.db = psycopg2.connect("host=localhost")
    self.m = utils.Map(self.db, options.map)
    if options.cart:
      self.interpolator = utils.Interpolator(options.cart, self.m)
    else:
      self.interpolator = None
    
    if options.output:
      self.out = options.output
    else:
      self.out = sys.stdout

  def render_region_paths(self, slide):
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
          "dataset_name": self.options.dataset,
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
        fill_colour = FILL_COLOUR if has_data else FILL_COLOUR_NO_DATA
        p = shapely.wkb.loads(str(g))
        self.render_multipolygon(p, fill_colour, slide)
          
    finally:
      c.close()

  def render_polygon_ring_cairo(self, ring, fill_colour=FILL_COLOUR, slide=1.0):
    first = True
    for x, y in ring.coords:
      if self.interpolator:
        x, y = self.interpolator(x, y, slide)
      if first:
        self.c.move_to(x, y)
        first = False
      else:
        self.c.line_to(x, y)
    
    self.c.close_path()
    if fill_colour:
      self.c.set_source_rgb(*fill_colour)
      if STROKE_COLOUR:
        self.c.fill_preserve()
      else:
        self.c.fill()
    if STROKE_COLOUR:
      self.c.set_source_rgb(*STROKE_COLOUR)
      self.c.stroke()

  def render_polygon_ring_pil(self, ring, fill_colour=FILL_COLOUR, slide=1.0):
    polygon_coords = []
    for x, y in ring.coords:
      if self.interpolator:
        x, y = self.interpolator(x, y, slide)
      polygon_coords.append((
        (x - self.m.x_min) * self.m.width / (self.m.x_max - self.m.x_min),
        self.m.height - (y - self.m.y_min) * self.m.height / (self.m.y_max - self.m.y_min),
      ))
      
    self.draw.polygon(polygon_coords, outline=STROKE_COLOUR, fill=fill_colour)

  def render_polygon_ring(self, *args, **kwargs):
      if self.options.cairo:
          self.render_polygon_ring_cairo(*args, **kwargs)
      else:
          self.render_polygon_ring_pil(*args, **kwargs)

  def render_polygon(self, polygon, fill_colour=FILL_COLOUR, slide=1.0):
    for ring in polygon.exterior:
      self.render_polygon_ring(ring, fill_colour, slide)

  def render_multipolygon(self, multipolygon, fill_colour=FILL_COLOUR, slide=1.0):
    for g in multipolygon.geoms:
      self.render_polygon_ring(g.exterior, fill_colour, slide)
      
      # XXXX This is not remotely correct, of course
      for interior in g.interiors:
        self.render_polygon_ring(interior, fill_colour, slide)
  
  def render_circles_cairo(self, slide=1.0):
    c = self.db.cursor()
    c.execute("""
      with t as (select ST_Transform(location, %s) p from {table_name})
      select ST_X(t.p), ST_Y(t.p) from t
    """.format(table_name=self.options.circles), (self.m.srid,) )
    
    r,g,b = CIRCLE_FILL_COLOUR
    self.c.set_source_rgba(r,g,b, self.options.circle_opacity)
    for x, y in c:
        if self.interpolator:
          x, y = self.interpolator(x, y, slide)
        self.c.arc(x, y, self.options.circle_radius, 0, 2*math.pi)
        self.c.fill()
    c.close()

  def render_circles(self, *args, **kwargs):
    if self.options.cairo:
      self.render_circles_cairo(*args, **kwargs)
    else:
      raise Exception("Circles are not yet implemented in PIL mode")
  
  def render_map(self):
    if self.options.anim_frames:
      for frame in range(self.options.anim_frames):
        frame_filename = self.out % (frame,)
        print "Rendering frame to %s" % (frame_filename,)
        self.render_frame(frame / (self.options.anim_frames - 1), frame_filename)
    else:
      self.render_frame(1.0, self.out)
  
  def render_frame_cairo(self, slide, output_file):
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

    self.render_region_paths(slide)
    if self.options.circles:
      self.render_circles(slide)

    surface.write_to_png(output_file)
    surface.finish()

  def render_frame_pil(self, slide, output_file):
    if self.options.overlay_on:
      image = PIL.Image.open(self.options.overlay_on)
    else:
      image = PIL.Image.new("RGB", (self.m.width, self.m.height), None)
    
    self.draw = PIL.ImageDraw.Draw(image)
    
    self.render_region_paths(slide)
    if self.options.circles:
      self.render_circles(slide)
    
    image.save(output_file, "PNG")

  def render_frame(self, *args, **kwargs):
      if self.options.cairo:
          self.render_frame_cairo(*args, **kwargs)
      else:
          self.render_frame_pil(*args, **kwargs)

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
  
  parser.add_option("", "--anim-frames",
                    action="store", default=None, type="int",
                    help="Number of frames of animation to produce")
  
  parser.add_option("", "--circles",
                    action="store",
                    help="the name of the table containing data points to plot")
  parser.add_option("", "--circle-radius",
                    action="store", default=500, type="int",
                    help="radius of circles (default %default)")
  parser.add_option("", "--circle-opacity",
                    action="store", default=0.1, type="float",
                    help="opacity of circles (default %default)")

  parser.add_option("", "--cairo",
                    action="store_true", default=True,
                    help="use Cairo")
  parser.add_option("", "--pil",
                    action="store_false", dest="cairo",
                    help="use PIL")
  parser.add_option("", "--overlay-on",
                    action="store",
                    help="overlay the paths on the specified background image")
  
  (options, args) = parser.parse_args()
  if args:
    parser.error("Unexpected non-option arguments")
  
  if not options.map:
    parser.error("Missing option --map")
  
  if options.anim_frames:
    if not options.cart:
      parser.error("Animation requires a --cart file")
    if not options.output:
      parser.error("Animation requires that you specify an output file template")
    try:
      options.output % (0,)
    except:
      parser.error("Output filename '%s' does not contain a %%d template" % (options.output,))
  
  AsPNG(options=options).render_map()

main()
