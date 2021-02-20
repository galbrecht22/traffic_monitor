import os
import shutil
from zipfile import ZipFile
import requests


def remove_gtfs(file_path):
    if os.path.isdir(file_path):
        print('Removing gtfs folder...')
        shutil.rmtree(file_path)
        print('Done!')


def download_url(url, chunk_size=128):
    save_path = os.path.join('../../tm-etl/data/', url.split('/')[-1])
    print('Downloading url...')
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
    print('Done!')
    return save_path


def extract_zip(file_path):
    with ZipFile(file_path, 'r') as zf:
        zf.printdir()
        print('Extracting the files now...')
        zf.extractall(file_path[:-4])
        print('Done!')
    os.remove(file_path)


zip_url = "https://bkk.hu/gtfs/budapest_gtfs.zip"
folder = '../../tm-etl/data/budapest_gtfs'

remove_gtfs(folder)
zip_file = download_url(zip_url)
extract_zip(zip_file)
