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
mysql = pymysql.connect(user=id, passwd=pw[id], host="localhost",
                        db=db[id], port=23474, charset="utf8", autocommit=True)
with mysql.cursor() as commander:
    n = int(input("sql number: "))
    for _ in range(n):
        m = input("SQL: ")
        commander.execute(m)
        print(commander.fetchall())

mysql.close()
