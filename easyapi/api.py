import os
import json
from server import PromptServer
from aiohttp import web
import execution

extension_folder = os.path.dirname(os.path.realpath(__file__))


def reset_history_size(max_size=execution.MAXIMUM_HISTORY_SIZE, isStart=False):
    configDataFilePath = os.path.join(extension_folder, 'config')
    if not os.path.exists(configDataFilePath):
        os.mkdir(configDataFilePath)
        configFile = os.path.join(configDataFilePath, "easyapi.json")
        with open(configFile, 'w+', encoding="utf-8") as file:
            json.dump({"history_max_size": max_size}, file, indent=2)
    else:
        configFile = os.path.join(configDataFilePath, "easyapi.json")
        if not os.path.exists(configFile):
            with open(configFile, 'w+', encoding="utf-8") as file:
                json.dump({"history_max_size": max_size}, file, indent=2)
        else:
            with open(configFile, 'r+', encoding="UTF-8") as file:
                data = json.load(file)
                if not isStart:
                    data['history_max_size'] = max_size

            with open(configFile, 'w+', encoding="UTF-8") as file:
                json.dump(data, file, indent=2)


def register_routes():
    @PromptServer.instance.routes.post("/easyapi/history/size")
    async def set_history_size(request):
        json_data = await request.json()
        size = json_data["maxSize"]
        if size is not None:
            promptQueue = PromptServer.instance.prompt_queue
            with promptQueue.mutex:
                maxSize = int(size)
                execution.MAXIMUM_HISTORY_SIZE = maxSize
                history = promptQueue.history
                end = len(history) - maxSize
                i = 0
                for key in list(history.keys()):
                    if i >= end:
                        break
                    history.pop(key)
                    i = i + 1
                reset_history_size(maxSize)
            return web.Response(status=200)

        return web.Response(status=400)

    @PromptServer.instance.routes.get("/easyapi/history/maxSize")
    async def get_history_size(request):
        maxSize = execution.MAXIMUM_HISTORY_SIZE
        with open(os.path.join(extension_folder, 'config/easyapi.json'), 'r', encoding="UTF-8") as file:
            data = json.load(file)
            if data['history_max_size'] is not None:
                maxSize = data['history_max_size']

        return web.json_response({"maxSize": maxSize})


def init():
    reset_history_size(isStart=True)
    register_routes()

