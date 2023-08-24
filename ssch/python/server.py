import websockets
import asyncio
import json
import pymysql
import traceback
import csv
from sqlModule import reset_time
from makeXl import makeFile
from copy import deepcopy as copy
from logs import log as logging
from pymysql import cursors
from datetime import datetime


""" 
pursue
0 = connect request
1 = request informations
2 = add to waiters
3 = delete from waiters
4 = bed possibility
5 = diagnosis possibility
6 = confirm from server
7 = add patient to daily db
8 = edit daily db
9 = delete patient from daily db
10 = request csv file

header
"t" = teacher
"s" = student
"""


def makeCSV():
    # raise RuntimeError("my mom")
    with open(file=f'/var/www/html/ssch/csv/{dateFileName}.daily.csv', mode='w', encoding='utf-8') as csvf:
        res = sql_executor(sql_command, 'select * from daily', 10, "01", None)
        keys = ["id", "number", "name", "sex", "disease", "treat", "time"]
        writer = csv.DictWriter(csvf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(res)
        csvf.close()


def sql_command(command):
    with mysql.cursor() as commander:
        commander.execute(command)
        res = commander.fetchall()
        return res


def initializeId(tableN):
    with mysql.cursor() as commander:
        commander.execute('SET @count=0')
        commander.execute(f'update {tableN} SET id=@count:=@count+1')
        commander.execute(f'alter table {tableN} auto_increment=1')


def sql_executor(func, sql, pursue, num, data):
    try:
        return func(sql)
    except:
        err = traceback.format_exc()
        print('err01 :', err)
        logging(err, dateFileName)
        raise RuntimeError(
            f"pursue: {pursue}, mysql stdio error{num}: data = {data}")


def inputSql(db, keys, data):
    queries = []
    for key in keys:
        queries.append(f'"{data[key]}"')
    return f'insert into {db}({", ".join(keys)}) values({", ".join(queries)})'


def delSql(db, time):
    return f'delete from {db} where time="{time}"'


def restart():
    res = sql_executor(sql_command, "select * from daily", -1, "01", "restart")
    for r in res:
        sql_executor(sql_command, inputSql(
            "yearly", day_keys, r), -1, "02", "restart")
    sql_executor(sql_command, "truncate daily", -1, "04", "restart")
    sql_executor(sql_command, "truncate waiters", -1, "05", "restart")
    reset_time()


def getTime():
    ret = {}
    for h in range(8, 18):
        if h == 12: continue
        hour = str(h).rjust(2, '0')
        ret[hour] = []
        res = sql_executor(
            sql_command, f'select min from time_{hour} where pos=0', 'setting', '01', None)
        for r in res:
            ret[hour].append(r['min'])
    return ret


def form(status=1, header=0, body_return=-1, body_body=[]):
    """websocket으로 보낼 반환값을 받는 함수

    Args:
        status: 상태 메시지입니다. 0은 실패, 1은 성공입니다.
        header: content의 타입입니다. pursue와 동일합니다.
        body: content 본문입니다.

    Return:
        json 형태로 반환 객체를 바꾸어 줍니다.
    """
    return json.dumps({"stat": status, "content": {"header": header, "body": {"return": body_return, "body": body_body}}})


async def sending_2_all(except_websocket=None, header=0, body_return=-1, body_body=[]):
    """추가/수정/삭제된 데이터 정보를 다른 websocket들에게 보냄

    Args:
        except_websocket: 데이터를 보낸 웹소켓을 말한다. 제외해야 한다.
        header: pursue와 같다. 2, 3, 4, 5 중 하나이다.
        body: 변경된 데이터 값을 뜻한다.

    Return:
        없음

    Feature:
        asynchronous function
    """
    global others
    removeds = []
    for other in others:
        if other != except_websocket:
            try:
                await other.send(form(header=header, body_return=body_return, body_body=body_body))
            except:
                removeds.append(other)
    for removed in removeds:
        others.remove(removed)
    else:
        print(f"disconnected - {len(removed)}")


async def service(websocket, path):
    try:
        async for message in websocket:
            global teacher, others, possible, bed, date, time_flag, waiter_flag, time, waiter

            if date != datetime.now().strftime("%Y.%m.%d"):
                restart()
                main()

            if time_flag:
                time = getTime()
                time_flag = False
            if waiter_flag:
                waiter = sql_executor(
                    sql_command, 'select * from waiters', 'setting', "01", None)
                waiter_flag = False

            print(message)
            message = json.loads(message)
            pursue, stat, content_header, content_body = message["type"], message[
                'stat'], message["content"]["header"], message["content"]["body"]

            if pursue == 0:
                if content_header == "t":
                    teacher = websocket
                elif content_header == "s":
                    others.add(websocket)
                else:
                    raise RuntimeError(
                        "pursue: 1, content_header error: neither t or s")
                await websocket.send(form(header=6, body_return=0))

            elif pursue == 1:
                if content_header == "t":
                    res_d = sql_executor(
                        sql_command, 'select * from daily', pursue, "02", None)
                    ret = {"waiters": waiter, "daily": res_d,
                           "diagPos": possible, "bedNum": bed}
                    await websocket.send(form(header=6, body_return=1, body_body=ret))
                elif content_header == "s":
                    ret = {"times": time, "bedNum": bed,
                           "diagPos": possible}
                    await websocket.send(form(header=6, body_return=1, body_body=ret))
                else:
                    raise RuntimeError(
                        "pursue: 1, content_header error: neither t or s")

            elif pursue == 2:
                if content_header == "s":
                    data = copy(content_body)
                    h, m = data['time'].split(":")
                    if m in time[h] or not (8 <= int(h) <= 17) or h == '12':
                        await websocket.send(form(header=6, body_return=2, body_body=-1))
                        return
                    sql_executor(
                        sql_command, f'update time_{h} set pos=0 where min="{m}"', pursue, "01", data)
                    time_flag = True
                    sql = inputSql(
                        "waiters", wait_keys, data)
                    sql_executor(sql_command, sql, pursue, "02", data)
                    waiter_flag = True
                    # content_body structure : {'number':~, 'name':~, 'sex':~, 'symptom':~, 'time':~}
                    await sending_2_all(header=2, body_body=data['time'])
                    try:
                        await teacher.send(form(header=2, body_body=data))
                    except:
                        raise RuntimeError(
                            f"pursue: 2, teacher not already connected = {data}")
                else:
                    raise RuntimeError(
                        "pursue: 2, content_header error: not s")
                await websocket.send(form(header=6, body_return=2))

            elif pursue == 3:
                if content_header == "t":
                    data = copy(content_body)
                    h, m = data['time'].split(":")
                    sql_executor(
                        sql_command, f'update time_{h} set pos=1 where min="{m}"', pursue, "01", data)
                    time_flag = True
                    # waiters = list(filter(lambda x: x['time'] != content_body, waiters))
                    sql = delSql("waiters", data)
                    sql_executor(sql_command, sql, pursue, "02", data)
                    sql_executor(initializeId, "waiters", pursue, "03", data)
                    waiter_flag = True
                    await sending_2_all(header=3, body_body=data)
                else:
                    raise RuntimeError(
                        "pursue: 3, content_header error: not t")
                await websocket.send(form(header=6, body_return=3))

            elif pursue == 4:
                if content_header == "t":
                    bed += content_body
                    if bed > 4 or bed < 0:
                        bed -= content_body
                        raise RuntimeError(
                            "pursue: 4, bed remain over(under)flow")
                    await sending_2_all(header=4, body_body=bed)
                else:
                    raise RuntimeError(
                        "pursue: 4, content_header error: not t")
                await websocket.send(form(header=6, body_return=4))

            elif pursue == 5:
                if content_header == "t":
                    possible = content_body
                    await sending_2_all(header=5, body_body=possible)
                else:
                    raise RuntimeError(
                        "pursue: 5, content_header error: not t")
                await websocket.send(form(header=6, body_return=5))

            elif pursue == 7:
                if content_header == "t":
                    data = copy(content_body)

                    sql = inputSql(
                        "daily", day_keys, data)
                    sql_executor(sql_command, sql, pursue, "01", data)

                    sql = delSql("waiters", data['time'])
                    sql_executor(sql_command, sql, pursue, "02", data)
                    waiter_flag = True

                    res = sql_executor(
                        sql_command, f'select * from daily', pursue, "03", data)
                    await sending_2_all(header=3, body_body=data['time'])
                else:
                    raise RuntimeError(
                        "pursue: 5, content_header error: not t")
                await websocket.send(form(header=6, body_return=7, body_body=res))

            elif pursue == 8:
                if content_header == "t":
                    data = copy(content_body)
                    for id, value in content_body.items():
                        queries = []
                        for val in value:
                            queries.append(f'{val[0]}="{val[1]}"')
                        sql_executor(
                            sql_command, f'update daily set {", ".join(queries)} where id={id}', pursue, "01", data)
                else:
                    raise RuntimeError(
                        "pursue: 8, content_header error: not t")
                await websocket.send(form(header=6, body_return=8))

            elif pursue == 9:
                if content_header == "t":
                    data = content_body
                    sql = delSql('daily', data)
                    sql_executor(sql_command, sql, pursue, "01", data)
                    sql_executor(initializeId, "daily", pursue, "02", data)
                else:
                    raise RuntimeError(
                        "pursue: 9, content_header error: not t")
                await websocket.send(form(header=6, body_return=9, body_body=res))

            elif pursue == 10:
                if content_header == "t":
                    res = sql_executor(
                        sql_command, 'select * from daily', pursue, "01", None)
                    tm = datetime.now().strftime("%Y.%m")
                    ret01_m = ret02_m = ret03_m = ret01_w = ret02_w = ret03_w = []

                    for t in treatType:
                        ret01_m.append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="남" and disease like "%{t}%"', pursue, "02", None)['cnt'])
                        ret01_w.append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="여" and disease like "%{t}%"', pursue, "03", None)['cnt'])
                        ret02_m.append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "{tm}%" and sex="남" and disease like "%{t}%"', pursue, "04", None)['cnt'] + ret01_m[-1])
                        ret02_w.append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "{tm}%" and sex="여" and disease like "%{t}%"', pursue, "05", None)['cnt'] + ret01_w[-1])
                        ret03_m.append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="남" and disease like "%{t}%"', pursue, "06", None)['cnt'] + ret01_m[-1])
                        ret03_w.append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="여" and disease like "%{t}%"', pursue, "07", None)['cnt'] + ret01_w[-1])

                    makeFile(
                        res,
                        [
                            ['성별'] + copy(treatType) + ['', '', '계'],
                            ['남'] + ret01_m + ['', '', str(sum(ret01_m))],
                            ['여'] + ret01_w + ['', '', str(sum(ret01_w))],
                            ['남'] + ret02_m + ['', '', str(sum(ret02_m))],
                            ['여'] + ret02_w + ['', '', str(sum(ret02_w))],
                            ['남'] + ret03_m + ['', '', str(sum(ret03_m))],
                            ['여'] + ret03_w + ['', '', str(sum(ret03_w))]
                        ],
                        dateFileName
                    )
                else:
                    raise RuntimeError(
                        "pursue: 9, content_header error: not t")
                await websocket.send(form(header=6, body_return=10, body_body=f"{dateFileName}"))

            else:
                raise RuntimeError(
                    "main if clause, pursue is not 1 ~ 5 or 7~10")
    except:
        err = traceback.format_exc()
        logging(err, dateFileName)
        print('err02 :', err)
        await websocket.send(form(status=0))


def main():
    global teacher, others, possible, bed, mysql, date, dateFileName, time_flag, waiter_flag, time, waiter  # , logger
    date = datetime.now().strftime("%Y.%m.%d")
    dateFileName = ''.join(date.split('.'))
    open(f"/var/www/html/ssch/logs/{dateFileName}.log", 'w')
    teacher = None  # 선생님 웹소켓
    others = set()  # 다른 학생들의 웹소켓 정보
    time_flag = False
    waiter_flag = False
    # waiters = {} # 지금 기다리고 있는 학생들 리스트, [ 학년반, 이름, 성별, 증상, 시간 ] 5가지로 이루어져 있다.
    # 예약된 시간, "hour" : [ "appointedMinute1", "appointedMinute2" ]의 형식임
    possible = False  # 현재 진료 가능한 상황인지 여부, 0은 불가능 1은 가능
    bed = 4  # 현재 사용 가능한 침대 개수(0~2)
    mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                            db="ssch", charset="utf8", cursorclass=cursors.DictCursor, autocommit=True)
    time = getTime()
    waiter = sql_executor(
        sql_command, 'select * from waiters', 'setting', "01", None)
    # logger = makeLogger()
    logging("server (re)started", dateFileName)


main()
wait_keys = ["number", "name", "sex", "time", "symptom"]
day_keys = ["number", "name", "sex", "time", "disease", "treat"]
treatType = "호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(
    " ")
server = websockets.serve(service, "0.0.0.0", 52125)
loop = asyncio.get_event_loop()
loop.run_until_complete(server)
loop.run_forever()
