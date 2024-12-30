from telethon import TelegramClient, sync
import os

# 你的API ID和API Hash
api_id = '27348698'
api_hash = '74bda3592eec2671ebb0aa429a6164da'

# 会话文件路径
session_file = 'C:/Users/hosha/Documents/GitHub/Seft-Deploy/session_name.session'

# 创建客户端
client = TelegramClient(session_file, api_id, api_hash)

# 连接到Telegram
client.start()

# 下载文件的函数
def download_file(file_id, save_path):
    message = client.get_messages('me', ids=file_id)
    file = message.download_media(file=save_path)
    print(f'文件已下载到: {file}')

# 示例：下载文件
file_id = 'NF13-65669-6-2.7z.001'  # 替换为你的文件ID
save_path = os.path.join(os.getcwd(), 'downloaded_file.zip')
download_file(file_id, save_path)

# 断开客户端
client.disconnect()