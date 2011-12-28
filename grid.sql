-- with constants as (
--     select 500 xwidth
--          , 250 ywidth
--          , 17005833.3305252 xmax
--          , 8625154.47184994 ymax
-- ),
-- pregrid as (
--     select x, y
--          , xmax * 2 * x / xwidth - xmax mx
--          , ymax * 2 * y / ywidth - ymax my
--     from constants
--        , (select generate_series(0,xwidth-1) x from constants) xs
--        , (select generate_series(0,ywidth-1) y from constants) ys
-- ),
-- grid as(
--     select x, y
--          , ST_Transform(
--              ST_SetSRID(
--                ST_MakePoint(mx, my)
--                , 954030
--              ), 4326
--            ) pt_4326
--     from pregrid
-- )
-- select grid.y
--      , grid.x
--      , country.name
-- from grid
-- left join country
--     on ST_Contains(country.the_geom, grid.pt_4326)
-- order by y, x
-- ;




create table grid as(
    with constants as (
        select 500 width
             , 250 height
             , 17005833.3305252 xmax
             , 8625154.47184994 ymax
    ),
    pregrid as (
        select x, y
             , xmax * 2 * x / width - xmax mx
             , ymax * 2 * y / height - ymax my
        from constants
           , (select generate_series(0, width)  x from constants) xs
           , (select generate_series(0, height) y from constants) ys
    )
    select x, y
         , ST_Transform(
             ST_SetSRID(
               ST_MakePoint(mx, my)
               , 954030
             ), 4326
           ) pt_4326
    from pregrid
);



-- This is quite slow, and it’s nice to be able to watch its progress,
-- which is impossible if it’s done in pure SQL as a single update.
-- It is slowed down massively by Europe, where there are lots of little
-- countries.

alter table grid add column country_gid integer references country (gid);

create or replace function grid_set_countries() returns void as $$
  declare
    r record;
  begin
    for r in select generate_series(0, 249) i loop
      raise notice 'Updating grid row y=%', r.i;
      update grid
      set country_gid = country.gid
      from country
      where ST_Contains(country.the_geom, grid.pt_4326)
      and grid.y = r.i;
    end loop;
  end;
$$ language 'plpgsql';

select grid_set_countries();


select grid.x, grid.y
from grid
join country
  on country.gid = grid.country_gid
where country.iso2 = 'GB';

