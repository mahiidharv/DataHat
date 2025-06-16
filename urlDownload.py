import requests 
import pandas as pd 
import io 
def download_file(url, logger=None):
    '''Download a file from a given URL and read it content into a dataframe'''
    logger.info(f"Downloading file from {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200: 
            urlData = response.content
            if url.endswith('.csv'):
                return pd.read_csv(io.StringIO(urlData.decode('utf-8')))
            elif url.endswith('.csv.gz'):
                return pd.read_csv(io.BytesIO(urlData), compression='gzip')
            else:
                raise ValueError("Unsupported file format. Only .csv and .csv.gz are supported.")
                return pd.DataFrame()
        else:
            raise Exception(f"Failed to download file from {url}, status code: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {e}")
        return pd.DataFrame() 