import twocaptcha.api, requests, time, sys
from smsactivateru import Sms, SmsTypes, SetStatus, GetStatus
try:
    from twocaptcha import TwoCaptcha
except:
    print('2captcha 모듈이 설치되지 않았습니다')
    print('pip install 2captcha-python')
    time.sleep(5)
    sys.exit(1)



def discord_verify(sms_apikey, captcha_apikey, phone_number, phone_id, user_token, user_password):
    def Cancel(_id):
        SetStatus(id=_id, status=SmsTypes.Status.Cancel).request(wrapper)

    def Sent(_id):
        SetStatus(id=_id, status=SmsTypes.Status.SmsSent).request(wrapper)

    def Finish(_id):
        SetStatus(id=_id, status=SmsTypes.Status.End).request(wrapper)

    success = {'success': True, 'time': None, 'withCaptcha': False}
    wrapper = Sms(sms_apikey)
    solver = TwoCaptcha(captcha_apikey)

    d_headers = {
        "accept": "*/*",
        "accept-language": "it",
        "authorization": user_token,
        "content-type": "application/json",
        "origin": "https://discord.com",
        "referer": "https://discord.com/channels/@me",
        "sec-ch-ua": 'Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
        "x-debug-options": "bugReporterEnabled",
        "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzkzLjAuNDU3Ny44MiBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiOTMuMC40NTc3LjgyIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tL2xvZ2luIiwicmVmZXJyaW5nX2RvbWFpbiI6ImRpc2NvcmQuY29tIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjk3NjYyLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
    }

    data = {"phone": phone_number, 'captcha_key': None}
    response = requests.post('https://discord.com/api/v9/users/@me/phone', headers=d_headers, json=data)

    if response.status_code != 204:
        try:
            cap = response.json()["captcha_service"]
        except KeyError:
            if 'Unauthorized' in response.json()["message"]:
                Cancel(phone_id)
                return {'success': False, 'reason': 'Invalid Token'}
            elif 'Invalid phone number' in response.json()["message"]:
                Cancel(phone_id)
                return {'success': False, 'reason': 'Cannot verify with this number'}
            else:
                Cancel(phone_id)
                return {'success': False, 'reason': 'Unknown Error', 'detail': response.json()["message"]}

        try:
            print('hCaptcha 발생')
            result = solver.hcaptcha(sitekey='f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34',
                                     url='https://discord.com/api/v9/users/@me/phone')
            success['withCaptcha'] = True
        except twocaptcha.api.NetworkException as e:
            Cancel(phone_id)
            
        data['captcha_key'] = result['code']
        response = requests.post('https://discord.com/api/v9/users/@me/phone', headers=d_headers, json=data)

    print('[+] 인증번호 수신 대기중...')
    Sent(phone_id)
    start = time.time()

    count = 1
    while True:
        time.sleep(1)
        response = GetStatus(id=phone_id).request(wrapper)
        if response['code']:
            sms_code = response['code']
            print(f'[+] 인증번호가 수신 되었습니다. {sms_code}')
            break
        count += 1
        if count == 20:
            Cancel(phone_id)
            return {'success': False, 'reason': 'SMS TimeOut'}

    if "Rimuovi l'account prima" in str(response['code']):
        return {'success': False, 'reason': 'Already'}
    
    data = {"phone": phone_number, "code": sms_code}
    response = requests.post('https://discord.com/api/v9/phone-verifications/verify', headers=d_headers, json=data)
    try:
        sms_token = response.json()['token']
    except Exception as e:
        return {'success': False, 'reason': 'Unknown Error', 'detail': e}

    data = {"phone_token": sms_token, "password": user_password}
    response = requests.post('https://discord.com/api/v9/users/@me/phone', headers=d_headers, json=data)

    Finish(phone_id)
    success['time'] = round(time.time() - start, 1)
    return success #{'success': None, 'time': None, 'withCaptcha': False}
