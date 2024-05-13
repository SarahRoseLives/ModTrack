import configparser

# Read config from file
def load_config():
    config = configparser.ConfigParser()
    config.read("config.txt")
    return config

# Load configuration
config = load_config()

# Define our Config Definitions

# [ModTrack] Config
BOT_NAME = config.get(section='ModTrack', option='BOT_NAME')
BOT_DESCRIPTION = config.get(section='ModTrack', option='BOT_DESCRIPTION')
BOT_PREFIX = config.get(section='ModTrack', option='BOT_PREFIX')
LOG_CONSOLE_TO_DISCORD = config.get(section='ModTrack', option='LOG_CONSOLE_TO_DISCORD')


# [OpenTTDAdmin] Config
SERVER = config.get(section='OpenTTDAdmin', option='SERVER')
PORT = int(config.get(section='OpenTTDAdmin', option='PORT'))
PASSWORD = config.get(section='OpenTTDAdmin', option='PASSWORD')

# [Discord] Config
TOKEN = config.get(section='Discord', option='TOKEN')
BOT_ID_ON_DISCORD = int(config.get(section='Discord', option='BOT_ID_ON_DISCORD'))
DISCORD_ADMIN_ROLE_ID = int(config.get(section='Discord', option='DISCORD_ADMIN_ROLE_ID'))

# Channel declarations
CHANNEL_ADMIN_REQUEST = int(config.get(section='Discord', option='CHANNEL_ADMIN_REQUEST'))
CHANNEL_CHAT_MESSAGES = int(config.get(section='Discord', option='CHANNEL_CHAT_MESSAGES'))
CHANNEL_BOT_COMMANDS = int(config.get(section='Discord', option='CHANNEL_BOT_COMMANDS'))
CHANNEL_LOG_MESSAGES = int(config.get(section='Discord', option='CHANNEL_LOG_MESSAGES'))