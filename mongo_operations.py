import os
import pandas as pd 
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError   
def create_collection(client,db_name, collection_name,logger):
    '''Create a new collection in MongoDB'''
    db = client[db_name]
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        logger.info(f"Collection '{collection_name}' created successfully.")
    else:
        logger.info(f"Collection '{collection_name}' already exists.")
        
        
def upsert_mongodb_using_key(df,client,db_name,collection_name,upsert_key_column,logger):
    '''Upsert a dataframe into MongoDB using a specified key'''
    logger.info(f"Upserting DataFrame into MongoDB collection '{collection_name}' in database '{db_name}' using key '{upsert_key_column}'")
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input df must be a pandas DataFrame.")    
    if not client:
        raise ValueError("MongoDB client is not connected. Please provide a valid MongoDB client.")
    if not db_name:
        raise ValueError("Database name is not provided. Please specify a valid database name.")
    if not collection_name:
        raise ValueError("Collection name is not provided. Please specify a valid collection name.")
    if not upsert_key_column:   
        raise ValueError("Upsert key column is not provided. Please specify a valid upsert key column.")
    if df.empty:
        raise ValueError("Input DataFrame is empty. Please provide a valid DataFrame with data to upsert.")
    if not isinstance(upsert_key_column, str):
        raise ValueError("Upsert key column must be a string representing the column name.")
    if upsert_key_column not in df.columns:
        raise ValueError(f"Upsert key column '{upsert_key_column}' does not exist in the DataFrame.")   
    db = client[db_name]
    if collection_name not in db.list_collection_names():
        logger.info(f"Collection '{collection_name}' does not exist. Creating new collection.")
        collection = create_collection(client, db_name, collection_name,logger)
    else:
        logger.info(f"Collection '{collection_name}' already exists. Proceeding with upsert operation.")
        collection = db[collection_name]
    
    if df.empty:
        logger.info("Warning: The DataFrame is empty. No data to upsert.")
        return
    else: 
        records = df.to_dict(orient='records')
        logger.info(f"DataFrame contains {len(records)} rows and {len(df.columns)} columns.")
    
    if upsert_key_column not in df.columns:
        raise ValueError(f"Upsert key column '{upsert_key_column}' does not exist in the DataFrame.")
    
    if not records:
        logger.info("Warning: No records to upsert. The DataFrame may be empty or contain no valid data.")
        return
        
        
    logger.info(f"Attempting to store/upsert {len(records)}  data entries...")

    # Perform upsert operation for each record
    operations = []
    for record in records:
        # Ensure the upsert key exists in the row
        filter_query = {upsert_key_column: record[upsert_key_column]}
        update_doc = {"$set": record}
        operations.append(UpdateOne(filter_query, update_doc, upsert=True))
    
    if operations:
        try:
            result = collection.bulk_write(operations)
            logger.info(f"Upserted {result.upserted_count} new documents and modified {result.modified_count} existing documents.")
        except Exception as e:
            logger.info(f"Error during bulk upsert: {e}")

    client.close() 
    logger.info(f"Upsert operation completed successfully for collection '{collection_name}' in database '{db_name}'.")
    return True