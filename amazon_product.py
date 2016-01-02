import datetime


class amazon_product:
    asin = ""
    current_price = 0.0
    title = ""
    lable = ""

    def __init__(self, asin, current_price, lable, title):
        self.asin = asin
        self.current_price = current_price
        self.lable = lable
        self.title = title

    def display(self):
        print("Title: %s,Asin:%s,current_price: %0.2f" % (self.title, self.asin, self.current_price))

    def __str__(self):
        return "Title: {0:s},Asin:{1:s},current_price: {2:0.2f}".format(self.title, self.asin, self.current_price)
