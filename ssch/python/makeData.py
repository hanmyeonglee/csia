import pymysql
from random import choice
from random import randint

mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                        db="ssch", charset="utf8", autocommit=True)
names = ['James', 'Robert', 'John', 'Michael', 'David', 'William', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Charles', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Andrew', 'Paul', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Gregory', 'Alexander', 'Patrick', 'Frank', 'Raymond', 'Jack',
         'Dennis', 'Jerry', 'Tyler', 'Aaron', 'Jose', 'Adam', 'Nathan', 'Henry', 'Zachary', 'Douglas', 'Peter', 'Kyle', 'Noah', 'Ethan', 'Jeremy', 'Walter', 'Christian', 'Keith', 'Roger', 'Terry', 'Austin', 'Sean', 'Gerald', 'Carl', 'Harold', 'Dylan', 'Arthur', 'Lawrence', 'Jordan', 'Jesse', 'Bryan', 'Billy', 'Bruce', 'Gabriel', 'Joe', 'Logan', 'Alan', 'Juan', 'Albert', 'Willie', 'Elijah', 'Wayne', 'Randy', 'Vincent', 'Mason', 'Roy', 'Ralph', 'Bobby', 'Russell', 'Bradley', 'Philip', 'Eugene']
dis = "호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(
    " ")

with mysql.cursor() as commander:
    for _ in range(100):
        s = f'insert into daily(number, name, sex, time, disease, treat) values("{choice(["M", "H"])}{randint(1, 4)}-{randint(1, 4)}", "{choice(names)}", "{choice(["남", "여"])}", "{str(randint(8, 17)).rjust(2, "0")}:{str(randint(0, 59)).rjust(2, "0")}", "{choice(dis)}", "{"테스트"*randint(1, 5)}")'
        commander.execute(s)
    for _ in range(500):
        s = f'insert into yearly(number, name, sex, time, disease, treat) values("{choice(["M", "H"])}{randint(1, 4)}-{randint(1, 4)}", "{choice(names)}", "{choice(["남", "여"])}", "2023.08.{str(randint(25, 29)).rjust(2, "0")} {str(randint(8, 17)).rjust(2, "0")}:{str(randint(0, 59)).rjust(2, "0")}", "{choice(dis)}", "{"테스트"*randint(1, 5)}")'
        commander.execute(s)
