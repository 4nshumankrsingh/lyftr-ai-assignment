from urllib.parse import urlparse, urljoin

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def make_absolute_url(base_url: str, relative_url: str) -> str:
    """Convert relative URL to absolute"""
    if relative_url.startswith(('http://', 'https://', '//')):
        if relative_url.startswith('//'):
            return f"https:{relative_url}"
        return relative_url
    return urljoin(base_url, relative_url)

def get_base_url(url: str) -> str:
    """Extract base URL from full URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"