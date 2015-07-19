import  sys
import  os
import  win32api
import  win32gui
import  struct
import  time
from    ctypes import *
from    fontTools import ttLib
from    win32con import *
import  logging
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib          import Binary
import datetime
import base64

SERVER_IP       = "0.0.0.0"
PORT            = 6969



FONT_SPECIFIER_NAME_ID      =   4
FONT_SPECIFIER_FAMILY_ID    =   1
FR_PRIVATE                  =   0x10

logger      = logging.getLogger('fuzzlog')
filelogger  = logging.FileHandler('log.txt')
formatter   = logging.Formatter('%(message)s')
filelogger.setFormatter(formatter)
logger.addHandler(filelogger)
logger.setLevel(logging.INFO)



class fuzzer_window():

    def __init__(self):

        win32gui.InitCommonControls()
        self.hinst = windll.kernel32.GetModuleHandleW(None)

    def CreateWindow(self):

        reg     =   self.RegisterClass()
        hwnd    =   self.BuildWindow(reg)
        return hwnd

    def RegisterClass(self):

        WndProc         =   {WM_DESTROY: self.OnDestroy}
        wc              =   win32gui.WNDCLASS()
        wc.hInstance    =   self.hinst
        wc.hbrBackground=   WHITE_BRUSH
        wc.hCursor      =   win32gui.LoadCursor(0, IDC_ARROW)
        wc.hIcon        =   win32gui.LoadIcon(0, IDI_APPLICATION)
        wc.lpszClassName=   "ttf fuzzer"
        wc.lpfnWndProc  =   WndProc
        reg             =   win32gui.RegisterClass(wc)
        return reg

    def BuildWindow(self, reg):

        hwnd    =   windll.user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_NOACTIVATE,
            reg,
            "ttf fuzzer",
            WS_POPUP,
            200,
            300,
            50,
            50,
            0,
            0,
            self.hinst,
            0)
        windll.user32.ShowWindow(hwnd, SW_SHOW)
        windll.user32.UpdateWindow(hwnd)
        return hwnd

    def OnDestroy(self, hwnd, message, wparam, lparam):

        win32gui.PostQuitMessage(0)
        return True


class font_fuzzer():

    def __init__(self, filepath):
        self.filepath = filepath

    def fuzz(self):

        logger.info('Start fuzzing: ' + self.filepath)

        self.ttffont    = ttLib.TTFont(self.filepath)
        self.fontname   = font_util.shortName(self.ttffont)[1]

        self.logfont    = win32gui.LOGFONT()
        self.htr        = windll.gdi32.AddFontResourceExA(self.filepath, FR_PRIVATE, None)

        self.hwin       = fuzzer_window()
        self.hwnd       = self.hwin.CreateWindow()
        self.hdc        = windll.user32.GetDC(self.hwnd)

        logger.info('Create font')
        self.logfont.lfHeight         = 20
        self.logfont.lfFaceName       = self.fontname
        self.logfont.lfWidth          = 0
        self.logfont.lfEscapement     = 0
        self.logfont.lfOrientation    = 0
        self.logfont.lfWeight         = FW_NORMAL
        self.logfont.lfItalic         = False

        self.logfont.lfUnderline      = False
        self.logfont.lfStrikeOut      = False
        self.logfont.lfCharSet        = DEFAULT_CHARSET
        self.logfont.lfOutPrecision   = OUT_DEFAULT_PRECIS
        self.logfont.lfClipPrecision  = CLIP_DEFAULT_PRECIS
        self.logfont.lfPitchAndFamily = DEFAULT_PITCH | FF_DONTCARE


        self.hfont          = win32gui.CreateFontIndirect(self.logfont)
        self.oldfont        = win32gui.SelectObject(self.hdc, self.hfont)


        ETO_GLYPH_INDEX     =   16
        text                =   "luffy"
        windll.gdi32.TextOutA(self.hdc, 5, 5, text, len(text))


        windll.gdi32.DeleteObject(win32gui.SelectObject(self.hdc, self.oldfont))
        windll.gdi32.GdiFlush()
        windll.gdi32.RemoveFontResourceExW(self.filepath, FR_PRIVATE, None)


        time.sleep(1)
        windll.user32.ReleaseDC(self.hwnd, self.hdc)
        windll.user32.DestroyWindow(self.hwnd)

        logger.info('End fuzzing: ' + self.filepath)




class font_util():
    @staticmethod
    def shortName(font):
        name = ""
        family = ""

        for record in font['name'].names:
            if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
                if '\000' in record.string:
                    name = unicode(record.string, 'utf-16-be').encode('utf-8')
                else:
                    name = record.string
            elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family:
                if '\000' in record.string:
                    family = unicode(record.string, 'utf-16-be').encode('utf-8')
                else:
                    family = record.string
            if name and family:
                break
        return name, family



class fuzzer_service():

    def ping(self):
        return "Hello World"

    def send_font(self, data):
        self.fontname = "font/" + str(int(time.time())) + ".ttf"
        fontfile = open(self.fontname, "wb")
        fontfile.write(base64.b64decode(data))
        fontfile.close()

        try:
            self.fuzz()
        except Exception:
            return "[-] fuzz failed"

    def fuzz(self):
        fuzzer = font_fuzzer(self.fontname)
        fuzzer.fuzz()
        return "[+] Fuzz successfully"




server = SimpleXMLRPCServer((SERVER_IP, PORT), logRequests = True, allow_none = True)
server.register_introspection_functions()
server.register_multicall_functions()
server.register_instance(fuzzer_service())

try:
    server.serve_forever()
except KeyboardInterrupt:
    print "Exiting"











