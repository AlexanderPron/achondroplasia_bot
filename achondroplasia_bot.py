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
import io


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
config = configparser.ConfigParser()
DEV_SETTINGS = os.path.join(BASE_DIR, "config/dev_settings.ini")
SETTINGS = os.path.join(BASE_DIR, "config/settings.ini")
ASK_Q_TEXT = "Задайте интересующий Вас вопрос в одном сообщении.\n\
В нём же можете оставить дополнительные контактные данные для получения ответа\n\
Также ответ придёт Вам в этот чат"
curr_settings = ""
log_file = os.path.join(BASE_DIR, "logs/bot.log")
rules_file = os.path.join(BASE_DIR, "messages/rules.txt")
default_google_forms_link = "https://workspace.google.com/intl/ru/products/forms/"
default_donate_url = "https://achondroplasia.ru/campaign/donate/"
start_text_file = os.path.join(BASE_DIR, "messages/start_text.txt")
acho_info_file = os.path.join(BASE_DIR, "messages/acho_info.txt")
patient_register_file = os.path.join(BASE_DIR, "messages/patient_register_start_msg.txt")
patient_register_agree_msg_file = os.path.join(BASE_DIR, "messages/patient_register_agree_msg.txt")
specialist_register_file = os.path.join(BASE_DIR, "messages/specialist_register.txt")
DEFAULT_START_TEXT = "<b>Выберите интересующую вас опцию</b>"
DEFAULT_ACHO_INFO = "<b>Ахондроплазия</b> - это известное с древности наследственное заболевание человека, \
проявляющееся в нарушении процессов энхондрального окостенения (вероятно, в результате дефектов \
окислительного фосфорилирования) на фоне нормальных эпостального и периостального окостенений, \
что ведет к карликовости за счет недоразвития длинных костей; характеризуется наличием \
врождённых аномалий, в частности врождённого стеноза позвоночного канала"
DEFAULT_PATIENT_REGISTER_MSG = "Мы будем рады принять и предложить разные программы и всестороннюю помощь и поддержку. \
Приглашаем присоединиться к чатам пациентского общения и к информационному каналу организации «Немаленькие люди»"
DEFAULT_PATIENT_REGISTER_AGREE_MSG = "Мы рады, что вы разделяете правила общения «Немаленьких людей»"
DEFAULT_SPECIALIST_REGISTER_MSG = ""


def add_log(msg_text, msg_type="info", log_file=log_file):
    with io.open(log_file, "a", encoding="utf-8") as f:
        record = f'\n[{datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] {msg_type.upper()}: {msg_text}'
        f.write(record)


config = configparser.ConfigParser()
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    curr_settings = DEV_SETTINGS
else:
    config.read(SETTINGS)
    curr_settings = SETTINGS
if not os.path.isfile(log_file):
    open(log_file, "w")
if not os.path.isfile(rules_file):
    open(rules_file, "w")
try:
    TOKEN = config["Telegram"]["token"]
    MANAGEMENT_IDS = config["Telegram"]["management_ids"]
except Exception:
    print(f"Something wrong with {curr_settings}")
    add_log(f"Something wrong with {curr_settings}", msg_type="error", log_file=log_file)
    exit()
try:
    if config["Google"]["forms_link"]:
        google_forms_link = config["Google"]["forms_link"]
        donate_url = config["BotData"]["donate_url"]
    else:
        google_forms_link = default_google_forms_link
except Exception:
    google_forms_link = default_google_forms_link
try:
    if config["BotData"]["donate_url"]:
        donate_url = config["BotData"]["donate_url"]
    else:
        donate_url = default_donate_url
except Exception:
    donate_url = default_donate_url
bot = telebot.TeleBot(TOKEN, parse_mode=None)
logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)
# telebot.logger.setLevel(logging.DEBUG)


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
    if os.path.isfile(rules_file):
        with io.open(rules_file, encoding="utf-8") as f:
            rules_text = f.read()
    else:
        rules_text = "Правила пока не указаны, но скоро они появятся"
        add_log(
            msg_text=f"{rules_file}: file not found. Check your {curr_settings}", msg_type="warning", log_file=log_file
        )
    if rules_text:
        bot.send_message(message.chat.id, text=rules_text, parse_mode="html")
    else:
        rules_text = "Правила пока не указаны, но скоро они появятся"
        bot.send_message(message.chat.id, text=rules_text, parse_mode="html")
        add_log(msg_text=f"{rules_file}: file is empty", log_file=log_file)


