-- World map

-- $ shp2pgsql -W LATIN1 -s 4326 TM_WORLD_BORDERS-0/TM_WORLD_BORDERS-0.3.shp country | psql

insert into division (name) values ('countries');
insert into region (division_id, name, the_geom) (
    select currval('division_id_seq'), iso2, the_geom from country
);

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


-- # Loading the county boundaries from the OS
-- $ shp2pgsql -s 27700 bdline_gb/data/county_region.shp county |psql
-- $ shp2pgsql -s 27700 district_borough_unitary_region.shp unitary_region |psql

insert into division (name) values ('utas');
insert into map (
  division_id,
  name, srid,
  x_min, y_min,  x_max, y_max,
  width, height
) values (
  currval('division_id_seq'),
  'os-britain', 27700,
  5513, 5333.6, 655989, 1220301.5, -- select ST_Extent(the_geom) from county_or_uta;
  250, 500
);

select populate_grid('os-britain');

insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), name, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from county
);
insert into region (division_id, name, the_geom, area) (
    select currval('division_id_seq'), name, ST_Transform(the_geom, 4326), ST_Area(ST_Transform(the_geom, 4326))
    from unitary_region
    where area_code in ('UTA', 'MTD')
);

select grid_set_regions('os-britain', 'utas');
