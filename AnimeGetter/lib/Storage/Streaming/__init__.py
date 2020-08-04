from google.cloud import storage
from google.resumable_media import requests, common
from google.auth.transport.requests import AuthorizedSession
from pyasn1.type.univ import Boolean
from requests import get

class Save(object):
    def __init__(self, bucket: str, blob_name: str, blob_aditional_info: dict={}, chunk_size: int=1024 * 1024):
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket)
        self._blob = self._bucket.blob(blob_name)
        self._blob_aditional_info = blob_aditional_info

        self._buffer = b''
        self._chunk_size = chunk_size
        self._buffer_size = 0
        self._read = 0

        self._transport = AuthorizedSession(
            credentials=self._client._credentials
        )
        self._request = None

    def __enter__(self):
        self._start()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self._stop()

    def _check_if_bucket_exists(self) -> Boolean:

        if not self._bucket.exists():
            print('[ERROR] Inexistent bucket.')
            return False
        
        return True
    
    def _start(self):
        if self._check_if_bucket_exists():
            url = (
                f'https://www.googleapis.com/upload/storage/v1/b/'
                f'{self._bucket.name}/o?uploadType=resumable'
            )
            self._request = requests.ResumableUpload(
                upload_url=url, chunk_size=self._chunk_size
            )
            self._request.initiate(
                transport=self._transport,
                content_type='video/mp4',
                stream=self,
                stream_final=False,
                metadata={
                    'name': self._blob.name,
                    'metadata': {
                        'id': str(self._blob_aditional_info.get('id')),
                        'anime': str(self._blob_aditional_info.get('anime')),
                        'episode': str(self._blob_aditional_info.get('episode'))
                    }
                },
            )
        else:
            raise Exception

    def _stop(self):
        self._request.transmit_next_chunk(self._transport)

    def streaming(self, data: bytes) -> int:
        data_len = len(data)
        self._buffer_size += data_len
        self._buffer += data
        del data
        while self._buffer_size >= self._chunk_size:
            try:
                self._request.transmit_next_chunk(self._transport)
            except common.InvalidResponse:
                self._request.recover(self._transport)
        return data_len

    def read(self, chunk_size: int) -> bytes:
        to_read = min(chunk_size, self._buffer_size)
        memview = memoryview(self._buffer)
        self._buffer = memview[to_read:].tobytes()
        self._read += to_read
        self._buffer_size -= to_read
        return memview[:to_read].tobytes()

    def tell(self) -> int:
        return self._read
        

if __name__ == '__main__':
    req = get('https://www.drupal.org/files/project-images/file_resup_step_3_0.png', stream=True)
    client = storage.Client()
    with Save(bucket='animeon-cdn-bucket', blob_name='img.jpg') as cdn:
        for chunk in req.iter_content(chunk_size=1024 * 1024):
            if chunk:
                cdn.streaming(chunk)