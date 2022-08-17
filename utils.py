import datetime

def get_timestamp():
    date_now = datetime.datetime.now()
    return date_now.strftime('%Y-%d-%m'+ 'T' + '%H-%M-%S-%f')
