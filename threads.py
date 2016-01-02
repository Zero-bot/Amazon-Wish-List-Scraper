from threading import Thread
import time


def timer(name,delay):
    count = 0
    print('Started:'+name)
    while count < 10:
        print(name, count)
        time.sleep(delay)
        count +=1
    print('Done')

def threder():
    t1=Thread(target=timer,args=('A',2))
    t2=Thread(target=timer,args=('B',1))
    t1.start()
    t2.start()

threder()