import requests

class Search(object):
    def __init__(self, query: str, key: str):
        self._key = key
        self._base_url = f'https://www.googleapis.com/customsearch/v1?key={self._key}&cx=003161414223777051064:0mj8wjajmco&q={query}-wallpaper-desktop&imgSize=huge&searchType=image'

    def execute(self):
        
        req = requests.get(self._base_url)

        if req.status_code == 200:
            return req.json().get('items', [])[0].get('link')