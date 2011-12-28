
create table division (
  id   serial primary key,
  name varchar not null unique
);

CREATE TABLE region (
  id serial PRIMARY KEY,
  division_id integer not null references division (id),
  name varchar(60) not null,
  unique (division_id, name),
  unique (id, division_id),
  area double precision not null
);
SELECT AddGeometryColumn('','region','the_geom','4326','MULTIPOLYGON',2);
CREATE INDEX "region_geom" on region using gist(the_geom);
ALTER TABLE region add constraint "region_area_ck" CHECK (area = ST_Area(the_geom));

create table map (
  id   serial primary key,
  division_id integer not null references division(id),
  unique (id, division_id),
  name varchar not null unique,
  srid integer not null,
  x_min numeric(20,5) not null,
  x_max numeric(20,5) not null check (x_max > x_min),
  y_min numeric(20,5) not null,
  y_max numeric(20,5) not null check (y_max > y_min),
  width integer not null check (width > 0),
  height integer not null check (height > 0)
);

create table grid (
  map_id      integer not null references map(id),
  division_id integer not null,
  constraint "grid_map_ref" foreign key (map_id, division_id) references map(id, division_id),
  
  x           integer not null,
  y           integer not null,
  constraint "grid_uq" unique (map_id, x, y),
  
  region_id   integer null,
  constraint "grid_division_region_fkey" foreign key (region_id, division_id) references region(id, division_id)
);
SELECT AddGeometryColumn('','grid','pt_4326','4326','POINT',2);
CREATE INDEX "grid_pt_4326" on grid using gist(pt_4326);

-- To restore the pt_4326 values if something bad happens to them:
--
-- update grid
-- set pt_4326 = ST_Transform(
--                ST_SetSRID(
--                  ST_MakePoint(
--                     (map.x_max - map.x_min) * grid.x / map.width  + map.x_min,
--                     (map.y_max - map.y_min) * grid.y / map.height + map.y_min
--                  )
--                  , map.srid
--                ), 4326
--              )
-- from map
-- where map.id = grid.map_id;



create table dataset (
   id serial primary key,
   name varchar not null unique,
   division_id integer not null references division(id),
   unique (id, division_id)
);

create table data_value (
    dataset_id integer not null,
    division_id integer not null,
    constraint "data_value_dataset_fkey" foreign key (dataset_id, division_id) references dataset(id, division_id),
    region_id integer not null,
    constraint "data_value_region_fkey" foreign key (region_id, division_id) references region (id, division_id),
    value numeric(16,1) not null
);



