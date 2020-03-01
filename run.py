if __name__ == "__main__":
    from common.countdown_bot import CountdownBot
    from pathlib import Path
    import os

    bot = CountdownBot(
        Path(os.path.abspath(__file__)).parent
    )
    bot.init()
    bot.start()

    os.kill(os.getpid(), 1)
