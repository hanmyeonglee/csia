from datetime import datetime


def log(message, date):
    with open(f'/var/www/html/ssch/logs/{date}.log', mode='a', encoding='utf-8') as lg:
        lg.write(
            f'\n\n\n==============={datetime.now().strftime("%H:%M:%S")}===============\n\n')
        lg.write(message)
