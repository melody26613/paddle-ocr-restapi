import asyncio
import aiohttp

URL = "http://192.168.50.19:20000/ocr/dict"
FILE_PATH = "test.png"

MAX_THREAD = 18

async def send_request(session, idx):
    with open(FILE_PATH, "rb") as f:
        data = aiohttp.FormData()
        data.add_field("file", f, filename="test.png", content_type="image/png")

        async with session.post(URL, data=data) as resp:
            text = await resp.text()
            print(f"Response {idx}: {resp.status} {text[:100]}")  # print first 100 chars

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, i) for i in range(MAX_THREAD)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
