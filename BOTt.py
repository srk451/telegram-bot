# import sqlite3
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
# from datetime import datetime
# import pytz
# import csv
# import os
# import time
# from openpyxl import Workbook
# import urllib.parse  # Для кодирования/декодирования имени пользователя

# # Токен вашего бота
# TOKEN = '8031537354:AAGWj9NsFcP8_NV7CSvKWPz7L1EQcG4WDIw'

# # Глобальная переменная для хранения времени сообщений
# user_message_times = {}

# # Порог для "подозрительных" сообщений: 5 сообщений за 10 секунд
# MAX_MESSAGES = 5  # Максимум сообщений за 10 секунд
# TIME_LIMIT = 10   # Время, за которое проверяются сообщения (в секундах)

# # Функция для добавления или обновления пользователя в базе данных
# def add_or_update_user(user_id, username, full_name):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS user (
#                     telegram_id INTEGER PRIMARY KEY,
#                     username TEXT,
#                     full_name TEXT,
#                     is_verified BOOLEAN DEFAULT 0)''')
#     c.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
#     user = c.fetchone()
#     if user:
#         c.execute("UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?", (username, full_name, user_id))
#     else:
#         c.execute("INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
#     conn.commit()
#     conn.close()

# # Функция для получения списка пользователей из базы данных
# def get_users_from_db():
#     # Подключение к базе данных SQLite
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Запрос на получение всех пользователей
#     c.execute("SELECT id, telegram_id, username, phone_number FROM users")
#     users = c.fetchall()

#     # Закрытие соединения с базой данных
#     conn.close()

#     return users

# # Функция для проверки активности пользователя
# def is_spamming(user_id):
#     current_time = time.time()
    
#     # Если пользователя нет в словаре, создаём для него новый список сообщений
#     if user_id not in user_message_times:
#         user_message_times[user_id] = []
    
#     # Очищаем старые сообщения (старше чем TIME_LIMIT секунд)
#     user_message_times[user_id] = [timestamp for timestamp in user_message_times[user_id] if current_time - timestamp < TIME_LIMIT]
    
#     # Добавляем текущее время
#     user_message_times[user_id].append(current_time)
    
#     # Если количество сообщений больше лимита, считаем, что это спам
#     if len(user_message_times[user_id]) > MAX_MESSAGES:
#         return True
#     return False

# # Подключение к базе данных для пользователей и транзакций
# def create_database():
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Создание таблицы пользователей с дополнительными полями
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             telegram_id INTEGER UNIQUE NOT NULL,
#             username TEXT,
#             language TEXT DEFAULT 'en',
#             phone_number TEXT,
#             registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             balance REAL DEFAULT 0
#         )
#     ''')

