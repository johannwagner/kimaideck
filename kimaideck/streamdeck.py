import logging
import threading
import time
import os
from zoneinfo import ZoneInfo
from datetime import datetime

import dateutil.relativedelta
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image, ImageDraw, ImageFont

from kimaideck.kimai import Kimai

logger = logging.getLogger(__name__)

class StreamDeckPage:

    def __init__(self, manager):
        self.manager = manager

    def _get_asset_path(self, rel_path):
        script_dir = os.path.dirname(__file__) 
        abs_file_path = os.path.join(script_dir, rel_path)
        return abs_file_path

    def _get_wrapped_text(self, text: str, font: ImageFont.ImageFont,
                          line_length: int):
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return '\n'.join(lines)

    def _render_simple_text(self, deck, index, text):
        image = PILHelper.create_image(deck)

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self._get_asset_path('./assets/Roboto-Regular.ttf'), 14)
        text = self._get_wrapped_text(text, font, line_length=76)
        draw.text((image.width / 2, image.height / 2), text=text, font=font, anchor="mm", fill="white")

        key_image = PILHelper.to_native_format(deck, image)
        deck.set_key_image(index, key_image)

    def _render_simple_asset(self, deck, index, asset_path):
        icon = Image.open(self._get_asset_path(asset_path))
        image = PILHelper.create_scaled_image(deck, icon, margins=[4, 4, 4, 4])
        key_image = PILHelper.to_native_format(deck, image)
        deck.set_key_image(index, key_image)

    def render(self, deck):
        pass

    def on_key_press(self, deck, key_index, press_time):
        pass


class PaginationStreamDeckPage(StreamDeckPage):

    def __init__(self, manager, elements):
        super().__init__(manager)
        self.index = 0
        self.elements = elements

    def get_element_shard(self, deck, index):
        max_elements = (deck.KEY_ROWS * deck.KEY_COLS) - 1
        return self.elements[(index * max_elements):(index * max_elements) + max_elements]

    def render_index(self, deck, index, element):
        pass

    def on_element_press(self, element):
        pass

    def render(self, deck):
        elements = self.get_element_shard(deck, self.index)

        max_elements = deck.KEY_ROWS * deck.KEY_COLS

        for index in range(max_elements - 1):
            if len(elements) > index:
                element = elements[index]
                self.render_index(deck, index, element)
            else:
                deck.set_key_image(index, None)

        self._render_simple_asset(deck, max_elements - 1, './assets/next_plan.bmp')

    def on_key_press(self, deck, key_index, press_time):
        action_key = (deck.KEY_ROWS * deck.KEY_COLS) - 1

        if key_index == action_key and press_time < 2000:
            element_shard = self.get_element_shard(deck, self.index + 1)
            if len(element_shard) == 0:
                self.index = 0
                logger.debug("Resetting index, index=0")
            else:
                self.index += 1
                logger.debug(f"Adding to index, index={self.index}")

            return {
                "action": "render"
            }

        elif key_index == action_key and press_time >= 2000:
            logger.debug(f"Jumping back to DashStreamDeckPage...")
            return {
                "action": "switch_page",
                "page": DashStreamDeckPage(self.manager)
            }
        else:
            logger.debug(f"Element {key_index} pressed")
            element_shard = self.get_element_shard(deck, self.index)
            element = element_shard[key_index]
            return self.on_element_press(element)


class CustomerStreamDeckPage(PaginationStreamDeckPage):

    def __init__(self, manager):
        all_customers = manager.kimai.get_customers()
        projects = manager.kimai.get_all_projects()

        customers_with_active_projects = set([p['parentTitle'] for p in projects])
        customers = [c for c in all_customers if c['name'] in customers_with_active_projects]

        super().__init__(manager, customers)

    def render_index(self, deck, index, customer):
        self._render_simple_text(deck, index, customer['name'])

    def on_element_press(self, customer):
        return {
            "action": "switch_page",
            "page": ProjectStreamDeckPage(self.manager, customer)
        }


class ProjectStreamDeckPage(PaginationStreamDeckPage):

    def __init__(self, manager, customer):
        projects = manager.kimai.get_projects(customer['id'])
        super().__init__(manager, projects)

    def render_index(self, deck, index, project):
        self._render_simple_text(deck, index, project['name'])

    def on_element_press(self, project):
        return {
            "action": "switch_page",
            "page": ActivityStreamDeckPage(self.manager, project)
        }


