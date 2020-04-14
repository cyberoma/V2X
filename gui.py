from PyQt5 import QtWidgets
from UI.mainwindow import Ui_MainWindow
from UI.plotwindow import Ui_PlotWindow

from functools import partial
import sys
import random
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
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
    client_changed = pyqtSignal(object)
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
            client_list = server.get_clients()
            # get report from client
            message = server.get_msg()
            self.client_changed.emit(client_list)
            self.report_recv.emit(message)
        # thread closed
        self.finished.emit()

    def interrupt(self):
        server.broadcast('stop_report', to='all')
        self._actice = False
        self.wait()


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

        self.x_curr = 0
        self.y_curr = 0

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
            # check area to forward or discard data

            _, host_curr = self.message['addr']
            pos_dict = server.extract_pos()
            x_curr, y_curr = pos_dict[host_curr]

            if stat.check_area(x_curr, y_curr):
                # broadcast to other clients
                server.broadcast(self.report, host=self.message['addr'])
                print(pos_dict)
                # self.plot.update_plot(x_curr, y_curr)
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
        self.plot.plot_clients()

    # ---------------------------

    def thread_complete(self):
        print('Thread closed!')


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui_plot = Ui_PlotWindow()
        self.ui_plot.setupUi(self)

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_plot)
        self.clients_list = []

        self.ui_plot.graphWidget.setTitle("Localization")
        self.ui_plot.graphWidget.setLabel('left', 'Y')
        self.ui_plot.graphWidget.setLabel('bottom', 'X')
        self.ui_plot.graphWidget.showGrid(x=True, y=True)
        self.ui_plot.graphWidget.addLegend()

        self.y = [0] * 4  # list of zeros
        self.x = [0] * 4

        self.y2 = [0] * 4  # list of zeros
        self.x2 = [0] * 4

        self.data_line = []

    def plot(self, x, y, plotname, pen):
        return self.ui_plot.graphWidget.plot(x, y, name=plotname, pen=pen)

    def _filter_list(self, list_):
        # filter duplicates in list with tuples of two values
        d = {}
        for idx, client_tuple in enumerate(list_):
            _id, _addr = client_tuple
            d[_addr] = None
        return list(d)

    def plot_clients(self):
        self.clients_list = server.get_clients()
        self.clients_list = self._filter_list(self.clients_list)

        pen_color = ['w', 'r', 'b', 'g']
        # create plots of the clients
        for idx, data in enumerate(self.clients_list):
            self.data_line.append(self.plot(self.x, self.y, data, pen_color[idx]))

    def update_plot(self):
        self.x = self.x[1:]  # Remove the first element.
        self.x.append(random.randint(1, 10))  # Add a new value

        self.y = self.y[1:]  # Remove the first
        self.y.append(random.randint(1, 10))  # Add a new value.

        self.data_line[0].setData(self.x, self.y, symbol='o')  # Update the data.
        self.data_line[0].scatter.setData(x=[self.x[-1]], y=[self.y[-1]])  # set scatter only to last element

        self.x2 = self.x2[1:]  # Remove the first element.
        self.x2.append(random.randint(10, 20))  # Add a new value

        self.y2 = self.y2[1:]  # Remove the first
        self.y2.append(random.randint(10, 20))  # Add a new value.

        self.data_line[1].setData(self.x2, self.y2, symbol='o')  # Update the data.
        self.data_line[1].scatter.setData(x=[self.x2[-1]], y=[self.y2[-1]])  # set scatter only to last element

        # for d in self.data_line:
        #     self.x = self.x[1:]  # Remove the first element.
        #     self.x.append(random.randint(1, 10))  # Add a new value
        #
        #     self.y = self.y[1:]  # Remove the first
        #     self.y.append(random.randint(1, 10))  # Add a new value.
        #     d.setData(self.x, self.y, symbol='o', symbolSize='15')  # Update the data.
        #     # d.scatter.setData(x=[self.x[-1]], y=[self.y[-1]])  # set scatter only to last element

    def showEvent(self, event):
        self.timer.start()

    def closeEvent(self, event):
        self.timer.stop()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