#     # Создание таблицы для транзакций
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS transactions4 (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             amount REAL NOT NULL,
#             description TEXT,
#             date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#     ''')

#     # Таблица для истории входов с user_id
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS login_history (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             username TEXT NOT NULL,
#             login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users(id)
#         )
#     ''')

#     conn.commit()
#     conn.close()

# # Функция для добавления администратора
# def add_admin(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO admins (telegram_id) VALUES (?)", (telegram_id,))
#         conn.commit()
#         print(f"User {telegram_id} has been added as an admin.")
#     except sqlite3.IntegrityError:
#         print(f"User {telegram_id} is already an admin.")
#     finally:
#         conn.close()

# # Пример добавления нового админа:
# # add_admin(996317285)  # Замените на ID нового администратора

# # Проверка, является ли пользователь администратором
# def is_admin(user_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (user_id,))
#     result = c.fetchone()
#     conn.close()
#     return result is not None

# # Добавить нового админа в базу данных
# def add_admin_to_db(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("INSERT INTO admins (telegram_id) VALUES (?)", (telegram_id,))
#     conn.commit()
#     conn.close()

# # Удалить админа из базы данных
# def remove_admin_from_db(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
#     conn.commit()
#     conn.close()

# # Функция для получения списка администраторов с username
# def get_admins():
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("""
#         SELECT a.telegram_id, u.username
#         FROM admins a
#         LEFT JOIN users u ON a.telegram_id = u.telegram_id
#     """)
#     admins = c.fetchall()
#     conn.close()
#     return admins

# def add_user(telegram_id, username=None, language='en', phone_number=None):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Получаем текущее время с учетом временной зоны
#     current_time = get_current_time()

#     c.execute("INSERT INTO users (telegram_id, username, language, phone_number, registration_date) VALUES (?, ?, ?, ?, ?)", 
#               (telegram_id, username, language, phone_number, current_time))
#     conn.commit()
#     conn.close()

# def get_current_time():
#     # Указываем временную зону для Казахстана (UTC+6)
#     tz = pytz.timezone('Asia/Almaty')  # Казахстан, UTC+6
#     now = datetime.now(tz)  # Получаем текущее время в выбранной временной зоне

#     # Форматируем время так, чтобы оно не содержало микросекунд и временной зоны
#     return now.strftime('%Y-%m-%d %H:%M:%S')  # Только дата и время

# def update_last_activity_and_log_in(user_id, username):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Вставляем запись в историю логинов
#     c.execute("INSERT INTO login_history (user_id, username, login_time) VALUES (?, ?, ?)",
#               (user_id, username, get_current_time()))
#     conn.commit()
#     conn.close()

# def update_last_activity_and_log_in(telegram_id, username):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Получаем user_id для пользователя
#     c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
#     user = c.fetchone()

#     if user:
#         user_id = user[0]
#     else:
#         # Если пользователь не найден, создаем нового
#         add_user(telegram_id, username)
#         user_id = c.lastrowid

#     current_time = get_current_time()

#     # Обновление времени последней активности пользователя
#     c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))

#     # Добавление записи о входе в историю с user_id и username
#     c.execute("INSERT INTO login_history (user_id, username, login_time) VALUES (?, ?, ?)", 
#               (user_id, username, current_time))

#     conn.commit()
#     conn.close()

# def add_username_column_to_login_history():
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Проверяем, существует ли уже колонка 'username' в таблице login_history
#     c.execute("PRAGMA table_info(login_history);")
#     columns = c.fetchall()
    
#     # Извлекаем список имен столбцов
#     column_names = [column[1] for column in columns]

#     if 'username' not in column_names:
#         # Если столбца нет, добавляем его
#         c.execute("PRAGMA foreign_keys=off;")  # Отключаем ограничения внешнего ключа для изменения структуры таблицы
#         c.execute('''
#             ALTER TABLE login_history
#             ADD COLUMN username TEXT;
#         ''')
#         c.execute("PRAGMA foreign_keys=on;")  # Включаем ограничения внешнего ключа обратно
#         print("Column 'username' added to login_history table.")
#     else:
#         print("Column 'username' already exists in login_history table.")

#     conn.commit()
#     conn.close()

# # Функция для очистки данных пользователей
# def clear_users_data():
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("DELETE FROM users")
#     c.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'users'")  # Сбросить ID
#     conn.commit()
#     conn.close()

# # Функция для очистки транзакций
# def clear_transactions_data():
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("DELETE FROM transactions4")
#     c.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'transactions4'")  # Сбросить ID
#     conn.commit()
#     conn.close()

# def logout_user(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     current_time = get_current_time()

#     # Обновление последней активности при выходе
#     c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))

#     conn.commit()
#     conn.close()

# # Функция для обновления времени последней активности пользователя
# def update_last_activity(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Получаем текущее время с учетом временной зоны (KZT - UTC+6)
#     current_time = get_current_time()
    
#     print(f"Updating last activity for user {telegram_id} to {current_time}")  # Для отладки

#     # Обновляем запись в базе данных
#     c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))
#     conn.commit()

#     # Проверим, обновлена ли строка в базе данных
#     c.execute("SELECT last_activity FROM users WHERE telegram_id = ?", (telegram_id,))
#     result = c.fetchone()

#     if result:
#         print(f"Last activity successfully updated: {result[0]}")  # Для отладки
#     else:
#         print(f"No user found with telegram_id {telegram_id}")  # Для отладки

#     conn.close()

# # Функция для обновления языка пользователя
# def update_user_language(telegram_id, language):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
#     conn.commit()
#     conn.close()

# # Функция для обновления телефона пользователя
# def update_user_phone(telegram_id, phone_number):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ?", (phone_number, telegram_id))
#     conn.commit()
#     conn.close()

# def update_last_activity(telegram_id):
#     try:
#         conn = sqlite3.connect('transactions4.db')
#         conn.isolation_level = None  # Отключаем авто-commit для явного контроля транзакций
#         c = conn.cursor()

#         # Получаем текущее время с учетом временной зоны (KZT - UTC+6)
#         current_time = get_current_time()

#         print(f"Updating last activity for user {telegram_id} to {current_time}")  # Для отладки

#         # Начинаем транзакцию
#         c.execute("BEGIN TRANSACTION;")
        
#         # Обновляем запись в базе данных
#         c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))
#         conn.commit()  # Фиксируем изменения

#         # Проверим, обновлена ли строка в базе данных
#         c.execute("SELECT last_activity FROM users WHERE telegram_id = ?", (telegram_id,))
#         result = c.fetchone()

#         if result:
#             print(f"Last activity successfully updated: {result[0]}")  # Для отладки
#         else:
#             print(f"No user found with telegram_id {telegram_id}")  # Для отладки

#     except sqlite3.OperationalError as e:
#         print(f"Database error: {e}")
#     finally:
#         conn.close()  # Обязательно закрываем соединение после завершения работы

# # Функция для получения информации о пользователе
# def get_user_language(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,))
#     result = c.fetchone()
#     conn.close()
#     return result[0] if result else None

# # Функция для получения username пользователя
# def get_user_username(telegram_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT username FROM users WHERE telegram_id = ?", (telegram_id,))
#     result = c.fetchone()
#     conn.close()
#     return result[0] if result else None

# def add_transaction(user_id, amount, description):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Получаем текущее время с учетом временной зоны
#     current_time = get_current_time()  # Например, '2024-11-28 10:18:00'
    
#     # Вставляем транзакцию с правильным временем
#     c.execute('''
#         INSERT INTO transactions4 (user_id, amount, description, date)
#         VALUES (?, ?, ?, ?)
#     ''', (user_id, amount, description, current_time))
    
#     # Получаем id пользователя и его текущий баланс
#     c.execute("SELECT id, balance FROM users WHERE telegram_id = ?", (user_id,))
#     user = c.fetchone()
    
#     if user:
#         user_id_in_db = user[0]  # id пользователя в базе данных
#         current_balance = user[1]  # Текущий баланс
        
#         # Обновляем баланс пользователя: добавляем сумму к текущему балансу (для дохода или расхода)
#         new_balance = current_balance + amount  # Для дохода: увеличиваем, для расхода: уменьшаем
#         c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id_in_db))
        
#         # Добавляем транзакцию в таблицу транзакций
#         c.execute("INSERT INTO transactions4 (user_id, amount, description) VALUES (?, ?, ?)",
#                   (user_id_in_db, amount, description))
#         conn.commit()
#     conn.close()

# # Функция для получения транзакций пользователя
# def get_transactions(user_id):
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()

#     # Получаем id пользователя
#     c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
#     user = c.fetchone()

#     if user:    
#         user_id_in_db = user[0]  # id пользователя в базе данных
#         # c.execute("SELECT * FROM transactions4 WHERE user_id = ? ORDER BY date DESC", (user_id_in_db,))
#         # Выполняем JOIN для получения данных о транзакциях и username
#         c.execute("""
#             SELECT t.id, t.user_id, u.username, t.amount, t.description, t.date
#             FROM transactions4 t
#             JOIN users u ON t.user_id = u.id
#             WHERE t.user_id = ? ORDER BY t.date DESC
#         """, (user_id_in_db,))
#         transactions = c.fetchall()
#     else:
#         transactions = []

#     conn.close()
#     return transactions

# kz_timezone = pytz.timezone('Asia/Almaty')

# # Функция для экспорта транзакций в CSV с учетом часового пояса
# def export_transactions_to_csv(user_id):
#     transactions = get_transactions(user_id)
#     if not transactions:
#         return None

#     # Путь к файлу CSV
#     filename = f"transactions_{user_id}.csv"
    
#     with open(filename, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         # Заголовок CSV файла
#         writer.writerow(["ID", "User ID", "Username", "Amount", "Description", "Date"])
        
#         # Запись транзакций
#         for transaction in transactions:
#             # Получаем время транзакции (предположим, что оно в 6-й колонке)
#             transaction_time_utc = transaction[5]  # Время в формате UTC из базы данных

#             # Преобразуем строку времени в объект datetime
#             transaction_time = datetime.strptime(transaction_time_utc, '%Y-%m-%d %H:%M:%S')

#             # Преобразуем время из UTC в Казахстанский часовой пояс
#             transaction_time = pytz.utc.localize(transaction_time).astimezone(kz_timezone)

#             # Преобразуем время в строку в формате 'YYYY-MM-DD HH:MM:SS'
#             transaction_time_kz = transaction_time.strftime('%Y-%m-%d %H:%M:%S')

#             # Запись строки в файл
#             writer.writerow([transaction[0], transaction[1], transaction[2], transaction[3], transaction[4], transaction_time_kz])

#     return filename

# # Функция для экспорта транзакций в Excel с учетом часового пояса
# def export_transactions_to_excel(user_id):
#     transactions = get_transactions(user_id)
#     if not transactions:
#         return None

#     # Создаем новый Excel файл
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "Transactions"

#     # Заголовок Excel файла
#     ws.append(["ID", "User ID", "Username", "Amount", "Description", "Date"])

#     # Запись транзакций в файл
#     for transaction in transactions:
#         # Получаем время транзакции (предположим, что оно в 6-й колонке)
#         transaction_time_utc = transaction[5]  # Время в формате UTC из базы данных

#         # Преобразуем строку времени в объект datetime
#         transaction_time = datetime.strptime(transaction_time_utc, '%Y-%m-%d %H:%M:%S')

#         # Преобразуем время из UTC в Казахстанский часовой пояс
#         transaction_time = pytz.utc.localize(transaction_time).astimezone(kz_timezone)

#         # Преобразуем время в строку в формате 'YYYY-MM-DD HH:MM:SS'
#         transaction_time_kz = transaction_time.strftime('%Y-%m-%d %H:%M:%S')

#         # Запись строки в файл
#         ws.append([transaction[0], transaction[1], transaction[2], transaction[3], transaction[4], transaction_time_kz])

#     # Путь к файлу Excel
#     filename = f"transactions_{user_id}.xlsx"
#     wb.save(filename)

#     return filename

# # Функция для перевода текста в зависимости от языка
# def get_translated_text(language, key):
#     translations = {
#         'en': {
#             'welcome': "Hello! I'm your financial bot. How can I help you?\n/help",
#             'help': "Here are the commands you can use:\n/start - Welcome message\n/help - Show this message\n/balance - Show your transactions\n/add_income <amount> - Add income\n/add_expense <amount> - Add expense\n/export_excel - Exports transactions in Excel format.\n/export_csv - Exports transactions in CSV format.\n/choose_language - Change language",
#             'balance': "Your transactions:",
#             'add_income': "Income of {amount} added!",
#             'add_expense': "Expense of {amount} added!",
#             'no_transactions': "You have no transactions.",
#             'phone_requested': "Please send your phone number to complete registration.",
#             'phone_saved': "Your phone number has been saved successfully!\nTo continue, press /start"
#         },
#         'ru': {
#             'welcome': "Привет! Я бот для учета финансов. Чем могу помочь?\n/help",
#             'help': "Вот команды, которые вы можете использовать:\n/start - Приветственное сообщение\n/help - Показать это сообщение\n/balance - Показать список транзакций\n/add_income <сумма> - Добавить доход\n/add_expense <сумма> - Добавить расход\n/export_excel - Экспортирует транзакции в формат Excel.\n/export_csv - Экспортирует транзакции в формат CSV.\n/choose_language - Изменить язык",
#             'balance': "Ваши транзакции:",
#             'add_income': "Доход в размере {amount} добавлен!",
#             'add_expense': "Расход в размере {amount} добавлен!",
#             'no_transactions': "У вас нет транзакций.",
#             'phone_requested': "Пожалуйста, отправьте свой номер телефона для завершения регистрации.",
#             'phone_saved': "Ваш номер телефона был успешно сохранен!\nЧтобы продолжить, нажмите /start"
#         },
#         'kk': {
#             'welcome': "Сәлем! Мен қаржы боты боламын. Қалай көмектесе аламын?\n/help",
#             'help': "Мына командаларды қолдана аласыз:\n/start - Қош келдіңіз хабарламасы\n/help - Осы хабарламаны көрсету\n/balance - Сіздің транзакцияларыңызды көрсету\n/add_income <сомма> - Кіріс қосу\n/add_expense <сомма> - Шығыс қосу\n/export_excel - Транзакцияларды Excel форматында экспорттайды.\n/export_csv - Транзакцияларды CSV форматында экспорттайды.\n/choose_language - Тілді өзгерту",
#             'balance': "Сіздің транзакцияларыңыз:",
#             'add_income': "Кіріс {amount} соммасы қосылды!",
#             'add_expense': "Шығыс {amount} соммасы қосылды!",
#             'no_transactions': "Сіздің транзакцияларыңыз жоқ.",
#             'phone_requested': "Тіркелуді аяқтау үшін телефоныңызды жіберіңіз.",
#             'phone_saved': "Телефон нөміріңіз сәтті сақталды!\nЖалғастыру үшін /start басыңыз"
#         }
#     }
#     return translations.get(language, translations['en']).get(key, key)

# async def start(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     username = update.message.from_user.username  # Получаем username (никнейм)
#     language = get_user_language(user_id)
#     user = update.message.from_user
#     user_id = user.id
#     username = user.username
#     full_name = user.full_name

#     # Проверка на спам
#     if is_spamming(user_id):
#         await update.message.reply_text("Вы отправляете сообщения слишком быстро. Пожалуйста, не спамьте.")

#     if not language:
#         # Регистрируем пользователя по умолчанию с русским языком
#         add_user(user_id, username, 'ru')
#         language = 'ru'

#     # Обновляем время последней активности
#     update_last_activity(user_id)  # Здесь мы обновляем last_activity

#     # Выводим в терминал никнейм пользователя
#     print(f"User {username} (ID: {user_id}) started the bot.")  # Здесь выводим никнейм

#     # Проверка и добавление пользователя, если его нет в базе
#     if not get_user_language(user_id):
#         add_user(user_id, username)

#     # Проверяем, зарегистрирован ли пользователь
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
#     result = c.fetchone()
#     conn.close()

#     if result is None:
#         # Если пользователь не найден, регистрируем его
#         add_user(user_id, username)
#         message = "Welcome! You have been registered.\n \nДобро пожаловать! Вы зарегистрированы.\n \nҚош келдіңіз! Сіз тіркелдіңіз."
#     else:
#         # Если пользователь уже зарегистрирован, обновляем его активность
#         username = update.message.from_user.username
#         update_last_activity_and_log_in(user_id, username)
#         message = f"Welcome back, {username}! Last login: {result[6]}\n \nДобро пожаловать обратно, {username}! Последний вход: {result[6]}\n \nҚайтадан қош келдіңіз, {username}! Соңғы кіру: {result[6]}"

#     await update.message.reply_text(message)

#     # Проверяем, является ли пользователь администратором
#     if is_admin(user_id):
#         await update.message.reply_text(
#             f"Привет, {username}!\n"
#             "Вы зашли как администратор.\n"
#             "Для подробностей используйте команду\n/admin."
#         )

#     # Проверяем, указан ли номер телефона
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT phone_number FROM users WHERE telegram_id = ?", (user_id,))
#     result = c.fetchone()
#     conn.close()

#     if result and result[0] is None:  # Если телефонный номер пустой, запрашиваем его
#         keyboard = [
#             [KeyboardButton("Send phone number", request_contact=True)]
#         ]
#         reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
#         await update.message.reply_text(
#             get_translated_text(language, 'phone_requested'),
#             reply_markup=reply_markup
#         )
#     else:
#         text = get_translated_text(language, 'welcome')
#         await update.message.reply_text(text)

# async def admin_command(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):
#         await update.message.reply_text("Команды для администраторов ↓\n \n/add_admin — Добавляет пользователя как администратора.\n/remove_admin — Удаляет пользователя из списка администраторов.\n/list_admins — Выводит список всех администраторов.\n/list_users — Выводит список всех пользователей.\n/notify_admins — Отправляет уведомление всем администраторам.\n/clear_data — Очищает данные (например, пользователей или транзакции) в базе данных.\n/check_profile - Проверяет состояние аккаунта.")
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# # Команда /notify_admins
# async def notify_admins(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         # Сообщение для отправки всем администраторам
#         notification_message = " ".join(context.args) if context.args else "Default notification message."

#         admins = get_admins()
#         if admins:
#             for admin in admins:
#                 admin_telegram_id = admin[0]  # ID администратора
#                 try:
#                     await context.bot.send_message(admin_telegram_id, notification_message)
#                 except Exception as e:
#                     print(f"Error sending message to {admin_telegram_id}: {e}")
#             await update.message.reply_text("Notification sent to all admins.\n \nУведомление отправлено всем администраторам.\n \nХабарламаны барлық администраторларға жібердік.")
#         else:
#             await update.message.reply_text("There are no admins to notify.\n \nНет администраторов, которых нужно уведомить.\n \nХабарландыратын администраторлар жоқ.")
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# # Команда /add_admin
# async def add_admin(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         try:
#             new_admin_id = int(context.args[0])  # Получаем ID нового администратора из аргументов
#             add_admin_to_db(new_admin_id)  # Добавляем нового админа в базу данных
#             await update.message.reply_text(f"User {new_admin_id} has been added as an admin.\n \nПользователь {new_admin_id} добавлен в качестве администратора.\n \n Қолданушы {new_admin_id} администратор ретінде қосылды.")
#         except (IndexError, ValueError):
#             await update.message.reply_text("Please provide the Telegram ID of the user.\n \nУкажите, пожалуйста, идентификатор пользователя Telegram.\n \nTelegram пайдаланушының идентификаторын көрсетіңіз.")
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# # Команда /remove_admin
# async def remove_admin(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         try:
#             admin_id = int(context.args[0])  # Получаем ID администратора из аргументов
#             remove_admin_from_db(admin_id)  # Удаляем администратора из базы данных
#             await update.message.reply_text(f"User {admin_id} has been removed from admin.\n \nПользователь {admin_id} был удален из администратора.\n \nҚолданушы {admin_id} администратор ретінде өшірілді")
#         except (IndexError, ValueError):
#             await update.message.reply_text("Please provide the Telegram ID of the user.\n \nУкажите, пожалуйста, идентификатор пользователя Telegram.\n \nTelegram пайдаланушының идентификаторын көрсетіңіз.")
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# # Команда для администраторов, чтобы проверить подозрительный аккаунт
# async def check_profile(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id

#     if not is_admin(user_id):
#         await update.message.reply_text("Вы не являетесь администратором.")
#         return

#     target_user_id = int(context.args[0]) if context.args else None
#     if target_user_id is None:
#         await update.message.reply_text("Пожалуйста, укажите ID пользователя для проверки.")
#         return

#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT username, full_name FROM users WHERE telegram_id = ?", (target_user_id,))
#     result = c.fetchone()
#     conn.close()

#     if result:
#         username, full_name = result
#         # Проверяем, заполнены ли данные
#         if not username or not full_name:
#             await update.message.reply_text(f"Профиль пользователя {target_user_id} выглядит подозрительным. Заполните данные профиля.")
#         else:
#             await update.message.reply_text(f"Профиль пользователя {target_user_id}: {username}, {full_name}. Данные в порядке.")
#     else:
#         await update.message.reply_text(f"Пользователь с ID {target_user_id} не найден в базе.")

# # Команда /list_admins
# async def list_admins(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         admins = get_admins()
#         if admins:
#             message = "List of all admins:\nСписок всех администраторов:\nБарлық администраторлардың тізімі:\n \n"
#             for admin in admins:
#                 telegram_id = admin[0]
#                 username = admin[1] if admin[1] else "No username"
#                 message += f"ID: {telegram_id}, Username: @{username}\n"
#             await update.message.reply_text(message)
#         else:
#             await update.message.reply_text("There are no admins.\n \nАдминистраторов нет.\n \nАдминистраторлар жоқ.")
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# async def logout(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     logout_user(user_id)
#     await update.message.reply_text("You have successfully logged out.\n \nВы успешно вышли из системы.\n \nСіз системадан сәтті шықтыңыз.")

# async def login_history(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     username = update.message.from_user.username

#     # Получаем историю входов по user_id
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT login_time FROM login_history WHERE user_id = ? ORDER BY login_time DESC", (user_id,))
#     login_times = c.fetchall()
#     conn.close()

#     # Формируем ответ
#     if login_times:
#         message = "Your login history:\n \nВаша история входа:\n \nСіздің шығу тарихыңыз:\n"
#         for login_time in login_times:
#             message += f"{login_time[0]}\n"
#     else:
#         message = "No login history available.\n \nИстория входов отсутствует.\n \nКіру тарихы жоқ."

#     await update.message.reply_text(message)

# # Команда help
# async def help_command(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     language = get_user_language(user_id)
#     text = get_translated_text(language, 'help')
#     await update.message.reply_text(text)

# # Обработчик команды /add_income
# async def add_income(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     language = get_user_language(user_id)
    
#     try:
#         amount = float(context.args[0])  # Получаем сумму из аргументов
#         description = 'Доход'
#         add_transaction(user_id, amount, description)  # Добавляем транзакцию
#         await update.message.reply_text(get_translated_text(language, 'add_income').format(amount=amount))
#     except (IndexError, ValueError):
#         await update.message.reply_text("Please specify the amount in the correct format: /add_income <amount>\n \nПожалуйста, укажите сумму в правильном формате: /add_income <цифра>\n \nӨтініш, ақшаны дұрыс форматта көрсетіңіз: /add_income <сан>")

# # Команда для добавления расхода
# async def add_expense(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     language = get_user_language(user_id)
#     try:
#         amount = float(context.args[0])  # Получаем сумму из аргументов
#         description = 'Расход'
#         add_transaction(user_id, amount, description)
#         await update.message.reply_text(get_translated_text(language, 'add_expense').format(amount=amount))
#     except (IndexError, ValueError):
#         await update.message.reply_text("Please specify the amount in the correct format: /add_expense <amount>\n \nПожалуйста, укажите сумму в правильном формате: /add_expense <цифра>\n \nӨтініш, ақшаны дұрыс форматта көрсетіңіз: /add_expensel <сан>")

# # Команда для выбора языка
# async def choose_language(update: Update, context: CallbackContext) -> None:
#     keyboard = [
#         [InlineKeyboardButton("English", callback_data='en')],
#         [InlineKeyboardButton("Русский", callback_data='ru')],
#         [InlineKeyboardButton("Қазақша", callback_data='kk')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text("Please select your language / Выберите язык / Тіл таңдаңыз", reply_markup=reply_markup)

# # Обработчик для получения номера телефона
# async def handle_contact(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     phone_number = update.message.contact.phone_number

#     # Сохраняем номер телефона в базе данных
#     update_user_phone(user_id, phone_number)

#     # Подтверждаем сохранение номера
#     language = get_user_language(user_id)
#     await update.message.reply_text(get_translated_text(language, 'phone_saved'))

# # Команда /clear_data
# async def clear_data(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         # Запросим у пользователя, что именно нужно очистить
#         keyboard = [
#             [InlineKeyboardButton("Очистить данные пользователей.", callback_data="clear_users")],
#             [InlineKeyboardButton("Очистить транзакции.", callback_data="clear_transactions")],
#             [InlineKeyboardButton("Отмена.", callback_data="cancel_clear")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await update.message.reply_text("Что вы хотите очистить?", reply_markup=reply_markup)
#     else:
#         await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# # Обработчик выбора очистки данных
# async def clear_data_callback(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     user_id = query.from_user.id

#     if is_admin(user_id):
#         if query.data == "clear_users":
#             clear_users_data()
#             await query.edit_message_text("User data has been cleared.\n \nДанные пользователей были очищены.\n \nПайдаланушылардың деректері тазартылды.")
#         elif query.data == "clear_transactions":
#             clear_transactions_data()
#             await query.edit_message_text("Transactions have been cleared.\n \nТранзакции были очищены.\n \nТранзакциялар тазартылды.")
#         elif query.data == "cancel_clear":
#             await query.edit_message_text("The data clear operation was cancelled.\n \nОперация очищения данных отменена.\n \nДеректерді тазалау операциясы тоқтатылды.")
#     else:
#         await query.edit_message_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# async def balance(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     language = get_user_language(user_id)
    
#     # Получаем транзакции пользователя
#     transactions = get_transactions(user_id)

#     # Получаем баланс пользователя
#     conn = sqlite3.connect('transactions4.db')
#     c = conn.cursor()
#     c.execute("SELECT balance FROM users WHERE telegram_id = ?", (user_id,))
#     result = c.fetchone()
#     conn.close()

#     # Если баланс найден, показываем его
#     if result:
#         balance = result[0]
#     else:
#         balance = 0  # Если нет записи о балансе, возвращаем 0

#     # Формируем сообщение с транзакциями и балансом
#     if transactions:
#         message = get_translated_text(language, 'balance') + "\n"
#         for transaction in transactions:
#             message += f"ID: {transaction[0]}, Сумма: {transaction[2]}, Описание: {transaction[3]}, Дата: {transaction[4]}\n"
#         message += f"\nБаланс: {balance}"  # Добавляем текущий баланс
#     else:
#         message = get_translated_text(language, 'no_transactions') + f"\nБаланс: {balance}"

#     await update.message.reply_text(message)

# # Обработчик для изменения языка
# async def language_callback(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     user_id = query.from_user.id
#     language = query.data  # Получаем выбранный язык из callback_data

#     # Обновляем язык пользователя в базе данных
#     update_user_language(user_id, language)

#     # Отправляем сообщение, что язык был изменен
#     text = get_translated_text(language, 'welcome')
#     await query.answer()  # Подтверждаем обработку нажатия
#     await query.edit_message_text(text)  # Обновляем сообщение

# # Команда для экспорта транзакций в CSV
# async def export_csv(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id

#     # Экспорт транзакций в CSV
#     filename = export_transactions_to_csv(user_id)
#     if filename:
#         with open(filename, 'rb') as file:
#             await update.message.reply_document(document=file)
#         os.remove(filename)  # Удаляем файл после отправки
#     else:
#         await update.message.reply_text("You have no transactions to export.\n \nУ вас нет транзакций для экспорта.\n \nЭкспортталатын транзакцияларыңыз жоқ.")

# # Команда для экспорта транзакций в Excel
# async def export_excel(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id

#     # Экспорт транзакций в Excel
#     filename = export_transactions_to_excel(user_id)
#     if filename:
#         with open(filename, 'rb') as file:
#             await update.message.reply_document(document=file)
#         os.remove(filename)  # Удаляем файл после отправки
#     else:
#         await update.message.reply_text("You have no transactions to export.\n \nУ вас нет транзакций для экспорта.\n \nЭкспортталатын транзакцияларыңыз жоқ.")

# # Функция обработки сообщений
# async def handle_message(update: Update, context: CallbackContext) -> None:
#     user = update.message.from_user
#     user_id = user.id
    
#     # Проверка на спам
#     if is_spamming(user_id):
#         await update.message.reply_text("Вы отправляете слишком много сообщений. Пожалуйста, не спамьте.")
#     else:
#         await update.message.reply_text(f"Сообщение от {user.username}: {update.message.text}")

# # Команда для списка пользователей
# async def list_users(update: Update, context: CallbackContext) -> None:
#     user_id = update.effective_user.id
    
#     # Проверяем, является ли пользователь администратором
#     if not is_admin(user_id):
#         await update.message.reply_text("У вас нет доступа к списку пользователей.")
#         return

#     # Получаем список пользователей из базы данных
#     users = get_users_from_db()
#     if users:
#         users_text = "Список всех пользователей:\n"
#         for user in users:
#             user_id, telegram_id, username, phone_number = user
#             users_text += f"ID: {user_id}, Telegram ID: {telegram_id}, Username: @{username}, Телефон: {phone_number}\n"
#         await update.message.reply_text(users_text)
#     else:
#         await update.message.reply_text("Нет зарегистрированных пользователей.")

# # Команда для отображения истории входов
# async def login_history(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):
#         # Создаем клавиатуру с выбором
#         keyboard = [
#             [InlineKeyboardButton("Все входы", callback_data="view_all")],
#             [InlineKeyboardButton("Входы с конкретным пользователем", callback_data="view_with_user")],
#             [InlineKeyboardButton("Входы без username", callback_data="view_without_user")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await update.message.reply_text("Выберите, что вы хотите просмотреть:", reply_markup=reply_markup)
#     else:
#         await update.message.reply_text("У вас нет прав на использование этой команды.")

# # Обработчик выбора действия
# async def view_login_history_callback(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     user_id = query.from_user.id

#     if is_admin(user_id):
#         if query.data == "view_all":
#             await show_all_logins(query)
#         elif query.data == "view_with_user":
#             await show_logins_with_user(query)
#         elif query.data == "view_without_user":
#             await show_logins_without_user(query)
#         else:
#             await query.edit_message_text(f"Неизвестная команда: {query.data}")
#     else:
#         await query.edit_message_text("У вас нет прав на использование этой команды.")

# # Функция для отображения всех входов
# async def show_all_logins(query):
#     try:
#         conn = sqlite3.connect('transactions4.db')
#         c = conn.cursor()
#         c.execute("SELECT user_id, username, login_time FROM login_history ORDER BY login_time DESC")
#         logins = c.fetchall()
#         conn.close()

#         if logins:
#             message = "Все входы:\n"
#             for login in logins:
#                 message += f"User ID: {login[0]}, Username: {login[1] or 'None'} | Время входа: {login[2]}\n"
            
#             # Разбиваем сообщение на части, если оно слишком длинное
#             MAX_MESSAGE_LENGTH = 4096
#             if len(message) > MAX_MESSAGE_LENGTH:
#                 parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
#                 for part in parts:
#                     await query.edit_message_text(part)
#             else:
#                 await query.edit_message_text(message)
#         else:
#             await query.edit_message_text("Нет данных о входах.")
#     except Exception as e:
#         await query.edit_message_text(f"Ошибка: {e}")

# # Функция для отображения входов с конкретным пользователем (с выбором пользователя)
# async def show_logins_with_user(query):
#     try:
#         conn = sqlite3.connect('transactions4.db')
#         c = conn.cursor()
#         c.execute("SELECT DISTINCT username FROM login_history WHERE username IS NOT NULL")
#         users = c.fetchall()
#         conn.close()

#         if users:
#             keyboard = []
#             for user in users:
#                 username = user[0]
#                 encoded_username = urllib.parse.quote(username)  # Кодируем username в URL
#                 keyboard.append([InlineKeyboardButton(username, callback_data=f"view_user_{encoded_username}")])
            
#             keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
#             reply_markup = InlineKeyboardMarkup(keyboard)
#             await query.edit_message_text("Выберите пользователя для фильтрации входов:", reply_markup=reply_markup)
#         else:
#             await query.edit_message_text("Нет пользователей с именами для фильтрации.")
#     except Exception as e:
#         await query.edit_message_text(f"Ошибка: {e}")

# # Функция для отображения входов выбранного пользователя
# async def show_logins_for_user(query, username):
#     try:
#         # Декодируем username перед использованием в SQL запросе
#         decoded_username = urllib.parse.unquote(username)

#         conn = sqlite3.connect('transactions4.db')
#         c = conn.cursor()
#         c.execute("SELECT user_id, username, login_time FROM login_history WHERE username = ? ORDER BY login_time DESC", (decoded_username,))
#         logins = c.fetchall()
#         conn.close()

#         if logins:
#             message = f"Входы пользователя {decoded_username}:\n"
#             for login in logins:
#                 message += f"User ID: {login[0]} | Время входа: {login[2]}\n"
            
#             # Разбиваем сообщение на части, если оно слишком длинное
#             MAX_MESSAGE_LENGTH = 4096
#             if len(message) > MAX_MESSAGE_LENGTH:
#                 parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
#                 for part in parts:
#                     await query.edit_message_text(part)
#             else:
#                 await query.edit_message_text(message)
#         else:
#             await query.edit_message_text(f"Нет входов для пользователя {decoded_username}.")
#     except Exception as e:
#         await query.edit_message_text(f"Ошибка: {e}")

# # Функция для отображения входов без username
# async def show_logins_without_user(query):
#     try:
#         conn = sqlite3.connect('transactions4.db')
#         c = conn.cursor()
#         c.execute("SELECT user_id, username, login_time FROM login_history WHERE username IS NULL ORDER BY login_time DESC")
#         logins = c.fetchall()
#         conn.close()

#         if logins:
#             message = "Входы без username:\n"
#             for login in logins:
#                 message += f"User ID: {login[0]} | Время входа: {login[2]}\n"
            
#             # Разбиваем сообщение на части, если оно слишком длинное
#             MAX_MESSAGE_LENGTH = 4096
#             if len(message) > MAX_MESSAGE_LENGTH:
#                 parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
#                 for part in parts:
#                     await query.edit_message_text(part)
#             else:
#                 await query.edit_message_text(message)
#         else:
#             await query.edit_message_text("Нет входов без username.")
#     except Exception as e:
#         await query.edit_message_text(f"Ошибка: {e}")

# # Обработчик для выбора конкретного пользователя (после того, как был выбран пользовател)
# async def user_selection_callback(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     user_id = query.from_user.id

#     if is_admin(user_id):
#         # Проверяем, что имя пользователя корректное
#         if query.data.startswith("view_user_"):
#             # Извлекаем имя пользователя из callback_data и декодируем его
#             username = query.data.replace("view_user_", "")
#             decoded_username = urllib.parse.unquote(username)
#             await show_logins_for_user(query, decoded_username)
#         elif query.data == "cancel":
#             await query.edit_message_text("Операция отменена.")
#         else:
#             await query.edit_message_text(f"Неизвестная команда: {query.data}")
#     else:
#         await query.edit_message_text("У вас нет прав на использование этой команды.")

# # Запуск приложения
# def main():
#     add_username_column_to_login_history()
#     create_database()

#     # Создание приложения
#     application = Application.builder().token(TOKEN).build()

#     # Команда для просмотра истории входов
#     application.add_handler(CommandHandler("login_history", login_history))

#     # Обработчик нажатий на кнопки
#     application.add_handler(CallbackQueryHandler(view_login_history_callback, pattern="^(view_all|view_with_user|view_without_user)$"))

#     # Обработчик для выбора пользователя
#     application.add_handler(CallbackQueryHandler(user_selection_callback, pattern="^view_user_"))

#     # Обработчик для кнопки отмены
#     application.add_handler(CallbackQueryHandler(user_selection_callback, pattern="^cancel$"))

#     # Регистрируем обработчики команд
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("help", help_command))
#     application.add_handler(CommandHandler("balance", balance))
#     application.add_handler(CommandHandler("add_income", add_income))
#     application.add_handler(CommandHandler("logout", logout))
#     application.add_handler(CommandHandler("login_history", login_history))
#     application.add_handler(CommandHandler("add_expense", add_expense))
#     application.add_handler(CommandHandler("choose_language", choose_language))
#     application.add_handler(CommandHandler("admin", admin_command))
#     application.add_handler(CommandHandler("add_admin", add_admin))
#     application.add_handler(CommandHandler("remove_admin", remove_admin))
#     application.add_handler(CommandHandler("list_admins", list_admins))  # Команда для списка админов
#     application.add_handler(CommandHandler("notify_admins", notify_admins))  # Добавляем команду уведомлений для админов
#     application.add_handler(CommandHandler("clear_data", clear_data))  # Команда для очистки данных
#     application.add_handler(CallbackQueryHandler(clear_data_callback))  # Обработчик для выбора очистки данных
#     application.add_handler(CommandHandler("check_profile", check_profile))  # Команда для проверки профиля администратором
#     application.add_handler(CommandHandler("list_users", list_users))  # Команда для списка пользв.


#     # Регистрируем обработчики команд
#     application.add_handler(CommandHandler("export_csv", export_csv))
#     application.add_handler(CommandHandler("export_excel", export_excel))

#     # Регистрируем обработчик выбора языка
#     application.add_handler(CallbackQueryHandler(language_callback))

#     # Регистрируем обработчик для получения номера телефона
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Для всех текстовых сообщений
#     # Запускаем бота
#     application.run_polling()

# if __name__ == '__main__':
#     main()

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime
import pytz
import csv
import os
import time
from openpyxl import Workbook
import urllib.parse  # Для кодирования/декодирования имени пользователя

# Токен вашего бота
TOKEN = '8031537354:AAGWj9NsFcP8_NV7CSvKWPz7L1EQcG4WDIw'

# Словарь для преобразования русской раскладки в латинскую
KEYBOARD_TRANSLIT = {
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i',
    'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']', 'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f',
    'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
    'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm', 'б': ',',
    'ю': '.', 'я': '/', 'ё': '`', ' ': ' '
}

