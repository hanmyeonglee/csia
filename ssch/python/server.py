import websockets
import asyncio
import json
import pymysql
import traceback
import hashlib
from sqlModule import reset_time
from makeXl import makeFile
from copy import deepcopy as copy
from logs import log as logging
from pymysql import cursors
from datetime import datetime
from random import shuffle


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


class Client:
    def __init__(self, websocket):
        self.client = websocket
        self.time = datetime.now().timestamp()

    def timeUpdate(self):
        self.time = datetime.now().timestamp()

    def conTest(self):
        if self.client.closed:
            return False
        elif datetime.now().timestamp() - self.time > 600:
            self.client.close()
            return False
        else:
            return True


def hash160(string):
    return hashlib.new('ripemd160', string.encode()).digest().hex()


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


def delSql(db, uniq):
    return f'delete from {db} where uniq="{uniq}"'


def selData(db, pursue, num):
    ret = sql_executor(
        sql_command, f'select * from {db} order by time', pursue, num, None)
    for i, r in enumerate(ret):
        r['id'] = i+1
    return ret


def restart():
    res = selData("daily", -1, "01")
    for r in res:
        sql_executor(sql_command, inputSql(
            "yearly", day_keys, r), -1, "02", "restart")
    sql_executor(sql_command, "truncate daily", -1, "04", "restart")
    sql_executor(sql_command, "truncate waiters", -1, "05", "restart")
    reset_time()


def getTime():
    ret = {}
    for h in range(8, 18):
        if h == 12:
            continue
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
    for client in others:
        try:
            other = client.client
        except:
            others.remove(client)
            continue
        if other != except_websocket and client.conTest:
            try:
                await other.send(form(header=header, body_return=body_return, body_body=body_body))
            except:
                removeds.append(other)
    for removed in removeds:
        others.remove(removed)
    else:
        print(f"disconnected - {len(removeds)}")


