import datetime

from google.cloud import bigquery

class Bigquery(object):
    def __init__(self, dataset: str, table: str, father_info: str):
        self._client = bigquery.Client()
        self._dataset = dataset
        self._table = table
        self._table_ref = self._client.get_table(f'animeon.{self._dataset}.{self._table}')
        
        self.father_info = father_info
    
    def __enter__(self):
        self._check_if_anime_exists()
        return self
    
    def __exit__(self, exc_type, *_):
        pass
    
    def _check_if_anime_exists(self):
        query = f"""
            SELECT
                id
            FROM
                `animeon.{self.dataset}.animes`
            WHERE
                id LIKE '{self.father_info.get("id")}'
        """
        
        job = self._client.query(query)
        results = [res for res in job.result()]

        if results == []:
            
            row = [
                datetime.datetime.now(),
                self.father_info.get('id'),
                self.father_info.get('title'),
                self.father_info.get('episodes'),
                self.father_info.get('synopsis'),
                self.father_info.get('genres'),
                None,
                bool(self.father_info.get('airing')),
                self.father_info.get('score'),
                self.father_info.get('thumbnail'),
                self.father_info.get('banner'),
                self.father_info.get('en_title'),
                self.father_info.get('PV'),
            ]

            self.insert(row=row, optional_table='animes')
    
    def insert(self, row: list=[], optional_table: str=None):
        if optional_table:
            errors = self._client.insert_rows(table=self._client.get_table(f'animeon.{self._dataset}.{optional_table}'), rows=[row])
        else:
            errors = self._client.insert_rows(table=self._table_ref, rows=[row])

        if errors == []:
            print("[SUCCESS] All rows has been added.")