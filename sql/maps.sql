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
