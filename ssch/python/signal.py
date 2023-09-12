import websockets
import asyncio
import json


async def listen():
    url = "ws://localhost:52125"
    print('prepare')
    async with websockets.connect(url) as ws:
        js = json.dumps(
            {
                "type": "ping",
                "stat": 1,
                "content": {
                    "header": "",
                    "body": []
                }
            }
        )
        print("send")
        await ws.send(js)
        msg = await ws.recv()
        print(msg)
        re = json.loads(msg)["content"]['body']['return']
        print(re)
        print(len(re))
        if msg == "pong":
            ws.close()

asyncio.get_event_loop().run_until_complete(listen())
