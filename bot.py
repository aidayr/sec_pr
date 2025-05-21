import telebot
from telebot import types
from texts import RESTAURANT_TEXTS, SPA_TEXTS, CAR_DEALERSHIP_TEXTS, COMMON_TEXTS
from config import BOT_TOKEN, BUSINESS_CONFIG

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояния игроков
user_states = {}


class UserState:
    def __init__(self, business_type):
        config = BUSINESS_CONFIG[business_type]
        self.capital = config["initial_capital"]
        self.rating = 5.0
        self.business_type = business_type
        self.current_situation = 0
        self.profit_multiplier = 1.0
        self.score = 0
        self.max_situations = config["situations"]

    def apply_effect(self, effect):
        self.capital += effect.get("capital_change", 0)
        self.rating += effect.get("rating_change", 0)
        self.profit_multiplier *= (1 + effect.get("profit_change", 0))
        self.score += effect.get("score", 0)
        self.rating = max(0, min(10, self.rating))
        self.current_situation += 1

    def get_business_texts(self):
        return {
            "Ресторан": RESTAURANT_TEXTS,
            "Спа-салон": SPA_TEXTS,
            "Автосалон": CAR_DEALERSHIP_TEXTS
        }[self.business_type]


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*BUSINESS_CONFIG.keys())

    bot.send_message(
        chat_id=message.chat.id,
        text=COMMON_TEXTS["start"],
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text in BUSINESS_CONFIG)
def select_business(message):
    user_id = message.chat.id
    business_type = message.text
    user_states[user_id] = UserState(business_type)
    user_state = user_states[user_id]

    business_texts = user_state.get_business_texts()
    start_text = business_texts[business_type]["start"].format(
        business=business_type,
        capital=user_state.capital,
        rating=user_state.rating
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(COMMON_TEXTS["continue"])

    bot.send_message(
        chat_id=user_id,
        text=start_text,
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == COMMON_TEXTS["continue"])
def continue_game(message):
    user_id = message.chat.id
    user_state = user_states.get(user_id)

    if not user_state:
        return start(message)

    if user_state.current_situation >= user_state.max_situations:
        return end_game(user_id)

    send_situation(user_id)


def send_situation(user_id):
    user_state = user_states[user_id]
    business_texts = user_state.get_business_texts()
    situation_num = user_state.current_situation + 1
    situation_key = f"situation{situation_num}"

    if situation_key not in business_texts[user_state.business_type]:
        return end_game(user_id)

    situation = business_texts[user_state.business_type][situation_key]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*situation["options"].keys())

    status_text = f"""{situation['description']}

Текущее состояние:
• Капитал: {user_state.capital:,} руб
• Рейтинг: {user_state.rating:.1f}
• Баллы: {user_state.score}"""

    bot.send_message(
        chat_id=user_id,
        text=status_text,
        reply_markup=markup
    )


def end_game(user_id):
    user_state = user_states[user_id]
    business_texts = user_state.get_business_texts()

    final_text = f"""

Итоговые результаты ({user_state.business_type}):
 Капитал: {user_state.capital:,} руб
 Рейтинг: {user_state.rating:.1f}
 Набрано баллов: {user_state.score}/80

{COMMON_TEXTS["end"]}"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(COMMON_TEXTS["restart"])

    bot.send_message(
        chat_id=user_id,
        text=final_text,
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == COMMON_TEXTS["restart"])
def restart(message):
    start(message)


@bot.message_handler(func=lambda message: True)
def handle_choice(message):
    user_id = message.chat.id
    user_state = user_states.get(user_id)

    if not user_state:
        return

    business_texts = user_state.get_business_texts()
    situation_num = user_state.current_situation + 1
    situation_key = f"situation{situation_num}"

    if situation_key not in business_texts[user_state.business_type]:
        return end_game(user_id)  # Если ситуации закончились

    situation = business_texts[user_state.business_type][situation_key]

    if message.text not in situation["options"]:
        bot.send_message(user_id, "Пожалуйста, выберите один из предложенных вариантов")
        return

    choice_data = situation["options"][message.text]
    effect = {
        "capital_change": choice_data["capital_change"],
        "rating_change": choice_data["rating_change"],
        "profit_change": choice_data["profit_change"],
        "score": choice_data["score"]
    }
    user_state.apply_effect(effect)

    response = choice_data["response"].format(
        capital=user_state.capital,
        rating=user_state.rating
    )

    # Отправляем ответ на выбор
    bot.send_message(
        chat_id=user_id,
        text=response
    )

    # Проверяем, была ли это последняя ситуация
    if user_state.current_situation >= user_state.max_situations:
        end_game(user_id)  # Показываем итоги сразу
    else:
        # Показываем кнопку "Продолжить" только если есть еще ситуации
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(COMMON_TEXTS["continue"])
        bot.send_message(
            chat_id=user_id,
            text="Возникла новая проблема:",
            reply_markup=markup
        )


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)