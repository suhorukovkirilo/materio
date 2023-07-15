import telebot
from telebot import types
from datetime import datetime, timedelta
from time import sleep
from app import app, database
from models import User

bot = telebot.TeleBot("")
events = {}
money = {}
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Оплатити")
    btn2 = types.KeyboardButton("Поповнити рахунок")
    btn3 = types.KeyboardButton("Вивести")
    btn4 = types.KeyboardButton("Магазини")
    btn5 = types.KeyboardButton("Про бота")
    btn6 = types.KeyboardButton("Мій аккаунт")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, text=f"Вітаю, {message.from_user.first_name}, у боті Tig Wallet, де ви можете легко оплатити будь-які попупки у магазинах партнерів.",  reply_markup=markup)
    if message.from_user.id not in events:
        sleep(1)
        bot.send_message(message.chat.id, text="Йде автоматична реєстрація нового користувача...")
        sleep(4)
        bot.send_message(message.chat.id, text=f"Ідентифікатор користувача: {message.from_user.id}")
        sleep(1)
        bot.send_message(message.chat.id, text=f"Ім'я користувача: {message.from_user.username}")
        sleep(1)
        bot.send_message(message.chat.id, text=f"Прізвище/Ім'я: {message.from_user.first_name}/{message.from_user.last_name}")
        sleep(1)
        bot.send_message(message.chat.id, text="Реєстрація пройшла успішна")
        money[message.from_user.id] = 0
    events[message.from_user.id] = None

@bot.message_handler(commands=['pay'])
def pay(message):
    text = message.text.split()[1:]
    if len(text) >= 4:
        if text[0] == "materio":
            with app.app_context():
                if User.query.filter_by(name=text[1]).first():
                    if text[2] in ['pro', 'vip']:
                        if text[3] in ['month', 'year']:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                            markup.add(types.KeyboardButton("Підтвердити"))
                            costs = "5" if text[2] == "pro" and text[3] == "month" else "50" if text[2] == "pro" and text[3] == "year" else \
                            "15" if text[2] == "vip" and text[3] == "month"else "150"
                            if int(costs) <= money[message.from_user.id]:
                                bot.send_message(message.chat.id, text=f"Ви бажаєте придбати в магазині {text[0]} тариф {text[2]} {text[3]} за "
                                                                        + costs + f"$ для користувача {text[1]}")
                                events[message.from_user.id] = message.text
                                money[message.from_user.id] -= int(costs)
                                bot.send_message(message.chat.id, text="Для підтвердження оплати натисніть кнопку нижче", reply_markup=markup)
                            else:
                                bot.send_message(message.chat.id, text="Недостатньо коштів на рахунку")
                                bot.send_message(message.chat.id, text=f"На вашому рахунку: {money[message.from_user.id]}$, а потрібно {costs}$")
                        else:
                            bot.send_message(message.chat.id, text=f"Materio: План може бути лише місячний(month) або річний(year)")
                    else:
                        bot.send_message(message.chat.id, text=f"Materio: План {text[2]} не знайдено")
                else:
                    bot.send_message(message.chat.id, text=f"Materio: Користувача {text[1]} не знайдено")
        else:
            bot.send_message(message.chat.id, text=f"Магазин {text[0]} не знайдено")
    else:
        bot.send_message(message.chat.id, text="Невірний формат повідомлення оплати")
        bot.send_message(message.chat.id, text="/pay <shop> <user> <plan> <plan time>")

@bot.message_handler(commands=['add'])
def add(message):
    if len(message.text.split()) == 1:
        bot.send_message(message.chat.id, text="Ви не ввели суму поповнення")
    else:
        try:
            add_sum = int(message.text.split()[1].replace(",", "."))
            events[message.from_user.id] = message.text
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Підтвердити"))
            bot.send_message(message.chat.id, text="Ви збираєтеся поповнити рахунок на " + str(add_sum) + "$")
            bot.send_message(message.chat.id, text="Щоб підтвердити поповнення натисніть кнопку нижче", reply_markup=markup)
        except:
            bot.send_message(message.chat.id, text="Неправильна введена сума")

