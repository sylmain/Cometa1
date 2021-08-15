from PyQt5.QtCore import QThread, pyqtSignal, Qt
from functions_pkg.send_get_request import GetRequest
from equipment_pkg.equipment import test_result
URL_START = "https://fgis.gost.ru/fundmetrology/eapi"
class SearchThread(QThread):
    msg_signal = pyqtSignal(str)

    def __init__(self, url, parent=None):
        QThread.__init__(self, parent)
        self.url = url
        self.is_running = True

    def run(self):
        if self.is_running:
            self.sleep(1)
            print("thread running")
            print(self.url)
            resp = GetRequest.getRequest(self.url)
            print(resp)
            print("thread stopped")
            self.msg_signal.emit(resp)
        else:
            self.msg_signal.emit("stop")


def send_request(url):
    thread = SearchThread(f"{URL_START}/{url}")
    thread.msg_signal.connect(_on_getting_resp, Qt.QueuedConnection)

    thread.start()

# --------------------------------------ОБРАБОТКА ПОЛУЧЕННОГО ОТВЕТА ОТ СЕРВЕРА------------------------------------
def _on_getting_resp(resp):
    test_result(resp)
    # print(resp)
