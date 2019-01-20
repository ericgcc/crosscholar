from library.timer import Timer
from library.timer import Requestmeter

total_requests = 0
rm = Requestmeter()


def requests_by_sec_counter():
    rm.request_by_second.append(total_requests - rm.request_by_second[-1])
    print(">>>:", total_requests)
    print("s:", rm.request_by_second[-1])


def requests_by_min_counter():
    rm.request_by_minute.append(total_requests - rm.request_by_minute[-1])
    print(">>>:", total_requests)
    print("m:", rm.request_by_minute[-1])


if __name__ == '__main__':
    timer = Timer()

    timer.events.on_second = requests_by_sec_counter
    timer.events.on_minute = requests_by_min_counter
    timer.start()

    while True:
        total_requests += 1

    seconds, minutes, hours = timer.finish()

    print(seconds, minutes, hours)
