from threading import Thread, Lock
from tinydb import TinyDB
import pika
import json
import requests
import bs4

# Initialize TinyDB for storing scraped data
db = TinyDB('scraped_data.json', indent=4, separators=(',', ': '), ensure_ascii=False, encoding='utf-8')
lock = Lock()


def extract_product_details(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        title = soup.find("header", class_="adPage__header").text.strip()

        price_element = soup.find("span", class_="adPage__content__price-feature__prices__price__value")
        price = price_element.text.strip() if price_element else "Price not found"

        currency_element = soup.find("span", class_="adPage__content__price-feature__prices__price__currency")
        currency = currency_element.text.strip() if currency_element else ""

        seller = soup.find("dl", class_="adPage__aside__stats__owner").text.strip()
        description = soup.find("div", class_="adPage__content__description grid_18").text.strip()
        characteristics = soup.find("div", class_="adPage__content__features__col grid_9 suffix_1").text.strip()
        region = soup.find("dl", class_="adPage__content__region grid_18").text.strip()

        product_details = {
            "Title": title,
            "Price": f"{price} {currency}",
            "Seller": seller,
            "Description": description,
            "Characteristics": characteristics,
            "Region": region,
        }

        return product_details

    else:
        print(f"Failed to retrieve the product page. Status code: {response.status_code}")
        return None



def callback(ch, method, properties, body, thread_num):
    url = body.decode()  # Callback function to process a message from the queue
    scraped_data = extract_product_details(url)

    if scraped_data:
        with lock:  # Insert scraped data into TinyDB
            db.insert(scraped_data)
        print(f"Thread {thread_num}: Processing URL - {url}")


def process_data_from_queue(thread_num):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='url_queue')
    channel.basic_consume(queue='url_queue', on_message_callback=lambda ch, method, properties, body: callback(ch,
                                                                                                               method,
                                                                                                               properties,
                                                                                                               body,
                                                                                                               thread_num),
                          auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    num_threads = 6

    print(f'{num_threads} threads are processing URLs at the same time.')
    threads = []
    # Start threads to process data from the queue
    for i in range(num_threads):
        thread = Thread(target=process_data_from_queue, args=(i,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
