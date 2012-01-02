
import math
import re

class Map(object):
  def __init__(self, db, map_name):
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
    
    self.map_id, self.division_id, self.srid = map_id, division_id, srid
    self.width, self.height = width, height
    self.x_min, self.y_min, self.x_max, self.y_max = map(float, (x_min, y_min, x_max, y_max))

class Interpolator(object):
  """
  Linear interpolation for cartogram grids.
  """
  def __init__(self, grid_filename, the_map):
    self.m = the_map
    
    self.a = [ [ None for y in range(3*self.m.height+1) ] for x in range(3*self.m.width+1) ]
    grid_f = open(grid_filename, "r")
    
    line_number = 0
    for y in range(3*self.m.height+1):
      for x in range(3*self.m.width+1):
        line_number += 1
        line = grid_f.readline()
        if line is None:
          raise Exception("File ended unexpectedly")
        mo = re.match(r"^(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)$", line)
        if not mo:
          raise Exception("Failed to parse line %d of %s: %s" % (line_number, grid_filename, line))
        self.a[x][y] = float(mo.group(1)), float(mo.group(2))
    
    grid_f.close()

  def __call__(self, rx, ry):
    x = (rx - self.m.x_min) * self.m.width  / (self.m.x_max - self.m.x_min) + self.m.width
    y = (ry - self.m.y_min) * self.m.height / (self.m.y_max - self.m.y_min) + self.m.height
    if x < 0 or x > 3 * self.m.width or y < 0 or y > 3 * self.m.height:
      return rx, ry
    
    ix, iy = int(x), int(y)
    dx, dy = x - ix, y - iy
    
    tx = (1-dx)*(1-dy)*self.a[ix][iy][0] \
       + dx*(1-dy)*self.a[ix+1][iy][0]   \
       + (1-dx)*dy*self.a[ix][iy+1][0]   \
       + dx*dy*self.a[ix+1][iy+1][0]
      
    ty = (1-dx)*(1-dy)*self.a[ix][iy][1] \
       + dx*(1-dy)*self.a[ix+1][iy][1] \
       + (1-dx)*dy*self.a[ix][iy+1][1] \
       + dx*dy*self.a[ix+1][iy+1][1]
    
    return (
      (tx - self.m.width)  * (self.m.x_max - self.m.x_min) / self.m.width  + self.m.x_min,
      (ty - self.m.height) * (self.m.y_max - self.m.y_min) / self.m.height + self.m.y_min,
    )
        
