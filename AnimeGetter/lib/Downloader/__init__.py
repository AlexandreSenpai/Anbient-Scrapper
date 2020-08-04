from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
import sys
import time

import requests

from ..Storage import Streaming

class AsyncDownloader(object):
    def __init__(self, url_list: list=[]):
        self._processes = cpu_count()
        self._elapsed = 0
        self._url_list = url_list
        self.successes = 0

    def __enter__(self):
        self._start()
        self._elapsed = time.time()
        return self
    
    def __exit__(self, exc_type, *_):
        time_until_complete = round(time.time() - self._elapsed)
        print(f'[INFO] Anime download took {time_until_complete}')

    def save(self, single_url: str):
        if single_url is not None:

            download_episode_request = requests.get(single_url.get('url'), stream=True)

            download_start_time = time.clock()

            total_length: int = int(download_episode_request.headers.get('content-length'))

            download_progress = 0

            if download_episode_request.status_code == 200:
                with Streaming.Save(bucket='animeon-cdn-bucket', blob_name=f'episodes/{single_url.get("id")}', blob_aditional_info=single_url) as cdn:
                    for chunk in download_episode_request.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            cdn.streaming(chunk)
                            download_progress += len(chunk)
                            done = int(50 * download_progress / total_length)

                            sys.stdout.write("\r[%s%s] %s bps - %s" % 
                                ('=' * done, ' ' * (50-done), 
                                download_progress//(time.clock() - download_start_time), 
                                single_url.get("file")[1:])
                            )
                            
                            print('')

                print(f'[SUCCESS] {single_url.get("file")} done.')
                self.successes += 1
    
    def _start(self):
        with ThreadPool(processes=self._processes) as pool:
            pool.map(func=self.save, iterable=self._url_list)
            pool.close()
            pool.join()

