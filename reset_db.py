#!/usr/bin/env python3
import os
import sys
import sqlite3

# Удаляем базу
if os.path.exists('recipes.db'):
    os.remove('recipes.db')
    print("✅ База данных удалена")

# Импортируем и запускаем
from app import app, init_database

with app.app_context():
    init_database()
    print("✅ База пересоздана с правильными данными")

print("\nТеперь запустите:")
print("python3 app.py")