@bot.message_handler(commands=["start"])
def start_cmd(message):
    global user_data_for_join
    user_data_for_join = {}
    start_keyboard = InlineKeyboardMarkup(row_width=1)
    # start_keyboard = ReplyKeyboardMarkup()
    start_keyboard.add(
        # InlineKeyboardButton("Что такое ахондроплазия", callback_data="about_acho"),
        # InlineKeyboardButton("Регистрация новых пациентов", callback_data="register_patient_menu"),
        # InlineKeyboardButton("Регистрация специалистов", callback_data="register_specialist_menu"),
        InlineKeyboardButton(
            "Перейти на сайт achondroplasia.ru",
            callback_data="join_news_channel",
            url="https://achondroplasia.ru/",
        ),
        InlineKeyboardButton(
            "Подписаться на новостной канал",
            callback_data="join_news_channel",
            url="https://t.me/achondroplasia_ru",
        ),
        # InlineKeyboardButton("Вступить в группу", callback_data="join_group_btn"),
        InlineKeyboardButton("Задать вопрос", callback_data="ask_question"),
        InlineKeyboardButton("Отправить контент для публикации", callback_data="send_content"),
        InlineKeyboardButton("Сделать пожертвование", callback_data="donate", url=donate_url),
        # InlineKeyboardButton("Предложить сотрудничество", callback_data="partnership"),
    )
    if message.from_user.is_bot:
        bot.send_message(
            message.chat.id,
            text=DEFAULT_START_TEXT,
            reply_markup=start_keyboard,
            parse_mode="html",
        )
    else:
        if os.path.isfile(start_text_file):
            with io.open(start_text_file, encoding="utf-8") as f:
                start_text = f.read()
        else:
            start_text = DEFAULT_START_TEXT
            add_log(
                msg_text=f"{start_text_file}: file not found. Using default message",
                msg_type="warning",
                log_file=log_file,
            )
        bot.send_message(
            message.chat.id,
            text=start_text,
            reply_markup=start_keyboard,
            parse_mode="html",
        )

        # @bot.callback_query_handler(func=lambda call: call.data.startswith("about_acho"))
        # def about_acho(call: CallbackQuery):
        #     keyboard = InlineKeyboardMarkup(row_width=1)
        #     keyboard.add(
        #         InlineKeyboardButton(
        #             "Перейти на сайт achondroplasia.ru",
        #             callback_data="join_news_channel",
        #             url="https://achondroplasia.ru/",
        #         ),
        #         InlineKeyboardButton(
        #             "Подписаться на новостной канал",
        #             callback_data="join_news_channel",
        #             url="https://t.me/achondroplasia_ru",
        #         ),
        #         InlineKeyboardButton("Задать вопрос", callback_data="ask_question"),
        #         InlineKeyboardButton("Сделать пожертвование", callback_data="donate"),
        #         InlineKeyboardButton("Предложить сотрудничество", callback_data="partnership"),
        #     )
        #     keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
        #     if os.path.isfile(acho_info_file):
        #         with io.open(acho_info_file, encoding="utf-8") as f:
        #             acho_info = f.read()
        #     else:
        #         acho_info = DEFAULT_ACHO_INFO
        #         add_log(
        #             msg_text=f"{acho_info_file}: file not found. Using default message",
        #             msg_type="warning",
        #             log_file=log_file,
        #         )
        #     bot.edit_message_text(
        #         chat_id=call.message.chat.id,
        #         message_id=call.message.message_id,
        #         text=acho_info,
        #         reply_markup=keyboard,
        #         parse_mode="html",
        #     )

        # @bot.callback_query_handler(func=lambda call: call.data.startswith("register_patient_menu"))
        # def register_patient_menu(call: CallbackQuery):
        #     keyboard = InlineKeyboardMarkup(row_width=1)
        #     keyboard.add(
        #         InlineKeyboardButton("Библиотека материалов по ахондроплазии", callback_data="acho_library"),
        #         InlineKeyboardButton("Задать вопрос", callback_data="ask_question"),
        #         InlineKeyboardButton("Присоединиться к пациентскому реестру", callback_data="join_patient_registry"),
        #         InlineKeyboardButton(
        #             "Подписаться на новостной канал",
        #             callback_data="join_news_channel",
        #             url="https://t.me/achondroplasia_ru",
        #         ),
        #         InlineKeyboardButton(
        #             "Вся информация, новости,проекты - на сайте achondroplasia.ru",
        #             callback_data="join_news_channel",
        #             url="https://achondroplasia.ru/",
        #         ),
        #         InlineKeyboardButton("Присоединиться к пациентским чатам", callback_data="join_patient_chats"),
        #     )
        #     keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
        #     if os.path.isfile(patient_register_file):
        #         with io.open(patient_register_file, encoding="utf-8") as f:
        #             patient_register_msg = f.read()
        #     else:
        #         patient_register_msg = DEFAULT_PATIENT_REGISTER_MSG
        #         add_log(
        #             msg_text=f"{patient_register_file}: file not found. Using default message",
        #             msg_type="warning",
        #             log_file=log_file,
        #         )
        #     bot.edit_message_text(
        #         chat_id=call.message.chat.id,
        #         message_id=call.message.message_id,
        #         text=patient_register_msg,
        #         reply_markup=keyboard,
        #     )

        # @bot.callback_query_handler(func=lambda call: call.data.startswith("acho_library"))
        # def acho_library(call: CallbackQuery):
        #     keyboard = InlineKeyboardMarkup(row_width=1)
        #     keyboard.row(InlineKeyboardButton("Назад", callback_data="register_patient_menu"))
        #     bot.edit_message_text(
        #         chat_id=call.message.chat.id,
        #         message_id=call.message.message_id,
        #         text="Пока не понятно что тут",
        #         reply_markup=keyboard,
        #     )

        # @bot.callback_query_handler(func=lambda call: call.data.startswith("join_patient_registry"))
        # def join_patient_registry(call: CallbackQuery):
        #     keyboard = InlineKeyboardMarkup(row_width=1)
        #     keyboard.row(InlineKeyboardButton("Назад", callback_data="register_patient_menu"))
        #     bot.edit_message_text(
        #         chat_id=call.message.chat.id,
        #         message_id=call.message.message_id,
        #         text="Пока не понятно что тут",
        #         reply_markup=keyboard,
        #     )

        # @bot.callback_query_handler(func=lambda call: call.data.startswith("join_patient_chats"))
        # def join_patient_chats(call: CallbackQuery):
        #     keyboard = InlineKeyboardMarkup(row_width=1)
        #     keyboard.add(
        #         InlineKeyboardButton(
        #             "Я ознакомился с правилами и принимаю их",
        #             callback_data="agree_rules",
        #         ),
        #         InlineKeyboardButton("Назад", callback_data="register_patient_menu"),
        #     )
        #     keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))

        #     if os.path.isfile(rules_file):
        #         with io.open(rules_file, encoding="utf-8") as f:
        #             rules_text = f.read()
        #     else:
        #         rules_text = "Правила пока не указаны, но скоро они появятся"
        # add_log(
        #     msg_text=f"{rules_file}: file not found. Check your {curr_settings}",
        #     msg_type="warning",
        #     log_file=log_file,
        # )


