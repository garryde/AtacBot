import json

import requests


def get_full_data(number: str) -> dict:
    url = "https://www.atac.roma.it/Service/WebService.asmx/GetRealTimeData"
    data = {'languageName': 'it', 'stopCode': number}
    headers = {'Host': 'www.atac.roma.it', 'Content-Type': 'application/json'}
    result = requests.post(url, json=data, headers=headers).text
    result_dic = json.loads(result)
    return result_dic


def get_stop_name(result_dic: dict) -> str:
    result_set = result_dic['RealTimeData']['stopdata']
    if result_set is None:
        return ""
    else:
        return result_set[0]['palinanome']


def get_status(result_dic: dict) -> str:
    result_set = result_dic['RealTimeData']['stopdetail']
    txt = ""
    if result_set is None:
        txt = "No Bus"
    else:
        for bus in result_set:
            txt += bus['line'] + "  "+bus['distanzaAVM'].replace('FERMATA', 'Stop').replace('FERMATE', 'Stops').replace('A CAPOLINEA','At The Terminal').replace('IN ARRIVO', 'Arriving') + "\n"
    return txt


class Atac:
    pass

