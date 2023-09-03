import pymysql


def reset_time():
    mysql = pymysql.connect(user="ssch", passwd="rBXAm7WN", host="localhost",
                            db="ssch", charset="utf8", autocommit=True)
    """ with mysql.cursor() as commander:
        commander.execute(
            f'create table waiters(id smallint(10) not null auto_increment, number char(5), name varchar(20), sex char(10), time char(7), symptom varchar(10000), uniq char(40), primary key(id))')
        commander.execute(
            f'create table daily(id smallint(10) not null auto_increment, number char(5), name varchar(20), sex char(10), time char(7), disease varchar(400), treat varchar(1000), uniq char(40), primary key(id))')
        commander.execute(
            f'create table yearly(id smallint(10) not null auto_increment, number char(5), name varchar(20), sex char(10), time char(20), disease varchar(400), treat varchar(1000), uniq char(40), primary key(id))')
        commander.execute(
            f'create table posttime(posttime char(15))')
        commander.execute(
            f'insert into posttime values("1970.01.01")')
        for i in range(8, 18):
            if i == 12:
                continue
            h = str(i).rjust(2, '0')
            commander.execute(
                f'create table time_{h}(min char(5), pos tinyint(1), primary key(min))')
            for j in range(0, 60):
                m = str(j).rjust(2, '0')
                commander.execute(f'insert into time_{h} values("{m}", 1)')
        commander.execute('select * from posttime')
        print(commander.fetchall()) """

    with mysql.cursor() as commander:
        for i in range(8, 18):
            if i == 12:
                continue
            h = str(i).rjust(2, '0')
            commander.execute(
                f'update time_{h} set pos=1')
    mysql.close()
