#!/usr/bin/env python
# Filename: parameters.py
"""
introduction: get the parameter from file

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 06 May, 2016
"""

import sys,os

saved_parafile_path ='para_default.ini'

def read_Parameters_file(parafile,parameter):
    try:
      inputfile = open(parafile, 'r')
    except IOError:
      raise IOError("Error: Open file failed, path: %s"%os.path.abspath(parafile))
    list_of_all_the_lines = inputfile.readlines()
    value = False
    for i in range(0,len(list_of_all_the_lines)):
        line = list_of_all_the_lines[i]
        if line[0:1] == '#' or len(line) < 2:
            continue
        lineStrs = line.split('=')
        lineStrleft = lineStrs[0].strip()     #remove ' ' from left and right
        if lineStrleft.upper() == parameter.upper():
            value = lineStrs[1].strip()
            break
    inputfile.close()
    return value

def get_string_parameters(parafile,name):
    if parafile =='':
        parafile = saved_parafile_path
    result = read_Parameters_file(parafile,name)
    if result is False:
        raise ValueError('get %s parameter failed'%name)
    else:
        return result

def get_string_parameters_None_if_absence(parafile,name):
    if parafile =='':
        parafile = saved_parafile_path
    result = read_Parameters_file(parafile,name)
    if result is False or len(result) < 1:
        return None
    else:
        return result

def get_bool_parameters_None_if_absence(parafile,name):
    if parafile =='':
        parafile = saved_parafile_path
    result = read_Parameters_file(parafile,name)
    if result is False or len(result) < 1:
        return None
    if result.upper()=='YES':
        return True
    else:
        return False

def get_bool_parameters(parafile,name):
    value = get_bool_parameters_None_if_absence(parafile,name)
    if value is None:
        raise ValueError(' %s not set in %s' % (name, parafile))
    return value

def get_digit_parameters_None_if_absence(parafile,name,datatype):
    if parafile =='':
        parafile = saved_parafile_path
    result = read_Parameters_file(parafile,name)
    if result is False or len(result) < 1:
        return None
    try:
        if datatype == 'int':
            digit_value = int(result)
        else:
            digit_value = float(result)
    except ValueError:
            raise ValueError('convert %s to digit failed , exit'%(name))

    return digit_value

def get_digit_parameters(parafile,name,datatype):
    value = get_digit_parameters_None_if_absence(parafile, name, datatype)
    if value is None:
        raise ValueError(' %s not set in %s'%(name, parafile))
    return value


def get_string_list_parameters_None_if_absence(parafile,name):
    str_value = get_string_parameters_None_if_absence(parafile, name)
    if str_value is None:
        return None
    attributes_list = []

    # if the list is in a txt file
    if str_value.endswith('.txt') and len(str_value.split(',')) == 1:
        with open(str_value, 'r') as f_obj:
            lines = f_obj.readlines()
            lines = [item.strip() for item in lines]
            return lines

    attributes_init = str_value.split(',')
    if len(attributes_init) < 1:
        return None
    else:
        for att_str in attributes_init:
            str_temp = att_str.strip()  # remove certain characters (such as whitespace) from the left and right parts of strings
            if len(str_temp) > 0:
                attributes_list.append(str_temp)
        if len(attributes_list) < 1:
            return None
        else:
            return attributes_list

def get_string_list_parameters(parafile,name):
    str_value = get_string_list_parameters_None_if_absence(parafile,name)
    if str_value is None or len(str_value) < 1:
        raise ValueError('No inference area is set in %s' % parafile)
    return str_value


def test_readparamters():
    parafile = 'setting.ini'

    return True

def main():
    test_readparamters()
    pass


if __name__=='__main__':
    main()
