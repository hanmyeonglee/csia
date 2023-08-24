import pymysql
from random import choice
from random import randint

mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                        db="ssch", charset="utf8", autocommit=True)
with mysql.cursor() as commander:
    for _ in range(20):
        s = f'insert into yearly(number, name, sex, time, disease, treat) values("M1-1", "test", "{choice(["남", "여"])}", "2023.08.17 {randint(8, 18)}:{randint(0, 60)}", "{choice("호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(" "))}", "test")'
        print(s)
        commander.execute(s)

