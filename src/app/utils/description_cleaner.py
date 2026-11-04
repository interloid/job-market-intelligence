import ftfy
from bs4 import BeautifulSoup


def clean_job_description(html: str | None) -> str | None:

    if html is None:
        return None

    html = ftfy.fix_text(html)

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator="\n", strip=True)

    return text