#     if rules_text:
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text=rules_text,
#             reply_markup=keyboard,
#             parse_mode="html",
#         )
#     else:
#         rules_text = "Правила пока не указаны, но скоро они появятся"
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text=rules_text,
#             reply_markup=keyboard,
#             parse_mode="html",
#         )
#         add_log(msg_text=f"{rules_file}: file is empty", log_file=log_file)


# @bot.callback_query_handler(func=lambda call: call.data.startswith("agree_rules"))
# def get_link_to_google_forms(call: CallbackQuery):
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     keyboard.add(
#         InlineKeyboardButton(
#             "Заполнить анкету",
#             callback_data="enter_data_for_google_form",
#             url=google_forms_link,
#         ),
#     )
#     keyboard.row(
#         InlineKeyboardButton("Назад", callback_data="register_patient_menu"),
#         InlineKeyboardButton("В начало", callback_data="cmd_START"),
#     )

#     if os.path.isfile(patient_register_agree_msg_file):
#         with io.open(patient_register_agree_msg_file, encoding="utf-8") as f:
#             agree_msg = f.read()
#     else:
#         agree_msg = DEFAULT_PATIENT_REGISTER_AGREE_MSG
#         add_log(
#             msg_text=f"{patient_register_agree_msg_file}: file not found. Using default message",
#             msg_type="warning",
#             log_file=log_file,
#         )
#     if agree_msg:
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text=agree_msg,
#             reply_markup=keyboard,
#             parse_mode="html",
#         )
#     else:
#         agree_msg = DEFAULT_PATIENT_REGISTER_AGREE_MSG
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text=agree_msg,
#             reply_markup=keyboard,
#             parse_mode="html",
#         )
#         add_log(msg_text=f"{agree_msg}: file is empty", log_file=log_file)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# @bot.callback_query_handler(func=lambda call: call.data.startswith("register_specialist_menu"))
# def register_specialist_menu(call: CallbackQuery):
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     keyboard.add(
#         InlineKeyboardButton("Библиотека материалов по ахондроплазии", callback_data="acho_library"),
#         InlineKeyboardButton("Задать вопрос", callback_data="ask_question"),
#         InlineKeyboardButton("Внести данные в реестр специалистов", callback_data="add_data_specialist_registry"),
#         InlineKeyboardButton(
#             "Подписаться на новостной канал",
#             callback_data="join_news_channel",
#             url="https://t.me/achondroplasia_ru",
#         ),
#         InlineKeyboardButton(
#             "Вся информация, новости,проекты - на сайте achondroplasia.ru",
#             callback_data="join_news_channel",
#             url="https://achondroplasia.ru/",
#         ),
#         InlineKeyboardButton("Подписаться на рассылку новостей: оставить email", callback_data="subscribe"),
#     )
#     keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
#     if os.path.isfile(specialist_register_file):
#         with io.open(specialist_register_file, encoding="utf-8") as f:
#             specialist_register_msg = f.read()
#     else:
#         specialist_register_msg = DEFAULT_SPECIALIST_REGISTER_MSG
#         add_log(
#             msg_text=f"{specialist_register_file}: file not found. Using default message",
#             msg_type="warning",
#             log_file=log_file,
#         )
#     bot.edit_message_text(
#         chat_id=call.message.chat.id,
#         message_id=call.message.message_id,
#         text=specialist_register_msg,
#         reply_markup=keyboard,
#         parse_mode="html",
#     )


# @bot.callback_query_handler(func=lambda call: call.data.startswith("add_data_specialist_registry"))
# def add_data_specialist_registry(call: CallbackQuery):
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     keyboard.row(InlineKeyboardButton("Назад", callback_data="register_specialist_menu"))
#     bot.edit_message_text(
#         chat_id=call.message.chat.id,
#         message_id=call.message.message_id,
#         text="Пока не понятно что тут",
#         reply_markup=keyboard,
#     )


# ====== Блок для подписки на новости =======


@bot.callback_query_handler(func=lambda call: call.data.startswith("subscribe"))
def subscribe_enter_email(call: CallbackQuery):
    msg_instance = bot.send_message(
        chat_id=call.message.chat.id,
        text="Введите email",
    )
    bot.register_next_step_handler(msg_instance, subscribe_check_email)


def subscribe_check_email(message):
    if validators.email(message.text):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="cmd_START"),
            # InlineKeyboardButton("Назад", callback_data="register_specialist_menu"),
        )
        bot.send_message(
            message.chat.id,
            "Вы подписались на регулярную рассылку новостей об ахондроплазии и других скелетных дисплазиях \
(письма приходят не чаще 1 раза в месяц). !!! СЕРВИС ВРЕМЕННО НЕ РАБОТАЕТ !!!",
            reply_markup=keyboard,
        )
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё раз! (example@mail.ru)")
        bot.register_next_step_handler(message, subscribe_check_email)