async def service(websocket, path):
    try:
        async for message in websocket:
            global teacher, others, possible, bed, date, time_flag, waiter_flag, time, waiter
            print(dir(websocket))
            if date != datetime.now().strftime("%Y.%m.%d"):
                restart()
                main()

            if time_flag:
                time = getTime()
                time_flag = False
            if waiter_flag:
                waiter = selData("waiters", 'setting', "01")
                waiter_flag = False

            print(message)
            message = json.loads(message)
            pursue, stat, content_header, content_body = message["type"], message[
                'stat'], message["content"]["header"], message["content"]["body"]

            if pursue == 0:
                if content_header == "t":
                    teacher = websocket
                elif content_header == "s":
                    others.add(Client(websocket))
                else:
                    raise RuntimeError(
                        "pursue: 1, content_header error: neither t or s")
                await websocket.send(form(header=6, body_return=0))

            elif pursue == 1:
                if content_header == "t":
                    res_d = selData("daily", pursue, "01")
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
                    temp = list(data.values())
                    shuffle(temp)
                    data["uniq"] = hash160(
                        ''.join(temp))
                    sql = inputSql(
                        "waiters", wait_keys, data)
                    sql_executor(sql_command, sql, pursue, "02", data)
                    waiter_flag = True
                    # content_body structure : {'number':~, 'name':~, 'sex':~, 'symptom':~, 'time':~}
                    await sending_2_all(header=2, body_body=data['time'])
                    try:
                        await teacher.send(form(header=2, body_body=data))
                    except:
                        pass
                    sql_executor(
                        sql_command, f'update time_{h} set pos=0 where min="{m}"', pursue, "01", data)
                    time_flag = True
                    for client in others:
                        try:
                            other = client.client
                            if other == websocket:
                                client.timeUpdate()
                            break
                        except:
                            others.remove(other)
                            continue
                else:
                    raise RuntimeError(
                        "pursue: 2, content_header error: not s")
                await websocket.send(form(header=6, body_return=2))

            elif pursue == 3:
                if content_header == "t":
                    data = copy(content_body)
                    h, m = data['time'].split(":")
                    uniq = data['uniq']
                    # waiters = list(filter(lambda x: x['time'] != content_body, waiters))
                    sql = delSql("waiters", uniq)
                    sql_executor(sql_command, sql, pursue, "02", data)
                    sql_executor(initializeId, "waiters", pursue, "03", data)
                    waiter_flag = True
                    await sending_2_all(header=3, body_body=data)
                    sql_executor(
                        sql_command, f'update time_{h} set pos=1 where min="{m}"', pursue, "01", data['time'])
                    time_flag = True
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

                    sql = delSql("waiters", data['uniq'])
                    sql_executor(sql_command, sql, pursue, "02", data)
                    waiter_flag = True

                    res = selData("daily", pursue, "03")
                    await sending_2_all(header=3, body_body=data['time'])
                else:
                    raise RuntimeError(
                        "pursue: 5, content_header error: not t")
                await websocket.send(form(header=6, body_return=7, body_body=res))

            elif pursue == 8:
                if content_header == "t":
                    data = copy(content_body)
                    for crit, value in content_body.items():
                        queries = []
                        for val in value:
                            queries.append(f'{val[0]}="{val[1]}"')
                        sql_executor(
                            sql_command, f'update daily set {", ".join(queries)} where uniq="{crit}"', pursue, "01", data)
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
                    res = selData("daily", pursue, "03")
                else:
                    raise RuntimeError(
                        "pursue: 9, content_header error: not t")
                await websocket.send(form(header=6, body_return=9, body_body=res))

            elif pursue == 10:
                if content_header == "t":
                    res = sql_executor(
                        sql_command, "select id, number, name, sex, time, disease, treat from daily order by time", pursue, "01", None)
                    for i, r in enumerate(res, start=1):
                        r['id'] = i
                    tm = datetime.now().strftime("%Y.%m")
                    ret = [[] for _ in range(6)]

                    for t in treatType:
                        ret[0].append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="남" and disease like "%{t}%"', pursue, "02", None)[0]['cnt'])
                        ret[1].append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="여" and disease like "%{t}%"', pursue, "03", None)[0]['cnt'])
                        ret[2].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "{tm}%" and sex="남" and disease like "%{t}%"', pursue, "04", None)[0]['cnt'] + ret[0][-1])
                        ret[3].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "{tm}%" and sex="여" and disease like "%{t}%"', pursue, "05", None)[0]['cnt'] + ret[1][-1])
                        ret[4].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="남" and disease like "%{t}%"', pursue, "06", None)[0]['cnt'] + ret[0][-1])
                        ret[5].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="여" and disease like "%{t}%"', pursue, "07", None)[0]['cnt'] + ret[1][-1])

                    makeFile(
                        res,
                        [
                            ['성별'] + copy(treatType) + ['', '', '계'],
                            ['남'] + ret[0] + ['', '', str(sum(ret[0]))],
                            ['여'] + ret[1] + ['', '', str(sum(ret[1]))],
                            ['남'] + ret[2] + ['', '', str(sum(ret[2]))],
                            ['여'] + ret[3] + ['', '', str(sum(ret[3]))],
                            ['남'] + ret[4] + ['', '', str(sum(ret[4]))],
                            ['여'] + ret[5] + ['', '', str(sum(ret[5]))]
                        ],
                        date
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
        time_flag = True
        waiter_flag = True


async def close_confirm():
    while True:
        await asyncio.sleep(300)  # 300초마다 실행
        for client in others:
            try:
                flag = client.conTest()
                if not flag:
                    others.remove(client)
                    del client
            except:
                continue


async def server():
    server = await websockets.serve(service, "0.0.0.0", 52125)
    return asyncio.gather(asyncio.create_task(server), asyncio.create_task(close_confirm()))


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
    waiter = selData("waiters", 'setting', "01")
    # logger = makeLogger()
    logging("server (re)started", dateFileName)


main()
wait_keys = ["number", "name", "sex", "time", "symptom", "uniq"]
day_keys = ["number", "name", "sex", "time", "disease", "treat", "uniq"]
treatType = "호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(
    " ")
server = server()
loop = asyncio.get_event_loop()
loop.run_until_complete(server)
loop.run_forever()