# Глобальная переменная для хранения времени сообщений
user_message_times = {}

# Порог для "подозрительных" сообщений: 5 сообщений за 10 секунд
MAX_MESSAGES = 5  # Максимум сообщений за 10 секунд
TIME_LIMIT = 10   # Время, за которое проверяются сообщения (в секундах)

def translit(text: str) -> str:
    """Функция для преобразования русских букв в латинские."""
    return ''.join(KEYBOARD_TRANSLIT.get(c, c) for c in text.lower())

# Функция для добавления или обновления пользователя в базе данных
def add_or_update_user(user_id, username, full_name):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    is_verified BOOLEAN DEFAULT 0)''')
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    user = c.fetchone()
    if user:
        c.execute("UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?", (username, full_name, user_id))
    else:
        c.execute("INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
    conn.commit()
    conn.close()

# Функция для получения списка пользователей из базы данных
def get_users_from_db():
    # Подключение к базе данных SQLite
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Запрос на получение всех пользователей
    c.execute("SELECT id, telegram_id, username, phone_number FROM users")
    users = c.fetchall()

    # Закрытие соединения с базой данных
    conn.close()

    return users

# Функция для проверки активности пользователя
def is_spamming(user_id):
    current_time = time.time()
    
    # Если пользователя нет в словаре, создаём для него новый список сообщений
    if user_id not in user_message_times:
        user_message_times[user_id] = []
    
    # Очищаем старые сообщения (старше чем TIME_LIMIT секунд)
    user_message_times[user_id] = [timestamp for timestamp in user_message_times[user_id] if current_time - timestamp < TIME_LIMIT]
    
    # Добавляем текущее время
    user_message_times[user_id].append(current_time)
    
    # Если количество сообщений больше лимита, считаем, что это спам
    if len(user_message_times[user_id]) > MAX_MESSAGES:
        return True
    return False

# Подключение к базе данных для пользователей и транзакций
def create_database():
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Создание таблицы пользователей с дополнительными полями
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            language TEXT DEFAULT 'en',
            phone_number TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            balance REAL DEFAULT 0
        )
    ''')

    # Создание таблицы для транзакций
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions4 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Таблица для истории входов с user_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# Функция для добавления администратора
def add_admin(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()
        print(f"User {telegram_id} has been added as an admin.")
    except sqlite3.IntegrityError:
        print(f"User {telegram_id} is already an admin.")
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect('transactions4.db')  # Замените на имя вашей базы данных
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")  # Получаем ID всех пользователей
    users = c.fetchall()
    conn.close()
    return users

# Пример добавления нового админа:
add_admin(996317285)  # Замените на ID нового администратора

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Функция для добавления нового администратора в базу данных
def add_admin_to_db(telegram_id):
    try:
        conn = sqlite3.connect('transactions4.db')  # Открываем базу данных
        c = conn.cursor()

        # Используем INSERT OR IGNORE, чтобы избежать ошибки при дублировании
        c.execute("INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)", (telegram_id,))
        
        conn.commit()  # Сохраняем изменения
        conn.close()  # Закрываем соединение
        print(f"Администратор с ID {telegram_id} успешно добавлен или уже существует.")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении администратора: {e}")
# Пример использования функции
new_admin_id = 996317285  # Замените на реальный Telegram ID
add_admin_to_db(new_admin_id)

# Удалить админа из базы данных
def remove_admin_from_db(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

# Функция для получения списка администраторов с username
def get_admins():
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("""
        SELECT a.telegram_id, u.username
        FROM admins a
        LEFT JOIN users u ON a.telegram_id = u.telegram_id
    """)
    admins = c.fetchall()
    conn.close()
    return admins

def add_user(telegram_id, username=None, language='en', phone_number=None):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Получаем текущее время с учетом временной зоны
    current_time = get_current_time()

    c.execute("INSERT INTO users (telegram_id, username, language, phone_number, registration_date) VALUES (?, ?, ?, ?, ?)", 
              (telegram_id, username, language, phone_number, current_time))
    conn.commit()
    conn.close()

def get_current_time():
    # Указываем временную зону для Казахстана (UTC+6)
    tz = pytz.timezone('Asia/Almaty')  # Казахстан, UTC+6
    now = datetime.now(tz)  # Получаем текущее время в выбранной временной зоне

    # Форматируем время так, чтобы оно не содержало микросекунд и временной зоны
    return now.strftime('%Y-%m-%d %H:%M:%S')  # Только дата и время

def update_last_activity_and_log_in(user_id, username):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Вставляем запись в историю логинов
    c.execute("INSERT INTO login_history (user_id, username, login_time) VALUES (?, ?, ?)",
              (user_id, username, get_current_time()))
    conn.commit()
    conn.close()

def update_last_activity_and_log_in(telegram_id, username):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Получаем user_id для пользователя
    c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()

    if user:
        user_id = user[0]
    else:
        # Если пользователь не найден, создаем нового
        add_user(telegram_id, username)
        user_id = c.lastrowid

    current_time = get_current_time()

    # Обновление времени последней активности пользователя
    c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))

    # Добавление записи о входе в историю с user_id и username
    c.execute("INSERT INTO login_history (user_id, username, login_time) VALUES (?, ?, ?)", 
              (user_id, username, current_time))

    conn.commit()
    conn.close()

