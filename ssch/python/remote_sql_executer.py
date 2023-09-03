import pymysql
pw = {
    "root": "todkagh",
    "login": "DnKPnTZH5&dDDB%v",
    "ssch": "rBXAm7WN"
}
db = {
    "login": "account",
    "ssch": "ssch"
}
id = input("id: ")
if id == "root":
    db[id] = input("db: ")
mysql = pymysql.connect(user="login", passwd=pw[id], host="localhost",
                        db=db[id], charset="utf8", autocommit=True)
with mysql.cursor() as commander:
    n = int(input("sql number: "))
    for _ in range(n):
        m = input("SQL: ")
        commander.execute('%s', m)

mysql.close()
