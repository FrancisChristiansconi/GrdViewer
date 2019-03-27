import os.path
import traceback
import time


timedic = {}
indent = ' '
level = 0

def trace(message=''):
    global level
    stack = traceback.extract_stack()
    (filepath, _, procname, _) = stack[-2]
    filename = os.path.basename(filepath)
     
    if message == '':
        temp = (level + 1) * indent + filename + '>>' + procname

    else:
        key = filename + '>>' + procname
        if message == 'in':
            timedic[key] = time.time()
            temp = level * indent + filename + '>>' + procname + '>>' + message
            level += 1
        elif message == 'out':
            try:
                message = message + ':' + '{0:0.2f} sec.'.format(time.time() - timedic[key])
                level -= 1
                temp = level * indent + filename + '>>' + procname + '>>' + message   
            except KeyError:
                temp = 'utils.trace: No corresponding "in" tag in the function.'           
    print(temp)