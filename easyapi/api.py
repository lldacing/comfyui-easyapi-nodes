import os
import json

import nodes
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

    @PromptServer.instance.routes.post("/easyapi/prompt")
    async def post_prompt(request):
        print("got prompt")
        json_data = await request.json()
        json_data = PromptServer.instance.trigger_on_prompt(json_data)
        prompt_id = json_data["prompt_id"]
        print("prompt_id={}".format(json_data["prompt_id"]))

        if "number" in json_data:
            number = float(json_data['number'])
        else:
            number = PromptServer.instance.number
            if "front" in json_data:
                if json_data['front']:
                    number = -number

            PromptServer.instance.number += 1

        if "prompt" in json_data:
            prompt = json_data["prompt"]
            valid = execution.validate_prompt(prompt)
            extra_data = {}
            if "extra_data" in json_data:
                extra_data = json_data["extra_data"]

            if "client_id" in json_data:
                extra_data["client_id"] = json_data["client_id"]
            if valid[0]:
                outputs_to_execute = valid[2]
                PromptServer.instance.prompt_queue.put((number, prompt_id, prompt, extra_data, outputs_to_execute))
                response = {"prompt_id": prompt_id, "number": number, "node_errors": valid[3]}
                return web.json_response(response)
            else:
                print("invalid prompt:", valid[1])
                return web.json_response({"error": valid[1], "node_errors": valid[3]}, status=400)
        else:
            return web.json_response({"error": "no prompt", "node_errors": []}, status=400)

    @PromptServer.instance.routes.post("/easyapi/interrupt")
    async def post_interrupt(request):
        json_data = await request.json()
        prompt_id = json_data["prompt_id"]
        current_queue = PromptServer.instance.prompt_queue.get_current_queue()
        queue_running = current_queue[0]
        if queue_running is not None and len(queue_running) > 0:
            if len(queue_running[0]) > 0 and queue_running[0][1] == prompt_id:
                nodes.interrupt_processing()

        delete_func = lambda a: a[1] == prompt_id
        PromptServer.instance.prompt_queue.delete_queue_item(delete_func)
        return web.Response(status=200)


def init():
    reset_history_size(isStart=True)
    register_routes()
