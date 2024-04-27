import telebot
from telebot import types
import re
import requests_funcs as rf
from config import base_url, secret_key, headers, sbpMerchantId, user_file_path, admin_file_path, bot_key # type: ignore
import pandas as pd
import uuid

bot = telebot.TeleBot(bot_key)
is_admin = False
is_user = False
is_waiting_for_password = False

def add_admin(message: types.Message) -> bool:
    '''Добавляет нового админа, если такого нет в системе'''
    if is_person_known(message, admin_file_path):
        return False
    fileOpen = open(admin_file_path, 'a', encoding='utf-8')
    fileOpen.write(f'{message}\n')
    fileOpen.close()
    return True

def delete_admin(message) -> bool:
    '''Удаляет админа из системы, если таковой существует'''
    if not is_person_known_str(message.text, admin_file_path):
        return 'Данного пользователя нет в системе'
    with open(admin_file_path, "r", encoding='utf-8') as fileOpen:
        lines = fileOpen.readlines()
    with open(admin_file_path, "w", encoding='utf-8') as fileOpen:
        for line in lines:
            if line != f'{str(message.text)}\n':
                fileOpen.write(line)
    return 'Администратор успешно удален'


def is_person_known(message: types.Message, file_path: str) -> bool:
    '''Ищет юзера внутри ситемы и возвращает булевое занчение'''
    person_data = pd.read_csv(file_path, dtype=str)
    id = str(message.from_user.id)
    if person_data.query("login == @id").empty:
        return False
    return True

def is_person_known_str(message: str, file_path: str) -> bool:
    '''Ищет юзера внутри ситемы и возвращает булевое занчение'''
    person_data = pd.read_csv(file_path, dtype=str)
    if person_data.query("login == @message").empty:
        return False
    return True


def add_user(message: types.Message) -> str:
    '''добавляет пользователя и возвращает статус операции'''
    if is_person_known(message, user_file_path):
        return 'Данный пользователь уже в системе'
    with open(user_file_path, 'a', encoding='utf-8') as file:
        file.write(f'{message.text}\n')
    return 'Пользователь успешно добавлен'

def delete_user(message) -> None:
    '''удаляет юзера из системы, если таковой существует, возвращает статус операции'''
    if not is_person_known_str(message.text, user_file_path):
        return 'Данного пользователя нет в системе'
    with open(user_file_path, "r", encoding='utf-8') as fileOpen:
        lines = fileOpen.readlines()
    with open(user_file_path, "w", encoding='utf-8') as fileOpen:
        for line in lines:
            if line != f'{str(message.text)}\n':
                fileOpen.write(line)
    return 'Пользователь успешно удален'

def get_qr_status_by_id(message):
    '''выводит статус qr-кода'''
    bot.send_message(message.chat.id, f'Введите id qr-кода, пример: AD4EE12A105D4F5EA234BABFCA10E178')
    def step(message):
        if re.match(r'[a-zA-Z0-9]{32}', message.text):
            dict = rf.get_qr_request(base_url + message.text, None, {'Authorization': f'Bearer {secret_key}'})
            bot.send_message(message.chat.id, dict['qrStatus'])
        else:
            bot.send_message(message.chat.id, 'неправильный формат строки, попробуйте ещё!')
    bot.register_next_step_handler(message, step)

def create_qr_code(message):
    '''создаёт qr-код, отображает его img, id и ссылку'''
    bot.send_message(message.chat.id, f'Введите стоимость заказа')
    def step(message):
        if re.match(r'\d*', message.text):
            dict = rf.create_qr_request(base_url, { "qrType": "QRDynamic", "amount": message.text, "order": generate_order(), "sbpMerchantId": sbpMerchantId })
            try:
                bot.send_photo(message.chat.id, dict['qrUrl'], 'Id qr-кода ' + dict['qrId'])
                bot.send_message(message.chat.id, 'форма оплаты - ' + dict['payload'])
            except:
                bot.send_message(message.chat.id, dict)
        else:
            bot.send_message(message.chat.id, 'неправильный формат стоимости, попробуйте ещё!')
    bot.register_next_step_handler(message, step)

def get_qr_code(message):
    '''выводит платёжную страницу qr-кода'''
    bot.send_message(message.chat.id, f'Введите id qr-кода, пример: AD4EE12A105D4F5EA234BABFCA10E178')
    def step(message):
        if re.match(r'[a-zA-Z0-9]{32}', message.text):
            dict = rf.get_qr_request(base_url + message.text, None, {'Authorization': f'Bearer {secret_key}'})
            bot.send_message(message.chat.id, dict['payload'])
        else:
            bot.send_message(message.chat.id, 'неправильный формат строки, попробуйте ещё!')
    bot.register_next_step_handler(message, step)

