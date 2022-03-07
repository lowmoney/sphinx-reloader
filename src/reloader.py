from __future__ import print_function
import os, time, shutil, datetime
from stat import S_ISDIR, S_ISREG
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils
import src.config as config


class File:
    def __init__(self, lastModified:int, path:str) -> None:
        self.last_modified = lastModified
        self.path = path

    def _is_valid_operand(self, other):
        return hasattr(other, "last_modified")

    def __ne__(self, other) -> bool:
        if self._is_valid_operand(other):
            return self.last_modified != other.last_modified
        else:
            return NotImplemented


class DirectorySnapshot:
    def __init__(self, path) -> None:
        self.snapshot = {}
        self.path = path
        self.walk(self.path)
        self.modified_path = None
    
    def walk(self, path):
        for f in os.listdir(path):
            pathname = os.path.join(path,f)
            mode = os.stat(pathname).st_mode

            if S_ISDIR(mode):
                self.walk(pathname)
            elif S_ISREG(mode):
                file = File(os.stat(pathname).st_mtime, pathname)
                self.snapshot[os.stat(pathname).st_ino] = file

    def _is_valid_operand(self, other):
        if hasattr(other, "snapshot"):
            if len(other.snapshot) > 0:
                return True
        
        return False

    def __ne__(self, other) -> bool:
        if self._is_valid_operand(other):
            for i in self.snapshot.keys():
                if other.snapshot[i] != self.snapshot[i]:
                    self.modified_path = self.snapshot[i].path
                    return True
            return False
        else:
            return NotImplemented

class Watcher:
    def __init__(self, source_path, build_path, interval = 1) -> None:
        self.source_path = source_path
        self.build_path = build_path
        self.interval = interval

    def run(self):
        print("\nstarting watcher")
        global lastBuild
        try:
            while True:
                app = None
                snapshot_one = DirectorySnapshot(self.source_path)
                time.sleep(self.interval)
                snapshot_two = DirectorySnapshot(self.source_path)

                if snapshot_one != snapshot_two:
                    print("\033[38;2;188;212;230;1mchange detected at source directory \u279D rebuilding project ({})\033[0m".format(datetime.datetime.now().time().strftime("%H:%m:%S")))
                    print(" \033[38;2;250;82;82;1m\u21B3 {}\n\033[0m".format(snapshot_one.modified_path))
                    shutil.rmtree(self.build_path, ignore_errors=True)

                    with patch_docutils(self.source_path), docutils_namespace():
                        app = Sphinx(srcdir = self.source_path, confdir = self.source_path, doctreedir = self.build_path, outdir = self.build_path, buildername="html", status=None)
                        app.add_js_file(None, body="""const myInterval=setInterval(reloader,1000);function reloader(){fetch("/__reloader__").then((res)=>{res.ok?205===res.status&&window.location.reload():clearInterval(myInterval)}).catch(e=>{clearInterval(myInterval)})}""")
                        app.build()

                    if app:
                        if app.statuscode == 0:
                            config.lastBuild = time.time()
                            print("\033[38;2;55;178;77mbuild created, refreshing webpage\n\033[0m")

        except KeyboardInterrupt:
            raise KeyboardInterrupt