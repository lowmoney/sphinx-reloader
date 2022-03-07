import sys, threading, argparse
from socketserver import TCPServer
from os.path import exists, join
from src.reloader import Watcher
from src.doc_server import ServerHandler

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

        if not exists(self.sourcePath):
            raise FileNotFoundError("\n\033[38;2;250;82;82;1msource directory could not be found\033[0m\nlooked at: {}\n".format(self.sourcePath))

        if not exists(join(self.sourcePath, 'conf.py')):
            raise FileNotFoundError("\n\033[38;2;250;82;82;1mconf.py file not found, not a valid Sphinx source directory\033[0m\nlooked at : {}\n".format(self.sourcePath))

        if not exists(join(self.sourcePath, 'index.rst')):
            raise FileNotFoundError("\n\033[38;2;250;82;82;1mindex.rst file not found, not a valid Sphinx source directory\033[0m\nlooked at : {}\n".format(self.sourcePath))

    def run(self):
        watcher = Watcher(self.sourcePath, self.buildPath)
        
        try:
            watcher.run()
        except KeyboardInterrupt:
            print("\nKilling reloader, this may take a second")
        except Exception as e:
            raise e


def main(argv = sys.argv[1:]):
    args = parser.parse_args(argv)

    if args.source == None and args.build == None:
        parser.error("the following arguments are required: source, build")
    
    PORT = 8000

    sphinxWebServer = TCPServer(("127.0.0.1", PORT), ServerHandler)
    webServerThread = None


    try:
        sphinxReloader = SphinxReloader(source_path=args.source, build_path=args.build, build_format=args.format)

        webServerThread = threading.Thread(target = sphinxWebServer.serve_forever)
        webServerThread.daemon = True
        webServerThread.start()

        print("\033[38;2;229;153;247mserving docs at: http://{}:{} \u2197\n\033[0m".format(sphinxWebServer.server_address[0], sphinxWebServer.server_address[1]))

        sphinxReloader.run()
    except (KeyboardInterrupt, FileNotFoundError) as e:
        print(e)
    except OSError as e:
        print("The server port may still be in use")
        print(e)
    finally:
        if webServerThread:
            if webServerThread.is_alive():
                print("\nkilling server, if this takes too long press CTRL+C again")
                sphinxWebServer.shutdown()
        
        sys.exit()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))