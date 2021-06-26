# -*- coding: utf-8 -*-
import redis as r

import logging
from time import time

redis = r.Redis()
logging.basicConfig(filename='backup.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')

TIMEOUT = 300

def main():

    # Using bgsave instead save because save command blocks all other clients while saving
    start_time = time()
    last_save = redis.lastsave()
    if redis.bgsave():
        while True:
            if redis.lastsave() != last_save:
                break
            if start_time + TIMEOUT < time():
                logging.error("Timeout elapsed!")
                return            
    else:
        logging.error("bgsave raised!")

if __name__ == "__main__":
    main()