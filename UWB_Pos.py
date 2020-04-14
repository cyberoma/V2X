# Import File IO, pyPlot and pySerial
import sys
import time
import warnings
import platform
import numpy as np
import serial
import math


def connect2radio(port):
    # Configure and open serial object connecting to radio
    s = serial.Serial(port, 115200)
    print('Serial port ' + port + ' opened!')
    return s


def catgetconfig(srl, msgID, rspID):
    # Set REQUEST and CONFIRM type
    msgType = "0x0003"
    sync_pattern = np.array([int("0xa5a5", 0)], dtype=np.uint16).view(np.uint8)
    msg_length = (np.array([4], dtype=np.uint16).byteswap(True)).view(np.uint8)
    msg_id = (np.array([msgID], dtype=np.uint16).byteswap(True)).view(np.uint8)
    rsp_id = (np.array([rspID], dtype=np.uint32).byteswap(True)).view(np.uint8)
    msg_type = (np.array([int(msgType, 0)], dtype=np.uint16).byteswap(True)).view(np.uint8)
    srl.write(bytes(list(np.concatenate((sync_pattern, msg_length, msg_type, msg_id, rsp_id), axis=None))))
    # Catch the XXX_GET_CONFIG_CONFIRM response with 4 byte serial prefix
    confirmType = "0x0103"
    confirmMsgLength = 12
    Ktry = 0
    while srl.inWaiting() < confirmMsgLength and Ktry < 1000:
        Ktry = Ktry + 1
        time.sleep(0.0001)
    if Ktry >= 1000:
        sys.exit("Timed out waiting for response from radio!")
    msg = list(srl.read(srl.inWaiting()))
    confirm = None
    while not confirm:
        length_msg = int((np.array([msg[2], msg[3]], dtype=np.uint8).view(np.uint16)).byteswap(True))
        typus = hex(int(((np.array([msg[4], msg[5]], dtype=np.uint8)).view(np.uint16)).byteswap(True)))
        identifier = int((np.array([msg[6], msg[7]], dtype=np.uint8).view(np.uint16)).byteswap(True))
        msgDict = {"status": int(np.array([msg[83], msg[82], msg[81], msg[80]], dtype=np.uint8).view(np.uint32))}
        if typus == confirmType and identifier == msgID:
            if typus == confirmType:
                confirm = True
                if msgDict["status"] != 0:  # status = 0 -> success
                    warnings.warn("Error code -> debug me!")
                # Fill dictionary
                msgDict["nodeID"] = int(np.array([msg[11], msg[10], msg[9], msg[8]], dtype=np.uint8).view(np.uint32))
                msgDict["mode"] = int(np.array([msg[12]], dtype=np.uint8))
                msgDict["antmode"] = np.uint8(int(msg[13]))
                msgDict["codeCh"] = int(np.array([msg[14]], dtype=np.uint8))
                msgDict["transgain"] = int(np.array([msg[15]], dtype=np.int8))
                msgDict["pwrupmode"] = int(np.array([msg[16]], dtype=np.uint8))
                msgDict["prm"] = int(np.array([msg[20], msg[19], msg[18], msg[17]], dtype=np.uint8))  # Range in mm
                msgDict["timestamp"] = int(
                    np.array([msg[79], msg[78], msg[77], msg[76]], dtype=np.uint8).view(np.uint32))
            else:
                # Message is not CONFIRM type -> next message
                msg = msg[length_msg:]
    return msgDict


