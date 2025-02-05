import re
from urllib.parse import urlparse
from pydantic import HttpUrl, ValidationError


def is_external(url: HttpUrl, base_url: HttpUrl) -> bool:
    return base_url.host not in url.host

def is_same_host(host1: str, host2: str):
    regex = re.compile(f'^(www\\.)?{host2}$')
    return True if regex.match(host1) else False

def is_relative_to_base(url: str, base_url:HttpUrl) -> tuple[bool, HttpUrl | None]:
    urlparsed = urlparse(url)
    if urlparsed:
        try:
            if is_same_host(urlparsed.netloc, base_url.host) and \
                urlparsed.path.startswith(base_url.path):
                return True, HttpUrl(url)
            elif not urlparsed.netloc and \
                urlparsed.path.startswith(base_url.path):
                httpUrl = f'{str(base_url)}{url.strip('/')}' \
                    if url.startswith('/') \
                    else f'{str(base_url)}{url}'
                return True, HttpUrl(url=httpUrl)
            else:
                return False, None
        except ValidationError as e:
            return False, None
    else:
        print(f'[utils] - [is_relative_to_base] - Invalid url {url}')
        return False, None

def is_valid_url(url: str) -> HttpUrl | None:
    try:
        return HttpUrl(url) if urlparse(url) else None
    except ValidationError as e:
        return None