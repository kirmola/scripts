import argparse
import asyncio
import json
import logging
from datetime import datetime
from os import environ, system, name
from string import ascii_lowercase
import aiohttp
import boto3


def saveAndPushToR2(jsonData, hostlanguage ,file_prefix:str):
    filename = f"{hostlanguage}_{file_prefix}_{datetime.now().strftime('%d_%m_%Y')}.json"
    s3 = boto3.resource('s3',
                        endpoint_url=f'https://{environ.get("ACCOUNT_ID")}.r2.cloudflarestorage.com',
                        aws_access_key_id=environ.get("ACCESS_KEY_ID"),
                        aws_secret_access_key=environ.get(
                            "SECRET_ACCESS_KEY")
                        )
    s3.Bucket(environ["BUCKET_NAME"]).put_object(
        Key=filename, Body=json.dumps(jsonData), ContentType = "application/json"
    )
    logging.info(f"{file_prefix} uploaded successfully to Cloudflare R2.")

async def fetchData(session, url):
    async with session.get(url) as response:
        data = await response.text()
        return data


async def main(hostlanguage):

    GOOGLE_URLS = [f"https://www.google.com/complete/search?q={letter}&client=chrome&hl={hostlanguage}" for letter in ascii_lowercase]

    async with aiohttp.ClientSession() as session:
        try:                        
            data = []
            for eachURL in GOOGLE_URLS:
                task = asyncio.ensure_future(fetchData(session, eachURL))
                data.append(task)
                logging.info(f"Request No. {GOOGLE_URLS.index(eachURL)} completed.")
            results = await asyncio.gather(*data)
            jsonData = {}
            for each in results:
                data = json.loads(each)
                jsonData.update({
                    data[0]:data[1]
                })
            logging.info("Now will upload to R2")
            saveAndPushToR2(jsonData, hostlanguage,"alphabets")
        except Exception as e:
            logging.error(f"Request for {eachURL} failed. Reason: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(
    filename="request.log",
    level=logging.INFO,
    format="%(asctime)s |%(levelname)s| %(message)s",
    filemode= "w"
)

    asyncio.run(main("en-IN"))