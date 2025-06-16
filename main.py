# Upstox NSE Instrument Data ETL

# 1. Download data from url (typically csv files)
import os
import sys 
import requests 
import warnings
warnings.filterwarnings("ignore")
import pandas as pd 
import io 
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError 
from sqlite3 import Connection, connect 
from dotenv import dotenv_values 
from pathlib import Path



from loggy import setup_logging

from transformations import filter_normalize, extract_df
from urlDownload import download_file
from sqlite_operations import upsert_sqlite_using_key
from mongo_operations import upsert_mongodb_using_key 


def main(config,logger):
    
    upstox_nse = download_file(config['UPSTOX_NSE_INSTRUMENT_URL'],logger=logger)
    dhan_scrip = download_file(config['DHAN_SCRIP_MASTER_URL'],logger=logger)
    if upstox_nse.empty or dhan_scrip.empty:
        logger.error("Failed to download one or both datasets. Exiting.")
        return 
        # 1. (i) Filter and normalize Upstox NSE data:


        # 2. (i) Filter only NSE Equity instruments: 
        # 
        #         - Upstox: exchange == "NSE" and instrument_type == "EQ" 
        # 
        #         - Dhan: SEM_EXM_EXCH_ID == "NSE" and SEM_INSTRUMENT_NAME == "EQUITY" 
        #         
        #         - Normalize trading_symbol for joining (e.g., trim and uppercase) 

    upstox = filter_normalize(df=upstox_nse,
                              exchange_col=config['UPSTOX_EXCHANGE_COL'], 
                              instrument_type_col=config["UPSTOX_INSTRUMENT_TYPE_COL"], 
                              exchange_value=config['UPSTOX_EXCHANGE_VALUE'], 
                              instrument_type_value=config['UPSTOX_INSTRUMENT_TYPE_VALUE'],
                              logger = logger)
    dhan = filter_normalize(df = dhan_scrip, 
                            exchange_col=config['DHAN_EXCHANGE_COL'], 
                            instrument_type_col=config["DHAN_INSTRUMENT_TYPE_COL"], 
                            exchange_value=config['DHAN_EXCHANGE_VALUE'], 
                            instrument_type_value=config['DHAN_INSTRUMENT_TYPE_VALUE'],
                            logger=logger)
    
    logger.info(f"Size of Upstox:{upstox.shape[0]}")
    logger.info(f"Size of Dhan:{dhan.shape[0]}")
    
    # 3.  Load 
    # - MongoDB: 
    #   - Store filtered Upstox data as JSON in market_data.upstox_nse 
    #   - Upsert using instrument_key 
    # - SQL (PostgreSQL or SQLite): 
    #   - Store filtered Dhan data in a table called dhan_nse 
    #   - Upsert using security_id or trading_symbol 

    mongo_connection_url = config['MONGO_CONNECTION_URL']
    mongo_db_name = config['MONGO_DB_NAME'] 
    mongo_collection_name = config['MONGO_COLLECTION_NAME']

    sqlite_db_location = config['SQLITE_DB_LOCATION']
    sqlite_db_name = config['SQLITE_DB_NAME'] 
    sqlite_table_name = config['SQLITE_TABLE_NAME'] 
    
    sqlite_connection_url = f"{os.path.join(os.path.abspath(sqlite_db_location), sqlite_db_name)}"
    if not os.path.exists(sqlite_connection_url):
        os.makedirs(sqlite_connection_url)

    
    logger.info(f"sqllite_connection_url:{sqlite_connection_url}")

    # Upsert Upstox data into MongoDB
    client = MongoClient(mongo_connection_url)
    upsert_mongodb_using_key(df=upstox,
                            client=client,
                            db_name=mongo_db_name,
                            collection_name=mongo_collection_name, 
                            upsert_key_column='instrument_key',
                            logger=logger)  
    logger.info(f"MongoDB upsert completed !!! :)")
    # Upsert Dhan data into SQLite
    conn = connect(sqlite_connection_url)   
    upsert_sqlite_using_key(df=dhan, 
                            db_name=sqlite_db_name, 
                            table_name=sqlite_table_name,
                            conn=conn, 
                            upsert_key_column='SEM_SMST_SECURITY_ID',
                            logger=logger)

    logger.info(f"Sqlite upsert completed !!! :)")
    
    # 2. (ii) Extract and map only the following fields: 
    #             - exchange (static: "NSE") 
    #             - instrument_key (from Upstox) 
    #             - symbol_name (from Dhan → SM_SYMBOL_NAME) 
    #             - security_id (from Dhan → SEM_SMST_SECURITY_ID) 
    #             - short_name (from Upstox) -- Column not found
    #             - name (from Upstox) 
    #             - isin (from Upstox) -- Column not found
    #             - trading_symbol (from both, used as join key)
    
    # 3.Extracted DataFrames:

    common_stocks, upstox_stocks_only, dhan_stocks = extract_df(
        df1=upstox, 
        df2=dhan, 
        on_col='tradingsymbol', 
        filter_columns=['exchange', 'instrument_key', 'symbol_name', 'security_id','name', 'tradingsymbol'],
        logger=logger,
        output_path=config['OUTPUT_PATH'] 
    )
    logger.info(f"Common Stocks: {len(common_stocks)}")
    logger.info(f"Upstox Stocks Only: {len(upstox_stocks_only)}")   
    logger.info(f"Dhan Stocks: {len(dhan_stocks)}")
    
    return "ETL completed successfully."

if __name__ == "__main__":
    config = dotenv_values("./.env")
    logger = setup_logging(log_path = config['LOG_PATH'])
    try:
        import datetime
        start = datetime.datetime.now()
        logger.info(f"ETL Started at time:{start}")
        result = main(config=config,logger=logger) 
        logger.info(result)
        end = datetime.datetime.now()
        logger.info(f"ETL Ended at time:{end}")
        logger.info(f"Time taken to finish the process of ETL:{end-start}")
    except Exception as e:  
        logger.error(f"An error occurred: {e}",exc_info=True)
        sys.exit(1)