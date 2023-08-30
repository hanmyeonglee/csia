import pymysql
from random import choice
from random import randint

mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                        db="ssch", charset="utf8", autocommit=True)
with mysql.cursor() as commander:
    for _ in range(100):
        s = f'insert into daily(number, name, sex, time, disease, treat) values("M1-1", "test", "{choice(["남", "여"])}", "2023.08.30 {str(randint(8, 18)).rjust(2, "0")}:{str(randint(0, 60)).rjust(2, "0")}", "{choice("호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(" "))}", "test")'
        commander.execute(s)
    for _ in range(500):
        s = f'insert into yearly(number, name, sex, time, disease, treat) values("M1-1", "test", "{choice(["남", "여"])}", "2023.08.{str(randint(25, 30)).rjust(2, "0")} {str(randint(8, 18)).rjust(2, "0")}:{str(randint(0, 60)).rjust(2, "0")}", "{choice("호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(" "))}", "test")'
        commander.execute(s)
