import urllib.parse
from datetime import datetime

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
        resp = self.session.get(self._url('timesheets/active/'))
        active_list = resp.json()
        if len(active_list) > 0:
            return active_list[0]
        return None


    def start_timetracking(self, project_id, activity_id):
        data = {
            "project": project_id,
            "activity": activity_id,
            "begin": datetime.now().isoformat()
        }
        resp = self.session.post(self._url(f'timesheets'), data=data)
        return resp.json()

    def stop_timetracking(self, timesheet_id):
        resp = self.session.get(self._url(f'timesheets/{timesheet_id}/stop'))
        return resp.json()

    def get_customers(self):
        resp = self.session.get(self._url(f'customers'))
        return resp.json()

    def get_all_projects(self):
        resp = self.session.get(self._url(f'projects'))
        return resp.json()

    def get_projects(self, customer_id):
        resp = self.session.get(self._url(f'projects?customer={customer_id}'))
        return resp.json()

    def get_activities(self, project_id):
        resp = self.session.get(self._url(f'activities?project={project_id}'))
        return resp.json()