# ====== Конец блока для подписки на новости =======


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
def cmd_func(call: CallbackQuery):
    if call.data == "cmd_START":
        start_cmd(call.message)
    elif call.data == "cmd_RULES":
        show_rules(call.message)
    # elif call.data == "cmd_JOIN":
    #     set_name(call.message)


# # =========== Блок ввода информации о пользователе =================
# def set_name(message):
#     global user_data_for_join
#     user_data_for_join = {}
#     user_data_for_join[message.chat.id] = {}
#     msg_instance = bot.send_message(message.chat.id, "Укажите Ваше имя")
#     bot.register_next_step_handler(msg_instance, set_surname)


# def set_surname(message):
#     msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
#     user_data_for_join[message.chat.id] = {"telegram": f"@{message.json['from']['username']}"}
#     user_data_for_join[message.chat.id]["name"] = message.text
#     bot.register_next_step_handler(msg_instance, set_email)


# def set_email(message):
#     msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
#     user_data_for_join[message.chat.id]["surname"] = message.text
#     bot.register_next_step_handler(msg_instance, end_reg)


# def end_reg(message):
#     if validators.email(message.text):
#         user_data_for_join[message.chat.id]["email"] = message.text
#         for id in MANAGEMENT_IDS.split(","):
#             bot.send_message(
#                 id,
#                 f"Новая заявка на вступление в группу \n{dict_to_formatstr(user_data_for_join[message.chat.id])}",
#                 parse_mode="html",
#             )
#         keyboard = InlineKeyboardMarkup()
#         keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
#         bot.send_message(
#             message.chat.id,
#             "Прекрасно! Запрос на вступление в группу отправлен нашему менеджеру. После изучения анкеты он с Вами \
# свяжется по почте или в Telegram",
#             reply_markup=keyboard,
#         )
#     else:
#         bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё разок! (example@mail.ru)")
#         bot.register_next_step_handler(message, end_reg)


