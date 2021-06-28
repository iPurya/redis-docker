# -*- coding: utf-8 -*-
import redis as r

import tempfile
import gzip
import shutil
import logging
import sys
import dropbox
import time
import datetime
import contextlib
import os
import config

redis = r.Redis()
rdb_path = '%s/%s' % (redis.config_get('dir')['dir'], redis.config_get('dbfilename')['dbfilename'])
rdb_path = 'dump.rdb'


logging.basicConfig(filename='backup.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO if config.LOGGING else logging.CRITICAL)
dbx = dropbox.Dropbox(config.DROPBOX_TOKEN)

MAX_CHUNK = 4 * 1024 * 1024
TIMEOUT = 300

def save_redis():

    # Using bgsave instead save because save command blocks all other clients while saving
    start_time = time.time()
    last_save = redis.lastsave()
    if redis.bgsave():
        while True:
            if redis.lastsave() != last_save:
                # No need to log info about saved, if we didn't got an error that means working successfuly
                break 
            if start_time + TIMEOUT < time.time():
                logging.error("Timeout elapsed!")
                return False
    else:
        logging.error("BGSAVE raised!")
        return False
    return True

def compress_file(file_path):

    temp_file = tempfile.NamedTemporaryFile(suffix=f"-redisbackup.gz")

    with open(file_path, 'rb') as f_in:
        with gzip.open(temp_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    temp_file.seek(0)
    return temp_file

def upload(file_path,compress=False):
    
    upload_path = "/redis/"
    if compress:
        file = compress_file(file_path)
        upload_path += f"backup{int(time.time())}.gz"
    else:
        file = open(file_path,"rb")
        upload_path += "dump.rdb"


    try:
        file_size = os.stat(file_path).st_size
        logging.debug(f"Uploading file {file_path} size {file_size}")
        with file as f:
            
            if file_size <= MAX_CHUNK:
                dbx.files_upload(
                    f.read(), upload_path, dropbox.files.WriteMode.overwrite
                )
            else:
                session_start = dbx.files_upload_session_start(
                    f.read(MAX_CHUNK)
                )
                cursor = dropbox.files.UploadSessionCursor(
                    session_start.session_id,
                    offset=f.tell()
                )
                # Commit contains path in Dropbox and write mode about file
                commit = dropbox.files.CommitInfo(upload_path, dropbox.files.WriteMode.overwrite)

                while f.tell() < file_size:
                    if (file_size - f.tell()) <= MAX_CHUNK:
                        dbx.files_upload_session_finish(
                            f.read(MAX_CHUNK),
                            cursor,
                            commit
                        )
                    else:
                        dbx.files_upload_session_append(
                            f.read(MAX_CHUNK),
                            cursor.session_id,
                            cursor.offset
                        )
                        cursor.offset = f.tell()
            
            
        logging.info(f"File {upload_path} uploaded successfully!")
        return True
    except dropbox.exceptions.ApiError as e:
        if (err.error.is_path() and
            err.error.get_path().reason.is_insufficient_space()):
            logging.error("Cannot back up; insufficient space.")
    except dropbox.exceptions.HttpError as e:
        logging.error(e)
    return False
def main():
    #if not save_redis(): return

    # Trying to makedir for redis backups
    try: 
        dbx.files_create_folder_v2("/redis")
        logging.info("Redis Folder created.")
    except: pass

    upload(rdb_path)
    upload(rdb_path,compress=True)
    

if __name__ == "__main__":
    main()