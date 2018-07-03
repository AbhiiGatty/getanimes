import requests
from tqdm import tqdm 
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def filename_from_url(url):
    # Get filename from a url with parameters
    tmp = urlparse(url)
    query = parse_qs(tmp.query)
    # extract the URL without query parameters and then get filename from it
    url_without_params = tmp._replace(query=None).geturl()
    file_name = Path(url_without_params).parts[-1]
    return file_name

def download_from_url(url, dir_name):
    file_size = int(requests.head(url).headers['Content-Length'])
    file_name  = filename_from_url(url)
    file_path = Path(dir_name) / file_name
    if file_path.exists():
        first_byte = file_path.stat().st_size
    else:
        first_byte = 0
    if first_byte >= file_size:
        return 
    header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
    pbar = tqdm(
        total=file_size, initial=first_byte,
        unit='B', unit_scale=True, desc=file_name)
    req = requests.get(url, headers=header, stream=True)
    with(open(file_name, 'ab')) as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()
