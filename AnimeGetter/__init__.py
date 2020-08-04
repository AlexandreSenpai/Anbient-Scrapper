import base64
import re
import time
import uuid
import sys

from bs4 import BeautifulSoup
import requests

from lib.Downloader import AsyncDownloader

class AnimeGetter(object):
    def __init__(self):
        self._BASE_URL = 'https://www.anbient.com'

    def _get_anime_list(self) -> dict:

        '''
            This function digs on anbient list of all animes and returns its informations.
        '''

        anbient_anime_list_request = requests.get(f'{self._BASE_URL}/anime/lista')

        if anbient_anime_list_request.status_code == 200:
            
            soup = BeautifulSoup(anbient_anime_list_request.content, 'html.parser')
            
            return_list = []

            table_list: list = soup.find('tbody', class_='list')
            for anime in table_list.findAll('tr'):
                
                anime_object = {
                    "title": anime.find('td', class_='titulo').find('a')['href'].split('/')[2],
                    "url": anime.find('td', class_='titulo').find('a')['href'],
                    "episodes": anime.find('td', class_='epi').text or 1,
                }

                return_list.append(anime_object)

            return return_list

        else:

            return None

    def _get_zippyshare_downloadable_links(self, zippyshare_file_page: str, url_prefix: str, link_id: int, anime_info: dict) -> dict:

        '''
            This function receives an zippyshare url and digs on zippyshare its zippyshare downloadable links.
        '''
        
        zippyshare_page_request = requests.get(zippyshare_file_page)

        if zippyshare_page_request.status_code == 200:
            soup = BeautifulSoup(zippyshare_page_request.content, 'html.parser')
            
            script_tag = str(soup.findAll('script')[9])
            start = script_tag.find("('dlbutton').href = ") + 20
            end = script_tag.find(';')

            dl_id = None
            file_name = None

            try:

                file_name = str(re.findall(r'"([^"]*)"', script_tag[start:end])[1])

                dl_id = str(re.findall(r'"([^"]*)"', script_tag[start:end])[0]) +\
                str(eval(re.findall(r'\((.*?)\)', script_tag[start:end])[0])) +\
                file_name
                
            except Exception as err:
                print(f'[ERROR] {err}')
            
            if dl_id is not None:
                return {
                    "id": str(uuid.uuid4().hex),
                    "url": f'https://{url_prefix}{dl_id}', 
                    "file": file_name,
                    "episode": link_id + 1,
                    "anime": str(base64.b64encode(bytes(str(anime_info.get("title")).encode('utf-8'))), encoding='utf-8')
                }

        else:
            if zippyshare_page_request.status_code == 500:
                print('[ERROR] Server Error.')
                return None
            else:
                print(zippyshare_page_request.text)
                return None
    
    def _get_zippyshare_file_links(self, anime_info: str) -> list:

        '''
            This function receives an anime information and digs on anbient its zippyshare links.
        '''

        download_queue: list = [None] * int(anime_info.get('episodes', 0))
        retry_time = 5

        anbient_page_request = requests.get(f'{self._BASE_URL}{anime_info.get("url")}')

        if anbient_page_request.status_code == 200:
            soup = BeautifulSoup(anbient_page_request.content, 'html.parser')

            anime_ajax_path: str = base64.b64decode(soup.find('a', class_='ajax padrao')['href']).decode('utf-8')
            ajax_page_request = requests.get(f'{self._BASE_URL}{anime_ajax_path}')

            if ajax_page_request.status_code == 200:

                soup = BeautifulSoup(ajax_page_request.content, 'html.parser')
                has_zippyshare = soup.find('div', class_='zippyshare')

                if has_zippyshare is not None:
                    
                    link_id = 0
                    link_list: list = has_zippyshare.findAll('li')

                    while None in download_queue:
                        for download in link_list:
                            if download_queue[link_id] is None:

                                zippyshare_url: str = download.find('a')['href']
                                url_prefix: str = zippyshare_url.split('/')[2]
                                
                                downloadable_link: dict = self._get_zippyshare_downloadable_links(
                                    zippyshare_file_page=zippyshare_url, 
                                    url_prefix=url_prefix, 
                                    link_id=link_id,
                                    anime_info=anime_info
                                )

                                if downloadable_link is not None:
                                    download_queue[link_id] = downloadable_link
                                    print(download_queue[link_id])
                                
                            link_id = link_id + 1 if link_id + 1 <= int(anime_info.get('episodes', 0)) - 1 else 0
                        
                        if None in download_queue:
                            
                            if retry_time == 15:
                                print('[ERROR] Maximum retries. Leaving the problems back.')
                                break

                            print(f"[INFO] There're some errors. Retrying in {retry_time}sec.")
                            
                            time.sleep(retry_time)
                            retry_time += 5

                else:
                    print('[ERROR] Zippyshare is not avaiable for this anime.')
        
        for item in download_queue:
            if item is not None:
                return download_queue

        return None
        
    def execute(self):

        print("[INFO] Downloading all anime list...")
        
        anime_list: list = self._get_anime_list()

        if anime_list is not None:
            print('[SUCCESS] Done.')
        
        _, anime_id = sys.argv
        anime_id = int(anime_id)

        for anime in anime_list[anime_id:]:
    
            target_anime = self._get_zippyshare_file_links(anime)

            if target_anime is not None:
                with AsyncDownloader(url_list=target_anime) as downloader:
                    print(f'[INFO] {downloader.successes} episodes downloaded with success.')

            percentage = round(float((anime_id/len(anime_list))*100), 2)
            
            print(f'{anime_id} de {len(anime_list)} :: {percentage}%')
            
            anime_id += 1

if __name__ == '__main__':
    AnimeGetter().execute()