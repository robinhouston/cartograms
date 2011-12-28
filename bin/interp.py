"""
Linear interpolation for cartogram grids.
"""

import math
import re


class Interpolator(object):
  def __init__(self, grid_filename, width, height, x_min, y_min, x_max, y_max):
    self.width, self.height = width, height
    self.x_min, self.y_min, self.x_max, self.y_max = map(float, (x_min, y_min, x_max, y_max))
    
    self.a = [ [ None for y in range(3*height+1) ] for x in range(3*width+1) ]
    grid_f = open(grid_filename, "r")
    
    line_number = 0
    for y in range(3*height+1):
      for x in range(3*width+1):
        line_number += 1
        line = grid_f.readline()
        if line is None:
          raise Exception("File ended unexpectedly")
        mo = re.match(r"^(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)$", line)
        if not mo:
          raise Exception("Failed to parse line %d: %s" % (line_number, line))
        self.a[x][y] = float(mo.group(1)), float(mo.group(2))

  def __call__(self, rx, ry):
    x = (rx - self.x_min) * self.width  / (self.x_max - self.x_min) + self.width
    y = (ry - self.y_min) * self.height / (self.y_max - self.y_min) + self.height
    if x < 0 or x > 3 * self.width or y < 0 or y > 3 * self.height:
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
      (tx - self.width)  * (self.x_max - self.x_min) / self.width  + self.x_min,
      (ty - self.height) * (self.y_max - self.y_min) / self.height + self.y_min,
    )
        
