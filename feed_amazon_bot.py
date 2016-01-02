import mysql.connector
import mysql.connector.errors
import amazon_product
import gmail_utils
import math
import time
USERNAME = 'pi'
PASSWORD = ''
IP = ''
DATABASE = ''
PORT = 3306


def connect():
    try:
        connection = mysql.connector.connect(user=USERNAME, password=PASSWORD, host=IP, database=DATABASE, port=PORT)
        return connection
    except mysql.connector.errors.InterfaceError:
        print('Can\'t connect to MySQL server on 192.168.2.11:3306')
        time.sleep(5)
        return connect()


def fetch_products():
    connection = connect()
    cursor = connection.cursor()
    query = 'select ASIN,CURRENT_PRICE,TITLE,PRICE_LABLE from amazon'
    stored_date = {}
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        for rows in result:
            asin = rows[0].encode('utf8')
            current_price = rows[1]
            title = rows[2].encode('utf8')
            lable = rows[3].encode('utf8')
            temp = amazon_product.amazon_product(asin=asin, title=title, current_price=current_price, lable=lable)
            # print(temp)
            stored_date.update({temp.asin: temp})
        return stored_date
    except mysql.connector.errors:
        print(mysql.connector.errors)
    finally:
        connection.close()


def add_new_product(new_products):
    connection = connect()
    cursor = connection.cursor()
    try:
        if new_products is not None:
            for products in new_products:
                current_product = new_products.get(products)
                query = 'insert into amazon (ASIN,CURRENT_PRICE,TITLE,PRICE_LABLE) values(\'%s\',%f,\'%s\',\'%s\')' \
                        % (
                        current_product.asin, current_product.current_price, current_product.title, current_product.lable)
                print(query)
                cursor.execute(query)
            connection.commit()
    except mysql.connector.errors:
        print(mysql.connector.errors)
        print('Exception in insert!')
    finally:
        cursor.close()
        connection.close()


def update_store(updated_product):
    connection = connect()
    cursor = connection.cursor()
    query = 'update amazon set CURRENT_PRICE=%f,price_lable=\'%s\' where asin=\'%s\'' % \
            (updated_product.current_price, updated_product.lable, updated_product.asin)
    cursor.execute(query)
    connection.commit()
    connection.close()


def move_to_history(product_stored, product_current):
    connection = connect()
    cursor = connection.cursor()
    percentage_diff = find_percent_diff(product_stored.current_price, product_current.current_price)
    if math.fabs(percentage_diff) > 5:
        if percentage_diff > 0:
            gmail_utils.create_message('Price of item in our wish list decreased',
                                       'Item:%s\r\nBefore:%.2f\r\nNow:%.2f\r\nChanged by:%f0.2'
                                       % (product_stored.title, product_stored.current_price,
                                          product_current.current_price, percentage_diff))
        else:
            gmail_utils.create_message('Price of item in our wish list Increased',
                                       'Item:%s\r\nBefore:%.2f\r\nNow:%.2f\r\nChanged by:%f0.2'
                                       % (product_stored.title, product_stored.current_price,
                                          product_current.current_price, percentage_diff))

    difference = product_current.current_price-product_stored.current_price
    query = 'insert into history (ASIN,CURRENT_PRICE,TITLE,PRICE_LABLE,difference) values(\'%s\',%f,\'%s\',\'%s\',%f)' \
            % (product_stored.asin, product_stored.current_price, product_stored.title, product_stored.lable, difference)
    print(query)
    cursor.execute(query)
    connection.commit()
    connection.close()


def check(list_from_current):
    print('++ Comparing with previous prices')
    print len(list_from_current)
    list_from_database = fetch_products()
    print len(list_from_current)
    check_removed_items(list_from_current, list_from_database)
    new_products_in_wish_list = {}
    try:
        for product_current_key in list_from_current:
            current_asin = product_current_key
            product_current = list_from_current.get(current_asin)
            if list_from_database.get(current_asin) is not None:
                product_stored = list_from_database.get(current_asin)
                if product_current.current_price < product_stored.current_price \
                        and product_current.lable != 'Out Of Stock':
                    print('Price changed from %.2f to %.2f for %s' % (product_stored.current_price,
                                                                      product_current.current_price,
                                                                      product_stored.title))
                    update_store(product_current)
                    move_to_history(product_stored, product_current)
                elif product_current.current_price > product_stored.current_price:
                    update_store(product_current)
                    move_to_history(product_stored, product_current)
            else:
                print ('New item %s' % product_current.title)
                print product_current
                new_products_in_wish_list.update({product_current.asin: product_current})
        return new_products_in_wish_list
    except Exception:
        print 'Exception in check method'


def check_removed_items(list_from_current, list_from_database):
    for items in list_from_database:
        if list_from_current.get(items) is None:
            delete(items)


def find_percent_diff(current, stored):
    return (stored-current)/stored*100


def delete(asin):
    print('Deleting removed items!')
    try:
        connection = connect()
        cursor = connection.cursor()
        query = 'delete from amazon where asin=\'%s\'' % asin
        cursor.execute(query)
        connection.commit()
    except:
        print('Exception while deleting record in amazon table')


def check_and_update(list_from_current):
    new_products = check(list_from_current)
    add_new_product(new_products)
