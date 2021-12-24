from logging.config import dictConfig
import sys, os, time, logging
from smsactivateru import Sms, SmsTypes, SmsService, GetBalance, GetNumber
from discord_sms_verification import discord_verify

user_password = 'abcd1234'  # 디스코드 비밀번호
sms_apikey = 'abcd1234'  # sms activate api키
captcha_apikey = 'abcd1234'  # 2captcha api키

api = Sms(sms_apikey)
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file']
    }
})


def verify(user_token):
    logging.debug(f'{user_token} 인증 시작')

    balance = GetBalance().request(api)  # 잔액
    if balance < 4.5:
        print('[!] 잔액이 부족합니다.')
        time.sleep(10)
        sys.exit(1)

    try:
        sms = GetNumber(service=SmsService().Discord, country=SmsTypes.Country.VN).request(api)
    except Exception as e:
        if 'NO_NUMBERS' in str(e):
            logging.debug('재고 부족')
            print('[!] 재고가 부족하여 재시도합니다.')
            time.sleep(2)
            verify(user_token)
        elif 'NO_BALANCE' in str(e):
            logging.debug('잔액 부족')
            print('[!] 잔액이 부족합니다.')
            time.sleep(10)
            sys.exit(1)
        else:
            print(f'[!] 오류가 발생하였습니다. 해당 토큰 인증을 건너 뜁니다. ({e})')
            with open('error.txt', 'a') as f:
                f.write(user_token + '\n')
            time.sleep(3)
            starts()

    sms_id = sms.id
    sms_num = '+' + sms.phone_number

    print()
    print(f'[♥] {user_token} 인증중...')
    logging.debug('번호 구매 성공')

    balance = GetBalance().request(api)
    print(f'[+] {sms_num}({sms_id}) 번호 구매가 완료되었습니다. 잔액: {balance}루블')

    result = discord_verify(sms_apikey=sms_apikey, captcha_apikey=captcha_apikey, phone_number=sms_num, phone_id=sms_id,
                            user_token=user_token, user_password=user_password)

    if result['success']:
        print(f'[+] 번호 인증이 완료되었습니다. ({result["time"]}s)')
        print()
        logging.debug(f'{user_token} 인증 성공')
        with open('output.txt', 'a') as f:
            f.write(user_token + '\n')

        if result['withCaptcha']:
            time.sleep(20)
        else:
            time.sleep(10)
        starts()
    else:
        reason = result['reason']

        if reason == 'Invalid Token':
            logging.debug(f'{user_token} 만료된 토큰')
            print(f'[!] 만료된 토큰입니다.')
            with open('error.txt', 'a') as f:
                f.write('<만료> ' + user_token + '\n')
            time.sleep(3)
            starts()
        elif reason == 'Cannot verify with this number':
            print(f'[-] 인증 불가한 번호이므로 재시도합니다.')
            time.sleep(3)
            verify(user_token)
        elif reason == 'Unknown Error':
            er = reason['detail']
            logging.debug(f'{user_token} 오류 발생 ({er})')
            print(f'[!] 오류가 발생하였습니다. 해당 토큰 인증을 건너 뜁니다. ({er})')
            with open('error.txt', 'a') as f:
                f.write(user_token + '\n')
            time.sleep(3)
            starts()
        elif reason == 'hCaptcha solve Error':
            er = reason['detail']
            logging.debug('캡챠 오류 발생')
            print(f'[!] hCaptcha 오류가 발생하였습니다. 재시도합니다. ({er})')
            time.sleep(3)
            verify(user_token)
        elif reason == 'SMS TimeOut':
            logging.debug('인증번호 미도착')
            print('[-] 인증번호가 도착하지 않아 인증을 재시도합니다.')
            time.sleep(3)
            verify(user_token)
        elif reason == 'Already':
            logging.debug('이미 등록된 번호')
            print('[-] 이미 등록된 번호입니다. 인증을 재시도합니다.')
            time.sleep(3)
            verify(user_token)

def starts():
    with open('tokens.txt', 'r') as f:
        tokens = f.readlines()
        try:
            token = tokens[0]
        except IndexError:
            print('[!] 남은 토큰이 없습니다.')
            logging.debug('토큰 소진')
            time.sleep(10)
            sys.exit(0)

    with open('tokens.txt', 'w') as f:
        tokens.remove(token)
        after = ''.join(tokens)
        f.write(after)

    verify(token.rstrip())


if __name__ == '__main__':
    if not os.path.isfile('error.txt'):
        f = open('error.txt', 'w')
        f.close()
    if not os.path.isfile('output.txt'):
        f = open('output.txt', 'w')
        f.close()
    starts()
