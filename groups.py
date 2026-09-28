import requests
import re
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.istu.edu/raspisanie/poisk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
}


def find_group_id(group_name: str) -> int | None:
    data = {"zapros": group_name}

    try:
        r = requests.post(SEARCH_URL, data=data, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r"/raspisanie/grup/(\d+)/", href)
        if m:
            name_in_link = a.get_text(strip=True)
            if name_in_link.lower() == group_name.lower():
                return int(m.group(1))

    return None


if __name__ == "__main__":
    for name in ["АСУб-23-1", "АСУб-23-2", "ИСИб-23-1", "Несуществующая-99"]:
        gid = find_group_id(name)
        print(f"{name} -> {gid}")