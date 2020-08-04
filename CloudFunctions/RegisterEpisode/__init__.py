import base64
import os
import datetime

import requests

from lib.Bigquery import Bigquery
from lib.MAL import AnimeInfo
from lib.Google.Images import Search

def main(data, context):
    if data['contentType'] == 'video/mp4':
        anime_id = data['metadata']['id']
        episode = int(data['metadata']['episode'])
        media_link = f'https://storage.googleapis.com/animeon-cdn-bucket/episodes/{anime_id}'
        episode_thumbnail = 'https://i.nhentai.net/galleries/1691723/2.jpg'
        preview = 'https://i.nhentai.net/galleries/1691723/2.jpg'

        preview_req = requests.post('https://us-central1-animeon.cloudfunctions.net/ThumbGenerator', {"videoUrl": media_link, "title": anime_id})

        if preview_req.status_code == 200:
            episode_thumbnail = f'https://storage.googleapis.com/animeon-cdn-bucket/thumbnail/{anime_id}.png'
            preview = f'https://storage.googleapis.com/animeon-cdn-bucket/thumbnail/{anime_id}.gif'

        father_info = {
            'id': data['metadata']['anime'],
            'title': base64.b64decode(data['metadata']['anime']).decode('utf-8'),
        }

        MAL: dict = AnimeInfo(father_info.get('title')).extract()

        if MAL.get('banner') is None:
            MAL['banner'] = Search(query=father_info.get('title'), key=os.getenv('images_key')).execute()
        else:
            MAL['banner'] = MAL.get('banner').get('original')

        data = [
            datetime.datetime.now(),
            anime_id,
            father_info.get('id'),
            0,
            0,
            0,
            episode_thumbnail,
            preview,
            episode,
            media_link
        ]

        with Bigquery(dataset="animeon_animes_test", table="episodes", father_info={**father_info, **MAL}) as repo:
            repo.insert(row=data)
