def main():
  global options
  parser = optparse.OptionParser()
  parser.add_option("", "--map",
                    action="store",
                    help="the name of the map to use")
  parser.add_option("", "--dataset",
                    action="store",
                    help="the name of the dataset")
  
  (options, args) = parser.parse_args()
  if args:
    parser.error("Unexpected non-option arguments")
  
  if not options.dataset:
    parser.error("Missing option --dataset")
  if not options.map:
    parser.error("Missing option --map")
  

def delete_density_grid(map_name, dataset_name):
  c = db.cursor()
  c.execute("""
    delete from density_grid
    where map_id = (select id from map where name = %(map_name)s)
    and dataset_id = (select id from dataset where name = %(dataset_name)s)
  """, {
    "map_name": map_name,
    "dataset_name": dataset_name
  })
  c.close()

def populate_density_grid(map_name, dataset_name):
  c = db.cursor()
  c.execute("""
    insert into density_grid (
      map_id, dataset_id, x, y, density
    ) (
      with map as (
          select * from map where name = %(map_name)s
      ),
      dataset as (
          select * from dataset where name = %(dataset_name)s
      ),
      global_density as (
          select sum(data_value.value) / sum(region.area) density
          from map
             , dataset
             , region
          join data_value on region.id = data_value.region_id
          where data_value.dataset_id = dataset.id
            and region.division_id = map.division_id
      ),
      region_density as (
          select y, x, data_value.value / region.area density
               , grid.region_id
          from grid
          join map on grid.map_id = map.id
          left join (
             select region_id, value
             from data_value
             join dataset on data_value.dataset_id = dataset.id
          ) data_value using (region_id)
          left join region on data_value.region_id = region.id
          where region.division_id = map.division_id
      ),
      big_grid as (
          select xs.x, ys.y
          from (select generate_series(0, 3*map.width ) x from map) xs
             , (select generate_series(0, 3*map.height) y from map) ys
             , map
      )
      select map.id map_id
           , dataset.id dataset_id
           , big_grid.x, big_grid.y
           , coalesce(region_density.density, global_density.density) density
      from global_density
         , big_grid
      left join region_density on (
              big_grid.x = (select width from map)  + region_density.x
          and big_grid.y = (select height from map) + region_density.y)
         , map
         , dataset
    """, {
      "map_name": map_name,
      "dataset_name": dataset_name,
    })
    c.close()
    

main()
