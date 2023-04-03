import json
import logging
import requests
from config import Config

def get_full_data(number: str) -> dict:
    conf = Config()
    cookie = conf.read_str('cookie')

    url = "https://www.atac.roma.it/Service/WebService.asmx/GetRealTimeData"
    data = {'languageName': 'it', 'stopCode': number}
    headers = {
        'Host': 'www.atac.roma.it',
        'Accept': 'application/json, text/plain, */*',
        'Sec-Fetch-Site': 'same-origin',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Mode': 'cors',
        'Content-Type': 'application/json',
        'Origin': 'https://www.atac.roma.it',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.atac.roma.it/',
        'Content-Length': '40',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Cookie': cookie
    }

    result = requests.post(url, json=data, headers=headers)
    cookie = result.cookies.get_dict()
    cookie_str = ""
    for k,v in cookie.items():
        cookie_str += k+"="+v+"; "
    conf.write_cookie(cookie_str[:-2])

    try:
        result_dic = json.loads(result.text)["RealTimeData"]
        if result_dic['avmdata'] is None:
            return ""
        else:
            return result_dic
    except Exception as e:
        logging.error("get full data error; " + str(e))
        logging.error("\n"+"#"*50+"\n "+ result +" \n"+"#"*50)
        return ""


def get_stop_name(result_dic: dict) -> str:
    result_set = result_dic['stopdata']
    if result_set is None:
        return ""
    else:
        return result_set[0]['palinanome']


def get_status(result_dic: dict) -> str:
    result_set = result_dic['stopdetail']
    txt = ""
    if result_set is None:
        txt = "No Bus"
    else:
        empty_string = "            "
        for bus in result_set:
            txt += bus['line'] + empty_string[:(5-len(bus['line']))*2] +bus['distanzaAVM'].replace('FERMATA', 'Stop').replace('FERMATE', 'Stops').replace('A CAPOLINEA','At The Terminal').replace('IN ARRIVO', 'Arriving') + "\n"
    return txt

class Atac:
    pass
