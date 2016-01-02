from json import load
from urllib2 import urlopen
import gmail_utils
def get_public_ip():
    ip = load(urlopen('http://jsonip.com'))['ip']
    return ip

if __name__=='__main__':
    try:
        ip = get_public_ip()
    except:
        ip = "Can't Find Ip"
    gmail_utils.send_message("Public Ip", ip)
