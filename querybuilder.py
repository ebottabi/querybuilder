'''

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

'''

# Column-value mapping format string
_COL_MAP = '{}=?'


# Generates a comma-separated string of question marks, for SQL parameterization
def _qmarks(n):
    if hasattr(n, '__len__'):
        n = len(n)

    return ', '.join('?' for _ in range(n))


# Breaks a dict into tuples of keys and values while preserving relative order.
def _unmap_ordered(dct):
    return zip(*dct.items())


# Parses the argument signature of functions of the form f(attr=None, **kw_attr)
# so as to present the arguments as a single dict.
def _normalize(attr, kw_attr):
    if attr is not None:
        if not isinstance(attr, dict):
            attr = {k: None for k in attr}

        attr.update(kw_attr)
    else:
        attr = kw_attr

    return attr
            


class Query(object):
    
    '''The Query class.'''

    def __init__(self, table_name, escape_hook=None):

        '''

        The query constructor.
        Parameters:
            - `table_name` a string denoting the name of the table_name
                or a qualified database-dot-table_name path.
            - `escape_hook` a callback hook for sanitizing query column names.

        '''

        self._cmd_string = ''
        self._where_string = ''
        if escape_hook:
            self._fmt_params = {'table_name': escape_hook(table_name)}
        else:
            self._fmt_params = {'table_name': table_name}
    
        self._values = {'cmd': None, 'where': None}
        self.escape_hook = escape_hook


    def select(self, *attr):

        '''

        Build a query with the SELECT command.
        If `attr` is tuple of column name strings.
        If `attr` is empty, the query will be of the form:

            SELECT * FROM table_name

        '''

        if len(attr) == 1 and hasattr(attr[0], '__iter__'):
            attr = attr[0]

        if attr:
            self._cmd_string = 'SELECT {column_names} FROM {table_name}'
            if self.escape_hook:
                self._fmt_params['column_names'] = ', '.join(
                    map(self.escape_hook, attr)
                )
            else:
                self._fmt_params['column_names'] = ', '.join(attr)

        else:
            self._cmd_string = 'SELECT * FROM {table_name}'

        return self


    def insert(self, attr=None, **kw_attr):

        '''

        Build a query with the INSERT command.
        Parameters can be entered in the form:

            .insert(['colname1', 'colname2'])
            .insert(['colname1'], colname2='some_value')
            .insert({'colname1': 'value1'})
            .insert({'colname1': 'value1'}, colname2='value2')

        If the `attr` argument is an `int`, `insert()` constructs a query of the
        form:

            INSERT INTO table_name VALUES (?, ?, ...)

        where `attr` denotes the number of parameters to use in VALUES.

        '''

        if not isinstance(attr, int):
            attr = _normalize(attr, kw_attr)
            cols, vals = self._escape(_unmap_ordered(attr))
            self._cmd_string = 'INSERT INTO {table_name} ({column_names}) VALUES ({param_marks})'
            self._fmt_params['column_names'] = ', '.join(cols)
            self._fmt_params['param_marks'] = _qmarks(cols)
            self._values['cmd'] = vals
        else:
            self._cmd_string = 'INSERT INTO {table_name} VALUES ({param_marks})'
            self._fmt_params['param_marks'] = _qmarks(attr)

        return self

    def update(self, attr=None, **kw_attr):

        '''

        Build a query with the UPDATE command.

        Parameters can be entered in the forms:

            .update(['colname1', 'colname2'])
            # Produces: ("UPDATE table_name SET colname1=?,colname2=?",)

            .update(['colname1'], colname2='some_value')
            # Produces: ("UPDATE table_name SET colname1=?,colname2=?", [None, 'some_value'])

            .update({'colname': 'some_value'})
            # Produces: ("UPDATE table_name SET colname=?", ['some_value'])

            .update({'colname1': 'value1'}, colname2='value2')
            # Produces: ("UPDATE table_name SET colname1=?,colname2=?", ['value1', 'value2'])

        '''

        attr = _normalize(attr, kw_attr)
        cols, vals = self._escape(_unmap_ordered(attr))
        self._cmd_string = 'UPDATE {table_name} SET {column_mapping}'
        self._fmt_params['column_mapping'] = ', '.join(_COL_MAP.format(c) for c in cols)
        self._values['cmd'] = vals
        return self

    def delete(self):

        '''

        Build a query with the DELETE command.

        '''

        self._cmd_string = 'DELETE FROM {table_name}'
        return self

    def _escape(self, colvals):
        if self.escape_hook:
            escaped = ((self.escape_hook(col), val)
                for col, val in zip(*colvals))
            return zip(
                *filter(lambda x: x[0] is not None, escaped)
            )

        return colvals

    def _where(self, is_any=False, attr=None, **kw_attr):
        attr = _normalize(attr, kw_attr)
        if is_any:
            joiner = ' OR '
        else:
            joiner = ' AND '

        cols, vals = self._escape(_unmap_ordered(attr))
        self._where_string = 'WHERE {where_mapping}'
        self._fmt_params['where_mapping'] = joiner.join(_COL_MAP.format(c) for c in cols)
        self._values['where'] = vals
        return self

    def where_any(self, attr=None, **kw_attr):

        '''

        Build a query with an OR separated list of constraints.

        '''

        return self._where(True, attr, **kw_attr)

    def where_all(self, attr=None, **kw_attr):

        '''

        Build a query with an AND separated list of constraints.

        '''

        return self._where(False, attr, **kw_attr)

    def where(self, attr=None, **kw_attr):

        '''

        Same as `.where_all()`.

        '''

        return self.where_all(attr, **kw_attr)

    @property
    def values(self):
        vals = list(self._values['cmd'] or [])
        if self._values['where']:
            return vals + list(self._values['where'])

        return vals
    
    @property
    def is_complete(self):
        return self._cmd_string and self._fmt_params.get('table_name', None)

    def __str__(self):
        if self._where_string:
            return (self._cmd_string + ' ' + self._where_string).format(**self._fmt_params)

        try:
            return self._cmd_string.format(**self._fmt_params)
        except KeyError:
            return 'Incomplete Query on table: {}'.format(self._fmt_params['table_name'])

    def __repr__(self):
        return str(self)

    def sql(self, table=None, values=None, where=None):

        '''

        Returns a sqlite3 formatted argument list.

        '''

        if values:
            self._values['cmd'] = values

        if where:
            self._values['where'] = where

        if table:
            if self.escape_hook:
                self._fmt_params['table_name'] = self.escape_hook(table)
            else:
                self._fmt_params['table_name'] = table

        return (str(self),) + ((self.values,) or ())


