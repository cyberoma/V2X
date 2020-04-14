import socket
from messdaten import Report
import time
import sys

HEADERSIZE = 10

HOST = "192.168.178.65"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
# message = md.report()  # dict with report data


report = Report()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect((HOST, PORT))  # connects to server
        while True:
            # prepare report to send:
            x, y = report.create_report()['position']
            direction = report.create_report()['direction']
            speed = report.create_report()['speed']
            timestamp = report.create_report()['timestamp']

            message = f"P:({x},{y});D:{direction};S:{speed};T:{timestamp}"
            # send msg length and message
            message = f"{len(message):<{HEADERSIZE}}" + message

            s.send(message.encode())  # send report
            time.sleep(1)

            data_recv = s.recv(10)
            raw = data_recv.decode('utf-8')
            if raw == 'OK':
                print("response: ", data_recv.decode('utf-8'))
            elif data_recv.decode('utf-8') == 'stop_report':
                break
            else:
                continue

    except Exception as e:
        print(e)
        sys.exit()
