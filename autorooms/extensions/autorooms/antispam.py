#   Copyright 2017-2020 Michael Hall
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import datetime, timedelta


class AutoRoomAntiSpam:
    """
    Because people are jackasses
    """

    def __init__(self):
        self.event_timestamps = []

    def _interval_check(self, interval: timedelta, threshold: int):
        return (
            len(
                [t for t in self.event_timestamps if (t + interval) > datetime.utcnow()]
            )
            >= threshold
        )

    @property
    def spammy(self):
        return (
            self._interval_check(timedelta(seconds=5), 3)
            or self._interval_check(timedelta(minutes=1), 5)
            or self._interval_check(timedelta(hours=1), 30)
        )

    def stamp(self):
        self.event_timestamps.append(datetime.utcnow())
        # This is to avoid people abusing the bot to get
        # it ratelimited. We don't care about anything older than
        # 1 hour, so we can discard those events
        self.event_timestamps = [
            t
            for t in self.event_timestamps
            if t + timedelta(hours=1) > datetime.utcnow()
        ]
