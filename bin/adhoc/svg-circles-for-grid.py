#!/usr/bin/python

XMAX, YMAX = 17005833.3305252, 8625154.47184994
X, Y = 500, 250
for y in range(Y):
  for x in range(X):
    print '<circle id="r{1}c{0}" cx="{2}" cy="{3}" r="10000"/>'.format(
      x, y,
      XMAX * 2 * x / X - XMAX, YMAX * 2 * y / Y - YMAX
    )

