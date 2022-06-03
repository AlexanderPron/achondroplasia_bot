import telebot
from telebot.types import (
    ReplyKeyboardRemove,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
import datetime
import logging
import json
import configparser
import os.path
import validators


DEV_SETTINGS = "./dev_settings.ini"
SETTINGS = "./settings.ini"
# TODO Переделать получение текста правил из внешнего файла
RULES = "<b>Тут будут правила канала:</b> \n \
    <b>-</b> Не флудить \n \
    <b>-</b> Не оскорблять \n \
    <b>-</b> Не ругаться \n \
    <b>-</b> Не рекламировать"
ASK_Q_TEXT = "Задайте интересующий Вас вопрос в одном сообщении.\n \
В нём же можете оставить свои контактные данные для получения ответа (email, моб.телефон и пр.) \n \
Также ответ придёт Вам в этот чат"
CURR_SETTINGS = ""
config = configparser.ConfigParser()
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    CURR_SETTINGS = DEV_SETTINGS
else:
    config.read(SETTINGS)
    CURR_SETTINGS = SETTINGS
try:
    TOKEN = config["Telegram"]["token"]
    MANAGEMENT_IDS = config["Telegram"]["management_ids"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()
bot = telebot.TeleBot(TOKEN, parse_mode=None)
logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)


def dict_to_formatstr(dic):
    formated_str = ""
    for dic_key in dic:
        formated_str += f"<b>{dic_key}:</b> {dic.get(dic_key)}\n"
    return formated_str


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "Тут будет описание команд и возможностей бота")


@bot.message_handler(commands=["rules"])
def show_rules(message):
    bot.send_message(message.chat.id, text=RULES, parse_mode="html")


@bot.message_handler(commands=["start"])
def start_cmd(message):
    global user_data_for_join
    user_data_for_join = {}
    start_keyboard = InlineKeyboardMarkup()
    # start_keyboard = ReplyKeyboardMarkup()
    start_keyboard.row(
        InlineKeyboardButton("Хочу в группу", callback_data="join_group_btn"),
        InlineKeyboardButton("Задать вопрос", callback_data="ask_question"),
        # KeyboardButton("Хочу в группу"),
        # KeyboardButton("Задать вопрос"),
    )
    start_keyboard.row(
        InlineKeyboardButton("Поделиться", callback_data="send_info"),
        InlineKeyboardButton("Регистрация", callback_data="register"),
        # KeyboardButton("Поделиться"),
        # KeyboardButton("Регистрация"),
    )
    if message.from_user.is_bot:
        bot.send_message(
            message.chat.id,
            "Выберите действие",
            reply_markup=start_keyboard,
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Текст приветствия, {message.from_user.first_name}!",
            reply_markup=start_keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_group_btn"))
def start_join_group(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Правила канала", callback_data="cmd_RULES"),
        InlineKeyboardButton("Согласен с правилами, хочу вступить", callback_data="cmd_JOIN"),
    )
    keyboard.row(InlineKeyboardButton("Я передумал регистрироваться", callback_data="cmd_START"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Для получения доступа на наш канал Вам необходимо ознакомиться с \
правилами канала и рассказать немного о себе. ",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
def cmd_func(call: CallbackQuery):
    if call.data == "cmd_START":
        start_cmd(call.message)
    elif call.data == "cmd_RULES":
        show_rules(call.message)
    elif call.data == "cmd_JOIN":
        set_name(call.message)


# =========== Блок ввода информации о пользователе =================
def set_name(message):
    global user_data_for_join
    user_data_for_join[message.chat.id] = {}
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваше имя")
    bot.register_next_step_handler(msg_instance, set_surname)


def set_surname(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
    user_data_for_join[message.chat.id] = {"telegram": f"@{message.json['from']['username']}"}
    user_data_for_join[message.chat.id]["name"] = message.text
    bot.register_next_step_handler(msg_instance, set_email)


def set_email(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
    user_data_for_join[message.chat.id]["surname"] = message.text
    bot.register_next_step_handler(msg_instance, end_reg)


def end_reg(message):
    if validators.email(message.text):
        user_data_for_join[message.chat.id]["email"] = message.text
        for id in MANAGEMENT_IDS.split(","):
            bot.send_message(
                id,
                f"Новая заявка на вступление в группу \n{dict_to_formatstr(user_data_for_join[message.chat.id])}",
                parse_mode="html",
            )
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
        bot.send_message(
            message.chat.id,
            "Прекрасно! Запрос на вступление в группу отправлен нашему менеджеру. После изучения анкеты он с Вами \
свяжется по почте или в Telegram",
            reply_markup=keyboard,
        )
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё разок! (example@mail.ru)")
        bot.register_next_step_handler(message, end_reg)


# =========== Конец блока ввода информации о пользователе =================


@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_question"))
def start_question(call: CallbackQuery):
    msg_instance = bot.send_message(call.message.chat.id, ASK_Q_TEXT)
    bot.register_next_step_handler(msg_instance, send_question)


def send_question(message):
    for id in MANAGEMENT_IDS.split(","):
        b_mes = bot.forward_message(id, message.chat.id, message.id)
        # b_mes = bot.send_message(
        #     id,
        #     f'<b>Новый вопрос от @{message.json["from"]["username"]}!</b> \n"{message.text}"\n',
        #     parse_mode="html",
        # )
    bot.send_message(
        message.chat.id,
        "Ваш вопрос отправлен нашему менеджеру. Очень скоро Вам ответят \
сюда или одним из предоставленных вами способов",
    )
    print(b_mes)


# @bot.message_handler(func=lambda call: call.reply_to_message)
@bot.message_handler(chat_types=["channel", "groups"])
def test(message):
    print("+++++++++++=====Работает!!!!!++++____________")
    print(message)


def main():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
