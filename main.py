# DON'T RUN THIS AS I HAVEN'T TESTED IT, RUN BOT.PY AND ADMIN.PY SEPERATELY IF YOU WANT TO PLAY WITH MY BAD INCOMPLETE CODE

import threading
import subprocess

def run_script(script_name):
    subprocess.run(["python", script_name])

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_script, args=("bot.py",))
    admin_thread = threading.Thread(target=run_script, args=("admin.py",))

    bot_thread.start()
    admin_thread.start()

    bot_thread.join()
    admin_thread.join()
