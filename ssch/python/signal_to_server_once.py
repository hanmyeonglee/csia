import websockets
import asyncio
import json


async def listen():
    url = "ws://localhost:52125"
    async with websockets.connect(url) as ws:
        js = json.dumps(
            {
                "type": "ping",
                "enc": "initialize"
            }
        )
        await ws.send(js)
        msg = await ws.recv()
        re = json.loads(msg)["content"]['body']['return']
        if re == "pong":
            await ws.close()

asyncio.get_event_loop().run_until_complete(listen())
