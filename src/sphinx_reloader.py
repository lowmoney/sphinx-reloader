import time, sys, threading, argparse, shutil
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from os.path import exists, join
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils
from src.globals import building, lastReload, lastBuild

DESCRIPTION = '''A tool that monitors your Sphinx source directory. When changes are made, the build folder is rebuilt for you to see the changes made. It also creates a simple HTTP server in the background to easly browse the built docs'''
SOURCE = '''the absolute or relative directory where the doc files are being written to'''
BUILD = '''the absolute directory or relative where the doc files are rendered to'''
FORMAT = '''the format of the build files (HTML, Markdown, PDF, etc.). The default is html'''

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('source', help=SOURCE)
parser.add_argument('build', help=BUILD)
parser.add_argument('--format', '-f', type=str, help=FORMAT, default="html")


class SphinxReloader:
    def __init__(self, source_path:str = 'source', build_path:str = 'build', build_format:str = 'html') -> None:
        self.sourcePath = source_path

        self.buildPath = build_path
        self.buildFormat = build_format
        self.observer = Observer()

        if not exists(self.sourcePath):
            raise FileNotFoundError("\033[38;2;250;82;82;1msource directory could not be found\033[0m\nlooked at: {}\n".format(self.sourcePath))

        if not exists(join(self.sourcePath, 'conf.py')):
            raise FileNotFoundError("\033[38;2;250;82;82;1mconf.py file not found, not a valid Sphinx source directory\033[0m\nlooked at : {}\n".format(self.sourcePath))


    def run(self):
        eventHandler = Handler(self.sourcePath, self.buildPath, self.buildFormat)
        self.observer.schedule(eventHandler, self.sourcePath, recursive = True)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
        except Exception:
            self.shutdown()

    def shutdown(self):
        print("\nKilling reloader, this may take a second")
        self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self, source:str, build:str, buildFormat:str) -> None:
        self.source = source
        self.build = build
        self.buildFormat = buildFormat

        self._build()

    def _build(self):
        app = None
        shutil.rmtree(self.build)

        with patch_docutils(self.source), docutils_namespace():
            app = Sphinx(srcdir=self.source, confdir=self.source, doctreedir=self.build, outdir=self.build, buildername="html", status=None)
            app.add_js_file(None, body="""const myInterval=setInterval(reloader,1000);function reloader(){fetch("/__reloader__").then((res)=>{res.ok?205===res.status&&window.location.reload():clearInterval(myInterval)}).catch(e=>{clearInterval(myInterval)})}""")
            app.build()

        if app and app.statuscode==0:
            print("\033[38;2;55;178;77mbuild created, refreshing webpage\n\033[0m")

    def on_any_event(self, event):
        global lastBuild, building

        if event.is_directory:
            return

        if event.event_type == 'modified':

            if not building:
                building = True
                modifiedPath = event.src_path

                print("\033[38;2;188;212;230;1mchange detected at source directory \u279D rebuilding project ({})\033[0m".format(datetime.now().time().strftime("%H:%m:%S")))
                print(" \033[38;2;250;82;82;1m\u21B3 {}\n\033[0m".format(modifiedPath))

                self._build()

                building = False
                
                lastBuild = time.time()


class ServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="./build", **kwargs)

    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self) -> None:
        global lastReload, lastBuild

        if self.path == "/__reloader__":
            if lastReload < lastBuild:
                lastReload = time.time()
                self._set_headers(205)
            else:
                self._set_headers(200)

        else:
            return super().do_GET()

    def log_request(self, *args, **kwargs):
        return

def main(argv = sys.argv[1:]):
    args = parser.parse_args(argv)

    if args.source == None and args.build == None:
        parser.error("the following arguments are required: source, build")
    
    PORT = 8000

    sphinxWebServer = TCPServer(("127.0.0.1", PORT), ServerHandler)

    try:
        sphinxReloader = SphinxReloader(source_path=args.source, build_path=args.build, build_format=args.format)

        webServerThread = threading.Thread(target = sphinxWebServer.serve_forever)
        webServerThread.daemon = True
        webServerThread.start()

        print("\033[38;2;229;153;247mserving docs at: http://{}:{} \u2197\n\033[0m".format(sphinxWebServer.server_address[0], sphinxWebServer.server_address[1]))

        sphinxReloader.run()
    finally:
        sphinxWebServer.shutdown()
        print("\nkilling server, if this takes too long press CTRL+C again")
        sys.exit()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))