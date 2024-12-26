import telebot
import json
import os
from telebot import types
from cfg import BOT_TOKEN
from cfg import ADMIN_TELEGRAM_ID
from cfg import USERS_ID_FILE
from cfg import USER_INFO_FILE

bot = telebot.TeleBot(BOT_TOKEN)

# Функция для загрузки ID пользователей из файла
def load_user_ids():
    dir = 'users'
    try:
        with open(f'{dir}/{USERS_ID_FILE}', 'rb') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.decoder.JSONDecodeError:
        return []


# Функция для сохранения ID пользователей в файл
def save_user_ids(user_ids):
    dir = 'users'
    with open(f'{dir}/{USERS_ID_FILE}', 'w') as file:
        json.dump(user_ids, file)


# Функция для записи информации о пользователях в файл
def save_user_info(user_id, username):
    dir = 'users'
    with open(f'{dir}/{USER_INFO_FILE}', 'a') as file:
        file.write(f"{user_id} {username}\n")


# Загрузка ID пользователей
user_ids = load_user_ids()

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Обрабатывает команду /start"""
    args = message.text.split()
    if len(args) > 1:  # Если есть параметр
        try:
            target_id = int(args[1])  # Извлекаем ID из ссылки
            if target_id == message.from_user.id:
                bot.send_message(
                    message.chat.id,
                    "Вы не можете отправить сообщение самому себе!"
                )
                return
            
            if target_id in user_ids:
                msg = bot.send_message(
                    message.chat.id,
                    "Введите анонимное сообщение для отправки:"
                )
                bot.register_next_step_handler(msg, send_anonymous_message, target_id)
            else:
                bot.send_message(message.chat.id, "Пользователь не найден или ссылка недействительна.")
        except ValueError:
            bot.send_message(message.chat.id, "Некорректная ссылка.")
    else:
        user_id = message.from_user.id
        bot_username = bot.get_me().username
        unique_link = f"https://t.me/{bot_username}?start={user_id}"
        
         # Сохраняем ID и имя пользователя
        if message.chat.id not in user_ids:
            user_ids.append(message.chat.id)
            save_user_ids(user_ids)
            save_user_info(message.chat.id, message.chat.username)
            print(f'{message.from_user.first_name} с id {user_id} добавлен в список')
        
        bot.send_message(
            message.chat.id,
            f"Привет, {message.from_user.first_name}!\n\n"
            f"Вот твоя уникальная ссылка для получения анонимных сообщений:\n"
            f"{unique_link}\n\n"
            f"Поделись этой ссылкой, чтобы получать анонимные сообщения!"
            '\n\n\n'
            "Лучший ванильный сервер ReDrak(@ReDarkserv)"
        )

def send_anonymous_message(message, target_id):
    """Отправляет анонимное сообщение пользователю"""
    if not message.text:
        bot.send_message(message.chat.id, "Сообщение не может быть пустым.")
        return
    
    try:
        bot.send_message(
            target_id,
            f"Вам пришло анонимное сообщение:\n\n{message.text}"
        )
        markup = types.InlineKeyboardMarkup()
        more_print = types.InlineKeyboardButton(text="Написать ещё✍️", callback_data=f"more:{target_id}") 
        markup.add(more_print)
        bot.send_message(message.chat.id, "Сообщение успешно отправлено!", reply_markup=markup)

    except telebot.apihelper.ApiException:
        bot.send_message(message.chat.id, "Не удалось отправить сообщение. Возможно, пользователь заблокировал бота.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Обрабатывает команду /admin"""
    if message.chat.id == ADMIN_TELEGRAM_ID:
        bot.send_message(message.chat.id, "Вы вошли в admin panel")
        markup = types.InlineKeyboardMarkup()
        btn_off = types.InlineKeyboardButton(text="Выключить бота", callback_data="turn_off")
        btn_post = types.InlineKeyboardButton(text="Сделать пост", callback_data="send_post")

        markup.add(btn_off, btn_post)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('more'))
def print_more(call):
    """Обрабатывает нажатие кнопки 'Написать ещё'."""
    try:
        # Извлекаем target_id из callback_data
        target_id = int(call.data.split(':')[1])  # Пример callback_data: "more:12345678"
        
        if target_id in user_ids:
            msg = bot.send_message(
                call.message.chat.id,
                "Введите анонимное сообщение для отправки:"
            )
            bot.register_next_step_handler(msg, send_anonymous_message, target_id)
        else:
            bot.send_message(
                call.message.chat.id,
                "Пользователь не найден или ссылка недействительна."
            )
    except IndexError:
        bot.send_message(
            call.message.chat.id,
            "Ошибка: отсутствует информация о пользователе в данных кнопки."
        )
    except ValueError:
        bot.send_message(
            call.message.chat.id,
            "Ошибка: некорректный идентификатор пользователя в данных кнопки."
        )
    except Exception as e:
        bot.send_message(
            call.message.chat.id,
            "Произошла неожиданная ошибка. Пожалуйста, попробуйте снова."
        )
        print(f"Ошибка в print_more: {e}")


@bot.callback_query_handler(func=lambda call: call.data == 'turn_off')
def handle_turn_off(call):
    bot.send_message(call.message.chat.id, "Бот выключен.")
    bot.stop_polling()

@bot.callback_query_handler(func=lambda call: call.data == 'send_post')
def handle_send_post_init(call):
    bot.send_message(call.message.chat.id, "Напишите содержание поста для всех пользователей:")
    bot.register_next_step_handler(call.message, get_post_content)

def get_post_content(message):
    post_message = message.text
    if post_message:
        bot.send_message(message.chat.id, "Сообщение было разослано всем пользователям.")
        send_post_to_all_users(post_message)
    else:
        bot.send_message(message.chat.id, "Сообщение не может быть пустым.")

def send_post_to_all_users(post_message):
    for user_id in user_ids:
        try:
            bot.send_message(user_id, post_message)
        except Exception as e:
            print(f"Не удалось отправить пост пользователю {user_id}: {e}")

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Обрабатывает любые другие команды и текст"""
    if message.text.startswith('/'):
        bot.send_message(
            message.chat.id,
            "Неизвестная команда. Используйте /start для получения уникальной ссылки."
        )
    else:
        bot.send_message(
            message.chat.id,
            "Используйте команду /start для получения уникальной ссылки."
        )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
