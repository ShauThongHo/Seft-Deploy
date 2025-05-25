import pyautogui
import time

# 等待微信打开
time.sleep(5)

# 打开微信窗口
pyautogui.hotkey('win', 's')
time.sleep(0.5)
pyautogui.typewrite('WeChat')
time.sleep(0.5)
pyautogui.press('enter')

# 等待微信启动
time.sleep(5)

# 选择联系人
#pyautogui.typewrite('乄神龙殿乄')
#time.sleep(0.5)
#pyautogui.press('enter')

# 输入消息
pyautogui.typewrite('Hello, this is a scheduled message!')
time.sleep(0.5)
pyautogui.press('enter')