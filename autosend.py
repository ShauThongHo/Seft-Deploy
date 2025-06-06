import time
import requests

BOT_TOKEN = '你的Bot Token'
CHAT_ID = '目标聊天ID'
MESSAGE = '你好，这是测试消息'

for i in range(10):  # 每秒发送一条，共发送10条
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': f'{MESSAGE} #{i+1}'}
    requests.post(url, data=data)
    time.sleep(1)  # 每秒发送一次
