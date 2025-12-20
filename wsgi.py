import sys
import os

# Добавляем путь к проекту в sys.path
project_home = '/home/polinasrgz/RGZ-WEB-BACK'  # Измените на ваш путь
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Устанавливаем рабочую директорию
os.chdir(project_home)

# Импортируем приложение
from app import app as application
