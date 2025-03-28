import sys
import os
import telebot
import random
import sqlite3
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(token = bot_token)

con = sqlite3.connect('Anonim.db', check_same_thread=False)
cursor = con.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS Users(
    tg_id INTEGER,
    first_name TEXT,
    last_name TEXT,
    partner INTEGER
)''')
con.commit()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('/Doeb'))
keyboard.add(KeyboardButton('/help'))

keyboard2 = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard2.add(KeyboardButton('/NonDoeb'))

keyboard3 = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard3.add(KeyboardButton('/NonDoeb'))
keyboard3.add(KeyboardButton('/User_info'))

def is_person_in_data(message, tg_id):
    sqlite_select_query = """SELECT * from Users WHERE tg_id=?"""
    cursor.execute(sqlite_select_query, (message.from_user.id,))
    variants = cursor.fetchall()
    if len(variants) == 0:
        return 0;
    else:
        for row in variants:
            if row[3] == 0:
                return 1
            elif row[3] == 1:
                return 2
        return 3

def partner_search(message, tg_id):
    self_cursor = con.cursor()
    partner_cursor = con.cursor()
    sqlite_select_query = """SELECT * from Users WHERE tg_id=?"""

    self_cursor.execute(sqlite_select_query, tg_id)
    self = self_cursor.fetchone()

    partner_cursor.execute(sqlite_select_query, self[3])
    partner = partner_cursor.fetchone()
    
    self_cursor.close()
    partner_cursor.close()
    
    return partner

@bot.message_handler(commands=['start'])
def start(message):

    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    person_alive = is_person_in_data(message, tg_id)
    match person_alive:
        case 0: 
            cursor.execute(f"INSERT INTO Users VALUES(?, ?, ?, ?)", (tg_id, first_name, last_name, 0))
            con.commit()
        case 1: bot.send_message(message.chat.id, 'Привет, до кого доебемся сегодня?', reply_markup=keyboard)
        case 2: bot.send_message(message.chat.id, "Сейчас вы в поиске собеседника", reply_markup = keyboard2)
        case 3: bot.send_message(message.chat.id, 'Похоже вы уже с кем-то общаетесь! Попробуйте написать что-нибудь', reply_markup=keyboard2)

@bot.message_handler(commands= ['User_info'])
def User_info(message):
    if message.chat.id == 1167883149:
        partner = partner_search(message, 1167883149)
        bot.send_message(1167883149, f'User:{partner[0]}:\nFirst_name: {partner[1]}\nLast_name: {partner[2]}')
    else:
        bot.send_message(message.chat.id, 'Нельзя')

@bot.message_handler(commands=['Doeb'])
def Doeb(message):
    
    tg_id = message.from_user.id
    person = is_person_in_data(message, tg_id)
    match person:
        case 3: 
            bot.send_message(message.chat.id, "Вы уже общаетесь с кем-то! Напишите что-нибудь")
            return 1
        case 2: 
            bot.send_message(message.chat.id, "Сейчас вы в поиске собеседника")
            return 1

    sql_update_query = """Update Users set partner=? where tg_id=?"""
    self_data = (1, message.from_user.id)
    cursor.execute(sql_update_query, self_data)
    con.commit()

    bot.send_message(message.chat.id, 'Идет процесс...')
    cursor.execute("SELECT count(*) from Users WHERE partner=1")  #делаем запрос на кол-во строк в таблице с пользователями в поиске
    row_count = cursor.fetchone()
    count = row_count[0] - 1


    potential_partners = (cursor.execute('SELECT * FROM Users WHERE partner=1')).fetchall()
    if len(potential_partners) >= 2:
        Chet = 1
        Rand_partner = random.randint(1, count)
        for y in potential_partners:
            if y[0] != message.from_user.id:
                if Chet == Rand_partner:
                    sql_update_query = """Update Users set partner=? where tg_id=?"""
                    partner_id = y[0]
                    person_id = message.from_user.id
                    data = (person_id, partner_id)
                    data2 = (partner_id, person_id)
                    cursor.execute(sql_update_query, data)
                    con.commit()
                    cursor.execute(sql_update_query, data2)
                    con.commit()
                    if message.from_user.id == 1167883149: bot.send_message(message.chat.id, 'Соединение успешно установлено!', reply_markup=keyboard3)
                    else: bot.send_message(message.chat.id, 'Соединение успешно установлено!', reply_markup=keyboard2)

                    if y[0] == 1167883149: bot.send_message(y[0], 'До вас кто-то доебался!!', reply_markup=keyboard3)
                    else: bot.send_message(y[0], 'До вас кто-то доебался!!', reply_markup=keyboard2)

                    break
                else:
                    Chet += 1
    else:
        bot.send_message(message.chat.id, 'Пока людей, готовых к общению нет:(\nМы свяжем вас, как только они появятся!!', reply_markup=keyboard2)

@bot.message_handler(commands=['NonDoeb'])
def NonDoeb(message):
    cursor.execute('SELECT * FROM Users WHERE tg_id=?', (message.from_user.id,))
    partner_id = cursor.fetchone()[3] #айди подключенного ко мне человека

    bot.send_message(message.chat.id, 'Соединение успешно разорвано!', reply_markup=keyboard)
    bot.send_message(partner_id, 'Ваш партнер разорвал соединение!', reply_markup=keyboard)

    cursor.execute('SELECT * FROM Users WHERE tg_id=?', (partner_id, ))
    sql_update_query = """Update Users set partner=? where tg_id=?"""
    data_person = (0, message.from_user.id)
    data_partner = (0, partner_id)
    cursor.execute(sql_update_query, data_person)
    con.commit()
    cursor.execute(sql_update_query, data_partner)
    con.commit()

@bot.message_handler(content_types=['text'])
def get_User_Text(message):
    Mes = message.text
    cursor = con.cursor()
    cursor.execute('SELECT * FROM Users WHERE tg_id=?', (message.from_user.id,))
    self_partner = cursor.fetchone()[3]
    if self_partner == 0:
        bot.send_message(message.chat.id, 'Ты это кому? Попробуй доебаться до кого-нибудь')
    else:
        bot.send_message(self_partner, Mes)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Пока мне лень')

@bot.message_handler(content_types=['photo'])
def photo(message):
    cursor = con.cursor()
    cursor.execute('SELECT * FROM Users WHERE tg_id=?', (message.from_user.id,))
    self_partner = cursor.fetchone()[3]
    if self_partner == 0:
        bot.send_message(message.chat.id, 'Ты это кому? Попробуй доебаться до кого-нибудь')
    else:
        fileID = message.photo[-1].file_id

        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        image_id = random.randint(1, 100001)
        with open(f"image{image_id}.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        photo = open(f'image{image_id}.jpg', 'rb')

        bot.send_photo(self_partner, photo)
        photo.close()
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f'image{image_id}.jpg')
        os.remove(path)


bot.polling(none_stop=True)