@bot.message_handler(content_types=['text'])
def text(message):
    if message.text == "Підтвердити":
        event = events[message.from_user.id]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Оплатити")
        btn2 = types.KeyboardButton("Поповнити рахунок")
        btn3 = types.KeyboardButton("Вивести")
        btn4 = types.KeyboardButton("Магазини")
        btn5 = types.KeyboardButton("Про бота")
        btn6 = types.KeyboardButton("Мій аккаунт")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        if event.split()[0] == "/pay":
            active = datetime.utcnow() + timedelta(days=30 if event.split()[4] == "month" else 365)
            active = active.strftime("%Y-%m-%d")
            with app.app_context():
                User.query.filter_by(name=event.split()[2]).first().plan = f"{event.split()[3]} {active}"
                database.session.commit()
            bot.send_message(message.chat.id, text="Оплату успішно проведено", reply_markup=markup)
        elif event.split()[0] == "/add":
            add_sum = int(event.split()[1])
            money[message.from_user.id] += add_sum
            bot.send_message(message.chat.id, text="Ваш рахунок успішно поповнено")
            bot.send_message(message.chat.id, text="На вашому рахунку: " + str(money[message.from_user.id]) + "$", reply_markup=markup)
        events[message.from_user.id] = None
    elif message.text == "На головну":
        start(message)
    elif message.text == "Оплатити":
        bot.send_message(message.chat.id, text="Для оплати певного товару з вашого улюбленого магазину скопіюйте потрібно команду з магазину або введіть код нижче:")
        bot.send_message(message.chat.id, text="/pay <shop> <user> <plan> <plan time>\n<shop> - магазин в якому робиться покупка\n<user> - користувач, якому надійде товар/оплата\n<plan> і <time> - план та його час (якщо є)")
    elif message.text == "Поповнити рахунок":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/add 1")
        btn2 = types.KeyboardButton("/add 5")
        btn3 = types.KeyboardButton("/add 10")
        btn4 = types.KeyboardButton("/add 25")
        btn5 = types.KeyboardButton("/add 50")
        btn6 = types.KeyboardButton("На головну")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        bot.send_message(message.chat.id, text="Для того, щоб поповнити рахунок на певну суму введіть /add <sum>, де <sum> - це сума поповнення або виберітьодну з сум нижче", reply_markup=markup)
    elif message.text == "Вивести":
        bot.send_message(message.chat.id, text="На жаль, ви не можете вивести ваші кошти на вашу карту або електронний гаманець")
        bot.send_message(message.chat.id, text="Але в будь-який момент ви можете витратити їх в магазинах наших партнерів")
    elif message.text == "Магазини":
        bot.send_message(message.chat.id, text="Ось наші магазини:")
        bot.send_message(message.chat.id, text="Materio - це найкращий веб-сайт для онлайн створення і менеджування своїх приватних нотаток або публічних статтей, останні можуть можуть бачити усі, лайкати їх, коментувати та підписуватися на авторів")
        bot.send_message(message.chat.id, "Плани/Товари(Інформацію про кожен можна знайти на сайті партнера):\nPro місячний/річний за 5$/50$\nVIP місячний/річнй за 15$/150$")
        bot.send_message(message.chat.id, text="Google Pie - це найкраще місця для купівлі мобільних додатків")
        bot.send_message(message.chat.id, text="Плани/Товари(Інформацію про кожен можна знайти на сайті партнера):\nПоповнення рахунки на витрати в будь-якій з ігр на 5$/10$/25$/50$/100$")
    elif message.text == "Про бота":
        bot.send_message(message.chat.id, text="Tig pay або Tig wallet - це платформа для швидкої оплати товарів/планом в ваших улюбленних магазинах без надання їм жодних даних вашої картки. Ви можете легко поповнити кошти один раз та витрачати їх у будь-яких магазинах партнерів  скільки завгодно (поки не кіньчаться кошти). Ви не платите Tig wallet жодних комісій, їх платить тільки магазин.")
    elif message.text == "Мій аккаунт":
        bot.send_message(message.chat.id, text="Ваш аккаунт")
        bot.send_message(message.chat.id, text=f"Ідентифікатор: {message.from_user.id}\nІм'я користувача: {message.from_user.username}\nПрізвище/Ім'я: {message.from_user.first_name}/{message.from_user.last_name}\nКоштів: {str(money[message.from_user.id])}$")

if __name__ == "__main__":
    print("Бота запущено")
    bot.polling(none_stop=True)
