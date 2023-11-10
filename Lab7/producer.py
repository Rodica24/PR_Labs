import bs4
import threading
import requests
import json
import pika

arr = []  # list to store URLs
processed_urls = set()  # set to keep track of processed URLs
arr_lock = threading.Lock()


def crawling(url, maxNumPage=None, startPage=1):
    global url_to_send
    #  if the maximum page limit is reached
    if maxNumPage is not None and startPage > maxNumPage:
        return

    # send a get request to the specified URL
    response = requests.get(url.format(startPage))

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        links = soup.select(".block-items__item__title")

        for link in links:
            if "/booster/" not in link.get("href"):
                url_to_send = "https://999.md" + link.get("href")

                # check if the URL has been processed
                if url_to_send not in processed_urls:
                    send_url_to_queue(url_to_send)
                    processed_urls.add(url_to_send)

                # Use lock to ensure thread-safe appending to the arr list
                with arr_lock:
                    arr.append("https://999.md" + link.get("href"))

        print(f"Processed page {startPage}")

        crawling(url, maxNumPage, startPage + 1)

    else:
        print(f"Failed to retrieve the web page. Status code: {response.status_code}")

    # open a JSON file in write mode to store the list of URLs
    with open("parsed_links.json", "w", encoding="utf-8") as json_file:
        # acquire the lock before writing to the file for ensuring thread safety
        with arr_lock:
            json.dump({"parsed_links": arr}, json_file, indent=2, ensure_ascii=False)

    return arr


def send_url_to_queue(url):
    # check if the URL has not been processed
    if url not in processed_urls:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='url_queue')
        # publish the URL to the url_queue queue
        channel.basic_publish(exchange='', routing_key='url_queue', body=url)
        connection.close()

        # Add the URL to the set of processed URLs
        processed_urls.add(url)


if __name__ == "__main__":
    crawling("https://m.999.md/ro/list/phone-and-communication/mobile-phones?page={}", maxNumPage=3)
