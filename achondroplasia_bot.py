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
RULES = "<b>Тут будут правила канала:</b> \n \
    <b>-</b> Не флудить \n \
    <b>-</b> Не оскорблять \n \
    <b>-</b> Не ругаться \n \
    <b>-</b> Не рекламировать"
CURR_SETTINGS = ""
CHANNEL_ID = "-1001382027476"
MANAGER_ID = "5174228279"
INVITE_CHANNEL_LINK = "https://t.me/+xn49869KEOE1NjZi"
config = configparser.ConfigParser()
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    CURR_SETTINGS = DEV_SETTINGS
else:
    config.read(SETTINGS)
    CURR_SETTINGS = SETTINGS
try:
    TOKEN = config["Telegram"]["token"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()
bot = telebot.TeleBot(TOKEN, parse_mode=None)
logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)

# bot.forward_message


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "Тут будет описание команд и возможностей бота")


@bot.message_handler(commands=["rules"])
def show_rules(message):
    bot.send_message(message.chat.id, text=RULES, parse_mode="html")


def set_name(message):
    global user_data_for_join
    user_data_for_join = {}
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваше имя")
    bot.register_next_step_handler(msg_instance, set_surname)


def set_surname(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
    user_data_for_join["name"] = message.text
    bot.register_next_step_handler(msg_instance, set_email)


def set_email(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
    user_data_for_join["surname"] = message.text
    bot.register_next_step_handler(msg_instance, end_reg)


def end_reg(message):
    if validators.email(message.text):
        user_data_for_join["email"] = message.text
        bot.send_message(CHANNEL_ID, f"К нам присоединился новый участник - {str(user_data_for_join)}")
        bot.send_message(MANAGER_ID, f"У нас новичок - {str(user_data_for_join)}")
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
        bot.send_message(
            message.chat.id,
            f"Прекрасно! Приглашение на наш канал по ссылке - {INVITE_CHANNEL_LINK}",
            reply_markup=keyboard
        )
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё разок! (example@mail.ru)")
        bot.register_next_step_handler(message, end_reg)


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


@bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
def cmd_func(call: CallbackQuery):
    if call.data == "cmd_START":
        start_cmd(call.message)
    elif call.data == "cmd_RULES":
        show_rules(call.message)
    elif call.data == "cmd_JOIN":
        set_name(call.message)


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


def main():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