def delete_qr_code(message):
    '''удаляет существующий qr-код'''
    bot.send_message(message.chat.id, f'Введите id qr-кода, пример: AD4EE12A105D4F5EA234BABFCA10E178')
    def step(message):
        if re.match(r'[a-zA-Z0-9]{32}', message.text):
            dict = rf.delete_qr_request(base_url + message.text, None, {'Authorization': f'Bearer {secret_key}'})
            bot.send_message(message.chat.id, dict)
        else:
            bot.send_message(message.chat.id, 'неправильный формат строки, попробуйте ещё!')
    bot.register_next_step_handler(message, step)


def generate_order() -> str:
    return str(uuid.uuid1())


def verification(message: types.Message) -> str:
    '''проверяет на наличие пользователя в списках'''
    if is_person_known(message, admin_file_path):
        return 'admin'
    
    if is_person_known(message, user_file_path):
        return 'user'

    return 'unknown'


def user_btns_init(message) -> None:
    '''функция инициализации кнопок юзера'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🆔Получить статус по id")
    markup.add(btn1)
    bot.send_message(message.chat.id, text="Готов принимать заказ", reply_markup=markup)

def admin_btns_init(message) -> None:
    '''функция инициализации кнопок админа'''
    markup = types.ReplyKeyboardMarkup(
    resize_keyboard=True)
    btn1 = types.KeyboardButton("✅Добавить юзера")
    btn2 = types.KeyboardButton("❌Удалить юзера")
    btn3 = types.KeyboardButton("🆔Получить статус по id")
    btn4 = types.KeyboardButton("📊создать qr-code")
    btn5 = types.KeyboardButton("💸найти qr-code")
    btn6 = types.KeyboardButton("🛠️удалить qr-code")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, text="Здравствуйте хозяин, выберите запрос", reply_markup=markup)


def password_pass(message) -> bool:
    '''функция для окончательной авторизации пользователя'''
    person_data = pd.read_csv(admin_file_path, dtype=str)
    tg_id = str(message.from_user.id)
    if person_data.query("password == @message.text and login == @tg_id").empty:
        return False
    else:
        return True


@bot.message_handler(commands=['start'])
def init(message):
    '''функция верификации пользователей'''
    #bot.send_message(message.chat.id, message.from_user)
    global is_admin, is_user, is_waiting_for_password
    verif = verification(message)
    if verif == 'admin':
        bot.send_message(message.chat.id, 'Здравствуй администратор, ожидаю пароль')
        is_waiting_for_password = True
        return
    if verif == 'user':
        is_user = True
        user_btns_init(message)
        return
    else:
        bot.send_message(message.chat.id, text="Вы не найдены в списке пользователей ;(")
    return


@bot.message_handler(content_types=['text'])
def main(message):
    '''основная функция обработки запросов пользователя'''
    global is_admin, is_user, is_waiting_for_password

    if is_waiting_for_password:
        if password_pass(message):
            is_waiting_for_password = False
            is_admin = True
            admin_btns_init(message)
            return
        bot.send_message(message.chat.id, text="неверный пароль, попробуйте снова")
        return
    if not (is_user or is_admin):
        bot.send_message(message.chat.id, text="Вы не имеете право доступа к этой сети")
    elif message.text == '🆔Получить статус по id':
        get_qr_status_by_id(message)
        return
    elif not is_admin:
        bot.send_message(message.chat.id, text="Вы ошиблись в запросе или пока не обладаете правом использование данной функцией")
        return
    elif message.text == "✅Добавить юзера":

        bot.send_message(message.chat.id, 'Введите telegram_id пользователя')
        def step(message):
            bot.send_message(message.chat.id, add_user(message))
        bot.register_next_step_handler(message, step)
        
        return
    elif message.text == "❌Удалить юзера":
        
        bot.send_message(message.chat.id, 'Введите telegram_id пользователя')
        def step(message):
            bot.send_message(message.chat.id, delete_user(message))
        bot.register_next_step_handler(message, step)
        
        return
    elif message.text == '📊создать qr-code':
        create_qr_code(message)
        return

    elif message.text == '💸найти qr-code':
        get_qr_code(message)
        return
    elif message.text == '🛠️удалить qr-code':
        delete_qr_code(message)
        return
    else:
        bot.send_message(message.chat.id,'Не распознал запрос')
bot.polling(none_stop=True)