def add_username_column_to_login_history():
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Проверяем, существует ли уже колонка 'username' в таблице login_history
    c.execute("PRAGMA table_info(login_history);")
    columns = c.fetchall()
    
    # Извлекаем список имен столбцов
    column_names = [column[1] for column in columns]

    if 'username' not in column_names:
        # Если столбца нет, добавляем его
        c.execute("PRAGMA foreign_keys=off;")  # Отключаем ограничения внешнего ключа для изменения структуры таблицы
        c.execute('''
            ALTER TABLE login_history
            ADD COLUMN username TEXT;
        ''')
        c.execute("PRAGMA foreign_keys=on;")  # Включаем ограничения внешнего ключа обратно
        print("Column 'username' added to login_history table.")
    else:
        print("Column 'username' already exists in login_history table.")

    conn.commit()
    conn.close()

# Функция для очистки данных пользователей
def clear_users_data():
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("DELETE FROM users")
    c.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'users'")  # Сбросить ID
    conn.commit()
    conn.close()

# Функция для очистки транзакций
def clear_transactions_data():
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions4")
    c.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'transactions4'")  # Сбросить ID
    conn.commit()
    conn.close()

def logout_user(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    current_time = get_current_time()

    # Обновление последней активности при выходе
    c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))

    conn.commit()
    conn.close()