def catgetscan(srl):
    fullScanType = "0x0201"
    scn_data = 0
    timeout = 500
    while timeout > 0:
        while srl.inWaiting() > 0:
            # Read header - security loop (otherwise buffer problems)
            confirm = None
            while not confirm:
                # Read length of message
                msg = list(srl.read(4))
                sync_header = int(((np.array([msg[0], msg[1]], dtype=np.uint8)).view(np.uint16)).byteswap(True))
                length_msg = int(np.array([msg[3], msg[2]], dtype=np.uint8).view(np.uint16))
                if sync_header == int("0xa5a5", 0):
                    confirm = True
            # Read whole message and define type
            msg = list(srl.read(length_msg))
            typus = hex(int(((np.array([msg[0], msg[1]], dtype=np.uint8)).view(np.uint16)).byteswap(True)))
            # Check if scan info
            if typus == fullScanType:  # Yes: filter and plot scan data
                # Number of messages in this info
                n = int(((np.array([msg[50], msg[51]], dtype=np.uint8)).view(np.uint16)).byteswap(True))
                idx = int(((np.array([msg[48], msg[49]], dtype=np.uint8)).view(np.uint16)).byteswap(True))
                # Fill scan with existing messages
                scn_data = np.linspace(0, 0, 350 * n)
                for j in range(1, n + 1):
                    if idx != 0:
                        break
                    for i in range(1, 351):
                        scn_data[i - 1 + 350 * (j - 1)] = int(
                            ((np.array([msg[i * 4 + 48], msg[i * 4 + 49], msg[i * 4 + 50], msg[i * 4 + 51]],
                                       dtype=np.uint8)).view(np.int32)).byteswap(True))
                    # Do not read message in last run
                    if j != n:
                        # Read length of message
                        msg = list(srl.read(4))
                        sync_header = int(((np.array([msg[0], msg[1]], dtype=np.uint8)).view(np.uint16)).byteswap(True))
                        length_msg = int(((np.array([msg[2], msg[3]], dtype=np.uint8)).view(np.uint16)).byteswap(True))
                        # Discard scan if message without header
                        if sync_header != int("0xa5a5", 0):
                            break
                        msg = list(srl.read(length_msg))
                        typus = hex(int(((np.array([msg[0], msg[1]], dtype=np.uint8)).view(np.uint16)).byteswap(True)))
                        if typus != fullScanType:
                            print("Warning...")
                            break
                    else:
                        return scn_data
            else:  # No: delete message
                del msg
                print("No scan info -- Flushed!")
        timeout = timeout - 1
        time.sleep(0.01)
    return scn_data


def calc_pos(range_array, pos):
    # range_array = np.array([])
    # range_array_2 = np.array([])
    # range_array_3 = np.array([])
    # range_array_4 = np.array([])

    # range_array = np.array([range_m_mean, range_m_mean_2, range_m_mean_3]
    # Sample:
    # range_array = np.array([0.4, 0.4, 0.2])
    # pos = np.array([[0, 0], [40, 20], [0, 80]])

    # Least Squares , nur 3 Messgeräte
    d = range_array

    p1 = pos[0] * math.pow(10, -2)  # in m
    p2 = pos[1] * math.pow(10, -2)
    p3 = pos[2] * math.pow(10, -2)
    d1 = range_array[0]
    d2 = range_array[1]
    d3 = range_array[2]

    A = np.array([[1, -2 * p1[0], -2 * p1[1]], [1, -2 * p2[0], -2 * p2[1]], [1, -2 * p3[0], -2 * p3[1]]])
    b = np.array(
        [[d1 ** 2 - p1[0] ** 2 - p1[1] ** 2], [d2 ** 2 - p2[0] ** 2 - p2[1] ** 2], [d3 ** 2 - p3[0] ** 2 - p3[1] ** 2]])
    x = np.linalg.inv((np.transpose(A) @ A)) @ np.transpose(A) @ b  # dot product

    position = x[1:] * math.pow(10, 2)  # in cm
    return position


def ranging():
    # Connect to radio via serial port
    opSys = platform.system()
    if opSys == 'Windows':
        port = 'COM4'
    else:
        if opSys == 'Linux':
            port = '/dev/ttyUSB0'
        else:
            port = ''
    ser = connect2radio(port)

    range_array = np.array([])
    range_array_2 = np.array([])
    range_array_3 = np.array([])
    range_array_4 = np.array([])

    msgConfigDict = catgetconfig(ser, 0, 101)
    prm = msgConfigDict['prm']

    rangeInfo = float(prm) / 1000
