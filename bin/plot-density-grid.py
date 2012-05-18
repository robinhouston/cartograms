#!/usr/bin/python

import json
import optparse
import os
import sys

import PIL.Image, PIL.ImageFont, PIL.ImageDraw

def main(filename):
    d = []
    max_density = 0
    with open(filename) as f:
        meta = json.loads(f.next().strip())
        for y, line in enumerate(f):
            d.append([None] * meta["width"])
            for x, density in enumerate(map(float, line.strip().split(" "))):
                d[y][x] = density
                if density > max_density: max_density = density
    
    print "Density grid is %dx%d; taking middle ninth." % (meta["width"], meta["height"])
    print "Max density = %g" % (max_density,)
    if options.max_density: max_density = float(options.max_density)
    
    width, height = meta["width"]//3, meta["height"]//3
    im = PIL.Image.new("RGB", (width, height))
    pa = im.load()
    
    for x in xrange(width):
        for y in xrange(height):
            density = d[height + y][width + x]
            dp = int(255 * density / max_density)
            pa[(x, height - y - 1)] = (255, 255-dp, 255-dp)
    
    if options.text:
        text = options.text.format(**meta)
        font = PIL.ImageFont.truetype('/Library/Fonts/GillSans.ttc', 20, index=1)
        assert font.getname() == ("Gill Sans", "Bold")
        
        text_width, text_height = font.getsize(text)
        PIL.ImageDraw.Draw(im).text( (4, height - text_height), text, font=font, fill="white" )

    im.save(options.output or sys.out, "PNG")

if __name__ == "__main__":
    global options
    parser = optparse.OptionParser(usage="%prog [options] filename")
    parser.add_option("-o", "--output",
                      action="store",
                      help="the name of the output file (defaults to stdout)")
    parser.add_option("", "--max-density",
                      action="store",
                      help="the density that corresponds to total saturation")
    parser.add_option("", "--text",
                      action="store",
                      help="text to overlay on the image")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Wrong number of arguments")
    
    main(args[0])


"""

../newman-cart/cart --intermediate 1500 750 carbonmap/data/Maps/Cartogram\ data/Population.{density,cart}
mv carbonmap/data/Maps/Cartogram\ data/Population.cart.* cartogram-movies/
#max_density=$(bin/plot-density-grid.py -o /dev/null cartogram-movies/Population.cart.1 | perl -ne 'print$1 if/Max density = (.*)/')
max_density=5e+12

i=1; while [ -e "cartogram-movies/Population.cart.$i" ]
do
    echo "Processing cartogram-movies/Population.cart.$i"
    bin/plot-density-grid.py -o "$(printf cartogram-movies/Population.%03d.png $i)" --max-density="$max_density" --text="t = {t:.3f}" "cartogram-movies/Population.cart.$i"
    i=$[$i+1]
done

ffmpeg -f image2 -r 12 -i cartogram-movies/Population.%03d.png cartogram-movies/Population.mp4

"""

