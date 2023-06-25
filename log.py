import logging
import sys
from datetime import datetime

PATH_TIME = "log/" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"

log_file = PATH_TIME
log_fh = logging.FileHandler(log_file)
log_sh = logging.StreamHandler(sys.stdout)
log_format = '%(asctime)s: %(message)s'
# Possible levels: DEBUG, INFO, WARNING, ERROR, CRITICAL    
log_level = 'INFO' 
logging.basicConfig(format=log_format, level=log_level, 
    handlers=[log_sh, log_fh])