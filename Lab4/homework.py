import socket
import re
import json

HOST = '127.0.0.1'
PORT = 8080

def make_request(path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        request = f"GET {path} HTTP/1.1\r\nHost: {HOST}:{PORT}\r\n\r\n"
        client_socket.send(request.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
    return response

def parse_page(response):
    page_content = re.search(r'<body>(.*?)</body>', response, re.DOTALL)
    return page_content.group(1).strip() if page_content else response.strip()

def parse_product_page(response):
    product_details = {}
    fields = ["Name", "Author", "Price", "Description"]
    for field in fields:
        match = re.search(fr"{field}: (.*?)<br>", response)
        if match:
            product_details[field.lower()] = match.group(1)
    return product_details

def extract_product_links(response):
    product_links = re.findall(r'<a href=\'(/product/\d+)\'>', response)
    return product_links

def main():
    page_dict = {}
    pages = [('/contacts', 'Contacts'), ('/about', 'About Us')]

    for path, page_name in pages:
        page_response = make_request(path)
        page_content = parse_page(page_response)
        page_dict[page_name] = page_content


    product_listing_response = make_request('/products')
    product_links = extract_product_links(product_listing_response)
    product_dict = {}

   
    for link in product_links:
        product_response = make_request(link)
        product_details = parse_product_page(product_response)
        product_dict[link] = product_details

    for page_name, content in page_dict.items():
        print(f"{page_name} Page:")
        print(content)
        print("\n")

    for link, details in product_dict.items():
        print(f"Product URL: {link}")
        print(json.dumps(details, indent=4))
        print("\n")

if __name__ == "__main__":
    main()
