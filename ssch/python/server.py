import websockets
import asyncio
import json
import traceback
import hashlib
from sqlModule import *
from makeXl import makeFile
from copy import deepcopy as copy
from logs import log as logging
from datetime import datetime
from pytz import timezone
from random import shuffle
from ws_client import WsClient, NoKeyOrIVError
from RSA_layer import RSA_decrypt


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


def hash160(string):
    return hashlib.new('ripemd160', string.encode()).digest().hex()


def restart():
    res = selData("daily", -1, "01", dateFileName)
    for r in res:
        r['time'] = f"{date} {r['time']}"
        sql_executor(sql_command, inputSql(
            "yearly", day_keys, r), -1, "02", "restart", dateFileName)
    sql_executor(sql_command, "truncate daily", -
                 1, "04", "restart", dateFileName)
    sql_executor(sql_command, "truncate waiters", -
                 1, "05", "restart", dateFileName)
    sql_executor(sql_command, "truncate posttime", -
                 1, "06", "restart", dateFileName)
    sql_executor(
        sql_command, f"insert into posttime values('{date}')", -1, "07", "restart", dateFileName)
    reset_time()
    future = datetime.now(timezone('Asia/Seoul')).strftime('%m.%d')
    sql_executor(
        sql_command, f"insert into static values(0, 0, '{future}')", -1, "08", "restart", dateFileName)


def getTime():
    ret = {}
    for h in range(8, 17):
        if h == 12:
            continue
        hour = str(h).rjust(2, '0')
        ret[hour] = []
        res = sql_executor(
            sql_command, f'select min from time_{hour} where pos=0', 'setting', '01', None, dateFileName)
        for r in res:
            ret[hour].append(r['min'])
    return ret


def form(type=2, status=1, header=0, body_return=-1, body_body=[], client: WsClient = None):
    """websocket으로 보낼 반환값을 받는 함수

    Args:
        status: 상태 메시지입니다. 0은 실패, 1은 성공입니다.
        header: content의 타입입니다. pursue와 동일합니다.
        body: content 본문입니다.

    Return:
        json 형태로 반환 객체를 바꾸어 줍니다.
    """
    plain = json.dumps(
        {
            "stat": status,
            "content": {
                "header": header,
                "body": {
                    "return": body_return,
                    "body": body_body
                }
            }
        }
    )

    if type == 0:
        enc = plain
    elif type == 2:
        enc = client.encrypt(plain)

    return json.dumps(
        {
            "type": type,
            "enc": enc
        }
    )


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
    for client, other in others.items():
        if other.client != except_websocket:
            try:
                await other.send(form(header=header, body_return=body_return, body_body=body_body, client=other))
            except NoKeyOrIVError:
                pass
            except:
                removeds.append(client)
    for removed in removeds:
        del others[removed]


