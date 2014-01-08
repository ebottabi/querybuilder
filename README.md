querybuilder
============

Simple SQL(ite) query builder for python.


# The querybuilder module. #

Contains a Query class that simplifies the building of simple SQL(ite) queries.

Query supports the following commands:

* SELECT
    - SELECT (colname1, colname2, ...) FROM table_name [WHERE ...]
    - SELECT * FROM table_name [WHERE ...]
* INSERT
    - INSERT INTO table_name [(colname1, colname2, ...)] VALUES (?, ?, ...)
* UPDATE
    - UPDATE table_name SET colname1=value1, colname2=value2, ... [WHERE ...]
* DELETE
    - DELETE FROM table_name [WHERE ...]
* WHERE
    - ... WHERE colname=value
    - ... WHERE colname1=value1 AND colname2=value2 AND ...
    - ... WHERE colname1=value1 OR colname2=value2 OR ...

Note: Query _does not_ (yet) support `ORDER`. 

Example:

    my_query = Query('my_table_name').select('colname1').where(colname2='some_value').sql()
    my_query.sql()
    # Returns: ("SELECT colname1 FROM my_table_name WHERE colname2=?", ['some_value'])

    my_query.sql(where=['some_other_value'])
    # Returns: ("SELECT colname1 FROM my_table_name WHERE colname2=?", ['some_other_value'])
