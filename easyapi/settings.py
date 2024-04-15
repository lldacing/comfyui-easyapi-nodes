import os
import json
import execution

extension_folder = os.path.dirname(os.path.realpath(__file__))
# configDataFilePath = os.path.join(extension_folder, 'config')

# if not os.path.exists(configDataFilePath):
#     os.mkdir(configDataFilePath)


def reset_history_size(max_size=execution.MAXIMUM_HISTORY_SIZE, isStart=False):
    if not isStart:
        set_settings("history_max_size", max_size)
    # if not os.path.exists(configDataFilePath):
    #     os.mkdir(configDataFilePath)
    #     configFile = os.path.join(configDataFilePath, "easyapi.json")
    #     with open(configFile, 'w+', encoding="utf-8") as file:
    #         json.dump({"history_max_size": max_size}, file, indent=2)
    # else:
    #     configFile = os.path.join(configDataFilePath, "easyapi.json")
    #     if not os.path.exists(configFile):
    #         with open(configFile, 'w+', encoding="utf-8") as file:
    #             json.dump({"history_max_size": max_size}, file, indent=2)
    #     else:
    #         with open(configFile, 'r+', encoding="UTF-8") as file:
    #             data = json.load(file)
    #             if not isStart:
    #                 data['history_max_size'] = max_size
    #
    #         with open(configFile, 'w+', encoding="UTF-8") as file:
    #             json.dump(data, file, indent=2)


def get_settings(file="config/easyapi.json"):
    configFile = check_dir(file)
    setting = {}
    if not os.path.exists(configFile):
        with open(configFile, 'w+', encoding="utf-8") as file:
            json.dump({}, file, indent=2)
    else:
        with open(configFile, 'r+', encoding="utf-8") as file:
            setting = json.load(file)

    return setting


def set_settings(key, value, file="config/easyapi.json"):
    configFile = check_dir(file)
    setting_json = get_settings(file=file)
    setting_json[key] = value
    with open(configFile, 'w+', encoding="utf-8") as file:
        json.dump(setting_json, file, indent=2)


def check_dir(filePath):
    configDataFilePath = os.path.join(extension_folder, os.path.dirname(filePath))
    if not os.path.exists(configDataFilePath):
        os.mkdir(configDataFilePath)
    return os.path.join(configDataFilePath, os.path.basename(filePath))
