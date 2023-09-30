import pymysql
import traceback
from logs import log as logging
from pymysql import cursors


def make_connection():
    return pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                           db="ssch", port=23474, charset="utf8", cursorclass=cursors.DictCursor, autocommit=True)


def reset_time():
    con = make_connection()
    with con.cursor() as commander:
        for i in range(8, 17):
            if i == 12:
                continue
            h = str(i).rjust(2, '0')
            commander.execute(f'update time_{h} set pos=1')
    con.close()


def sql_command(command):
    con = make_connection()
    with con.cursor() as commander:
        commander.execute(command)
        res = commander.fetchall()
        con.close()
        return res


def initializeId(tableN):
    con = make_connection()
    with con.cursor() as commander:
        commander.execute('SET @count=0')
        commander.execute(f'update {tableN} SET id=@count:=@count+1')
        commander.execute(f'alter table {tableN} auto_increment=1')
        con.close()


def sql_executor(func, sql, pursue, num, data, dateFileName):
    try:
        return func(sql)
    except:
        err = traceback.format_exc()
        logging(err, dateFileName)
        raise RuntimeError(
            f"pursue: {pursue}, mysql stdio error{num}: data = {data}")


def inputSql(db, keys, data):
    queries = []
    for key in keys:
        queries.append(f'"{data[key]}"')
    return f'insert into {db}({", ".join(keys)}) values({", ".join(queries)})'


def delSql(db, uniq):
    return f'delete from {db} where uniq="{uniq}"'


def selData(db, pursue, num):
    ret = sql_executor(
        sql_command, f'select * from {db} order by time', pursue, num, None)
    for i, r in enumerate(ret):
        r['id'] = i+1
    return ret
