import os 
import logging 

def setup_logging(log_path):
    log_path_ = os.path.join(os.path.abspath(log_path),"datahat.log")
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s,%(msecs)d %(levelname)-8s [%(pathname)s:%(lineno)d]     %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        handlers=[
            logging.FileHandler(log_path_),
            logging.StreamHandler()
        ]           
    )
    logger = logging.getLogger("datahat")       
    logger.setLevel(logging.INFO)
    return logger