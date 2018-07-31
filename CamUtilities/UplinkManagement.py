from xml.etree import cElementTree as ElementTree

try:
    from urllib.request import urlopen, build_opener, HTTPCookieProcessor, HTTPErrorProcessor
    from http.cookiejar import CookieJar
except ImportError:
    from urllib2 import urlopen, build_opener, HTTPCookieProcessor, HTTPErrorProcessor
    from cookielib import CookieJar


class NoRedirection(HTTPErrorProcessor):

    def http_response(self, request, response):
        return response

    https_response = http_response


def dlink_dwr921_syslog(ip, user, passwd):
    try:
        cj = CookieJar()
        opener = build_opener(NoRedirection, HTTPCookieProcessor(cj))
        opener.open('http://{0}/log/in?un={1}&pw={2}&rd=/'.format(ip, user, passwd))
        syslog = opener.open('http://{0}/system.log'.format(ip))
        opener.open('http://{0}/log/out'.format(ip))
        return syslog.read()
    except:
        return None


def dlink_dwr921_reboot(ip, user, passwd):
    try:
        cj = CookieJar()
        opener = build_opener(NoRedirection, HTTPCookieProcessor(cj))
        opener.open('http://{0}/log/in?un={1}&pw={2}&rd=/'.format(ip, user, passwd))
        opener.open('http://{0}/uir/rebo.htm'.format(ip))
        opener.open('http://{0}/log/out'.format(ip))
        return True
    except:
        return False


def dlink_dwr921_stats(ip):
    try:
        resp = urlopen('http://%s/stats.xml' % ip)
        root = ElementTree.fromstring(resp.read())
        status = {
            'up':  root.findall("./wan3g/item[@name='uptime3g']")[0].text,
            'dbm': root.findall("./wan3g/item[@name='signaldbm']")[0].text,
            'rat': root.findall("./wan3g/item[@name='cntsta3g']")[0].text,
            'ip':  root.findall("./wan3g/item[@name='ip3g']")[0].text,
            'net': root.findall("./cardinfos/item[@name='networkname']")[0].text,
            'sig': root.findall("./cardinfos/item[@name='signal']")[0].text,
        }
        return status
    except:
        return None


if __name__ == '__main__':
    print(dlink_dwr921_stats('192.168.1.69:8999'))
    print(dlink_dwr921_syslog('192.168.1.69:8999', 'admin', 'admin'))
    #dlink_dwr921_reboot('192.168.1.69:8999', 'admin', 'admin')
