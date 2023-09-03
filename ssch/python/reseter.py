import pymysql
mysql = pymysql.connect(user="login", passwd="DnKPnTZH5&dDDB%v", host="localhost",
                        db="account", charset="utf8", autocommit=True)
with mysql.cursor() as commander:
    m = input("title: ")
    commander.execute('update teacherAccount set title="%s"', m)

mysql.close()
