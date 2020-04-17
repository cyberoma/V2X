from PyQt5 import QtWidgets
from UI.mainwindow import Ui_MainWindow
from UI.plotwindow import Ui_PlotWindow

import sys

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from tcp_server import TCPServer, Statistic

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
                # return empty list
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
        # send stop msg to all clients
        server.broadcast('stop', to='all')


class RunReportThread(QThread):
    client_changed = pyqtSignal(object)
    report_recv = pyqtSignal(object)
    finished = pyqtSignal()

    # thread for report
    def __init__(self):
        super(RunReportThread, self).__init__()
        self._actice = True

    def run(self):
        while self._actice:
            server.run_server()
            self.msleep(10)  # wait 10 ms
            # get clients_dict list -> necessary because host_list.remove function will called if closed
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


# Main Gui
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # initialize gui from QT Designer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.host_list = []
        self.report_active = True
        self.message = {}
        self.report = ''
        # command to start receiving reports
        self.cmd = 'start_report'
        # gui events
        self.ui.startButton.clicked.connect(self.on_start_button_click)
        self.ui.stopButton.clicked.connect(self.on_stop_button_click)
        self.ui.send_cmd_btn.clicked.connect(self.send_cmd)

        self.ui.connect_report_btn.clicked.connect(self.connect_report)
        self.ui.start_report_btn.clicked.connect(self.start_report)
        self.ui.stop_report_btn.clicked.connect(self.stop_report)
        self.ui.plot_btn.clicked.connect(self.plot_report)

        self.ui.stop_report_btn.setEnabled(False)
        self.ui.start_report_btn.setEnabled(False)
        # plot window
        self.plot = PlotWindow(self)

        self.x_curr = 0
        self.y_curr = 0

        self.pos_dict = {}

    # ------ Client Tab ---------

    def on_start_button_click(self):
        self.s = RunServerThread()
        print("clicked")
        self.s.client_changed.connect(self.print_clients)
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.s.finished.connect(self.thread_complete)
        self.s._actice = True
        self.ui.connect_report_btn.setEnabled(False)
        # starts the server thread
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
            # add to gui list
            self.ui.ipList.addItem(f"{client_id}: {client_host}")
        if to_remove:
            client_id, _ = to_remove[0]
            # delete from gui list
            self.ui.ipList.takeItem(self.ui.ipList.row(self.ui.ipList.findItems(str(client_id), Qt.MatchContains)[0]))

        self.host_list = client_list[:]

    # ---------------------------

    # ------ Command Tab ---------

    def send_cmd(self):
        # get selected host from list
        selected_item = self.ui.ipList.currentItem()

        cmd = self.ui.cmd_line.text()
        if selected_item and cmd:
            # prepare command to send
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
            # get host name from report
            _, host_curr = self.message['addr']
            # extract position from report
            x_curr, y_curr = server.extract_pos()
            # create dict for hostname and pos
            self.pos_dict[host_curr] = (x_curr, y_curr)
            # update plot
            self.plot.update_plot(self.pos_dict)
            # delete last hostname from dict to speed up the plot
            del self.pos_dict[host_curr]
            # check area to forward or discard data
            if stat.check_area(x_curr, y_curr):
                # broadcast to other clients
                server.broadcast(self.report, host=self.message['addr'])

            else:
                print('blocked!', (x_curr, y_curr))

    def connect_report(self):
        # create instance of Report thread
        self.r = RunReportThread()

        self.ui.connect_report_btn.setEnabled(False)

        self.ui.start_report_btn.setEnabled(True)
        self.ui.reportList.addItem('Connected to clients..')
        self.ui.reportList.addItem('Report created!')

    def start_report(self):
        # set while statement true to loop
        self.r._actice = True
        # gui events
        self.r.report_recv.connect(self.print_report)
        self.r.finished.connect(self.thread_complete)
        self.ui.start_report_btn.setEnabled(False)
        self.ui.stop_report_btn.setEnabled(True)
        # start report thread
        self.r.start()

    def stop_report(self):
        self.r.interrupt()
        self.ui.start_report_btn.setEnabled(True)
        self.ui.stop_report_btn.setEnabled(False)
        # create statistic
        forward, discard = stat.get_statistic()
        self.ui.reportList.addItem(f"forward:{forward}, discard:{discard}")

    def plot_report(self):
        # show plot window and initialize
        self.plot.show()
        self.plot.plot_clients()

    # ---------------------------

    def thread_complete(self):
        print('Thread closed!')


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # initialize Qt designer window
        self.ui_plot = Ui_PlotWindow()
        self.ui_plot.setupUi(self)
        # create timer to update plot -> actually don't use
        # self.timer = QTimer()
        # self.timer.setInterval(500)
        # self.timer.timeout.connect(self.update_plot)
        self.clients_list = []

        self.ui_plot.graphWidget.setTitle("Localization")
        self.ui_plot.graphWidget.setLabel('left', 'Y')
        self.ui_plot.graphWidget.setLabel('bottom', 'X')
        self.ui_plot.graphWidget.showGrid(x=True, y=True)
        self.ui_plot.graphWidget.addLegend()

        # create a buffer for plotting to visualize direction
        self.y = [0] * 4  # list of zeros
        self.x = [0] * 4
        # contain the host as key and last five pos as list -> see plot_clients() below
        self.x_update = {}
        self.y_update = {}

        self.data_line = {}
        self.count = 0

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
        # initialize the plot

        client_list = server.get_clients()
        self.clients_list = client_list
        # delete duplicates -> always two identical hosts, if report script is active
        self.clients_list = self._filter_list(self.clients_list)
        pen_color = ['w', 'r', 'b', 'g']

        # create plots of the clients
        for idx, data in enumerate(self.clients_list):
            # create obj of plot in data_line. We need this to update the plot
            self.data_line[data] = self.plot(self.x, self.y, data, pen_color[idx])
            # host as key and last five pos as list -> see in __init__ above
            self.x_update[data] = self.x
            self.y_update[data] = self.y

    def update_plot(self, pos_dict):
        if self.data_line:
            # get host name of pos_dict
            host = list(pos_dict.keys())[0]
            x_curr, y_curr = pos_dict[host]
            # create a new dict for update pos with hostname and list of last positions
            # in every call: delete the first pos and add a new one to the end
            self.x_update[host] = self.x_update[host][1:]  # Remove the first element.
            self.x_update[host].append(x_curr)  # Add a new value

            self.y_update[host] = self.y_update[host][1:]  # Remove the first
            self.y_update[host].append(y_curr)  # Add a new value.
            # update the data
            self.data_line[host].setData(self.x_update[host], self.y_update[host], symbol='o', symbolSize=15)
            # set scatter(symbol='o') only to last element
            self.data_line[host].scatter.setData(x=[self.x_update[host][-1]], y=[self.y_update[host][-1]])

    def showEvent(self, event):
        self.timer.start()

    def closeEvent(self, event):
        self.timer.stop()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
