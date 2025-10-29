import telebot

from intelligence.recorder import record_insu, record_food, record_misc
from config.constants import REGULAR_BOT_TOKEN as BOT_TOKEN
from config.utils import get_current_time
from intelligence.plotting_utils import plot_default

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Define keywords
enter_insulin = 'e:insu'
enter_food = 'e:food'
enter_misc = 'e:misc'
get_plot = 'g:plot'
# get_plot_for_ts = 'g:plot(ts)'
# get_plot_for_food = 'g:plot(food)'

# Define the keyboard
keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
keyboard.add(
    telebot.types.KeyboardButton(enter_insulin),
    telebot.types.KeyboardButton(enter_food),
    telebot.types.KeyboardButton(enter_misc),
    telebot.types.KeyboardButton(get_plot),
    # telebot.types.KeyboardButton(get_plot_for_ts),
    # telebot.types.KeyboardButton(get_plot_for_food)
)

# Define the state variable to keep track of the current input
current_input_key = None


@bot.message_handler(commands=['menu'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="select an option", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == enter_insulin)
def handle_enter_insulin(message):
    print(f"called {message.text}")
    global current_input_key
    current_input_key = enter_insulin
    bot.send_message(chat_id=message.chat.id, text="Please enter a number >>")


@bot.message_handler(func=lambda message: message.text == enter_food)
def handle_enter_food(message):
    print(f"called {message.text}")
    global current_input_key
    current_input_key = enter_food
    bot.send_message(chat_id=message.chat.id, text="Please enter food >>")


@bot.message_handler(func=lambda message: message.text == enter_misc)
def handle_enter_notes(message):
    print(f"called {message.text}")
    global current_input_key
    current_input_key = enter_misc
    bot.send_message(chat_id=message.chat.id, text="Please enter notes >>")


@bot.message_handler(func=lambda message: message.text == get_plot)
def handle_get_plot(message):
    print(f"called {message.text}")
    global current_input_key
    current_input_key = get_plot
    bot.send_message(chat_id=message.chat.id, text="Generating plot...")
    im_path = plot_default()
    try:
        with open(im_path, 'rb') as photo:
            bot.send_photo(chat_id=message.chat.id, photo=photo)
    except Exception as exc:
        bot.send_message(chat_id=message.chat.id, text=f"Plot cannot be created : {exc}")


# @bot.message_handler(func=lambda message: message.text == get_plot_for_food)
# def handle_get_plot_for_food(message):
#     # not implemented
#     print(f"called {message.text}")
#     global current_input_key
#     current_input_key = get_plot_for_food
#
# @bot.message_handler(func=lambda message: message.text == get_plot_for_ts)
# def handle_get_plot_for_ts(message):
#     # not implemented
#     print(f"called {message.text}")
#     global current_input_key
#     current_input_key = get_plot_for_ts

@bot.message_handler(func=lambda message: True)
def handle_value(message):
    global current_input_key
    print(f"Handling {current_input_key}")
    current_inputs_value = message.text
    chat_id = message.chat.id

    try:
        current_time = get_current_time()
        if current_input_key == enter_insulin:
            print(current_input_key, current_inputs_value)
            record_insu(event_ts=current_time, ins_val=int(current_inputs_value))
            bot.send_message(chat_id=chat_id, text=f"updated ins with {current_inputs_value}")
        elif current_input_key == enter_food:
            print(current_input_key, current_inputs_value)
            record_food(event_ts=current_time, food_text=current_inputs_value)
            bot.send_message(chat_id=chat_id, text=f"updated food notes with {current_inputs_value}")
        elif current_input_key == enter_misc:
            print(current_input_key, current_inputs_value)
            record_misc(event_ts=current_time, misc_text=current_inputs_value)
            bot.send_message(chat_id=chat_id, text=f"updated misc notes with {current_inputs_value}")
        elif current_input_key == get_plot:
            # does not need any values
            pass
        # elif current_input_key == get_plot_for_food:
        #     print(current_input_key, current_inputs_value)
        # elif current_input_key == get_plot_for_ts:
        #     print(current_input_key, current_inputs_value)
        current_input_key = None
    except ValueError:
        bot.send_message(chat_id=chat_id, text="Invalid input.")


def poll():
    bot.polling()


if __name__ == '__main__':
    poll()
