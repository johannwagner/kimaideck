import sys
import threading
import yaml
import logging
import time

from StreamDeck.DeviceManager import DeviceManager

from kimaideck.streamdeck import StreamDeckManager

logger = logging.getLogger(__name__)

def main() -> int:
    logging.basicConfig(level=logging.DEBUG)

    if not len(sys.argv) >= 2:
        logger.error("Missing configuration, please specify a configuration as first parameter")
        return 1

    config_file_name = sys.argv[1]

    config_file = open(config_file_name, 'r')
    config = yaml.safe_load(config_file)

    is_running = True
    while is_running:
        streamdecks = DeviceManager().enumerate()
        if len(streamdecks) == 0:
            logger.info("No streamdecks detected, waiting...")
            time.sleep(5)
            continue

        streamdeck = streamdecks[0]

        try:
            logger.info(f"Found streamdeck, initializing...")

            deck_manager = StreamDeckManager(streamdeck, config)
            deck_manager.run()

            for t in threading.enumerate():
                if t is threading.current_thread():
                    continue

                if t.is_alive():
                    t.join()
        except Exception as e:
            logger.error("Encountered an exception during rendering, resetting...")
            print(e)
        except KeyboardInterrupt as ki:
            is_running = False
        finally:
            try:
                streamdeck.reset()
            except:
                pass
            
            streamdeck.close()


    return 0

if __name__ == "__main__":
    sys.exit(main())