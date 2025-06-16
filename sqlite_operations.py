import sqlite3 
import pandas as pd 

def sqlite_table_check(table_name,cursor):
    listOfTables = cursor.execute(
    f"""SELECT name FROM sqlite_master WHERE type='table' 
    AND name="{table_name}"; """).fetchall()

    if listOfTables == []:
        return False
    else:
        return True 

def create_sqlite_schema(df,upsert_key_column):
    # Create a dynamic list of column definitions for the CREATE TABLE statement
    column_definitions = []
    for col in df.columns:
        col_type = 'TEXT' # Default
        if pd.api.types.is_integer_dtype(df[col]):
            col_type = 'INTEGER'
        elif pd.api.types.is_float_dtype(df[col]):
            col_type = 'REAL'
        if col == upsert_key_column:
            col_type += ' PRIMARY KEY' 
        elif col == 'trading_symbol':
            col_type += ' UNIQUE'
        column_definitions.append(f"{col} {col_type}")
    return column_definitions



def upsert_sqlite_using_key(df, db_name, table_name, conn,upsert_key_column,logger):
    '''Upsert a dataframe into SQLite using a specified key'''
    cursor = conn.cursor()
    logger.info(f"Upserting DataFrame into SQLite table '{table_name}' in database '{db_name}' using key '{upsert_key_column}'")
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input df must be a pandas DataFrame.")    
    if not db_name:
        raise ValueError("Database name is not provided. Please specify a valid database name.")    
    if not table_name:
        raise ValueError("Table name is not provided. Please specify a valid table name.")  
    if not cursor:
        raise ValueError("SQLite cursor is not connected. Please provide a valid SQLite cursor.")   
    if not upsert_key_column:
        raise ValueError("Upsert key column is not provided. Please specify a valid upsert key column.")
    if not isinstance(upsert_key_column, str):
        raise ValueError("Upsert key column must be a string representing the column name.")
    if df.empty:
        raise ValueError("Input DataFrame is empty. Please provide a valid DataFrame with data to upsert.") 
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input df must be a pandas DataFrame.")    
    if not table_name:
        raise ValueError("Table name is not provided. Please specify a valid table name.")
    if upsert_key_column not in df.columns:
        raise ValueError(f"Upsert key column '{upsert_key_column}' does not exist in the DataFrame.")
    if not sqlite_table_check(table_name, cursor):
        logger.info(f"Table '{table_name}' does not exist. Creating new table.")
        # Create table if it does not exist
        column_definitions = create_sqlite_schema(df, upsert_key_column)
        create_table_sql = f""" 
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(column_definitions)}
                );
            """
        logger.info(f"Creating table '{table_name}'")
        cursor.execute(create_table_sql)
    else:
        logger.info(f"Table '{table_name}' already exists. Proceeding with upsert operation.")
    
    if df.empty:
        logger.info("Warning: The DataFrame is empty. No data to upsert.")
        return
    
    logger.info(f"Attempting to store/upsert {df.shape[0]} data entries...")

    # Prepare data for executemany (values only)
    columns_for_insert = df.columns.tolist()
    placeholders = ', '.join(['?'] * len(columns_for_insert))
    
    # Use INSERT OR REPLACE for batch upsert
    sql_insert_or_replace = f"""
        INSERT OR REPLACE INTO {table_name} ({', '.join(columns_for_insert)})
        VALUES ({placeholders})
    """
    
    data_tuples = [tuple(row.values) for _, row in df[columns_for_insert].iterrows()]
    
    cursor.executemany(sql_insert_or_replace, data_tuples)
    conn.commit()
    successful_upserts = cursor.rowcount
    logger.info(f"SQLite batch upsert successful: {successful_upserts} rows affected.")
    cursor.close()
    conn.close()
        