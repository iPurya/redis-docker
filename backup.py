# -*- coding: utf-8 -*-
import redis as r

import tempfile
import gzip
import shutil
import logging
import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import time
import datetime
import contextlib
import os

redis = r.Redis()
logging.basicConfig(filename='backup.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
dbx = dropbox.Dropbox("_B9paEiAkZAAAAAAAAAAAV56R-01a_6LvQ4uIbciTGYhVnxAkFJo1on35A0RV85D")

MAX_CHUNK = 4 * 1024 * 1024
TIMEOUT = 300

def compress():

    # Using bgsave instead save because save command blocks all other clients while saving
    start_time = time.time()
    last_save = redis.lastsave()
    if redis.bgsave():
        while True:
            if redis.lastsave() != last_save:
                # No need to log info about saved, if we didn't got an error that means working successfuly
                break 
            if start_time + TIMEOUT < time.time():
                return logging.error("Timeout elapsed!")
    else:
        return logging.error("BGSAVE raised!")

    temp_file = tempfile.NamedTemporaryFile(suffix=f"-redisbackup.gz")
    rdb_path = '%s/%s' % (redis.config_get('dir')['dir'], redis.config_get('dbfilename')['dbfilename'])
    with open(rdb_path, 'rb') as f_in:
        with gzip.open(temp_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    temp_file.seek(0)
    return temp_file


def main():
    pass

if __name__ == "__main__":
    main()