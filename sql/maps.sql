-- World map

-- $ shp2pgsql -W LATIN1 -s 4326 TM_WORLD_BORDERS-0/TM_WORLD_BORDERS-0.3.shp country | psql

insert into division (name) values ('countries');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), iso2, the_geom, ST_Area(the_geom) from country
);

-- All the vertices are *very* close to grid-points on a 1E-6 grid,
-- so presumably were snapped to this grid at some point but have
-- drifted slightly due to accumulated errors of some sort when the
-- shape files were being prepared. Snapping back to the grid helps the
-- borders of neighbouring countries to match precisely where they should.
update region
set the_geom = ST_SnapToGrid(the_geom, 1E-6)
  , area = ST_Area(ST_SnapToGrid(the_geom, 1E-6))
where division_id = currval('division_id_seq');


insert into map (
  division_id,
  name, srid,
  x_min, x_max,
  y_min, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'world-robinson', 954030,
  -17005833.3305252, 17005833.3305252,
  -8625154.47184994, 8625154.47184994,
  500, 250;
  
);

select populate_grid('world-robinson');
select grid_set_regions('world-robinson', 'countries');


-- Map of Great Britain

-- bdline_gb data downloaded from http://www.ordnancesurvey.co.uk/oswebsite/products/boundary-line/index.html

-- # Loading the county boundaries from the OS
-- $ shp2pgsql -s 27700 bdline_gb/data/county_region.shp county |psql
-- $ shp2pgsql -s 27700 bdline_gb/data/district_borough_unitary_region.shp unitary_region |psql

insert into division (name) values ('utas');
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'os-britain', 27700,
  5500, -1000000, 5500 + 800000, -1000000 + 1035000,
  541, 700
);

select populate_grid('os-britain');

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from county
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from unitary_region
    where area_code in ('UTA', 'MTD')
);
update region
set name = 'E12000007'
where name = '999999'
and division_id = (select id from division where name = 'utas');

select grid_set_regions('os-britain', 'utas');




insert into division (name) values ('districts');
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'os-britain-districts', 27700,
  5500, -1000000, 5500 + 800000, -1000000 + 1035000,
  541, 700
);

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), code, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from unitary_region
);

select populate_grid('os-britain-districts')
     , grid_set_regions('os-britain-districts', 'districts');


-- US States

-- $ curl -LO http://geocommons.com/overlays/21424.zip
-- $ (mkdir 21424 && cd 21424 && unzip ../21424.zip)
-- $ shp2pgsql -s 4326 21424/usa_state_shapefile.shx | psql

-- http://spatialreference.org/ref/esri/102003/postgis/
INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( 9102003, 'esri', 102003, '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs ', 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["North_American_Datum_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["longitude_of_center",-96],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],PARAMETER["latitude_of_center",37.5],UNIT["Meter",1],AUTHORITY["EPSG","102003"]]');

insert into division (name) values ('us-states');
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), state_name, the_geom, ST_Area(the_geom) from usa_state_shapefile
);

-- robin=# select ST_Extent(ST_Transform(the_geom, 9102003)) from usa_state_shapefile where state_name not in ('Alaska', 'Hawaii');
--  BOX(-2354935.75 -1294963.875,2256319.25 1558806.125)

insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'usa-contiguous', 9102003,
  -2354935.75, -1294963.875, 2256319.25, 1558806.125,
  800, 500
);

select populate_grid('usa-contiguous')
     , grid_set_regions('usa-contiguous', 'us-states');





-- $ curl -LO http://www.nws.noaa.gov/geodata/catalog/national/data/s_01ja11.zip
-- $ (mkdir s_01ja11 && cd s_01ja11 && unzip ../s_01ja11.zip)
-- $ shp2pgsql -s 4326 s_01ja11/s_01ja11.shx | psql

-- select ST_Extent(ST_Transform(the_geom, 9102003)) from s_01ja11 where state not in ('AK', 'AH', 'AS', 'GU', 'HI', 'MP', 'PR', 'UM', 'VI');
--  BOX(-2356113.742898 -1337508.07561825,2258224.79945606 1565791.05687272)

delete from grid where division_id = (select id from division where name = 'us-states');
delete from region where division_id = (select id from division where name = 'us-states');
insert into region (division_id, name, the_geom, area) (
    select division.id, state, the_geom, ST_Area(the_geom)
    from s_01ja11
       , division
    where division.name = 'us-states'
);


delete from grid where map_id = (select id from map where name = 'usa-contiguous');
delete from map where name = 'usa-contiguous';
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) (select
    division.id,
    'usa-contiguous', 9102003,
    -2356113.742898, -1337508.07561825, 2258224.79945606, 1565791.05687272,
    800, 500
  from division
  where name = 'us-states'
);

select populate_grid('usa-contiguous')
     , grid_set_regions('usa-contiguous', 'us-states');

