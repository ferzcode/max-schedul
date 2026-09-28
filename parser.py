import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.istu.edu/raspisanie/grup/{group_id}/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}


def parse_schedule(group_id: int) -> list[dict]:
    url = BASE_URL.format(group_id=group_id)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    lessons = []
    current_day = None

    for el in soup.find_all(["h2", "div"]):
        classes = el.get("class", [])

        if "sch-list-day-header" in classes:
            current_day = el.get_text(" ", strip=True).replace(chr(0xA0), " ")
            continue

        if "sch-list-item" not in classes or current_day is None:
            continue

        time_el = el.find("div", class_="sch-list-item-time-inner")
        time_str = time_el.get_text(strip=True) if time_el else ""

        for week_div in el.find_all("div", class_="sch-list-item-week"):
            week_classes = week_div.get("class", [])
            if "week-even" in week_classes:
                week = "even"
            elif "week-odd" in week_classes:
                week = "odd"
            else:
                week = "all"

            for card in week_div.find_all("div", class_="schcls-item"):
                if "schcls-empty" in card.get("class", []):
                    continue

                name_el = card.find("div", class_="schcls-item-name")
                type_el = card.find("div", class_="schcls-item-distype")
                prepod_el = card.find("div", class_="schcls-item-prepod")
                aud_el = card.find("div", class_="schcls-item-aud")

                lessons.append({
                    "day": current_day,
                    "time": time_str,
                    "week": week,
                    "subject": name_el.get_text(strip=True) if name_el else "",
                    "type": type_el.get_text(strip=True) if type_el else "",
                    "teacher": prepod_el.get_text(strip=True) if prepod_el else "",
                    "room": aud_el.get_text(strip=True) if aud_el else "",
                })

    return lessons


if __name__ == "__main__":
    import json
    data = parse_schedule(478015)
    print(json.dumps(data, ensure_ascii=False, indent=2))
