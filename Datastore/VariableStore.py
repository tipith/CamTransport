import os
import json
import cam_config


def set_variable(src, name, value):
    file = 'vars.json'
    data = {}

    try:
        with open(os.path.join(file), 'r') as f:
            data = json.loads(f.read())
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}
        pass

    data.setdefault(src, {})
    data[src][name] = value

    if not os.path.exists(cam_config.variable_path):
        print("set_variable: creating path", cam_config.variable_path)
        os.makedirs(cam_config.variable_path)

    with open(os.path.join(cam_config.variable_path, file), 'w') as f:
        json.dump(data, f)
