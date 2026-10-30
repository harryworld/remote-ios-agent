import asyncio

from remote_ios_agent import AsyncRemoteIOS
from remote_ios_agent.workflows.runner import interact_verify


async def main():
    async with await AsyncRemoteIOS().session() as device:
        await device.launch("com.example.RemoteIOSDemo")
        result = await interact_verify(device, 200, 400)
        print(result["before"].path, result["after"].path, result["comparison"])


asyncio.run(main())