# Функция для обновления времени последней активности пользователя
def update_last_activity(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Получаем текущее время с учетом временной зоны (KZT - UTC+6)
    current_time = get_current_time()
    
    print(f"Updating last activity for user {telegram_id} to {current_time}")  # Для отладки

    # Обновляем запись в базе данных
    c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))
    conn.commit()

    # Проверим, обновлена ли строка в базе данных
    c.execute("SELECT last_activity FROM users WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()

    if result:
        print(f"Last activity successfully updated: {result[0]}")  # Для отладки
    else:
        print(f"No user found with telegram_id {telegram_id}")  # Для отладки

    conn.close()

# Функция для обновления языка пользователя
def update_user_language(telegram_id, language):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
    conn.commit()
    conn.close()

# Функция для получения данных из базы данных
def get_user_phone_from_db(user_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT phone_number FROM users WHERE telegram_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

# Функция для обновления телефона пользователя
def save_user_phone_to_db(user_id, phone_number):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ?", (phone_number, user_id))
    conn.commit()
    conn.close()

def update_last_activity(telegram_id):
    try:
        conn = sqlite3.connect('transactions4.db')
        conn.isolation_level = None  # Отключаем авто-commit для явного контроля транзакций
        c = conn.cursor()

        # Получаем текущее время с учетом временной зоны (KZT - UTC+6)
        current_time = get_current_time()

        print(f"Updating last activity for user {telegram_id} to {current_time}")  # Для отладки

        # Начинаем транзакцию
        c.execute("BEGIN TRANSACTION;")
        
        # Обновляем запись в базе данных
        c.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (current_time, telegram_id))
        conn.commit()  # Фиксируем изменения

        # Проверим, обновлена ли строка в базе данных
        c.execute("SELECT last_activity FROM users WHERE telegram_id = ?", (telegram_id,))
        result = c.fetchone()

        if result:
            print(f"Last activity successfully updated: {result[0]}")  # Для отладки
        else:
            print(f"No user found with telegram_id {telegram_id}")  # Для отладки

    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
    finally:
        conn.close()  # Обязательно закрываем соединение после завершения работы

# Функция для получения информации о пользователе
def get_user_language(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Функция для получения username пользователя
def get_user_username(telegram_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_transaction(user_id, amount, description):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Получаем текущее время с учетом временной зоны
    current_time = get_current_time()  # Например, '2024-11-28 10:18:00'
    
    # Вставляем транзакцию с правильным временем
    c.execute('''
        INSERT INTO transactions4 (user_id, amount, description, date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, amount, description, current_time))
    
    # Получаем id пользователя и его текущий баланс
    c.execute("SELECT id, balance FROM users WHERE telegram_id = ?", (user_id,))
    user = c.fetchone()
    
    if user:
        user_id_in_db = user[0]  # id пользователя в базе данных
        current_balance = user[1]  # Текущий баланс
        
        # Обновляем баланс пользователя: добавляем сумму к текущему балансу (для дохода или расхода)
        new_balance = current_balance + amount  # Для дохода: увеличиваем, для расхода: уменьшаем
        c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id_in_db))
        
        # Добавляем транзакцию в таблицу транзакций
        c.execute("INSERT INTO transactions4 (user_id, amount, description) VALUES (?, ?, ?)",
                  (user_id_in_db, amount, description))
        conn.commit()
    conn.close()

# Функция для получения транзакций пользователя
def get_transactions(user_id):
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()

    # Получаем id пользователя
    c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
    user = c.fetchone()

    if user:    
        user_id_in_db = user[0]  # id пользователя в базе данных
        # c.execute("SELECT * FROM transactions4 WHERE user_id = ? ORDER BY date DESC", (user_id_in_db,))
        # Выполняем JOIN для получения данных о транзакциях и username
        c.execute("""
            SELECT t.id, t.user_id, u.username, t.amount, t.description, t.date
            FROM transactions4 t
            JOIN users u ON t.user_id = u.id
            WHERE t.user_id = ? ORDER BY t.date DESC
        """, (user_id_in_db,))
        transactions = c.fetchall()
    else:
        transactions = []

    conn.close()
    return transactions

kz_timezone = pytz.timezone('Asia/Almaty')

# Функция для экспорта транзакций в CSV с учетом часового пояса
def export_transactions_to_csv(user_id):
    transactions = get_transactions(user_id)
    if not transactions:
        return None

    # Путь к файлу CSV
    filename = f"transactions_{user_id}.csv"
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Заголовок CSV файла
        writer.writerow(["ID", "User ID", "Username", "Amount", "Description", "Date"])
        
        # Запись транзакций
        for transaction in transactions:
            # Получаем время транзакции (предположим, что оно в 6-й колонке)
            transaction_time_utc = transaction[5]  # Время в формате UTC из базы данных

            # Преобразуем строку времени в объект datetime
            transaction_time = datetime.strptime(transaction_time_utc, '%Y-%m-%d %H:%M:%S')

            # Преобразуем время из UTC в Казахстанский часовой пояс
            transaction_time = pytz.utc.localize(transaction_time).astimezone(kz_timezone)

            # Преобразуем время в строку в формате 'YYYY-MM-DD HH:MM:SS'
            transaction_time_kz = transaction_time.strftime('%Y-%m-%d %H:%M:%S')

            # Запись строки в файл
            writer.writerow([transaction[0], transaction[1], transaction[2], transaction[3], transaction[4], transaction_time_kz])

    return filename

# Функция для экспорта транзакций в Excel с учетом часового пояса
def export_transactions_to_excel(user_id):
    transactions = get_transactions(user_id)
    if not transactions:
        return None

    # Создаем новый Excel файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Заголовок Excel файла
    ws.append(["ID", "User ID", "Username", "Amount", "Description", "Date"])

    # Запись транзакций в файл
    for transaction in transactions:
        # Получаем время транзакции (предположим, что оно в 6-й колонке)
        transaction_time_utc = transaction[5]  # Время в формате UTC из базы данных

        # Преобразуем строку времени в объект datetime
        transaction_time = datetime.strptime(transaction_time_utc, '%Y-%m-%d %H:%M:%S')

        # Преобразуем время из UTC в Казахстанский часовой пояс
        transaction_time = pytz.utc.localize(transaction_time).astimezone(kz_timezone)

        # Преобразуем время в строку в формате 'YYYY-MM-DD HH:MM:SS'
        transaction_time_kz = transaction_time.strftime('%Y-%m-%d %H:%M:%S')

        # Запись строки в файл
        ws.append([transaction[0], transaction[1], transaction[2], transaction[3], transaction[4], transaction_time_kz])

    # Путь к файлу Excel
    filename = f"transactions_{user_id}.xlsx"
    wb.save(filename)

    return filename

# Функция для перевода текста в зависимости от языка
def get_translated_text(language, key):
    translations = {
        'en': {
            'welcome': "Hello! I'm your financial bot. How can I help you?\n/help",
            'help': "Here are the commands you can use:\n/start - Welcome message\n/help - Show this message\n/balance - Show your transactions\n/add_income <amount> - Add income\n/add_expense <amount> - Add expense\n/export_excel - Exports transactions in Excel format.\n/export_csv - Exports transactions in CSV format.",
            'balance': "Your transactions:",
            'add_income': "Income of {amount} added!",
            'add_expense': "Expense of {amount} added!",
            'no_transactions': "You have no transactions.",
            'phone_requested': "Please send your phone number to complete registration.",
            'phone_saved': "Your phone number has been saved successfully!\nTo continue, press /start"
        },
        'ru': {
            'welcome': "Привет! Я бот для учета финансов. Чем могу помочь?\n/help",
            'help': "Вот команды, которые вы можете использовать:\n/start - Приветственное сообщение\n/help - Показать это сообщение\n/balance - Показать список транзакций\n/add_income <сумма> - Добавить доход\n/add_expense <сумма> - Добавить расход\n/export_excel - Экспортирует транзакции в формат Excel.\n/export_csv - Экспортирует транзакции в формат CSV.",
            'balance': "Ваши транзакции:",
            'add_income': "Доход в размере {amount} добавлен!",
            'add_expense': "Расход в размере {amount} добавлен!",
            'no_transactions': "У вас нет транзакций.",
            'phone_requested': "Пожалуйста, отправьте свой номер телефона для завершения регистрации.",
            'phone_saved': "Ваш номер телефона был успешно сохранен!\nЧтобы продолжить, нажмите /start"
        },
        'kk': {
            'welcome': "Сәлем! Мен қаржы боты боламын. Қалай көмектесе аламын?\n/help",
            'help': "Мына командаларды қолдана аласыз:\n/start - Қош келдіңіз хабарламасы\n/help - Осы хабарламаны көрсету\n/balance - Сіздің транзакцияларыңызды көрсету\n/add_income <сомма> - Кіріс қосу\n/add_expense <сомма> - Шығыс қосу\n/export_excel - Транзакцияларды Excel форматында экспорттайды.\n/export_csv - Транзакцияларды CSV форматында экспорттайды.",
            'balance': "Сіздің транзакцияларыңыз:",
            'add_income': "Кіріс {amount} соммасы қосылды!",
            'add_expense': "Шығыс {amount} соммасы қосылды!",
            'no_transactions': "Сіздің транзакцияларыңыз жоқ.",
            'phone_requested': "Тіркелуді аяқтау үшін телефоныңызды жіберіңіз.",
            'phone_saved': "Телефон нөміріңіз сәтті сақталды!\nЖалғастыру үшін /start басыңыз"
        }
    }
    return translations.get(language, translations['en']).get(key, key)

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username  # Получаем username (никнейм)
    language = get_user_language(user_id)
    user = update.message.from_user
    user_id = user.id
    username = user.username
    full_name = user.full_name

    # Проверяем, есть ли у пользователя номер телефона
    phone_data = get_user_phone_from_db(user_id)

    # Проверка на спам
    if is_spamming(user_id):
        await update.message.reply_text("Вы отправляете сообщения слишком быстро. Пожалуйста, не спамьте.")

    if not language:
        # Регистрируем пользователя по умолчанию с русским языком
        add_user(user_id, username, 'ru')
        language = 'ru'

    # Обновляем время последней активности
    update_last_activity(user_id)  # Здесь мы обновляем last_activity

    # Выводим в терминал никнейм пользователя
    print(f"User {username} (ID: {user_id}) started the bot.")  # Здесь выводим никнейм

    # Проверка и добавление пользователя, если его нет в базе
    if not get_user_language(user_id):
        add_user(user_id, username)

    # Проверяем, зарегистрирован ли пользователь
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    if result is None:
        # Если пользователь не найден, регистрируем его
        add_user(user_id, username)
        message = "Welcome! You have been registered.\n \nДобро пожаловать! Вы зарегистрированы.\n \nҚош келдіңіз! Сіз тіркелдіңіз."
    else:
        # Если пользователь уже зарегистрирован, обновляем его активность
        username = update.message.from_user.username
        update_last_activity_and_log_in(user_id, username)
        message = f"Welcome, {username}! Last login: {result[6]}\n \nДобро пожаловать, {username}! Последний вход: {result[6]}\n \nҚош келдіңіз, {username}! Соңғы кіру: {result[6]}"

    await update.message.reply_text(message)

    # Проверяем, является ли пользователь администратором
    if is_admin(user_id):
        await update.message.reply_text(
            f"Привет, {username}!\n"
            "Вы зашли как администратор.\n"
            "Для подробностей используйте команду\n/admin."
        )

    if phone_data and phone_data[0] is None:  # Если номера нет, запрашиваем его
        keyboard = [
            [KeyboardButton("Send phone number", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "Для завершение регистрации отправьте свой номер телефона.",  # Замените на перевод
            reply_markup=reply_markup
        )
    elif not phone_data:  # Если данные вообще отсутствуют (новый пользователь)
        # await update.message.reply_text("We need your phone number to proceed. Please send it.")
        keyboard = [
            [KeyboardButton("Send phone number", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "Для завершение регистрации отправьте свой номер телефона.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("\n/help - Помощь")  # Ответ, если телефон уже есть

async def admin_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):
        await update.message.reply_text("Команды для администраторов ↓\n \n/add_admin — Добавляет пользователя как администратора.\n/remove_admin — Удаляет пользователя из списка администраторов.\n/list_admins — Выводит список всех администраторов.\n/list_users — Выводит список всех пользователей.\n/notify_admins — Отправляет уведомление всем администраторам.\n/notify_users — Отправляет уведомление всем пользователям.\n/clear_data — Очищает данные (например, пользователей или транзакции) в базе данных.\n/check_profile - Проверяет состояние аккаунта.\n/login_history - Посмотреть все входы.")
    else:
        await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# Команда /notify_admins
async def notify_admins(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username  # Получаем имя пользователя, который вызвал команду
    full_name = update.message.from_user.full_name  # Получаем полное имя пользователя
    language = "en"  # Или используйте текущий язык пользователя, если это необходимо

    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        # Получаем сообщение для отправки
        if context.args:
            notification_message = " ".join(context.args)  # Собираем сообщение из аргументов
        else:
            # Если аргументов нет, уведомляем пользователя, что нужно ввести сообщение
            await update.message.reply_text(
                "Please provide a notification message.\n \nПожалуйста, укажите сообщение для уведомления.\n \nХабарлама мәтінін көрсетіңіз."
            )
            return

        # Логируем, кто отправил уведомление
        print(f"Admin {full_name} (@{username}) ID {user_id} отправляет уведомление.")

        # Получаем список администраторов
        admins = get_admins()
        if admins:
            for admin in admins:
                admin_telegram_id = admin[0]  # ID администратора
                try:
                    # Отправляем уведомление всем администраторам, добавив информацию о пользователе
                    await context.bot.send_message(
                        admin_telegram_id,
                        f"Уведомление от {full_name} (@{username}):\n\n{notification_message}"
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения {admin_telegram_id}: {e}")

            # Подтверждение успешной отправки уведомления
            await update.message.reply_text(
                "Notification sent to all admins.\n \nУведомление отправлено всем администраторам.\n \nХабарламаны барлық администраторларға жібердік."
            )
        else:
            # Если администраторов нет
            await update.message.reply_text(
                "There are no admins to notify.\n \nНет администраторов, которых нужно уведомить.\n \nХабарландыратын администраторлар жоқ."
            )
    else:
        # Если пользователь не является администратором
        await update.message.reply_text(
            "You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ."
        )

# async def notify_admins(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.from_user.id
#     if is_admin(user_id):  # Проверяем, является ли пользователь администратором
#         # Получаем сообщение для отправки
#         if context.args:
#             notification_message = " ".join(context.args)  # Собираем сообщение из аргументов
#         else:
#             # Если аргументов нет, уведомляем пользователя, что нужно ввести сообщение
#             await update.message.reply_text(
#                 "Please provide a notification message.\n \nПожалуйста, укажите сообщение для уведомления.\n \nХабарлама мәтінін көрсетіңіз."
#             )
#             return

#         # Получаем список администраторов
#         admins = get_admins()
#         if admins:
#             for admin in admins:
#                 admin_telegram_id = admin[0]  # ID администратора
#                 try:
#                     # Отправляем уведомление всем администраторам
#                     await context.bot.send_message(admin_telegram_id, notification_message)
#                 except Exception as e:
#                     print(f"Error sending message to {admin_telegram_id}: {e}")

#             # Подтверждение успешной отправки уведомления
#             await update.message.reply_text(
#                 "Notification sent to all admins.\n \nУведомление отправлено всем администраторам.\n \nХабарламаны барлық администраторларға жібердік."
#             )
#         else:
#             # Если администраторов нет
#             await update.message.reply_text(
#                 "There are no admins to notify.\n \nНет администраторов, которых нужно уведомить.\n \nХабарландыратын администраторлар жоқ."
#             )
#     else:
#         # Если пользователь не является администратором
#         await update.message.reply_text(
#             "You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ."
#         )

# Команда /notify_users

async def notify_users(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username  # Получаем имя пользователя, который вызвал команду
    full_name = update.message.from_user.full_name  # Получаем полное имя пользователя
    language = "en"  # Или используйте текущий язык пользователя, если это необходимо

    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        # Получаем сообщение для отправки
        if context.args:
            notification_message = " ".join(context.args)  # Собираем сообщение из аргументов
        else:
            # Если аргументов нет, уведомляем пользователя, что нужно ввести сообщение
            await update.message.reply_text(
                "Please provide a notification message.\n \nПожалуйста, укажите сообщение для уведомления.\n \nХабарлама мәтінін көрсетіңіз."
            )
            return

        # Логируем, кто отправил уведомление
        print(f"Admin {full_name} (@{username}) ID {user_id} отправляет уведомление всем пользователям.")

        # Получаем список всех пользователей из базы данных
        users = get_all_users()
        if users:
            for user in users:
                user_telegram_id = user[0]  # ID пользователя
                try:
                    # Отправляем уведомление каждому пользователю
                    await context.bot.send_message(
                        user_telegram_id,
                        f"Уведомление от {full_name} (@{username}):\n\n{notification_message}"
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения {user_telegram_id}: {e}")

            # Подтверждение успешной отправки уведомления
            await update.message.reply_text(
                "Notification sent to all users.\n \nУведомление отправлено всем пользователям.\n \nХабарламаны барлық пайдаланушыларға жібердік."
            )
        else:
            # Если пользователей нет
            await update.message.reply_text(
                "There are no users to notify.\n \nНет пользователей, которых нужно уведомить.\n \nХабарландыратын пайдаланушылар жоқ."
            )
    else:
        # Если пользователь не является администратором
        await update.message.reply_text(
            "You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ."
        )

# Преобразуем команду в правильную раскладку
async def handle_invalid_command(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.lower()
    
    # Проверка, если команда была введена с ошибочной раскладкой
    if user_input.startswith('/'):
        corrected_command = translit(user_input[1:])  # Преобразуем команду без '/'
        
        # Проверяем, если команда после трансляции существует
        if corrected_command in ["start", "help", "balance", "add_income", "logout", "login_history", "add_expense", "admin", "add_admin", "remove_admin", "list_admins", "list_users", "notify_admins", "notify_users", "clear_data", "check_profile"]:
            await update.message.reply_text(
                f"Вы случайно написали команду как {user_input}. Правильная команда: /{corrected_command}."
            )
            # В случае необходимости, вызовите обработчик для правильной команды
            # Пример: await start(update, context)
        else:
            await update.message.reply_text(f"Команда '{user_input}' не существует. Попробуйте снова.")

# Команда /add_admin
async def add_admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        try:
            new_admin_id = int(context.args[0])  # Получаем ID нового администратора из аргументов
            add_admin_to_db(new_admin_id)  # Добавляем нового админа в базу данных
            await update.message.reply_text(f"User {new_admin_id} has been added as an admin.\n \nПользователь {new_admin_id} добавлен в качестве администратора.\n \n Қолданушы {new_admin_id} администратор ретінде қосылды.")
        except (IndexError, ValueError):
            await update.message.reply_text("Please provide the Telegram ID of the user.\n \nУкажите, пожалуйста, идентификатор пользователя Telegram.\n \nTelegram пайдаланушының идентификаторын көрсетіңіз.")
    else:
        await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# Команда /remove_admin
async def remove_admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        try:
            admin_id = int(context.args[0])  # Получаем ID администратора из аргументов
            remove_admin_from_db(admin_id)  # Удаляем администратора из базы данных
            await update.message.reply_text(f"User {admin_id} has been removed from admin.\n \nПользователь {admin_id} был удален из администратора.\n \nҚолданушы {admin_id} администратор ретінде өшірілді")
        except (IndexError, ValueError):
            await update.message.reply_text("Please provide the Telegram ID of the user.\n \nУкажите, пожалуйста, идентификатор пользователя Telegram.\n \nTelegram пайдаланушының идентификаторын көрсетіңіз.")
    else:
        await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# Команда для администраторов, чтобы проверить подозрительный аккаунт
async def check_profile(update: Update, context: CallbackContext) -> None:
    try:
        target_user_id = int(context.args[0]) if context.args else None
        if target_user_id is None:
            await update.message.reply_text("Пожалуйста, укажите ID пользователя для проверки.")
            return

        # Подключаемся к базе данных
        conn = sqlite3.connect('transactions4.db')
        c = conn.cursor()
        
        # Выполняем запрос для получения всех необходимых данных
        c.execute("SELECT id, telegram_id, username, phone_number FROM users WHERE telegram_id = ?", (target_user_id,))
        result = c.fetchone()
        conn.close()

        # Проверяем, что результат не пустой
        if result:
            user_id, telegram_id, username, phone_number = result

            # Проверка на пустые поля
            if not username or username.strip() == "":
                await update.message.reply_text(f"Профиль пользователя {target_user_id} выглядит подозрительным. Заполните данные профиля (username).")
            elif not phone_number or phone_number.strip() == "":
                await update.message.reply_text(f"Профиль пользователя {target_user_id} выглядит подозрительным. Заполните данные профиля (телефон).")
            else:
                # Если все данные заполнены, показываем их в порядке
                await update.message.reply_text(f"Профиль пользователя {target_user_id}: "
                                                f"ID: {user_id}, Telegram ID: {telegram_id}, "
                                                f"Username: @{username}, Телефон: {phone_number}. Данные в порядке.")
        else:
            await update.message.reply_text(f"Пользователь с ID {target_user_id} не найден в базе.")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")

# Команда /list_admins
async def list_admins(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        admins = get_admins()
        if admins:
            message = "List of all admins:\nСписок всех администраторов:\nБарлық администраторлардың тізімі:\n \n"
            for admin in admins:
                telegram_id = admin[0]
                username = admin[1] if admin[1] else "No username"
                message += f"ID: {telegram_id}, Username: @{username}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("There are no admins.\n \nАдминистраторов нет.\n \nАдминистраторлар жоқ.")
    else:
        await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

async def logout(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    logout_user(user_id)
    await update.message.reply_text("You have successfully logged out.\n \nВы успешно вышли из системы.\n \nСіз системадан сәтті шықтыңыз.")

async def login_history(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Получаем историю входов по user_id
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT login_time FROM login_history WHERE user_id = ? ORDER BY login_time DESC", (user_id,))
    login_times = c.fetchall()
    conn.close()

    # Формируем ответ
    if login_times:
        message = "Your login history:\n \nВаша история входа:\n \nСіздің шығу тарихыңыз:\n"
        for login_time in login_times:
            message += f"{login_time[0]}\n"
    else:
        message = "No login history available.\n \nИстория входов отсутствует.\n \nКіру тарихы жоқ."

    await update.message.reply_text(message)

# Команда help
async def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)
    text = get_translated_text(language, 'help')
    await update.message.reply_text(text)

# Обработчик команды /add_income
async def add_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)
    
    try:
        amount = float(context.args[0])  # Получаем сумму из аргументов
        description = 'Доход'
        add_transaction(user_id, amount, description)  # Добавляем транзакцию
        await update.message.reply_text(get_translated_text(language, 'add_income').format(amount=amount))
    except (IndexError, ValueError):
        await update.message.reply_text("Please specify the amount in the correct format: /add_income <amount>\n \nПожалуйста, укажите сумму в правильном формате: /add_income <цифра>\n \nӨтініш, ақшаны дұрыс форматта көрсетіңіз: /add_income <сан>")

# Команда для добавления расхода
async def add_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)
    try:
        amount = float(context.args[0])  # Получаем сумму из аргументов
        description = 'Расход'
        add_transaction(user_id, amount, description)
        await update.message.reply_text(get_translated_text(language, 'add_expense').format(amount=amount))
    except (IndexError, ValueError):
        await update.message.reply_text("Please specify the amount in the correct format: /add_expense <amount>\n \nПожалуйста, укажите сумму в правильном формате: /add_expense <цифра>\n \nӨтініш, ақшаны дұрыс форматта көрсетіңіз: /add_expensel <сан>")

# # Функция для обработки контактов
# async def handle_contact(update: Update, context: CallbackContext):
#     user_id = update.message.from_user.id
#     contact = update.message.contact
#     phone_number = contact.phone_number  # Номер телефона
#     username = update.message.from_user.username

#     # Получаем номер телефона
#     phone_number = contact.phone_number

    # # Сохраняем номер телефона в базе данных
    # conn = sqlite3.connect('transactions4.db')
    # c = conn.cursor()
    # c.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ?", (phone_number, user_id))
    # conn.commit()
    # conn.close()

#     # Ответ пользователю
#     await update.message.reply_text(f"Спасибо, {username}! Ваш номер телефона {phone_number} был успешно сохранен.")

# Функция для обработки номера телефона
async def handle_phone(update, context):
    user_id = update.message.from_user.id
    phone_number = update.message.contact.phone_number

    # Проверяем, что номер телефона получен
    if phone_number:
        # Сохраняем номер телефона в базе данных
        save_user_phone_to_db(user_id, phone_number)
        await update.message.reply_text("Ваш номер телефона был успешно сохранен!\n/help - Помощь")
    else:
        await update.message.reply_text("Я не получил действительный номер телефона. Попробуйте еще раз.")
    # await update.message.reply_text("Ваш номер телефона был успешно сохранен!\n/help - Помощь")

# Команда /clear_data
async def clear_data(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):  # Проверяем, является ли пользователь администратором
        # Запросим у пользователя, что именно нужно очистить
        keyboard = [
            [InlineKeyboardButton("Очистить данные пользователей.", callback_data="clear_users")],
            [InlineKeyboardButton("Очистить транзакции.", callback_data="clear_transactions")],
            [InlineKeyboardButton("Отмена.", callback_data="cancel_clear")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Что вы хотите очистить?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

# Обработчик выбора очистки данных
async def clear_data_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if is_admin(user_id):
        if query.data == "clear_users":
            clear_users_data()
            await query.edit_message_text("User data has been cleared.\n \nДанные пользователей были очищены.\n \nПайдаланушылардың деректері тазартылды.")
        elif query.data == "clear_transactions":
            clear_transactions_data()
            await query.edit_message_text("Transactions have been cleared.\n \nТранзакции были очищены.\n \nТранзакциялар тазартылды.")
        elif query.data == "cancel_clear":
            await query.edit_message_text("The data clear operation was cancelled.\n \nОперация очищения данных отменена.\n \nДеректерді тазалау операциясы тоқтатылды.")
    else:
        await query.edit_message_text("You are not authorized to use this command.\n \nУ вас нет прав на использование этой команды.\n \nБұл команданы қолдануға сіздің құқығыныз жоқ.")

async def balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)
    
    # Получаем транзакции пользователя
    transactions = get_transactions(user_id)

    # Получаем баланс пользователя
    conn = sqlite3.connect('transactions4.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE telegram_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    # Если баланс найден, показываем его
    if result:
        balance = result[0]
    else:
        balance = 0  # Если нет записи о балансе, возвращаем 0

    # Формируем сообщение с транзакциями и балансом
    if transactions:
        message = get_translated_text(language, 'balance') + "\n"
        for transaction in transactions:
            message += f"ID: {transaction[0]}, Сумма: {transaction[2]}, Описание: {transaction[3]}, Дата: {transaction[4]}\n"
        message += f"\nБаланс: {balance}"  # Добавляем текущий баланс
    else:
        message = get_translated_text(language, 'no_transactions') + f"\nБаланс: {balance}"

    await update.message.reply_text(message)

# Команда для экспорта транзакций в CSV
async def export_csv(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Экспорт транзакций в CSV
    filename = export_transactions_to_csv(user_id)
    if filename:
        with open(filename, 'rb') as file:
            await update.message.reply_document(document=file)
        os.remove(filename)  # Удаляем файл после отправки
    else:
        await update.message.reply_text("You have no transactions to export.\n \nУ вас нет транзакций для экспорта.\n \nЭкспортталатын транзакцияларыңыз жоқ.")

# Команда для экспорта транзакций в Excel
async def export_excel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Экспорт транзакций в Excel
    filename = export_transactions_to_excel(user_id)
    if filename:
        with open(filename, 'rb') as file:
            await update.message.reply_document(document=file)
        os.remove(filename)  # Удаляем файл после отправки
    else:
        await update.message.reply_text("You have no transactions to export.\n \nУ вас нет транзакций для экспорта.\n \nЭкспортталатын транзакцияларыңыз жоқ.")

# Функция обработки сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    user_id = user.id
    
    # Проверка на спам
    if is_spamming(user_id):
        await update.message.reply_text("Вы отправляете слишком много сообщений. Пожалуйста, не спамьте.")
    else:
        await update.message.reply_text(f"Сообщение от {user.username}: {update.message.text}")

# Команда для списка пользователей
async def list_users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет доступа к списку пользователей.")
        return

    # Получаем список пользователей из базы данных
    users = get_users_from_db()
    if users:
        users_text = "Список всех пользователей:\n"
        for user in users:
            user_id, telegram_id, username, phone_number = user
            users_text += f"ID: {user_id}, Telegram ID: {telegram_id}, Username: @{username}, Телефон: {phone_number}\n"
        await update.message.reply_text(users_text)
    else:
        await update.message.reply_text("Нет зарегистрированных пользователей.")

# Команда для отображения истории входов
async def login_history(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if is_admin(user_id):
        # Создаем клавиатуру с выбором
        keyboard = [
            [InlineKeyboardButton("Все входы", callback_data="view_all")],
            [InlineKeyboardButton("Входы с конкретным пользователем", callback_data="view_with_user")],
            [InlineKeyboardButton("Входы без username", callback_data="view_without_user")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите, что вы хотите просмотреть:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("У вас нет прав на использование этой команды.")

# Обработчик выбора действия
async def view_login_history_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if is_admin(user_id):
        if query.data == "view_all":
            await show_all_logins(query)
        elif query.data == "view_with_user":
            await show_logins_with_user(query)
        elif query.data == "view_without_user":
            await show_logins_without_user(query)
        else:
            await query.edit_message_text(f"Неизвестная команда: {query.data}")
    else:
        await query.edit_message_text("У вас нет прав на использование этой команды.")

# Функция для отображения всех входов
async def show_all_logins(query):
    try:
        conn = sqlite3.connect('transactions4.db')
        c = conn.cursor()
        c.execute("SELECT user_id, username, login_time FROM login_history ORDER BY login_time DESC")
        logins = c.fetchall()
        conn.close()

        if logins:
            message = "Все входы:\n"
            for login in logins:
                message += f"User ID: {login[0]}, Username: {login[1] or 'None'} | Время входа: {login[2]}\n"
            
            # Разбиваем сообщение на части, если оно слишком длинное
            MAX_MESSAGE_LENGTH = 4096
            if len(message) > MAX_MESSAGE_LENGTH:
                parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
                for part in parts:
                    await query.edit_message_text(part)
            else:
                await query.edit_message_text(message)
        else:
            await query.edit_message_text("Нет данных о входах.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")

# Функция для отображения входов с конкретным пользователем (с выбором пользователя)
async def show_logins_with_user(query):
    try:
        conn = sqlite3.connect('transactions4.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT username FROM login_history WHERE username IS NOT NULL")
        users = c.fetchall()
        conn.close()

        if users:
            keyboard = []
            for user in users:
                username = user[0]
                encoded_username = urllib.parse.quote(username)  # Кодируем username в URL
                keyboard.append([InlineKeyboardButton(username, callback_data=f"view_user_{encoded_username}")])
            
            keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите пользователя для фильтрации входов:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Нет пользователей с именами для фильтрации.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")

# Функция для отображения входов выбранного пользователя
async def show_logins_for_user(query, username):
    try:
        # Декодируем username перед использованием в SQL запросе
        decoded_username = urllib.parse.unquote(username)

        conn = sqlite3.connect('transactions4.db')
        c = conn.cursor()
        c.execute("SELECT user_id, username, login_time FROM login_history WHERE username = ? ORDER BY login_time DESC", (decoded_username,))
        logins = c.fetchall()
        conn.close()

        if logins:
            message = f"Входы пользователя {decoded_username}:\n"
            for login in logins:
                message += f"User ID: {login[0]} | Время входа: {login[2]}\n"
            
            # Разбиваем сообщение на части, если оно слишком длинное
            MAX_MESSAGE_LENGTH = 4096
            if len(message) > MAX_MESSAGE_LENGTH:
                parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
                for part in parts:
                    await query.edit_message_text(part)
            else:
                await query.edit_message_text(message)
        else:
            await query.edit_message_text(f"Нет входов для пользователя {decoded_username}.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")

# Функция для отображения входов без username
async def show_logins_without_user(query):
    try:
        conn = sqlite3.connect('transactions4.db')
        c = conn.cursor()
        c.execute("SELECT user_id, username, login_time FROM login_history WHERE username IS NULL ORDER BY login_time DESC")
        logins = c.fetchall()
        conn.close()

        if logins:
            message = "Входы без username:\n"
            for login in logins:
                message += f"User ID: {login[0]} | Время входа: {login[2]}\n"
            
            # Разбиваем сообщение на части, если оно слишком длинное
            MAX_MESSAGE_LENGTH = 4096
            if len(message) > MAX_MESSAGE_LENGTH:
                parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
                for part in parts:
                    await query.edit_message_text(part)
            else:
                await query.edit_message_text(message)
        else:
            await query.edit_message_text("Нет входов без username.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")

# Обработчик для выбора конкретного пользователя (после того, как был выбран пользовател)
async def user_selection_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if is_admin(user_id):
        # Проверяем, что имя пользователя корректное
        if query.data.startswith("view_user_"):
            # Извлекаем имя пользователя из callback_data и декодируем его
            username = query.data.replace("view_user_", "")
            decoded_username = urllib.parse.unquote(username)
            await show_logins_for_user(query, decoded_username)
        elif query.data == "cancel":
            await query.edit_message_text("Операция отменена.")
        else:
            await query.edit_message_text(f"Неизвестная команда: {query.data}")
    else:
        await query.edit_message_text("У вас нет прав на использование этой команды.")

# Запуск приложения
def main():
    add_username_column_to_login_history()
    create_database()

    # Создание приложения
    application = Application.builder().token(TOKEN).build()

    # Команда для просмотра истории входов
    application.add_handler(CommandHandler("login_history", login_history))

    # Обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(view_login_history_callback, pattern="^(view_all|view_with_user|view_without_user)$"))

    # Обработчик для выбора пользователя
    application.add_handler(CallbackQueryHandler(user_selection_callback, pattern="^view_user_"))

    # Обработчик для кнопки отмены
    application.add_handler(CallbackQueryHandler(user_selection_callback, pattern="^cancel$"))

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("add_income", add_income))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("login_history", login_history))
    application.add_handler(CommandHandler("add_expense", add_expense))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("add_admin", add_admin))
    application.add_handler(CommandHandler("remove_admin", remove_admin))
    application.add_handler(CommandHandler("list_admins", list_admins))  # Команда для списка админов
    application.add_handler(CommandHandler("notify_admins", notify_admins))  # Добавляем команду уведомлений для админов
    application.add_handler(CommandHandler("notify_users", notify_users))  # Добавляем команду уведомлений для всех пользв.
    application.add_handler(CommandHandler("clear_data", clear_data))  # Команда для очистки данных
    application.add_handler(CallbackQueryHandler(clear_data_callback))  # Обработчик для выбора очистки данных
    application.add_handler(CommandHandler("check_profile", check_profile))  # Команда для проверки профиля администратором
    application.add_handler(CommandHandler("list_users", list_users))  # Команда для списка пользв.
    application.add_handler(MessageHandler(filters.CONTACT, handle_phone))  # Обрабатываем номер телефона
    # Регистрация обработчика для неверных команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_command))


    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("export_csv", export_csv))
    application.add_handler(CommandHandler("export_excel", export_excel))

    # Регистрируем обработчик для получения номера телефона
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Для всех текстовых сообщений

    application.run_polling()

if __name__ == '__main__':
    main()