import os
import dotenv

dotenv.load_dotenv()
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
WEBUNTIS_SERVER = os.environ.get('WEBUNTIS_SERVER')
WEBUNTIS_USERNAME = os.environ.get('WEBUNTIS_USERNAME')
WEBUNTIS_PASSWORD = os.environ.get('WEBUNTIS_PASSWORD')
WEBUNTIS_SCHOOL = os.environ.get('WEBUNTIS_SCHOOL')