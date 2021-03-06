# -*- coding:utf-8 -*-  
# Created by xupingmao on 2017/03/15
# 

"""Xnote的数据库配置"""
import os
import xutils
import xconfig
import web.db as db

sqlite3 = xutils.sqlite3

config = xconfig

class SqliteTableManager:
    """检查数据库字段，如果不存在就自动创建"""
    def __init__(self, filename, tablename, pkName=None, pkType=None, no_pk=False):
        self.filename = filename
        self.tablename = tablename
        self.db = sqlite3.connect(filename)
        if no_pk:
            # 没有主键，创建一个占位符
            sql = "CREATE TABLE IF NOT EXISTS `%s` (dummy int);" % tablename
        elif pkName is None:
            # 只有integer允许AUTOINCREMENT
            sql = "CREATE TABLE IF NOT EXISTS `%s` (id integer primary key autoincrement);" % tablename
        else:
            # sqlite允许主键重复，允许空值
            sql = "CREATE TABLE IF NOT EXISTS `%s` (`%s` %s primary key);" % (tablename, pkName, pkType)
        self.execute(sql)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def execute(self, sql, silent=False):
        cursorobj = self.db.cursor()
        try:
            if not silent:
                print(sql)
            cursorobj.execute(sql)
            kv_result = []
            result = cursorobj.fetchall()
            for single in result:
                resultMap = {}
                for i, desc in enumerate(cursorobj.description):
                    name = desc[0]
                    resultMap[name] = single[i]
                kv_result.append(resultMap)
            self.db.commit()
            return kv_result
        except Exception:
            raise

    def escape(self, strval):
        strval = strval.replace("'", "''")
        return "'%s'" % strval

    def add_column(self, colname, coltype, 
            default_value = None, not_null = False):
        """添加字段，如果已经存在则跳过，名称相同类型不同抛出异常"""
        sql = "ALTER TABLE `%s` ADD COLUMN `%s` %s" % (self.tablename, colname, coltype)

        # MySQL 使用 DESC [表名]
        columns = self.execute("pragma table_info('%s')" % self.tablename, silent=True)
        # print(columns.description)
        # description结构
        # ()
        for column in columns:
            name = column["name"]
            type = column["type"]
            if name == colname and type == coltype:
                # 已经存在
                return
        if default_value != None:
            if isinstance(default_value, str):
                default_value = self.escape(default_value)
            sql += " DEFAULT %s" % default_value
        if not_null:
            sql += " NOT NULL"
        self.execute(sql)

    def add_index(self, colname, is_unique = False):
        # sqlite的索引和table是一个级别的schema
        sql = "CREATE INDEX idx_%s_%s ON `%s` (`%s`)" % (self.tablename, colname, self.tablename, colname)
        try:
            self.execute(sql)
        except sqlite3.OperationalError:
            pass
        except Exception:
            xutils.print_exc()

    def drop_column(self, colname):
        # sql = "ALTER TABLE `%s` DROP COLUMN `%s`" % (self.tablename, colname)
        # sqlite不支持 DROP COLUMN 得使用中间表
        # TODO
        pass

    def close(self):
        self.db.close()

TableManager = SqliteTableManager

def init_table_test():
    path = os.path.join(xconfig.DATA_DIR, "test.db")
    with TableManager(path, "test") as manager:
        manager.add_column("id1", "integer", 0)
        manager.add_column("int_value", "int", 0)
        manager.add_column("float_value", "float")
        manager.add_column("text_value", "text", "")
        manager.add_column("name", "text", "test")
        manager.add_column("check", "text", "aaa'bbb")
        manager.add_index("check")

def init_table_file():
    with TableManager(config.DB_PATH, "file") as manager:
        manager.add_column("name",    "text", "")
        manager.add_column("content", "text", "")
        manager.add_column("size",    "long", 0)
        # 修改版本
        manager.add_column("version",  "int", 0)
        # 类型, markdown, post, mailist, file
        # 类型为file时，content值为文件的web路径
        manager.add_column("type", "text", "")
        
        # 关联关系
        # 上级目录
        manager.add_column("parent_id", "int", 0)
        # 使用file_tag表,兼容老代码,这里作为一个关键词存储，支持搜索
        manager.add_column("related", "text", "")

        # 统计相关
        # 访问次数
        # 创建时间ctime
        manager.add_column("sctime", "text", "")
        # 修改时间mtime
        manager.add_column("smtime", "text", "")
        # 访问时间atime
        manager.add_column("satime", "text", "")
        manager.add_column("visited_cnt", "int", 0)
        # 逻辑删除标记
        manager.add_column("is_deleted", "int", 0)
        # 是否公开
        manager.add_column("is_public", "int", 0)
        # 是否标记
        manager.add_column("is_marked", "int", 0)

        # 权限相关
        # 创建者
        manager.add_column("creator", "text", "")
        # 修改者
        manager.add_column("modifier", "text", "")
        # 权限组
        manager.add_column("groups", "text", "")
        
        # MD5
        manager.add_column("md5", "text", "")
        # 展示优先级，用于收藏等标记
        manager.add_column("priority", "int", 0)

