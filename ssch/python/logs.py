def log(message, date):
    with open(f'/var/www/html/ssch/logs/{date}.log', mode='a', encoding='utf-8') as lg:
        lg.write(message)
        lg.write('\n\n============================================\n\n')
