@echo off
cd /d "%~dp0"
echo ===================================
echo  诊断测试：确认 Pygame 是否正常工作
echo ===================================
echo .
echo 1. Python 版本:
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" --version
echo .
echo 2. Pygame 是否安装:
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -c "import pygame; print('pygame version:', pygame.version.ver)" 2>&1
echo .
echo 3. 尝试创建一个窗口（2秒后自动关闭）:
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -c "
import pygame
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('诊断测试 - 如果你能看到这个窗口说明pygame正常')
screen.fill((30, 30, 60))
pygame.draw.circle(screen, (255, 200, 50), (200, 150), 80)
pygame.display.flip()
import time
time.sleep(2)
pygame.quit()
print('窗口测试成功！')
" 2>&1
echo .
echo ===================================
echo 如果有报错，请截图发给我。
pause