def init_table_tag():
    # 2017/04/18
    with TableManager(config.DB_PATH, "file_tag", no_pk=True) as manager:
        # 标签名
        manager.add_column("name",    "text", "")
        # 标签ID
        manager.add_column("file_id", "int", 0)
        # 权限控制，标签不做用户区分, groups字段暂时废弃
        manager.add_column("groups",  "text", "")

def init_table_schedule():
    # 2017/05/24
    # task是计划任务
    # Job是已经触发的任务,倾向于一次性的
    with TableManager(config.DB_PATH, "schedule") as manager:
        manager.add_column("name", "text", "")
        manager.add_column("url",         "text", "")
        # manager.add_column("interval",    "integer", 60)
        manager.add_column("ctime",       "text", "")
        manager.add_column("mtime",       "text", "")
        # manager.add_column("repeat_type", "text", "interval")
        # manager.add_column("pattern",     "text", "00:00:00")
        manager.add_column("tm_wday", "text", "")  # Week Day no-repeat 一次性任务
        manager.add_column("tm_hour", "text", "")
        manager.add_column("tm_min",  "text", "")
        # 任务是否生效，用于一次性活动
        manager.add_column("active", "int", 1)
        manager.add_column("creator", "text", "")
        # 2017.10.21
        manager.add_column("message", "text", "") # 提醒消息
        manager.add_column("sound", "int", 0) # 是否语音提醒
        manager.add_column("webpage", "int", 0) # 是否网页提醒


def init_table_log():
    # 2017/05/21
    with TableManager(config.LOG_PATH, "xnote_log") as manager:
        manager.add_column("tag",      "text", "")
        manager.add_column("operator", "text", "")

def init_table_user():
    # 2017/05/21
    with TableManager(config.DB_PATH, "user") as manager:
        manager.add_column("name",       "text", "")
        manager.add_column("password",   "text", "")
        # 额外的访问权限
        manager.add_column("privileges", "text", "")
        manager.add_column("ctime",      "text", "")
        manager.add_column("mtime",      "text", "")

def init_table_message():
    # 用来存储比较短的消息
    # 2017/05/29
    with TableManager(config.DB_PATH, "message") as manager:
        manager.add_column("ctime", "text", "")
        manager.add_column("user",  "text", "")
        manager.add_column("content", "text", "")

def init_table_record():
    # 日志库和主库隔离开
    dbpath = os.path.join(xconfig.DATA_DIR, "record.db")
    with TableManager(dbpath, "record") as manager:
        manager.add_column("ctime", "text", "")
        # 添加单独的日期，方便统计用，尽量减少SQL函数的使用
        manager.add_column("cdate", "text", "")
        manager.add_column("type",  "text", "")
        # 自己把所有条件都组装到key里
        manager.add_column("key",  "text", "")
        manager.add_column("value", "text", "")

class FakeDB():

    def select(self, *args, **kw):
        from web.utils import IterBetter
        return IterBetter(iter([]))

    def update(self, *args, **kw):
        return 0

    def insert(self, *args, **kw):
        return None

    def query(self, *args, **kw):
        from web.utils import IterBetter
        return IterBetter(iter([]))

class DBWrapper:
    """ 基于web.db的装饰器 """

    _pool = dict()

    def __init__(self, dbpath, tablename):
        self.tablename = tablename
        self.dbpath = dbpath
        # SqliteDB 使用了threadlocal来实现，是线程安全的，使用全局单实例即可
        _db = DBWrapper._pool.get(dbpath)
        if _db is None:
            if sqlite3 is not None:
                _db = db.SqliteDB(db=dbpath)
            else:
                _db = FakeDB()
            DBWrapper._pool[dbpath] = _db
        self.db = _db

    def insert(self, *args, **kw):
        return self.db.insert(self.tablename, *args, **kw)

    def select(self, *args, **kw):
        return self.db.select(self.tablename, *args, **kw)

    def select_one(self, *args, **kw):
        return self.db.select(self.tablename, *args, **kw).first()

    def query(self, *args, **kw):
        return self.db.query(*args, **kw)

    def count(self, where=None, sql = None):
        if sqlite3 is None:
            return 0
        if sql is None:
            sql = "SELECT COUNT(1) AS amount FROM %s" % self.tablename
            if where:
                sql += " WHERE %s" % where
        return self.db.query(sql).first().amount

    def update(self, *args, **kw):
        return self.db.update(self.tablename, *args, **kw)

    def delete(self, *args, **kw):
        return self.db.delete(self.tablename, *args, **kw)

    def execute(self, sql, args=None):
        # 不建议使用，尽量使用query
        return xutils.db_execute(self.dbpath, sql, args)

def get_file_table():
    return DBWrapper(config.DB_PATH, "file")

def get_file_tag_table():
    return DBWrapper(config.DB_PATH, "file_tag")

def get_schedule_table():
    return DBWrapper(config.DB_PATH, "schedule")

def get_user_table():
    return DBWrapper(config.DB_PATH, "user")

def get_message_table():
    return DBWrapper(config.DB_PATH, "message")

def get_record_table():
    dbpath = os.path.join(xconfig.DATA_DIR, "record.db")
    return DBWrapper(dbpath, "record")


def init():
    if sqlite3 is None:
        # Jython
        return
    # init_table_test()
    init_table_user()
    init_table_file()
    init_table_tag()
    init_table_schedule()
    init_table_message()
    init_table_record()

