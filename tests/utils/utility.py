import os

from selectolax.parser import HTMLParser

SAMPLE_DIR = 'samples'

def read_file_content(filename) -> str:
    dirs = os.listdir(os.getcwd())
    if SAMPLE_DIR not in dirs:
        if 'tests' not in dirs:
            raise FileNotFoundError(f'{SAMPLE_DIR} not found in current \
                                    dir {os.getcwd()}')
        else:
            filepath = os.path.join('tests', SAMPLE_DIR, filename)
    else:
        filepath = os.path.join(SAMPLE_DIR, filename)
    print(f'Open file: {filepath}')
    with open(filepath, 'r') as file:
        content = file.read()
    return content.replace('\n', '')

def extract_link(htmlpage: str) -> list[str]:
    urls = []
    for anchor in HTMLParser(htmlpage).select('a').matches:
        if 'href' in anchor.attributes:
            urls.append(anchor.attributes['href'])
    return urls