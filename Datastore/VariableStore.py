import os
import json
import cam_config


def set_variable(src, name, value):
    var_file = os.path.join(cam_config.variable_path, 'vars.json')
    data = {}

    try:
        with open(var_file, 'r') as f:
            data = json.loads(f.read())
    except IOError:
        print('no variables file')
    except ValueError:
        print('invalid data file')

    data.setdefault(src, {})
    data[src][name] = value

    if not os.path.exists(cam_config.variable_path):
        print("set_variable: creating path", cam_config.variable_path)
        os.makedirs(cam_config.variable_path)

    with open(var_file, 'w') as f:
        json.dump(data, f)