async def service(websocket, path):
    try:
        async for message in websocket:
            global teacher, others, possible, bed, date, time_flag, waiter_flag, time, waiter, static, master, pubkey
            if date != datetime.now(timezone('Asia/Seoul')).strftime("%Y.%m.%d"):
                restart()
                main()

            if time_flag:
                time = getTime()
                time_flag = False
            if waiter_flag:
                waiter = selData("waiters", 'setting', "01", dateFileName)
                waiter_flag = False

            message = json.loads(message)
            print(message)
            if message['type'] == 0:
                message = json.loads(message['enc'])
            elif message['type'] == 1:
                message = json.loads(RSA_decrypt(message['enc']))
            elif message['type'] == 2:
                client: WsClient = others[websocket]
                message = json.loads(client.decrypt(message['enc']))
            elif message['type'] == "ping":
                if message['enc'] == "reconnect":
                    sql_executor(sql_command, "select 1", pursue,
                                 "01", None, dateFileName)
                await websocket.send(form(type=0, header=6, body_return="pong"))
                return
            print(message)
            pursue, stat, content_header, content_body = message["type"], message[
                'stat'], message["content"]["header"], message["content"]["body"]

            if pursue == 0:
                if content_header == "t":
                    teacher = WsClient(websocket=websocket)
                elif content_header == "s":
                    others[websocket] = WsClient(websocket=websocket)
                elif content_header == "m":
                    master = WsClient(websocket=websocket)
                else:
                    raise RuntimeError(
                        "pursue: 1, content_header error: neither t or s")
                await websocket.send(form(type=0, header=6, body_return=0, body_body=pubkey))

            elif pursue == 1:
                if content_header == "t":
                    res_d = selData("daily", pursue, "01", dateFileName)
                    ret = {"waiters": waiter, "daily": res_d,
                           "diagPos": possible, "bedNum": bed}
                    teacher.set_ki(content_body['key'], content_body['iv'])
                    await websocket.send(form(header=6, body_return=1, body_body=ret, client=teacher))
                elif content_header == "s":
                    ret = {"times": time, "bedNum": bed,
                           "diagPos": possible}
                    others[websocket].set_ki(
                        content_body['key'], content_body['iv'])
                    await websocket.send(form(header=6, body_return=1, body_body=ret, client=others[websocket]))
                else:
                    raise RuntimeError(
                        "pursue: 1, content_header error: neither t or s")

            elif pursue == 2:
                if content_header == "s":
                    data = copy(content_body)
                    h, m = data['time'].split(":")
                    if m in time[h] or not (8 <= int(h) <= 17) or h == '12':
                        await websocket.send(form(header=6, body_return=2, body_body=-1, client=others[websocket]))
                        return
                    temp = list(data.values())
                    shuffle(temp)
                    data["uniq"] = hash160(
                        ''.join(temp))
                    sql = inputSql(
                        "waiters", wait_keys, data)
                    sql_executor(sql_command, sql, pursue,
                                 "01", data, dateFileName)
                    sql_executor(
                        sql_command, f'update time_{h} set pos=0 where min="{m}"', pursue, "02", data['time'], dateFileName)
                    # content_body structure : {'number':~, 'name':~, 'sex':~, 'symptom':~, 'time':~}
                    await sending_2_all(header=2, body_body=data['time'])
                    try:
                        await teacher.send(form(header=2, body_body=data, client=teacher))
                        await master.send(form(header=2, body_body=data, client=master))
                    except:
                        pass
                    sql_executor(
                        sql_command, f"update static set total=static.total+1 where time='{static}'", pursue, "02", data, dateFileName)
                    if stat == 49:
                        sql_executor(
                            sql_command, f"update static set number=static.number+1 where time='{static}'", pursue, "03", data, dateFileName)
                    waiter_flag = True
                    time_flag = True
                else:
                    raise RuntimeError(
                        "pursue: 2, content_header error: not s")
                await websocket.send(form(header=6, body_return=2, client=others[websocket]))

            elif pursue == 3:
                if content_header == "t":
                    data = copy(content_body)
                    h, m = data['time'].split(":")
                    uniq = data['uniq']
                    # waiters = list(filter(lambda x: x['time'] != content_body, waiters))
                    sql = delSql("waiters", uniq)
                    sql_executor(sql_command, sql, pursue,
                                 "02", data, dateFileName)
                    sql_executor(initializeId, "waiters", pursue,
                                 "03", data, dateFileName)
                    waiter_flag = True
                    await sending_2_all(header=3, body_body=data['time'])
                    sql_executor(
                        sql_command, f'update time_{h} set pos=1 where min="{m}"', pursue, "01", data['time'], dateFileName)
                    time_flag = True
                else:
                    raise RuntimeError(
                        "pursue: 3, content_header error: not t")
                await websocket.send(form(header=6, body_return=3, client=teacher))

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
                await websocket.send(form(header=6, body_return=4, client=teacher))

            elif pursue == 5:
                if content_header == "t":
                    possible = content_body
                    await sending_2_all(header=5, body_body=possible)
                else:
                    raise RuntimeError(
                        "pursue: 5, content_header error: not t")
                await websocket.send(form(header=6, body_return=5, client=teacher))

            elif pursue == 7:
                if content_header == "t":
                    data = copy(content_body)

                    sql = inputSql(
                        "daily", day_keys, data)
                    sql_executor(sql_command, sql, pursue,
                                 "01", data, dateFileName)

                    sql = delSql("waiters", data['uniq'])
                    sql_executor(sql_command, sql, pursue,
                                 "02", data, dateFileName)
                    waiter_flag = True

                    res = selData("daily", pursue, "03", dateFileName)
                    await sending_2_all(header=3, body_body=data['time'])
                else:
                    raise RuntimeError(
                        "pursue: 5, content_header error: not t")
                await websocket.send(form(header=6, body_return=7, body_body=res, client=teacher))

            elif pursue == 8:
                if content_header == "t":
                    data = copy(content_body)
                    for crit, value in content_body.items():
                        queries = []
                        for val in value:
                            queries.append(f'{val[0]}="{val[1]}"')
                        sql_executor(
                            sql_command, f'update daily set {", ".join(queries)} where uniq="{crit}"', pursue, "01", data, dateFileName)
                else:
                    raise RuntimeError(
                        "pursue: 8, content_header error: not t")
                await websocket.send(form(header=6, body_return=8, client=teacher))

            elif pursue == 9:
                if content_header == "t":
                    data = content_body
                    sql = delSql('daily', data)
                    sql_executor(sql_command, sql, pursue,
                                 "01", data, dateFileName)
                    sql_executor(initializeId, "daily", pursue,
                                 "02", data, dateFileName)
                    res = selData("daily", pursue, "03", dateFileName)
                else:
                    raise RuntimeError(
                        "pursue: 9, content_header error: not t")
                await websocket.send(form(header=6, body_return=9, body_body=res, client=teacher))

            elif pursue == 10:
                if content_header == "t":
                    res = sql_executor(
                        sql_command, "select id, number, name, sex, time, disease, treat from daily order by time", pursue, "01", None, dateFileName)
                    for i, r in enumerate(res, start=1):
                        r['id'] = i
                    tm = datetime.now(timezone('Asia/Seoul')).strftime("%Y.%m")
                    ret = [[] for _ in range(6)]

                    for t in treatType:
                        ret[0].append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="남" and disease like "%{t}%"', pursue, "02", None, dateFileName)[0]['cnt'])
                        ret[1].append(sql_executor(
                            sql_command, f'select count(*) as cnt from daily where sex="여" and disease like "%{t}%"', pursue, "03", None, dateFileName)[0]['cnt'])
                        ret[2].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "%{tm}%" and sex="남" and disease like "%{t}%"', pursue, "04", None, dateFileName)[0]['cnt'] + ret[0][-1])
                        ret[3].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where time like "%{tm}%" and sex="여" and disease like "%{t}%"', pursue, "05", None, dateFileName)[0]['cnt'] + ret[1][-1])
                        ret[4].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="남" and disease like "%{t}%"', pursue, "06", None, dateFileName)[0]['cnt'] + ret[0][-1])
                        ret[5].append(sql_executor(
                            sql_command, f'select count(*) as cnt from yearly where sex="여" and disease like "%{t}%"', pursue, "07", None, dateFileName)[0]['cnt'] + ret[1][-1])

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
                await websocket.send(form(header=6, body_return=10, body_body=f"{dateFileName}", client=teacher))

            else:
                raise RuntimeError(
                    "main if clause, pursue is not 1 ~ 5 or 7~10 or pingpong")
    except:
        err = traceback.format_exc()
        logging(err, dateFileName)
        await websocket.send(form(type=0, status=0))
        time_flag = True
        waiter_flag = True


