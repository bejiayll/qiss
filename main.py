import dotenv
import os

import client

dotenv.load_dotenv()

token = os.getenv("TOKEN")

client.bot.run(token)