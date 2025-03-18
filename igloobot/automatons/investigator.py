import telebot

from config.constants import SELECT_BOT_TOKEN as BOT_TOKEN

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Define keywords
enter_insulin = 'e:insu'
enter_food = 'e:food'
enter_notes = 'e:notes'
get_plot = 'g:plot'
get_plot_for_ts = 'g:plot(ts)'
get_plot_for_food = 'g:plot(food)'

# Define the keyboard
keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
keyboard.add(
    telebot.types.KeyboardButton(enter_insulin),
    telebot.types.KeyboardButton(enter_food),
    telebot.types.KeyboardButton(enter_notes),
    telebot.types.KeyboardButton(get_plot),
    telebot.types.KeyboardButton(get_plot_for_ts),
    telebot.types.KeyboardButton(get_plot_for_food)
)

# Define the state variable to keep track of the current input
current_input = None

@bot.message_handler(commands=['menu', 'start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="select an option", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == enter_insulin)
def handle_enter_insulin(message):
    print(f"called {message.text}")
    global current_input
    current_input = enter_insulin

@bot.message_handler(func=lambda message: message.text == enter_food)
def handle_enter_food(message):
    print(f"called {message.text}")
    global current_input
    current_input = enter_food

@bot.message_handler(func=lambda message: message.text == enter_notes)
def handle_enter_notes(message):
    print(f"called {message.text}")
    global current_input
    current_input = enter_notes

@bot.message_handler(func=lambda message: message.text == get_plot)
def handle_enter_notes(message):
    print(f"called {message.text}")
    global current_input
    current_input = get_plot

@bot.message_handler(func=lambda message: message.text == get_plot_for_food)
def handle_enter_notes(message):
    print(f"called {message.text}")
    global current_input
    current_input = get_plot_for_food

@bot.message_handler(func=lambda message: message.text == get_plot_for_ts)
def handle_enter_notes(message):
    print(f"called {message.text}")
    global current_input
    current_input = get_plot_for_ts

@bot.message_handler(func=lambda message: True)
def handle_value(message):
    global current_input
    print(f"handling {current_input}")
    text = message.text
    chat_id = message.chat.id

    try:
        if current_input == enter_insulin:
            print(current_input, text)
        elif current_input == enter_food:
            print(current_input, text)
        elif current_input == enter_notes:
            print(current_input, text)
        elif current_input == get_plot:
            print(current_input, text)
        elif current_input == get_plot_for_food:
            print(current_input, text)
        elif current_input == get_plot_for_ts:
            print(current_input, text)
        current_input = None
    except ValueError:
        bot.send_message(chat_id=chat_id, text="Invalid input. Please enter a numerical value.")


if __name__ == '__main__':
    bot.polling()