# =========== Конец блока ввода информации о пользователе =================


@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_question"))
def ask_email(call):
    msg_instance = bot.send_message(call.message.chat.id, "Укажите ваш email")
    bot.register_next_step_handler(msg_instance, start_question)


def start_question(message):
    if validators.email(message.text):
        bot.send_message(message.chat.id, ASK_Q_TEXT)
        bot.register_next_step_handler(message, send_question, message.text)
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё раз.. (example@mail.ru)")
        bot.register_next_step_handler(message, start_question)


def send_question(message, user_email):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
    for id in MANAGEMENT_IDS.split(","):
        bot.send_message(
            id,
            f"Новый вопрос от @{message.from_user.username}\nemail: {user_email}",
        )
        bot.forward_message(
            id,
            message.chat.id,
            message.id,
        )
    bot.send_message(
        message.chat.id,
        "Ваш вопрос отправлен нашему менеджеру. Очень скоро Вам ответят \
сюда или одним из предоставленных вами способов",
        reply_markup=keyboard,
    )


@bot.channel_post_handler(func=lambda message: message.reply_to_message is not None)
def send_answer(message):
    if message.reply_to_message.forward_from:
        answer = f"Вы задавали вопрос: \n<code>{message.reply_to_message.text}</code>\nОтвет менеджера:\n \
<b>{message.text}</b>"
        bot.send_message(
            chat_id=message.reply_to_message.forward_from.id,
            text=answer,
            parse_mode="html",
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("send_content"))
def send_content(call):
    msg_instance = bot.send_message(call.message.chat.id, "Прикрепите контент")  # TODO Исправить сообщение
    bot.register_next_step_handler(msg_instance, get_content)


def get_content(message):
    if message.content_type in ["document", "audio", "photo", "video", "video_note", "voice"]:
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("В начало", callback_data="cmd_START"))
        for id in MANAGEMENT_IDS.split(","):
            bot.copy_message(
                id,
                message.chat.id,
                message.id,
                caption=f"Новая заявка на размещение контента от @{message.from_user.username}",
            )
        bot.send_message(
            message.chat.id,
            "Спасибо за то, что поделились с нами этой информацией!\
Контент отправлен нашему менеджеру. После проверки его содержимого мы опубликуем информацию на нашем \
информационном портале и в группе telegram",
            reply_markup=keyboard,
        )
    else:
        bot.register_next_step_handler(message, get_content)


def main():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
