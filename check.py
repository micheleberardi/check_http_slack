import os
from datetime import datetime

import redis
import logging
import time
from http.client import HTTPConnection, socket



# SECTION LOGS
datelog = datetime.now().strftime('%Y-%m-%d')
datelog2 = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename="/var/log/checker-" + datelog + ".log", filemode='a')

def get_site_status(url):
    response = get_response(url)
    #print(response.status)
    try:
        if getattr(response, 'status') == 200 or 302:
            return 'true'
    except AttributeError:
    	pass
    return 'false'

def get_response(url):
    '''Return response object from URL'''
    try:
        conn = HTTPConnection(url, timeout=2)
        conn.request('HEAD', '/')
        return conn.getresponse()
    except socket.error:
    	return None
    except:
        print('Bad URL:', url)
        logging.error('Bad URL:', url)

def get_redis_status(url):
    r = redis.StrictRedis(host="localhost", charset="utf-8", port=6379, db=0, decode_responses=True)
    try:
        if r.exists(url):
            return 'true'
    except AttributeError:
        pass
    return 'false'

def get_status(status_site,status_redis):
    r = redis.StrictRedis(host="localhost", charset="utf-8", port=6379, db=0, decode_responses=True)
    if status_site == 'true' and status_redis == 'true':
        #print("send recovery")
        timeset = r.get(url)
        #print(timeset)
        now = int(time.time())
        #print(now)
        timestamp = (now - int(timeset))
        #print(timestamp)
        time_down = timestamp / 1000 % 60
        os.system("/usr/bin/slack_nagios_bucksense.pl -field slack_channel=#nagios-test -field HOSTALIAS=' "+ url +" ' -field SERVICEDESC='WAS DOWN FOR "+str(time_down)+"'' NOW ' -field SERVICESTATE='OK' -field SERVICEOUTPUT='" + datelog2 + "' -field NOTIFICATIONTYPE='problem'")
        r.delete(url)
        return "SLACK RECOVERY"
    elif status_site == 'false' and status_redis == 'true':
        return "SLACK ALREADY SENT"
    elif status_site == 'false' and status_redis == 'false':
        #print("invia allarme")
        os.system("/usr/bin/slack_nagios_bucksense.pl -field slack_channel=#nagios-test -field HOSTALIAS=' "+ url +" ' -field SERVICEDESC='WEB SITE' -field SERVICESTATE='CRITICAL' -field SERVICEOUTPUT='" + datelog2 + "' -field NOTIFICATIONTYPE='OK'")
        now = int(time.time())
        r.set(url,now)
        return "SEND SLACK ALERT"
    else:
        return "EVERYTHING IS OK"



if __name__ == "__main__":
    urls = ('www.google.com','www.yahoo.com')
    while True:
        for url in urls:
            status_redis = get_redis_status(url)
            status_site = get_site_status(url)
            status = get_status(status_site,status_redis)
            logging.debug(
                "{}{}{}{}{}{}{}{}".format("WEBSITE : ", url, " REDIS : ", status_redis, ' STATUS SITE : ', status_site, ' NOTIFICA : ',status))
    time.sleep(1)