def main():
    global teacher, others, possible, bed, date, dateFileName, time_flag, waiter_flag, time, waiter, static, master, pubkey  # , logger
    date = datetime.now(timezone('Asia/Seoul')).strftime("%Y.%m.%d")
    dateFileName = ''.join(date.split('.'))
    static = datetime.now(timezone('Asia/Seoul')).strftime("%m.%d")
    teacher = None  # 선생님 웹소켓
    master = None
    others = dict()  # 다른 학생들의 웹소켓 정보
    time_flag = False
    waiter_flag = False
    # waiters = {} # 지금 기다리고 있는 학생들 리스트, [ 학년반, 이름, 성별, 증상, 시간 ] 5가지로 이루어져 있다.
    # 예약된 시간, "hour" : [ "appointedMinute1", "appointedMinute2" ]의 형식임
    possible = False  # 현재 진료 가능한 상황인지 여부, 0은 불가능 1은 가능
    bed = 4  # 현재 사용 가능한 침대 개수(0~2)
    time = getTime()
    waiter = selData("waiters", 'setting', "01", dateFileName)
    pubkey = open('/var/www/html/ssch/pem/pubkey.pem').read()
    # logger = makeLogger()
    logging("server (re)started", dateFileName)


wait_keys = ["number", "name", "sex", "time", "symptom", "uniq"]
day_keys = ["number", "name", "sex", "time", "disease", "treat", "uniq"]
treatType = "호흡기계 소화기계 순환기계 정신신경계 근골격계 피부피하계 비뇨생식기계 구강치아계 이비인후과계 안과계 감염병 알러지 기타".split(
    " ")
main()
if sql_executor(sql_command, 'select * from posttime', -1, "00", None, dateFileName)[0]['posttime'] != date:
    restart()
try:
    server = websockets.serve(service, "0.0.0.0", 52125)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()
except:
    err = traceback.format_exc()
    if "websockets.exceptions.ConnectionClosedError" not in err:
        logging("WARNING EXCEPTION - WEBSOCKET ERROR, CODE EDIT NEC\n\n" +
                err, dateFileName)
        time_flag = True
        waiter_flag = True
