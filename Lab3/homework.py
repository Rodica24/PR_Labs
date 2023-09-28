import bs4
import requests
import json

def extract_product_details(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        title = soup.find("header", class_="adPage__header").text.strip()
        price = soup.find("span", class_= "adPage__content__price-feature__prices__price__value").text.strip()
        currency = soup.find("span", class_="adPage__content__price-feature__prices__price__currency").text.strip()
        price_with_currency = f"{price} {currency}"
        seller = soup.find("dl", class_= "adPage__aside__stats__owner").text.strip()
        description = soup.find("div", class_="adPage__content__description grid_18").text.strip()
        characteristics = soup.find("div", class_="adPage__content__features__col grid_9 suffix_1").text.strip()
        region = soup.find("dl", class_="adPage__content__region grid_18").text.strip()

        product_details = {
            "Title": title,
            "Price": price_with_currency,
            "Seller": seller,
            "Description": description,
            "Characteristics": characteristics,
            "Region": region,
        }

        return product_details

    else:
        print(f"Failed to retrieve the product page. Status code: {response.status_code}")
        return None

url = "https://999.md/ro/84352521"
details = extract_product_details(url)

if details:
    json_details = json.dumps(details, indent=4, ensure_ascii=False)
    print(json_details)
