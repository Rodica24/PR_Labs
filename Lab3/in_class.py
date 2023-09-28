import bs4
import requests
import json


def crawling(url, maxNumPage=None, startPage=1):

    arr = []

    if maxNumPage is not None and startPage > maxNumPage:
        return

    response = requests.get(url.format(startPage))

    if response.status_code == 200:

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        links = soup.select(".block-items__item__title")

        for link in links:
            if "/booster/" not in link.get("href"):
                arr.append("https://999.md" + link.get("href"))

        crawling(url, maxNumPage, startPage + 1)

    else:
        print(f"Failed to retrieve the web page. Status code: {response.status_code}")

    return arr

arr = crawling("https://m.999.md/ro/list/phone-and-communication/mobile-phones?page={}", maxNumPage=3)

with open("parsed_links.json", "w") as json_file:
    for link in arr:
        json.dump(link, json_file)
        json_file.write("\n")

print(f"Parsed links have been saved to 'parsed_links.json'")