import os, time, shutil, datetime
from stat import S_ISDIR, S_ISREG
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils
from . import config

# class FileSnapshot:
#     '''An object that represents a snapshot in time of a File'''
#     def __init__(self, lastModified:int, path:str):
#         '''
#         Parameters
#         ------------
#         lastModified
#             A int value that represents the time the File object was created
#         path
#             A string value that represents the path of the file for the file object
#         '''
#         self.last_modified = lastModified
#         self.path = path

#     def _is_valid_operand(self, other):
#         return hasattr(other, "last_modified")

#     def __ne__(self, other) -> bool:
#         if self._is_valid_operand(other):
#             return self.last_modified != other.last_modified
#         else:
#             return NotImplemented


class DirectorySnapshot:
    '''An object that represents a snapshot in time of files in a directory'''
    def __init__(self, path:str) -> None:
        '''
        Parameters
        -----------
        path : str
            The directory path to take a snapshot of
        '''
        self._snapshot = {}
        self.path = path
        self.walk(self.path)
        self.modified_path = None
    
    def walk(self, path):
        '''
        Recursively walks the snapshot directory saving the times a file has been modified last and the path of the file

        Parameters
        -----------
        path : str
            The directory path to walk
        '''
        for f in os.listdir(path):
            pathname = os.path.join(path,f)
            mode = os.stat(pathname).st_mode

            if S_ISDIR(mode):
                self.walk(pathname)
            elif S_ISREG(mode):
                file = (os.stat(pathname).st_mtime, pathname)
                # file = FileSnapshot(os.stat(pathname).st_mtime, pathname)
                self._snapshot[os.stat(pathname).st_ino] = file

    def _is_valid_operand(self, other):
        if hasattr(other, "_snapshot"):
            if len(other._snapshot) > 0:
                return True
        
        return False

    def __ne__(self, other) -> bool:
        if self._is_valid_operand(other):
            for i in self._snapshot.keys():
                if other._snapshot[i][0] != self._snapshot[i][0]:
                    self.modified_path = self._snapshot[i][1]
                    return True
            return False
        else:
            return NotImplemented

class Watcher:
    def __init__(self, source_path, build_path, interval = .5) -> None:
        self.source_path = source_path
        self.build_path = build_path
        self.interval = interval

    def run(self):
        print("\nstarting watcher")
        global lastBuild
        try:
            while True:
                app = None

                snapshot_one:DirectorySnapshot = DirectorySnapshot(self.source_path)
                time.sleep(self.interval)
                snapshot_two:DirectorySnapshot = DirectorySnapshot(self.source_path)

                if snapshot_one != snapshot_two:
                    print(u"\u001b[38;5;201mchange detected at source directory \u279D rebuilding project ({})\u001b[0m".format(datetime.datetime.now().time().strftime("%H:%m:%S")))
                    print(u" \u001b[38;5;208m\u21B3 {}\n\u001b[0m".format(snapshot_one.modified_path))
                    shutil.rmtree(self.build_path, ignore_errors=True)

                    with patch_docutils(self.source_path), docutils_namespace():
                        app = Sphinx(srcdir = self.source_path, confdir = self.source_path, doctreedir = self.build_path, outdir = self.build_path, buildername="html", status=None)
                        app.add_js_file(None, body="""const myInterval=setInterval(reloader,1000);function reloader(){fetch("/__reloader__").then((res)=>{res.ok?205===res.status&&window.location.reload():clearInterval(myInterval)}).catch(e=>{clearInterval(myInterval)})}""")
                        app.build()

                    if app:
                        if app.statuscode == 0:
                            config.lastBuild = time.time()
                            print(u"\u001b[38;5;28mbuild created, refreshing webpage on next check\n\u001b[0m")

        except KeyboardInterrupt:
            raise KeyboardInterrupt