import numpy as np
import math


def str_to_dict(string):
    # get str in form: "string:value"
    # e.g: str = "x:10,y:20,z:30"
    to_dict = {}
    # check if string contains more than one command
    if "," in string:
        tmp_list = string.split(':')
        print(tmp_list)
        to_dict[tmp_list[0]] = tmp_list[1].split(',')  # get a list as value
        # print(to_dict)
        return to_dict
    else:
        tmp_list = string.split(':')
        to_dict[tmp_list[0]] = tmp_list[1]
        # print(to_dict)
        return to_dict


tmp = str_to_dict("speed:10")
print(tmp)


def calc_pos(range_array, pos):
    # range_array = np.array([])
    # range_array_2 = np.array([])
    # range_array_3 = np.array([])
    # range_array_4 = np.array([])

    # range_array = np.array([range_m_mean, range_m_mean_2, range_m_mean_3]

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


range_array = np.array([0.4, 0.4, 0.2])
pos = np.array([[0, 0], [40, 20], [0, 80]])

p = calc_pos(range_array, pos)
print(p)
