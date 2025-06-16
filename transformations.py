import os 
def filter_normalize(df, exchange_col, instrument_type_col, exchange_value, instrument_type_value,logger):
    '''Filter instruments based on exchange and instrument type'''
    logger.info(f"Filtering DataFrame for exchange: {exchange_value} and instrument type: {instrument_type_value}")
    if exchange_col not in df.columns or instrument_type_col not in df.columns:
        logger.error(f"Columns {exchange_col} or {instrument_type_col} not found in DataFrame")
        raise ValueError(f"Columns {exchange_col} or {instrument_type_col} not found in DataFrame") 
    elif exchange_value not in df[exchange_col].unique() or instrument_type_value not in df[instrument_type_col].unique():
        logger.error(f"Values {exchange_value} or {instrument_type_value} not found in DataFrame")
        raise ValueError(f"Values {exchange_value} or {instrument_type_value} not found in DataFrame")
    else:
        df = df[(df[exchange_col] == exchange_value) & (df[instrument_type_col] == instrument_type_value)]
        if "tradingsymbol" in df.columns:
            df['tradingsymbol'] = df['tradingsymbol'].apply(lambda x: x.strip()) 
            df['tradingsymbol'] = df['tradingsymbol'].str.upper()
        elif 'SEM_TRADING_SYMBOL' in df.columns:
            df.rename(columns={'SEM_TRADING_SYMBOL': 'tradingsymbol'}, inplace=True)
            df['tradingsymbol'] = df['tradingsymbol'].apply(lambda x: x.strip())
            df['tradingsymbol'] = df['tradingsymbol'].str.upper()
        else:
            logger.error("Column 'tradingsymbol' or 'SEM_TRADING_SYMBOL' not found in DataFrame")
            raise ValueError("Column 'tradingsymbol' or 'SEM_TRADING_SYMBOL' not found in DataFrame")

        return df 


def extract_df(df1, df2, on_col,filter_columns,logger,output_path):
    '''Merge two dataframes on a specified column'''
    output_path_ = os.path.abspath(output_path)
    if not os.path.exists(output_path_):
        os.makedirs(output_path_)
    logger.info(f"Merging DataFrames on column: {on_col}")
    if on_col not in df1.columns or on_col not in df2.columns:
        logger.error(f"Column {on_col} not found in one of the DataFrames")
        raise ValueError(f"Column {on_col} not found in one of the DataFrames")
    else:
        logger.info(f"Removing the duplicates in {on_col}")
        df1_duplicates = df1.duplicated(subset=[on_col]).sum()
        logger.info(f"Removing the duplicates { df1_duplicates} in {on_col} first dataframe")
        df2_duplicates = df2.duplicated(subset=[on_col]).sum()
        logger.info(f"Removing the duplicates{ df2_duplicates} in {on_col} second dataframe")
        df1.drop_duplicates(subset=[on_col], inplace=True) 
        df2.drop_duplicates(subset=[on_col], inplace=True) 
        merged_df = df1.merge(df2, how='outer', on=on_col, suffixes=('_df1', '_df2'), indicator=True) 
        merged_df.rename(columns={
            'SM_SYMBOL_NAME': 'symbol_name',
            'SEM_SMST_SECURITY_ID': 'security_id',
        }, inplace=True)
        # Filter matched records
        matched = merged_df[merged_df['_merge'] == 'both']
        matched = matched[filter_columns]
        matched.to_csv(os.path.join(output_path,"common_stocks.csv"), index=False)
        # Filter upstox stocks only
        upstox_stocks_only = merged_df[merged_df['_merge'] == 'left_only']
        upstox_stocks_only = upstox_stocks_only[filter_columns]
        upstox_stocks_only.to_csv(os.path.join(output_path,"only_in_upstox.csv"), index=False)
        # Filter dhan stocks only
        dhan_stocks = merged_df[merged_df['_merge'] == 'right_only']    
        dhan_stocks = dhan_stocks[filter_columns]
        dhan_stocks.to_csv(os.path.join(output_path,"only_in_dhan.csv"), index=False)
        return matched, upstox_stocks_only, dhan_stocks 