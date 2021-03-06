# encoding=utf-8
import web
import xtemplate
import xutils
import xtables
from . import dao

class handler:

    def GET(self):
        id = int(xutils.get_argument("id"))
        name = xutils.get_argument("name", "")
        parent_id = xutils.get_argument("parent_id", "")
        record = dao.get_by_id(id)
        db = xtables.get_file_table()
        pathlist = dao.get_pathlist(db, record)
        if parent_id != "":
            db.update(where=dict(id=id), parent_id = parent_id)
            raise web.seeother("/file/view?id=%s" % parent_id)

        if name != "" and name != None:
            filelist = dao.search_name(name, file_type="group")
            newlist = []
            for f in filelist:
                if f.id == id:
                    continue
                else:
                    newlist.append(f)
            filelist = newlist
        else:
            filelist = db.select(where=dict(type="group",is_deleted=0), limit=200, order="name DESC")
        return xtemplate.render("file/archive.html", record = record, pathlist=pathlist, filelist = filelist)

class ChangeType:
    
    def GET(self):
        type = xutils.get_argument("type")
        id = xutils.get_argument("id")
        db = xtables.get_file_table()
        db.update(where=dict(id=id), type=type)
        raise web.seeother("/file/view?id=%s"%id)
        

xurls = (
    r"/file/archive", handler,
    r"/file/archive/change_type", ChangeType
)