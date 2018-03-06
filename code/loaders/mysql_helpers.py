import sqlalchemy as sa
import time
import re


# Replace generalizable sql class placeholder
def get_mysql_field_types():
    """
    List out possible MySQL column types

    :return: list of str possible MySQL column types
    """
    t = ['BIGINT'
        , 'BIT'
        , 'CHAR'
        , 'DATETIME'
        , 'DECIMAL'
        , 'DOUBLE'
        , 'FLOAT'
        , 'INTEGER'
        , 'LONGBLOB'
        , 'LONGTEXT'
        , 'MEDIUMBLOB'
        , 'MEDIUMINT'
        , 'MEDIUMTEXT'
        , 'NCHAR'
        , 'NUMERIC'
        , 'NVARCHAR'
        , 'REAL'
        , 'SMALLINT'
        , 'TINYINT'
        , 'TEXT'
        , 'TIME'
        , 'TIMESTAMP'
        , 'VARCHAR'
        , 'YEAR']
    return(t)


def get_sa_eng(user, password, host, db):
    """
    Get sqlalchemy.engine.base.Engine object from user/database information

    :param user: str database username
    :param password: str database user password
    :param host: str name of database host server
    :param db: str name of MySQL database
    :return: sqlalchemy.engine object
    """

    eng_str = 'mysql+mysqlconnector://' + user + ':' + password + '@' + host + '/' + db
    eng = sa.engine.create_engine(eng_str)
    return(eng)


# Replace generalizable sql class placeholder
def get_mysql_table_schema(engine, table):
    """
    Get table schema from a MySQL table

    :param engine: sqlalchemy.engine.base.Engine
    :param table: str name of table in database
    :return: dictionary, keys are field names, values are dictionaries
    {'type': str SQL type, 'size': int field bytes}
    """
    inspector = sa.inspect(engine)
    column_types = get_mysql_field_types()
    schema_dict = dict()

    for field in inspector.get_columns(table):
        schema_dict[field['name']] = dict()
        schema_dict[field['name']]['type'] = [x for x in column_types if re.search(x, str(field['type']))]
        schema_dict[field['name']]['type'] = max(schema_dict[field['name']]['type'], key=len)
        if 'display_width' in dir(field['type']):
            schema_dict[field['name']]['size'] = int(field['type'].display_width)
        elif 'length' in dir(field['type']):
            schema_dict[field['name']]['size'] = int(field['type'].length)

    return(schema_dict)


def get_table_primary_keys(engine, table):
    """
    Get names of primary key field from a SQL table

    :param engine: sqlalchemy.engine.base.Engine
    :param table: str name of table in database
    :return: list of str names of primary keys of a SQL table
    """
    db = str(engine.url).split('/')[-1]
    query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '%s' " \
            "AND TABLE_NAME = '%s' AND COLUMN_KEY = 'PRI'" % (db, table)
    pk_list = list(map(lambda x: x[0], engine.execute(query).fetchall()))
    return(pk_list)


def get_staging_table_name(table):
    """
    Create name for a staging table by appending '_[unix datetime]'
    to the name of the table being staged for CRUD

    :param table: str name of table in database
    :return: str `table_[unix datetime]`
    """
    staging_table_name = table + '_' + str(int(time.time()))
    return(staging_table_name)


def make_staging_table(df, conn, name, verbose=True):
    """
    Upload a pandas.DataFrame to a MySQL database.
    Will replace any table in the database whose name is same as `name` parameter

    :param df: pandas.DataFrame for upload to the database
    :param conn: sqlalchemy.engine.base.Connection
    :param name: str name of table to give the DataFrame once in the database
    :param verbose: boolean indicator for whether to print message about the upload
    :return: None
    """
    if verbose:
        print('Moving %d rows into staging table %s' % (df.shape[0], name))

    df.to_sql(name
              , con=conn
              , if_exists='replace'
              , index=False)


def drop_table(conn, table, verbose=True):
    """
    Drop a table in an RDBMS database

    :param conn: sqlalchemy.engine.base.Connection
    :param table: str name of table to drop
    :param verbose: boolean indicator for whether to print the SQL to be executed
    :return: None
    """
    drop_stmt = 'DROP TABLE {0}'.format(table)

    if verbose:
        print('Executing SQL DROP statement:')
        print(drop_stmt)

    trans = conn.begin()
    try:
        conn.execute(drop_stmt)
        trans.commit()
    except:
        trans.rollback()
        raise


