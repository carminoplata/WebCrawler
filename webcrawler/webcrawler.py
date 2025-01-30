import sys
import logging
from pydantic import HttpUrl, ValidationError
from models import Link, Page

logger = logging.getLogger('webcrawler')
logging.basicConfig(level=logging.INFO)
logFile = logging.FileHandler('webcrawler.log')
logFile.setLevel(logging.DEBUG)
logConsole = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logFile.setFormatter(formatter)
logger.addHandler(logFile)



if __name__  == '__main__':
    # Start the webcrawler
    
    if len(sys.argv) < 2:
        logger.error('Usage: python webcrawler.py <url>')
        sys.exit(1)
    try:
        rootPage = Page(url=sys.argv[1])
    except ValidationError as e:
        logger.error(f'Error: {e}')
        print(f'Invalid URL: {sys.argv[1]}')
        sys.exit(1)
    logger.info(f'Starting webcrawler with root page: {rootPage.url}')