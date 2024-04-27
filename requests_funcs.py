import requests

def response_code_handler(code) -> bool:
    if code == 200:
        return True
    return False

def create_qr_request(url:str, body:dict=None, headers:dict={'Content-Type': 'application/json'}) -> any:
    '''http запрос для qr-кода типа POST'''
    response = requests.post(url, headers=headers, json=body)
    if not response_code_handler(response.status_code):
        return 'bad request'
    print("Status Code ", response.status_code)
    print("JSON Response ", response.json())
    return response.json()

def get_qr_request(url:str, body:dict=None, headers:dict={'Content-Type': 'application/json'}) -> any:
    '''http запрос для qr-кода типа GET'''
    response = requests.get(url, headers=headers, json=body)
    if not response_code_handler(response.status_code):
        return 'bad request'
    print("Status Code ", response.status_code)
    print("JSON Response ", response.json())
    return response.json()

def delete_qr_request(url:str, body:dict=None, headers:dict={'Content-Type': 'application/json'}) -> str:
    '''http запрос для qr-кода типа DELETE'''
    response = requests.delete(url, headers=headers, json=body)
    if not response_code_handler(response.status_code):
        return response.reason
    print("Status Code ", response.status_code)
    # print("JSON Response ", response.json())
    return 'all good, deleted!'
