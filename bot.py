import telebot
from telebot import types
from texts import RESTAURANT_TEXTS, COMMON_TEXTS
from config import BOT_TOKEN, BUSINESS_CONFIG

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}


def get_business_texts(business):
    """Возвращает тексты для выбранного бизнеса"""
    if business == "Ресторан":
        return RESTAURANT_TEXTS
    elif business == "Спа-салон":
        return 1
    else:
        return 1


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Ресторан", "Спа-салон", "Автосалон")
    bot.send_message(message.chat.id, COMMON_TEXTS["start"], reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in BUSINESS_CONFIG.keys())
def handle_business_choice(message):
    chat_id = message.chat.id
    business = message.text
    texts = get_business_texts(business)

    user_data[chat_id] = {
        'business': business,
        'capital': BUSINESS_CONFIG[business]["initial_capital"],
        'rating': 5.0,
        'stage': 1,
        'texts': texts
    }

    # Показываем первую ситуацию
    show_situation(chat_id, 1)


def show_situation(chat_id, situation_num):
    """Показывает ситуацию с соответствующим номером"""
    data = user_data[chat_id]
    texts = data['texts']

    if situation_num == 1:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*texts["situation1"].keys())

        bot.send_message(
            chat_id,
            texts["start"].format(
                business=data['business'],
                capital=data['capital'],
                rating=data['rating']
            ),
            reply_markup=markup
        )

    elif situation_num == 2:
        # Аналогично для ситуации 2
        pass


@bot.message_handler(func=lambda message: message.text in RESTAURANT_TEXTS["situation1"].keys())
def handle_situation1_choice(message):
    chat_id = message.chat.id
    choice = message.text
    data = user_data[chat_id]

    # Обработка выбора и изменение состояния
    if choice == "Игнорировать жалобу":
        data['rating'] -= 0.3
        response = data['texts']["situation1"]["ignore"]
    elif choice == "Извиниться и предложить скидку":
        data['rating'] += 0.2
        data['capital'] -= 50000
        response = data['texts']["situation1"]["discount"]
    # ... другие варианты

    # Переход к следующей ситуации
    data['stage'] += 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(COMMON_TEXTS["continue"])

    bot.send_message(
        chat_id,
        response + f"\n\nТекущий капитал: {data['capital']:,} руб\nРейтинг: {data['rating']:.1f}",
        reply_markup=markup
    )


# ... аналогичные обработчики для других ситуаций

@bot.message_handler(func=lambda message: message.text == COMMON_TEXTS["continue"])
def continue_game(message):
    chat_id = message.chat.id
    data = user_data[chat_id]
    show_situation(chat_id, data['stage'])


@bot.message_handler(func=lambda message: message.text == COMMON_TEXTS["restart"])
def restart_game(message):
    send_welcome(message)


@bot.message_handler(func=lambda message: message.text == "Закончить игру")
def end_game(message):
    bot.send_message(message.chat.id, COMMON_TEXTS["end"])


bot.polling()