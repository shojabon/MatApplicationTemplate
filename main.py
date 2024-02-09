import time

from MatApplication import MatApplication

if __name__ == '__main__':
    application = MatApplication()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break