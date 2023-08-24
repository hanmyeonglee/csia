import pymysql
from logs import log as logging

mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                        db="ssch", charset="utf8", autocommit=True)
""" with mysql.cursor() as commander:
    for i in range(8, 18):
        if i == 12: continue
        h = str(i).rjust(2, '0')
        commander.execute(
            f'create table time_{h}(min char(5), pos tinyint(1), primary key(min))')
        for j in range(0, 60):
            m = str(j).rjust(2, '0')
            commander.execute(f'insert into time_{h} values("{m}", 1)')
    commander.execute('select min from time_08 where pos=1')
    print(commander.fetchall()) """


def reset_time():
    with mysql.cursor() as commander:
        for i in range(8, 18):
            if i == 12:
                continue
            h = str(i).rjust(2, '0')
            commander.execute(
                f'update time_{h} set pos=1')
    mysql.close()
