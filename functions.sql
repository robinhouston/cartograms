create or replace function populate_grid (
  map_name varchar
) returns void as $$
begin
  insert into grid (
    map_id, division_id, x, y, pt_4326
  ) (
      with map as (
          select * from map where name = map_name
      ),
      pregrid as (
          select xs.x, ys.y
               , (map.x_max - map.x_min) * xs.x / map.width  + map.x_min mx
               , (map.y_max - map.y_min) * ys.y / map.height + map.y_min my
               , map.srid
          from map
             , (select generate_series(0, width)  x from map) xs
             , (select generate_series(0, height) y from map) ys
      )
      select currval('map_id_seq'), currval('division_id_seq')
           , x, y
           , ST_Transform(
               ST_SetSRID(
                 ST_MakePoint(mx, my)
                 , srid
               ), 4326
             ) pt_4326
      from pregrid
  );
end;
$$ language 'plpgsql';

create or replace function grid_set_regions(
  map_name varchar,
  division_name varchar
) returns void as $$
  declare
    r record;
  begin
    for r in select generate_series(0, height) i from map where name = map_name loop
      raise notice 'Updating grid row y=%', r.i;
      update grid
      set region_id = region.id
      from region
      join division on region.division_id = division.id
         , map
      where grid.map_id = map.id
      and division.name = division_name
      and map.name = map_name
      and ST_Contains(region.the_geom, grid.pt_4326)
      and grid.y = r.i;
    end loop;
  end;
$$ language 'plpgsql';
