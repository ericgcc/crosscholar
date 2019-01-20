from events import Events
from time import sleep
from threading import Thread
from typing import Tuple


class Timer:
    """
    A timer that counts seconds, minutes and hours and raises a event when a unit time occur.

    Attributes
    ----------
    alive : bool
        Causes the timers counts if True or stop if False.

    elapsed_seconds : int
        Number of seconds elapsed since the timer begun.

    elapsed_minutes: int
        Number of minutes elapsed since the timer begun.

    elapsed_hours: int
        Number of hours elapsed since the timer begun.

    events: Events
        The event trigger. Contains the event names on_second, on_minute, on_hour.

    """

    def __init__(self):
        self.alive = False
        self.elapsed_seconds = 0
        self.elapsed_minutes = 0
        self.elapsed_hours = 0
        self.events = Events(('on_second', 'on_minute', 'on_hour'))

    def count_seconds(self) -> None:
        """Raises the on_second event, every second and counts the seconds elapsed."""

        while self.alive:
            sleep(1)  # sleeping the thread a second
            self.elapsed_seconds += 1  # incrementing elapsed seconds by 1
            self.events.on_second()  # raising the event

    def count_minutes(self) -> None:
        """Raises the on_minute event, every minute and counts the minutes elapsed."""

        while self.alive:
            sleep(60)  # sleeping the thread a minute
            self.elapsed_minutes += 1  # incrementing elapsed minutes by 1
            self.events.on_minute()  # raising the event

    def count_hours(self) -> None:
        """Raises the on_hour event, every hour and counts the hours elapsed."""

        while self.alive:
            sleep(3600)  # sleeping the thread a hour
            self.elapsed_hours += 1  # incrementing elapsed hours by 1
            self.events.on_hour()  # raising the event


def time_units(total_seconds: int) -> Tuple[int, int, int]:
    """Convert a given number of seconds to hours, minutes and seconds.

    Parameters
    ----------
    total_seconds : int
        Total number of seconds to convert.

    Returns
    -------
    int, int, int
        Three integers representing the resultant seconds, minutes and hour of the conversion

    """

    hours = total_seconds // 3600
    minutes = (total_seconds // 60) % 60
    seconds = total_seconds % 60

    return seconds, minutes, hours


class Requestmeter:
    """
       This class works like a speedometer for requests. The members declared will calculate the request ratios made
       by unit of time (seconds, minutes, hours).

        Attributes
        ----------
        total_requests: int
            Counter of the total requests made.

        requests_by_second: list
            A two elements list that stores the requests made in each second. It functions like a log that registers
            the accumulated requests made in the previous second and the differential requests made in the last second.

        requests_by_minute: list
            A two elements list that stores the requests made in each minute. It functions like a log that registers
            the accumulated requests made in the previous minute and the differential requests made in the last minute.

        requests_by_hour: list
            A two elements list that stores the requests made in each hour. It functions like a log that registers
            the accumulated requests made in the previous hour and the differential requests made in the last hour.

        events: Events
            The event trigger. Contains the event names second_speed_limit_exceeded, minute_speed_limit_exceeded,
            hour_speed_limit_exceeded. Raises the corresponding event each time the speed limit has been exceeded.

        timer: Timer
            The timer that will count each second, minute and hour elapsed.

       Class Attributes
       ----------------
       speed_limits : list
           Maximum number of requests that must be sent per second, minute and hour, correspondingly.

        Notes
        -----
        The difference between the terms "by" and "per" used in the members of this class is clearly explained in
        https://english.stackexchange.com/a/22693

       """

    speed_limits = ()  # maximum number of requests per second, minute and hour, correspondingly

    def __init__(self, limits):
        Requestmeter.speed_limits = limits if limits is not None else (2, 9, 540)
        self.total_requests = 0
        self.requests_by_second = [0, 0]
        self.requests_by_minute = [0, 0]
        self.requests_by_hour = [0, 0]

        self.events = Events(('s_speed_limit_exceeded', 'm_speed_limit_exceeded', 'h_speed_limit_exceeded'))

        self.timer = Timer()

        # Event subscriptions
        self.timer.events.on_second = self.requests_by_second_counter
        self.timer.events.on_minute = self.requests_by_minute_counter
        self.timer.events.on_hour = self.requests_by_hour_counter

    def start(self):
        self.timer.alive = True
        seconds_thread = Thread(target=self.timer.count_seconds)
        minutes_thread = Thread(target=self.timer.count_minutes)
        hours_thread = Thread(target=self.timer.count_hours)

        seconds_thread.setDaemon(True)
        minutes_thread.setDaemon(True)
        hours_thread.setDaemon(True)

        seconds_thread.start()
        minutes_thread.start()
        hours_thread.start()

    def finish(self):
        # finishing all 3 threads
        self.timer.alive = False

        # returning elapsed time
        return self.timer.elapsed_seconds, self.timer.elapsed_minutes, self.timer.elapsed_hours

    def count(self):
        self.total_requests += 1

    # region Speed calculators
    def requests_per_second(self):
        return sum(self.requests_by_second[:]) / self.timer.elapsed_seconds

    def requests_per_minute(self):
        return sum(self.requests_by_minute[:]) / self.timer.elapsed_minutes

    def requests_per_hour(self):
        return sum(self.requests_by_hour[:]) / self.timer.elapsed_hours
    # endregion Speed calculators

    # region Timer event handlers
    def requests_by_second_counter(self):
        self.requests_by_second[0] = sum(self.requests_by_second[:])
        self.requests_by_second[-1] = self.total_requests - self.requests_by_second[0]
        print("s:", self.requests_by_second[-1])

        if self.requests_by_second[-1] > Requestmeter.speed_limits[0]:
            self.events.s_speed_limit_exceeded((self.requests_by_second[-1] / self.speed_limits[0])-1)

    def requests_by_minute_counter(self):
        self.requests_by_minute[0] = sum(self.requests_by_minute[:])
        self.requests_by_minute[-1] = self.total_requests - self.requests_by_minute[0]
        print("m:", self.requests_by_minute[-1])

        if self.requests_by_minute[-1] > Requestmeter.speed_limits[1]:
            self.events.m_speed_limit_exceeded((self.requests_by_minute[-1] / self.speed_limits[1])-1)

    def requests_by_hour_counter(self):
        self.requests_by_hour[0] = sum(self.requests_by_hour[:])
        self.requests_by_hour[-1] = self.total_requests - self.requests_by_hour[0]
        print("h:", self.requests_by_hour[-1])

        if self.requests_by_hour[-1] > Requestmeter.speed_limits[2]:
            self.events.h_speed_limit_exceeded((self.requests_by_hour[-1] / self.speed_limits[2])-1)
    # endregion Timer event handlers

    def summary(self):
        p_seconds, p_minutes, p_hours = time_units(self.timer.elapsed_seconds)

        print("Total requests: ", self.total_requests)
        print(f"Elapsed time: {self.timer.elapsed_hours} h | {self.timer.elapsed_minutes} m | "
              f"{self.timer.elapsed_seconds} s")
        print(f"Pretty time: {self.timer.elapsed_seconds} s = {p_hours}:{p_minutes}:{p_seconds}")
        print(f"rps: {self.total_requests/self.timer.elapsed_seconds} requests/second")

        print("Requests by second")
        print(self.requests_by_second)

        print("Requests by minute")
        print(self.requests_by_minute)

        print("Requests by hour")
        print(self.requests_by_hour)