class ActivityStreamDeckPage(PaginationStreamDeckPage):

    def __init__(self, manager, project):
        self.project = project
        activities = manager.kimai.get_activities(project['id'])
        super().__init__(manager, activities)

    def render_index(self, deck, index, activity):
        self._render_simple_text(deck, index, activity['name'])

    def on_element_press(self, activity):
        self.manager.kimai.start_timetracking(self.project['id'], activity['id'])

        return {
            "action": "switch_page",
            "page": DashStreamDeckPage(self.manager),
        }


class DashStreamDeckPage(StreamDeckPage):

    def __init__(self, manager):
        super().__init__(manager)

    def render(self, deck):

        logger.debug("Fetching active time tracking actions...")
        active_tracking = self.manager.kimai.get_active_timetracking()

        if active_tracking:
            logger.debug("Time tracking is active, showing information")

            dt1 = datetime.fromisoformat(active_tracking['begin'])
            dt2 = datetime.now(ZoneInfo("Europe/Berlin"))
            rd = dateutil.relativedelta.relativedelta(dt2, dt1)

            text = f"{str(rd.hours).zfill(2)}:{str(rd.minutes).zfill(2)}"

            elements = deck.KEY_ROWS * deck.KEY_COLS

            for element in range(elements - 5):
                deck.set_key_image(element, None)

            self._render_simple_text(deck, elements - 5, text)
            self._render_simple_text(deck, elements - 4, active_tracking['activity']['name'])
            self._render_simple_text(deck, elements - 3, active_tracking['project']['customer']['name'])
            self._render_simple_text(deck, elements - 2, active_tracking['project']['name'])
            self._render_simple_asset(deck, elements - 1, './assets/stop_circle.bmp')
        else:
            logger.debug("Time tracking is not active, showing start button")

            elements = deck.KEY_ROWS * deck.KEY_COLS
            for element in range(elements - 1):
                deck.set_key_image(element, None)

            self._render_simple_asset(deck, elements - 1, './assets/play_circle.bmp')


    def on_key_press(self, deck, key_index, press_time):
        action_key = (deck.KEY_ROWS * deck.KEY_COLS) - 1

        if not key_index == action_key:
            return

        active_tracking = self.manager.kimai.get_active_timetracking()

        if active_tracking:
            self.manager.kimai.stop_timetracking(active_tracking['id'])

            return {
                "action": "render"
            }

        else:
            return {
                "action": "switch_page",
                "page": CustomerStreamDeckPage(self.manager)
            }


class StreamDeckManager:

    def __init__(self, deck, config):
        self.current_deck_page = DashStreamDeckPage(self)
        self.deck = deck

        self.key_down_timer = dict()

        cfg_kimai = config['kimai']['api']
        self.kimai = Kimai(cfg_kimai['url'], cfg_kimai['user'], cfg_kimai['token'])

        self.deck.open()
        self.deck.reset()

        self.read_thread = threading.Thread(target=self.thread_render)
        self.read_thread.daemon = True

        self.last_render = None

    def thread_render(self):
        while self.deck.run_read_thread:
            if not self.last_render or time.time() - self.last_render > 30:
                self.current_deck_page.render(self.deck)
                self.last_render = time.time()
            time.sleep(1)

    def run(self):
        def key_change_callback(deck, key, state):
            if state == True:
                self.key_down_timer[key] = time.time()
            elif state == False:  # Technically, button is up again

                press_time = int((time.time() - self.key_down_timer[key]) * 1000)
                res = self.current_deck_page.on_key_press(self.deck, int(key), press_time)

                if res:
                    logger.debug(f"Key {key} does execute action {res['action']}")
                    if res['action'] == "render":
                        self.current_deck_page.render(deck)
                    if res['action'] == "switch_page":
                        current_deck_page = res['page']
                        self.current_deck_page = current_deck_page
                        logger.debug(f"Switching to {current_deck_page.__class__}")

                        self.current_deck_page.render(deck)
                else:
                    logger.debug(f"Key {key} did not execute any action")

        self.deck.set_key_callback(key_change_callback)
        self.read_thread.start()

