"""
Linear interpolation for cartogram grids.
"""

import math
import re

# The raw coordinate system goes from
# (-XMAX, -YMAX) at the bottom left to (XMAX, YMAX) at top right.
XMAX, YMAX = 17005833, 8625154

class Interpolator(object):
  def __init__(self, width, height, grid_filename):
    self.width, self.height = width, height
    self.a = [ [ None for y in range(height+1) ] for x in range(width+1) ]
    grid_f = open(grid_filename, "r")
    
    line_number = 0
    for y in range(height+1):
      for x in range(width+1):
        line_number += 1
        line = grid_f.readline()
        if line is None:
          raise Exception("File ended unexpectedly")
        mo = re.match(r"^(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)$", line)
        if not mo:
          raise Exception("Failed to parse line %d: %s" % (line_number, line))
        self.a[x][y] = float(mo.group(1)), float(mo.group(2))

  def __call__(self, rx, ry):
    x = (rx + XMAX) * self.width  / (2 * XMAX)
    y = (ry + YMAX) * self.height / (2 * YMAX)
    if x < 0 or x > self.width or y < 0 or y > self.height:
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
      tx * 2 * XMAX / self.width  - XMAX,
      ty * 2 * YMAX / self.height - YMAX,
    )
        
