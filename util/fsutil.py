# encoding=utf-8
import codecs
import os
import platform
import xutils
import base64

from . import logutil
from web.utils import Storage

''' read file '''
def readFile(path):
    try:
        fp = open(path, encoding="utf-8")
        content = fp.read()
        fp.close()
        return content
    except:
        fp = open(path, encoding="gbk")
        content = fp.read()
        fp.close()
        return content

def read_utf8(path):
    fp = open(path, encoding="utf-8")
    content = fp.read()
    fp.close()
    return content

def read(path):
    return readFile(path)

def readfile(path):
    return readFile(path)

def readRawFile(path):
    fp = open(path, "rb")
    buf = fp.read(1024)
    while buf:
        yield buf
        buf = fp.read(1024)
    fp.close()

def writeFile(path, content):
    fp = open(path, "wb")
    buffer = codecs.encode(content, "utf-8")
    fp.write(buffer)
    fp.close()
    return content

def writefile(path, content):
    return writeFile(path, content)

def writebytes(path, bytes):
    dirname = os.path.dirname(path)
    check_create_dirs(dirname)
    fp = open(path, "wb")
    fp.write(bytes)
    fp.close()
    return bytes

def readbytes(path):
    fp = open(path, "rb")
    bytes = fp.read()
    fp.close()
    return bytes

def removeFile(fullpath, raiseIfNotExists = False):
    if os.path.exists(fullpath):
        os.remove(fullpath)
    elif raiseIfNotExists:
        raise Error("file not exits!")

def remove(path):
    removeFile(path)

def copy(src, dest):
    bufsize = 64 * 1024 # 64k
    srcfp = open(src, "rb")
    destfp = open(dest, "wb")

    try:
        buf = srcfp.read(bufsize)
        while buf:
            destfp.write(buf)
            buf = srcfp.read(bufsize)
    except Exception as e:
        logutil.error("copy file from {} to {} failed", src, dest, e)

    srcfp.close()
    destfp.close()

def check_create_dirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def getFileExt(fname):
    if '.' not in fname:return ''
    return fname.split('.')[-1]

def getReadableSize(size):
    if size < 1024:
        return '%s B' % size
    elif size < 1024 **2:
        return '%.2f K' % (float(size) / 1024)
    elif size < 1024 ** 3:
        return '%.2f M' % (float(size) / 1024 ** 2)
    else:
        return '%.2f G' % (float(size) / 1024 ** 3)

def format_size(size):
    if size < 1024:
        return '%s B' % size
    elif size < 1024 **2:
        return '%.2f K' % (float(size) / 1024)
    elif size < 1024 ** 3:
        return '%.2f M' % (float(size) / 1024 ** 2)
    else:
        return '%.2f G' % (float(size) / 1024 ** 3)

formatSize = format_size
        
def renameFile(srcname, dstname):
    destDirName = os.path.dirname(dstname)
    if not os.path.exists(destDirName):
        os.makedirs(destDirName)
    os.rename(srcname, dstname)


def openDirectory(dirname):
    if os.name == "nt":
        os.popen("explorer %s" % dirname)
    elif platform.system() == "Darwin":
        os.popen("open %s" % dirname)

def get_file_size(filepath, format=True):
    try:
        st = os.stat(filepath)
        if st and st.st_size > 0:
            if format:
                return format_size(st.st_size)
            else:
                return st.st_size
        return "-"
    except OSError as e:
        return "-"


def get_relative_path(path, parent):
    path1 = os.path.abspath(path)
    parent1 = os.path.abspath(parent)
    # abpath之后最后没有/
    # 比如
    # ./                 -> /users/xxx
    # ./test/hello.html  -> /users/xxx/test/hello.html
    # 相减的结果是       -> /test/hello.html
    # 需要除去第一个/
    relative_path = path1[len(parent1):]
    return relative_path.replace("\\", "/")[1:]

class FileItem(Storage):

    def __init__(self, path, parent=None):
        # Fix ending
        # if os.path.isdir(path) and not path.endswith("/"):
        #     path = path + "/"
        self.path = path
        self.name = os.path.basename(path)
        self.size = get_file_size(path)

        if parent != None:
            self.name = get_relative_path(path, parent)

        # 处理Windows盘符
        if path.endswith(":"):
            self.name = path

        self.name = xutils.unquote(self.name)
        if os.path.isfile(path):
            self.type = "file"
            self.name = decode_name(self.name)
        else:
            self.type = "dir"
            self.path += "/"

    # sort方法重写__lt__即可
    def __lt__(self, other):
        if self.type == "dir" and other.type == "file":
            return True
        if self.type == "file" and other.type == "dir":
            return False
        return self.name < other.name

    # 兼容Python2
    def __cmp__(self, other):
        if self.type == other.type:
            return cmp(self.name, other.name)
        if self.type == "dir":
            return -1
        return 1

def splitpath(path):
    path   = path.replace("\\", "/")
    pathes = path.split("/")
    if path[0] == "/":
        last = ""
    else:
        last = None
    pathlist = []
    for vpath in pathes:
        if vpath == "":
            continue
        if last is not None:
            vpath = last + "/" + vpath
        pathlist.append(FileItem(vpath))
        last = vpath
    return pathlist

def decode_name(name):
    dirname = os.path.dirname(name)
    basename = os.path.basename(name)
    namepart, ext = os.path.splitext(basename)
    if ext in (".xenc", ".x0"):
        basename = base64.urlsafe_b64decode(namepart.encode("utf-8")).decode("utf-8")
        return os.path.join(dirname, basename)
    return name

def encode_name(name):
    namepart, ext = os.path.splitext(name)
    if ext in (".xenc", ".x0"):
        return name
    return base64.urlsafe_b64encode(name.encode("utf-8")).decode("utf-8") + ".x0"