# TODO: make this RDBMS-agnostic
# TODO: add schema specification to this
def insert(df, engine, table, id_fields, verbose=True):
    """
    Insert data into a SQL table with data in a pandas.DataFrame by running a
    statement "INSERT INTO table_1 t1 (SELECT `fields` FROM table_2 t2
    WHERE NOT EXISTS (SELECT * FROM t2 WHERE `t1.id_fields = t2.id_fields`);"

    :param df: pandas.DataFrame to use for data update
    :param engine: sqlalchemy.engine.base.Engine
    :param table: str name of table in the database to be updated
    :param id_fields: str or list of str fields in table used to identify unique data instances (rows)
    :param fields: list of str fields to be updated in table.
    :param verbose: boolean indicator for whether SQL UPDATE statement should be printed
    :return: list primary key values inserted into table
    """
    if type(id_fields) == str:
        id_fields = [id_fields]

    table_schema = get_mysql_table_schema(engine, table=table)
    staging_table_name = get_staging_table_name(table=table)
    inserted_pk_ids = None

    # ensure id_fields are legit
    table_fields = list(table_schema.keys())
    missing_id_fields = list(set(id_fields) - set(table_fields))
    missing_id_fields += list(set(id_fields) - set(df.columns))
    if missing_id_fields:
        raise ValueError('These fields are not in the %s table: %s' % (table, ', '.join(missing_id_fields)))
    primary_keys = get_table_primary_keys(engine, table=table)

    # Subset insert to just fields supplied in df
    fields = list(set(table_fields).intersection(set(df.columns)))

    # construct insert statement
    insert_stmt = 'INSERT INTO {0} ('.format(table) + ', '.join(fields) + ') SELECT '
    insert_stmt += '{0} FROM {1} t2'.format(', '.join(fields), staging_table_name)

    if id_fields:
        id_fields = list(set(id_fields))
        insert_stmt += ' WHERE NOT EXISTS (SELECT * FROM ' + table + ' WHERE '
        insert_stmt += ' AND '.join(table + '.' + field + ' = t2.' + field for field in id_fields)
        insert_stmt += ')'

    # Connect to database, upload data to staging
    conn = engine.connect()
    make_staging_table(df
                       , conn=conn
                       , name=staging_table_name)

    if verbose:
        print('Executing SQL INSERT statement:')
        print(insert_stmt)

    # SQL transaction block
    trans = conn.begin()
    try:
        conn.execute(insert_stmt)

        # construct *RETURNING*-like primary key returning phrase for MySQL database
        if engine.name.lower() == 'mysql' and len(primary_keys) == 1:
            last_insert_pk_id = conn.execute('SELECT LAST_INSERT_ID() FROM %s LIMIT 1;' % table).fetchall()[0][0]
            max_pk_id = conn.execute('SELECT MAX(%s) FROM %s LIMIT 1;' % (primary_keys[0], table)).fetchall()[0][0]
            if max_pk_id - last_insert_pk_id <= df.shape[0]:
                inserted_pk_ids = list(range(last_insert_pk_id, max_pk_id + 1))

        trans.commit()
        drop_table(conn
                   , table=staging_table_name)
    except Exception as e:
        trans.rollback()
        drop_table(conn
                   , table=staging_table_name)
        print(e)
        raise

    conn.close()

    return(inserted_pk_ids)


def update(df, engine, table, id_fields, fields='all', verbose=True):
    """
    Update data in a MySQL table with data in a pandas.DataFrame by running a
    statement "UPDATE table_1 INNER JOIN table_2 ON `id_fields = table2.id_fields`
    SET table_1.fields = table_2.fields"

    :param df: pandas.DataFrame to use for data update
    :param engine: sqlalchemy.engine.base.Engine
    :param table: name of table in the database where data will be updated
    :param id_fields: fields in table used to identify unique data instances (rows)
    :param fields: list of str or str, names fields to be updated in table.
    If `all`, all fields in df will be updated in table.
    :param verbose: boolean indicator for whether SQL UPDATE statement should be printed
    :return: None
    """
    table_schema = get_mysql_table_schema(engine, table=table)
    table_fields = list(table_schema.keys())
    staging_table_name = get_staging_table_name(table=table)
    primary_keys = get_table_primary_keys(engine, table=table)

    # Cast id_fields and fields as lists
    if type(id_fields) == str:
        id_fields = [id_fields]

    if type(fields) == list:
        fields = list(set(fields) - set(primary_keys))

    elif fields == 'all':
        fields = list(set(table_fields) - set(primary_keys))

    elif type(fields) == str:
        fields = [fields]

    # Subset update to just fields supplied in df
    fields = list(set(table_fields).intersection(set(df.columns)))

    # ensure id_fields are legit
    missing_id_fields = list(set(id_fields) - set(table_fields))
    missing_id_fields += list(set(id_fields) - set(df.columns))
    if missing_id_fields:
        raise ValueError('These fields are not in the %s table: %s' % (table, ', '.join(missing_id_fields)))

    # construct update statement: where id_field = staging_table.id_field
    update_stmt = 'UPDATE {0} INNER JOIN {1} ON '.format(table, staging_table_name)
    for field in id_fields:
        update_stmt += (table + '.' + field + ' = ' + staging_table_name + '.' + field)
        if field != id_fields[0]:
            update_stmt += ', '

    if fields:
        update_stmt += ' SET ' + ', '.join([table + '.' + field + ' = ' + staging_table_name
                                            + '.' + field for field in fields])
    # Connect to database, upload data to staging
    conn = engine.connect()
    make_staging_table(df
                       , conn=conn
                       , name=staging_table_name)

    if verbose:
        print('Executing SQL UPDATE statement:')
        print(update_stmt)

    # SQL transaction block
    trans = conn.begin()
    try:
        conn.execute(update_stmt)
        trans.commit()
        drop_table(conn
                   , table=staging_table_name)
    except Exception as e:
        trans.rollback()
        drop_table(conn
                   , table=staging_table_name)
        print(e)
        raise

    conn.close()