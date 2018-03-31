## TODO

### Make ETL python class
- `extract`, `transform`, and `load` should each be methods, where each method throws a notimplementederror if one of the prerequisite methods has not been run yet

- ETL class objects should have ability to make connections to database and gather names of tables corresponding to foreign keys that would be necessary for load

### Convert scraper scripts into ETL-inheriting classes
- table-ETL class objects should be instantiated from a table name

### Convert loader script into sequence of ETL class methods