import socket
import sys
import subprocess

# Client for Raspberry Pi to listen all commands from Desktop and parse

HOST = "192.168.178.65"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
HEADERSIZE = 10

command_word = "cmd"  # word to start receiving command.
report_start_word = "start_report"  # word to start command.
report_stop_word = "stop_report"
process_id = 0


# ---- Command functions ---- #


def speed(val):
    print("speed function called!", int(val))


def cord(cord_list):
    print(f"cord-> x:{cord_list[0]} | y:{cord_list[1]}")
    pass


def direction(*args):
    pass


# --------------------------- #

# control commands for parsing. e.g.: message = ['speed': 10] -> set speed to 10
control_commands = {'cord': cord, 'speed': speed, 'direction': direction}  # command_name: function_name


# parse all data and make decisions
# get data in format: "command_name:value"
# message: raw data from socket
def parse_data(message):
    data_command = message.decode('utf-8')
    # parse data in dic
    data_dic = str_to_dict(data_command)
    if data_dic is False:
        return False
    # go through from received dict and check if command is matched with commands in our dict
    for command in list(data_dic.keys()):
        if command in control_commands:
            print(f"command found: {command}")
            control_commands[command](data_dic[command])  # call the specific function and give list as parameter
        else:
            print("command not found:", command)
            break


def str_to_dict(string):
    # get str in form: "string:value"
    # e.g: str = "speed:10" or "cord:10,20"
    to_dict = {}
    # string contains more than one command
    try:
        if "," in string:
            tmp_list = string.split(':')
            to_dict[tmp_list[0]] = tmp_list[1].split(',')  # get a list as value
            return to_dict
        # string contains only one command
        else:
            tmp_list = string.split(':')
            to_dict[tmp_list[0]] = tmp_list[1]
            return to_dict
    except Exception as e:
        print('Error in command', e)
        return False


def send_stop_respond(sock):
    message = "OK"
    message = f"{len(message):<{HEADERSIZE}}" + message
    sock.sendall(message.encode('utf-8'))


def main():
    # start listening:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((HOST, PORT))  # connects to server
            # start report script:
            # subprocess.Popen(['python3', 'client_send_report.py'], stdout=subprocess.PIPE)
            while True:
                header = s.recv(1024).decode('utf-8')
                # if command_word is in message -> start parsing
                if header == command_word:
                    print("start to parse commands:")
                    data = s.recv(1024)
                    parse_data(data)
                # if server sends stop command
                elif header == 'stop':
                    send_stop_respond(s)
                else:
                    print(header)
        except IOError as e:
            print("Reading error:".format(str(e)))
            sys.exit()

        except Exception as e:
            print(str(e))
            sys.exit()

        except KeyboardInterrupt:
            print('Keyboard interrupt')
            sys.exit()


if __name__ == '__main__':
    main()
