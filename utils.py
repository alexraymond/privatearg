from agent_queue import *

def is_black_arg(arg_id):
    return arg_id % 2 == 0

def is_white_arg(arg_id):
    return arg_id % 2 != 0

def is_hypothesis_arg(arg_id):
    return arg_id % 4 < 2

def is_verified_arg(arg_id):
    return arg_id % 4 > 2

