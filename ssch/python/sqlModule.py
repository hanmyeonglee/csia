import traceback
from logs import log as logging


def reset_time(con):
    with con.cursor() as commander:
        for i in range(8, 17):
            if i == 12:
                continue
            h = str(i).rjust(2, '0')
            commander.execute(f'update time_{h} set pos=1')


def sql_command(con, command):
    with con.cursor() as commander:
        commander.execute(command)
        res = commander.fetchall()
        return res


def initializeId(con, tableN):
    with con.cursor() as commander:
        commander.execute('SET @count=0')
        commander.execute(f'update {tableN} SET id=@count:=@count+1')
        commander.execute(f'alter table {tableN} auto_increment=1')


def sql_executor(func, sql, pursue, num, data, dateFileName, con):
    try:
        return func(con, sql)
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


def selData(db, pursue, num, dateFileName, con):
    ret = sql_executor(
        sql_command, f'select * from {db} order by time', pursue, num, None, dateFileName, con)
    for i, r in enumerate(ret):
        r['id'] = i+1
    return ret
