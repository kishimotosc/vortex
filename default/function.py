# -*- coding:utf-8 -*-

def function_set(data, parameter):
    flag    = True
    value   = None
    message = ''
    
    [column, value,] = parameter
    data[column] = value
    return flag, message, value

def function_get(data, parameter):
    flag    = True
    value   = None
    message = ''
    
    [column,] = parameter
    value = data[column]
    return flag, message, value

functions = {
    'set'   : function_set,
    'get'   : function_get,
}