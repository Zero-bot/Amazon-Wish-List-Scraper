import httplib
import urllib
import check_connection
from bs4 import BeautifulSoup
import bs4
import amazon_product
import cookielib
import feed_amazon_bot
import mechanize
import time
import sys
import threading
import gmail_utils

__author__ = 'Napster'
USERNAME = ''
PASSWORD = ''

def get_page(product_id, isID):
    if isID:
        url = "/gp/product/"+product_id
    else:
        url=product_id
    connect = httplib.HTTPSConnection("www.amazon.in")
    connect.request("GET", url)
    response = connect.getresponse()
    h=response.getheaders()
    response.close()
    for headers in h:
        if headers[0]=="location":
            url=headers[1]
            connect.request("GET",headers[1])

    response = connect.getresponse()
    sock = urllib.urlopen(url)
    htmlsource= sock.read()
    sock.close()
    # print(htmlsource)
    return htmlsource


def find_price(my_wish):
    print('++Finding latest price from wish list')
    lists = {}
    for products in my_wish:
        temp = amazon_product.amazon_product
        splitted = str(products.encode('ascii', 'ignore')).split("/")
        asin = splitted[2]
        html_doc = (search_product(products, False))
        soup = BeautifulSoup(html_doc, 'html.parser')
        print(soup.title.contents[0])
        title = (soup.title.contents[0]).replace("'", "")
        temp.title = str(title)
        deal = soup.find(id="priceblock_dealprice")
        sale = soup.find(id="priceblock_saleprice")
        our = soup.find(id="priceblock_ourprice")
        lable=""
        if deal is not None:
            print("Deal price:"+deal.contents[1])
            current_price = float(str(deal.contents[1]).replace(',', ''))
            lable = "Deal"
        else:
            if sale is not None:
                print("Sale price:"+sale.contents[1])
                current_price = float(str(sale.contents[1]).replace(',', ''))
                lable = "Sale"
            else:
                if our is not None:
                    print("Amazon price:"+our.contents[1])
                    current_price = float(str(our.contents[1]).replace(',', ''))
                    lable = "Amazon"

                else:
                    print("Out of stock!")
                    current_price = 0
                    lable = "Out Of Stock"
        temp = amazon_product.amazon_product(asin=asin, title=title, current_price=current_price, lable=lable)
        lists.update({temp.asin: temp})
    return lists


def search_product(product_id, isID):
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    if isID:
        url = "/gp/product/"+product_id
    else:
        url=product_id
    browser.open("https://www.amazon.in/"+url)
    reponse = browser.response().read()
    browser.close()
    return reponse



def login_to_account():
    browser = mechanize.Browser()
    cokkie = cookielib.LWPCookieJar()
    browser.addheaders = [("User-agent", "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13")]
    browser.set_handle_robots(False)
    browser.set_cookiejar(cokkie)
    browser.open("https://www.amazon.in/gp/sign-in.html")
    print("++ Opening Amazon.com")
    browser.select_form(nr=0)
    browser.form['email'] = USERNAME
    browser.form['password'] = PASSWORD
    browser.submit()
    print("++ Logged in!")
    print("++ Opening WishList!")
    browser.open("https://www.amazon.in/gp/registry/wishlist")
    wishlist = browser.response().read()

    return wishlist


def get_all_product_ids(wishlist):
     print("++ Parsing Your wishlist")
     soup = BeautifulSoup(wishlist, 'html.parser')
     my_wish = []
     r=soup.find_all('h5')
     for q in r:
         for ele in q:
            if isinstance(ele, bs4.element.Tag):
                my_wish.append(ele.get("href"))
     return my_wish


def my_wish():
    wishlist = login_to_account()
    my_wish = get_all_product_ids(wishlist)
    print("++ Finding latest price")
    return my_wish


def login_and_process():
    while True:
        try:
            my_wish_list = my_wish()
            latest_price = find_price(my_wish_list)
            feed_amazon_bot.check_and_update(latest_price)
            count = 0
            while count < 10:
                latest_price = find_price(my_wish_list)
                feed_amazon_bot.check_and_update(latest_price)
                time.sleep(30)
                count += 1
        except Exception:
            print("Exception!!")
            time.sleep(10)
            while not check_connection.is_connected():
                time.sleep(10)


if __name__ == '__main__':
    # thread.start_new_thread(start_processing())
    # thread.start_new_thread(gmail_utils.serve_pi())
    amazon_thread = threading.Thread(target=login_and_process, args=())
    gmail_thread = threading.Thread(target=gmail_utils.serve_pi, args=())
    amazon_thread.start()
    gmail_thread.start()




