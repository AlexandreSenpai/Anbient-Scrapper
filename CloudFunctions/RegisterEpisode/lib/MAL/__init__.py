import requests

class AnimeInfo(object):
    def __init__(self, anime: str):
        self._base_url = 'https://kitsu.io/api/edge/anime'

        self.anime = anime

    
    def _get_anime_genres(self, anime_id: str) -> str:
        genre_page_request = requests.get(f'{self._base_url}/{anime_id}/genres')
        if genre_page_request.status_code == 200:
            
            genre_page_response = genre_page_request.json().get('data')
            extracted_genres = [genre.get('attributes').get('name') for genre in genre_page_response]

        return ', '.join(extracted_genres)

    
    def extract(self) -> dict:
        anime_info_request = requests.get(f'{self._base_url}?filter[text]={self.anime}')

        if anime_info_request.status_code == 200:

            anime_info_response = anime_info_request.json().get('data')[0].get('attributes')

            return_object = {
                "title": anime_info_response.get('canonicalTitle'),
                "synopsis": anime_info_response.get('synopsis', ''),
                "en_title": anime_info_response.get('titles', {}).get('en'),
                "score": round(float(anime_info_response.get('averageRating')) / 10, 2),
                "airing": True if anime_info_response.get('status') != 'finished' else False,
                "thumbnail": anime_info_response.get('posterImage', {}).get('original'),
                "banner": anime_info_response.get('coverImage', {}),
                "episodes": anime_info_response.get('episodeCount', 0),
                "tags": None,
                "PV": anime_info_response.get('youtubeVideoId'),
                "genres": self._get_anime_genres(anime_info_request.json().get('data')[0].get('id'))
            }

            return return_object

        else:
            return None

if __name__ == '__main__':
    print(AnimeInfo('zero-no-tsukaima').extract())