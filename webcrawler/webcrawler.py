import sys
from pydantic import HttpUrl
if __name__  == '__main__':
    # Start the webcrawler
    
    if len(sys.argv) < 2:
        print('Usage: python webcrawler.py <url>')
        sys.exit(1)
    url = HttpUrl.serialize_url(sys.argv[1])
    if not url:
        print(f'Invalid URL {sys.argv[1]}')
        sys.exit(1)
    """webcrawler = WebCrawler(sys.argv[1])
    webcrawler.start()"""