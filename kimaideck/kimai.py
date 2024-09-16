import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

class Kimai:

    def __init__(self, base_url, user, api_token):
        self.session = requests.Session()
        self.base_url = base_url
        self.session.headers.update({
            "X-AUTH-USER": user,
            "X-AUTH-TOKEN": api_token
        })


    def _url(self, path):
        return urllib.parse.urljoin(self.base_url, path)

    def get_active_timetracking(self):
        resp = self.session.get(self._url('timesheets/active'), timeout=10)
        active_list = resp.json()
        if len(active_list) > 0:
            return active_list[0]
        return None

    def get_last_activities(self):

        start_time = datetime.now(ZoneInfo("Europe/Berlin"))
        resp = self.session.get(self._url(f'timesheets?begin={str(start_time.year).zfill(4)}-{str(start_time.month).zfill(2)}-{str(start_time.day).zfill(2)}T00:00:00'), timeout=10)

        return resp.json()


    def start_timetracking(self, project_id, activity_id):
        data = {
            "project": project_id,
            "activity": activity_id,
            "begin": datetime.now().isoformat()
        }
        resp = self.session.post(self._url(f'timesheets'), data=data)
        return resp.json()

    def stop_timetracking(self, timesheet_id):
        resp = self.session.get(self._url(f'timesheets/{timesheet_id}/stop'), timeout=10)
        return resp.json()

    def get_customers(self):
        resp = self.session.get(self._url(f'customers'), timeout=10)
        return resp.json()

    def get_all_projects(self):
        resp = self.session.get(self._url(f'projects'), timeout=10)
        return resp.json()

    def get_projects(self, customer_id):
        resp = self.session.get(self._url(f'projects?customer={customer_id}'), timeout=10)
        return resp.json()

    def get_activities(self, project_id):
        resp = self.session.get(self._url(f'activities?project={project_id}'), timeout=10)
        return resp.json()
