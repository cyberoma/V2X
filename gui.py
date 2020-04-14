from PyQt5 import QtWidgets
from UI.mainwindow import Ui_MainWindow
from UI.plotwindow import Ui_PlotWindow

import sys
import random
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from testServer import TCPServer, Statistic
from ast import literal_eval as make_tuple

server = TCPServer()

# no send area
x_range = list(range(1, 9))
y_range = list(range(7, 15))
stat = Statistic(x_range, y_range)


class RunServerThread(QThread):
    # Signals for Gui
    client_changed = pyqtSignal(object)
    msg_received = pyqtSignal(object)
    finished = pyqtSignal()

    # run new Thread for server
    def __init__(self, parent=None):
        super().__init__(parent=None)
        self._actice = True

    def run(self):
        while self._actice:
            server.run_server()
            self.msleep(10)  # wait 10 ms
            # get clients_dict list
            result = server.get_clients()
            if result is None:
                # empty list
                result = []
            # get report from client
            report = server.get_msg()
            # emit signal to gui
            self.client_changed.emit(result)
            self.msg_received.emit(report)

        # thread finished
        self.finished.emit()

    def interrupt(self):
        self._actice = False
        server.broadcast('stop', to='all')


class RunReportThread(QThread):
    report_recv = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self):
        super(RunReportThread, self).__init__()
        self._actice = True

    def run(self):
        while self._actice:
            server.run_server()
            self.msleep(10)  # wait 10 ms
            # get clients_dict list -> necessary because host_list.remove function if closed
            server.get_clients()
            # get report from client
            message = server.get_msg()
            self.report_recv.emit(message)
        # thread closed
        self.finished.emit()

    def interrupt(self):
        server.broadcast('stop_report', to='all')
        self._actice = False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.host_list = []
        self.report_active = True
        self.message = {}
        self.report = ''
        # command to start receiving reports
        self.cmd = 'start_report'

        self.ui.startButton.clicked.connect(self.on_start_button_click)
        self.ui.stopButton.clicked.connect(self.on_stop_button_click)
        self.ui.send_cmd_btn.clicked.connect(self.send_cmd)

        self.ui.connect_report_btn.clicked.connect(self.connect_report)
        self.ui.start_report_btn.clicked.connect(self.start_report)
        self.ui.stop_report_btn.clicked.connect(self.stop_report)
        self.ui.plot_btn.clicked.connect(self.plot_report)

        self.ui.stop_report_btn.setEnabled(False)
        self.ui.start_report_btn.setEnabled(False)

        self.plot = PlotWindow(self)

    # ------ Client Tab ---------

    def on_start_button_click(self):
        self.s = RunServerThread()
        print("clicked")
        self.s.client_changed.connect(self.print_clients)
        # self.s.msg_received.connect(self.print_msg)
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.s.finished.connect(self.thread_complete)
        self.s._actice = True
        self.ui.connect_report_btn.setEnabled(False)

        self.s.start()

    def on_stop_button_click(self):
        self.s.interrupt()

        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.connect_report_btn.setEnabled(True)

    def print_clients(self, client_list):
        # if client is connected -> add to list
        new_host = list(set(client_list) - set(self.host_list))
        # if client connection lost -> delete from list
        to_remove = list(set(self.host_list) - set(client_list))

        if new_host:
            # tuple of host and id
            client_id, client_host = new_host[0]
            self.ui.ipList.addItem(f"{client_id}: {client_host}")
        if to_remove:
            client_id, _ = to_remove[0]
            self.ui.ipList.takeItem(self.ui.ipList.row(self.ui.ipList.findItems(str(client_id), Qt.MatchContains)[0]))

        self.host_list = client_list[:]

    # ---------------------------

    # ------ Command Tab ---------

    def send_cmd(self):
        selected_item = self.ui.ipList.currentItem()

        cmd = self.ui.cmd_line.text()
        if selected_item and cmd:
            selected_item_tuple = tuple(selected_item.text().replace(" ", "").split(':'))
            server.send_cmd_to_client(selected_item_tuple, cmd)
            self.ui.cmd_line.setText('')  # clear textbox

    # ---------------------------

    # ------ Report Tab ---------

    def print_report(self, m):
        if not m == self.message:
            self.message = m
            # prepare msg
            self.report = f"{self.message['addr']}> {self.message['data']}"
            # add to gui list and scroll down
            self.ui.reportList.addItem(self.report)
            self.ui.reportList.scrollToBottom()

            x_curr, y_curr = make_tuple(self.message['data'].split(';')[0].split(':')[1])
            if stat.check_area(x_curr, y_curr):
                # broadcast to other clients
                server.broadcast(self.report, host=self.message['addr'])
            else:
                print('blocked!', (x_curr, y_curr))

    def connect_report(self):
        self.r = RunReportThread()

        self.ui.connect_report_btn.setEnabled(False)

        self.ui.start_report_btn.setEnabled(True)
        self.ui.reportList.addItem('Connected to clients..')
        self.ui.reportList.addItem('Report created!')

    def start_report(self):

        self.r._actice = True
        self.r.report_recv.connect(self.print_report)
        self.r.finished.connect(self.thread_complete)
        self.ui.start_report_btn.setEnabled(False)
        self.ui.stop_report_btn.setEnabled(True)

        self.r.start()

    def stop_report(self):
        self.r.interrupt()
        self.ui.start_report_btn.setEnabled(True)
        self.ui.stop_report_btn.setEnabled(False)

        forward, discard = stat.get_statistic()
        self.ui.reportList.addItem(f"forward:{forward}, discard:{discard}")

    def plot_report(self):

        self.plot.show()

    # ---------------------------

    def thread_complete(self):
        print('Thread closed!')


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_plot = Ui_PlotWindow()
        self.ui_plot.setupUi(self)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)

        self.ui_plot.graphWidget.setTitle("Localization")
        self.ui_plot.graphWidget.setLabel('left', 'Y')
        self.ui_plot.graphWidget.setLabel('bottom', 'X')
        self.ui_plot.graphWidget.showGrid(x=True, y=True)

        self.x = [0] * 4
        self.y = [0] * 4  # list of zeros

        # self.plot([1, 2.5, 3, 3.5, 5, 4, 3, 2, 1], [30, 32, 34, 32, 33, 31, 29, 32, 35])
        self.data_line = self.plot(self.x, self.y)
        # self.data_line.scatter.setSymbol(symbol='o')
        # self.data_line.scatter.setSize(symbolSize='15')

    def plot(self, hour, temperature):
        return self.ui_plot.graphWidget.plot(hour, temperature, pen='r')

    def update_plot(self):
        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(random.randint(0, 10))  # Add a new random value.

        self.data_line.setData(self.x, self.y, symbol='o', symbolSize='15')  # Update the data.
        self.data_line.scatter.setData(x=[self.x[-1]], y=[self.y[-1]])

    def showEvent(self, event):
        self.timer.start()

    def closeEvent(self, event):
        self.timer.stop()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
