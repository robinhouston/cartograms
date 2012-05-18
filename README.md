Cartogram generation code

How to get started:

 * Install PostgreSQL and PostGIS.
 * Load the standard SRSs, if they’re not already loaded:

        psql < /usr/local/share/postgis/spatial_ref_sys.sql

 * Add World Robinson as well:

        # from http://spatialreference.org/ref/esri/54030/postgis/
        psql <<END
        INSERT into spatial_ref_sys (
            srid, auth_name, auth_srid,
            proj4text, srtext
        ) values (
            954030, 'esri', 54030,
            '+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs ',
              'PROJCS["World_Robinson",GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Robinson"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],UNIT["Meter",1],AUTHORITY["EPSG","54030"]]'
        );
        END

 * (Note that PROJ.4 < 4.8 has an error in its implementation of the Robinson projection:
   http://trac.osgeo.org/proj/ticket/113)

 * Create the schema using `sql/schema.sql` and define the functions using `sql/functions.sql`.

 * Load whatever maps you intend to use from `sql/maps.sql`, or define your own.

 * Prepare your dataset in CSV format.

 * Run `bin/load-data.py` to load your data into the database.
 
 * Run `bin/density-grid.py` to export a density grid, and then run [`cart`](http://www-personal.umich.edu/~mejn/cart/) to create a cartogram grid from it.
 
 * Run `bin/as-js.py` to generate a JSON file of SVG path data.
 
 * Use this JSON data to make a beautiful web app.
