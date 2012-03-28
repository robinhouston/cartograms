#!/usr/bin/python

import json
import optparse
import re
import shlex
import sys

import shapely.wkb
import psycopg2

import utils

class AsSVG(object):
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
    
    if options.exclude_regions:
      self.exclude_regions = set(shlex.split(options.exclude_regions))
    else:
      self.exclude_regions = set()

  def print_robinson_path(self):
    c = self.db.cursor()
    try:
      c.execute("""
        select ST_AsEWKB(ST_Transform(ST_Segmentize(ST_GeomFromText(
          'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))', 4326), 5), 954030))
      """)
      path_bin = c.fetchone()[0]
    finally:
      c.close()
  
    p = shapely.wkb.loads(str(path_bin))
    if self.f is None or self.options.static:
      print >>self.out, '<path id="robinson" d="{path}"/>'.format(path=self.polygon_as_svg(p, self.f))
    else:
      original_path = self.polygon_as_svg(p)
      morphed_path = self.polygon_as_svg(p, self.f)
      print >>self.out, """<path id="robinson" d="{original}">
        <animate dur="10s" repeatCount="indefinite" attributeName="d" 
           values="{original};{morphed};{morphed};{original};{original}"/>
      </path>""".format(original=original_path, morphed=morphed_path)

  def _simplification(self):
    if not hasattr(self, "simplification_dict"):
      setattr(self, "simplification_dict", {})
      for region_name in shlex.split(self.options.alternate_simplification_regions):
        self.simplification_dict[region_name] = self.options.alternate_simplification
      if self.options.simplification_json is not None:
        self.simplification_dict.update(json.loads(self.options.simplification_json))
    
    def q(x): return unicode(psycopg2.extensions.adapt(x))
    
    if self.simplification_dict:
      return "CASE name " + "".join([
        "WHEN {region_name} THEN {alternate_simplification} ".format(
          region_name=q(region_name),
          alternate_simplification=q(alternate_simplification),
        )
        for region_name, alternate_simplification
        in self.simplification_dict.items()
      ]) + "ELSE " + q(self.options.simplification) + " END"
    else:
      return q(self.options.simplification)
  
  def _transform(self, x, y):
    if not self.options.output_grid:
      return x, -y
    return (
      (x - self.m.x_min) * self.options.output_grid_width / (self.m.x_max - self.m.x_min),
      self.options.output_grid_height - (y - self.m.y_min) * self.options.output_grid_height / (self.m.y_max - self.m.y_min),
    )
  
  def region_paths(self):
    c = self.db.cursor()
    try:
      if self.options.dataset:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), {simplification})) g
               , exists(
                  select *
                  from data_value
                  join dataset on data_value.dataset_id = dataset.id
                  where dataset.name = %(dataset)s
                  and data_value.region_id = region.id) has_data
          from region
          where region.division_id = %(division_id)s
        """.format(simplification=self._simplification()), {
            "srid": self.m.srid,
            "simplification": self.options.simplification,
            "dataset": self.options.dataset,
            "division_id": self.m.division_id
        })
      else:
        c.execute("""
          select region.name
               , ST_AsEWKB(ST_Simplify(ST_Transform(region.the_geom, %(srid)s), {simplification})) g
               , false
          from region
          where region.division_id = %(division_id)s
        """.format(simplification=self._simplification()), {
            "srid": self.m.srid,
            "division_id": self.m.division_id
        })
      
      for region_name, g, has_data in c.fetchall():
        if region_name in self.exclude_regions:
          continue
        p = shapely.wkb.loads(str(g))
        yield region_name, p, has_data
    
    finally:
      c.close()
  
  def print_region_paths(self):
    for region_name, p, has_data in self.region_paths():
      region_key = region_name # XXXX only works if the region name is a valid id
      if self.options.classes:
        classes = shlex.split(self.options.classes)
      else:
        classes = []
      if self.options.dataset:
        classes += ["has-data"] if has_data else ["no-data"]
      
      if self.f is None or self.options.static:
        path = self.multipolygon_as_svg(p, self.f)
        if path:
          print >>self.out, '<path id="{region_key}" d="{path}" class="{classes}"/>'.format(region_key=region_key, path=path, classes=" ".join(classes))
      else:
        original_path = self.multipolygon_as_svg(p)
        if original_path:
          morphed_path = self.multipolygon_as_svg(p, self.f)
          print >>self.out, """<path id="{region_key}" d="{original}" class="{classes}">
            <animate dur="10s" repeatCount="indefinite" attributeName="d" 
                values="{original};{morphed};{morphed};{original};{original}"/>
          </path>""".format(region_key=region_key, original=original_path, morphed=morphed_path, classes=" ".join(classes))
  
  def print_region_paths_json(self):
    d = {}
    for region_name, p, has_data in self.region_paths():
      region_key = region_name # XXXX only works if the region name is a valid id
      d[region_key] = self.multipolygon_as_svg(p, self.f)
    print >>self.out, json.dumps(d)

  def polygon_ring_as_svg(self, ring, f):
      poly_arr = ["M"]
      first = True
      for x, y in ring.coords:
        if f:
          x, y = f(x, y)
        x, y = self._transform(x, y)
        poly_arr.append("%.0f" % x)
        poly_arr.append("%.0f" % y)
        if first:
          poly_arr.append("L")
          first = False
      poly_arr.pop(); poly_arr.pop() # Remove the last point
      poly_arr.append("Z")
      return poly_arr

  def polygon_as_svg(self, polygon, f=None):
    return " ".join(self.polygon_ring_as_svg(polygon.exterior, f))

  def multipolygon_as_svg(self, multipolygon, f=None):
    path_arr = []
    for g in multipolygon.geoms:
      path_arr.append(self.polygon_ring_as_svg(g.exterior, f))
      for interior in g.interiors:
        path_arr.append(self.polygon_ring_as_svg(interior, f))
  
    return " ".join(sum(path_arr, []))
  
  def print_circles(self):
    c = self.db.cursor()
    c.execute("""
    with t as (select ST_Transform(location, %s) p from {table_name})
    select ST_X(t.p), ST_Y(t.p) from t
    """.format(table_name=self.options.circles), (self.m.srid,) )
    if self.f is None:
      for x, y in c:
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>'.format(x=x, y=-y, r=self.options.circle_radius)
    elif self.options.static:
      for x, y in c:
        tx, ty = self.f(x, y)
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>'.format(x=tx, y=-ty, r=self.options.circle_radius)
    else:
      for x, y in c:
        tx, ty = self.f(x, y)
        print >>self.out, '<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}">'.format(x=x, y=-y, r=self.options.circle_radius)
        print >>self.out, '<animate dur="10s" repeatCount="indefinite" attributeName="cx" ' + \
                       'values="{x:.0f};{tx:.0f};{tx:.0f};{x:.0f};{x:.0f}"/>'.format(x=x, tx=tx)
        print >>self.out, '<animate dur="10s" repeatCount="indefinite" attributeName="cy" ' + \
                       'values="{y:.0f};{ty:.0f};{ty:.0f};{y:.0f};{y:.0f}"/>'.format(y=-y, ty=-ty)
        print >>self.out, '</circle>'
    c.close()

  def print_document(self):
    if self.options.output_grid:
      x_min = 0
      minus_y_max = 0
      x_extent = self.options.output_grid_width
      y_extent = self.options.output_grid_height
    else:
      x_min = self.m.x_min
      minus_y_max = -self.m.y_max
      x_extent = self.m.x_max-self.m.x_min
      y_extent = self.m.y_max-self.m.y_min
    
    if self.options.style:
      external_stylesheet = open(self.options.style, 'r').read()
    else:
      external_stylesheet = ""
    
    print >>self.out, """<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%(width)d" height="%(height)d" viewBox="%(x_min).5f %(minus_y_max).5f %(x_extent).5f %(y_extent).5f">
    <style type="text/css">
      path { fill: none; stroke: #a08070; stroke-width: %(stroke_width)s; }
      path.no-data { fill: white; }
      circle { fill: red; opacity: %(circle_opacity)f; }
      %(external_stylesheet)s
    </style>
    <path id="bounds" d="M %(x_min).5f %(minus_y_max).5f h %(x_extent).5f v %(y_extent).5f h -%(x_extent).5f Z"/>
    """ % {
      "width": self.m.width, "height": self.m.height,
      "x_min": x_min, "minus_y_max": minus_y_max,
      "x_extent": x_extent, "y_extent": y_extent,
      "stroke_width": self.options.stroke_width,
      "circle_opacity": self.options.circle_opacity,
      "external_stylesheet": external_stylesheet,
    }
    
    if self.options.robinson:
      self.print_robinson_path()
    
    self.print_region_paths()
    if self.options.circles:
      self.print_circles()
    print >>self.out, "</svg>"
  
  def print_json(self):
    self.print_region_paths_json()

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
  parser.add_option("", "--json",
                    action="store_true",
                    help="Output in JSON format")
  
  parser.add_option("", "--simplification",
                    action="store", default=1000,
                    help="how much to simplify the paths (default %default)")
  parser.add_option("", "--alternate-simplification",
                    action="store", type="int",
                    help="simplification to use for regions specified by --alternate-simplification-regions")
  parser.add_option("", "--alternate-simplification-regions",
                    action="store", default="",
                    help="regions that use alternate simplification, space-separated (or shell-quoted)")
  parser.add_option("", "--simplification-json",
                    action="store",
                    help="A JSON-encoded dict of region name => simplification")
  parser.add_option("", "--exclude-regions",
                    action="store",
                    help="Regions to exclude. Space-separated (shell-quoted)")
  
  parser.add_option("", "--output-grid",
                    action="store",
                    help="the output grid, in the form <width>x<height>")
  parser.add_option("", "--stroke-width",
                    action="store", default=2000,
                    help="width of SVG strokes (default %default)")
  
  parser.add_option("", "--classes",
                    action="store",
                    help="CSS classes to add to countries, optionally")
  parser.add_option("", "--style",
                    action="store",
                    help="a stylesheet to embed inline, optionally")

  parser.add_option("", "--robinson",
                    action="store_true", default=False,
                    help="include the Robinson map outline")

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
  
  if options.json:
    if options.static:
      parser.error("--static doesn't make sense in JSON mode: JSON output is always static")
    
    # Not all options are yet supported in JSON output mode
    # (Bear in mind as-js.py as an alternative, if you want output for Javascript)
    if options.circles:
      parser.error("--circles is not yet supported in JSON output mode")
    if options.robinson:
      parser.error("--robinson is not yet supported in JSON output mode")
  
  if options.output_grid:
    mo = re.match(r"^(\d+)x(\d+)$", options.output_grid)
    if mo is None:
      parser.error("Unrecognised value for --output-grid: " + options.output_grid)
    setattr(options, "output_grid_width", int(mo.group(1)))
    setattr(options, "output_grid_height", int(mo.group(2)))
  
  as_svg = AsSVG(options=options)
  if options.json:
    as_svg.print_json()
  else:
    as_svg.print_document()

main()
