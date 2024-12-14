# @title
from datetime import datetime, timedelta
from collections import deque


# Классы
class Driver:
    def __init__(self, driver_type, id):
        self.type = driver_type  # "A" или "B"
        self.id = id

        self.remaining_hours = 8 if driver_type == "A" else 21  # Рабочие часы для типа
        self.next_available_time = START_TIME  # Время, когда водитель будет доступен
        self.first_day = 1  # Первый рабочий день на неделе
        self.start_time = None
        self.route_count = 0
        self.current_bus = None


class Bus:
    def __init__(self, id):
        self.id = id
        self.schedule = []


class Shift:
    def __init__(self, driver, bus, start_time):
        self.driver = driver
        self.bus = bus
        self.start_time = start_time


# Параметры задачи
START_TIME = datetime.strptime("06:00", "%H:%M")
END_TIME = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)
PEAK_HOURS = [
    (datetime.strptime("07:00", "%H:%M"), datetime.strptime("09:00", "%H:%M")),
    (datetime.strptime("17:00", "%H:%M"), datetime.strptime("19:00", "%H:%M")),
]

NUM_BUSES = 10
buses = [Bus(i) for i in range(1, NUM_BUSES)]

ROUTE_DURATION = timedelta(minutes=60)
LUNCH_DURATION = timedelta(minutes=60)
BREAK_DURATION = timedelta(minutes=15)

PEAK_MAX_WAIT = 10  # Минуты
NON_PEAK_MAX_WAIT = 20  # Минуты
DAYS = [i for i in range(1, 8)]


# Функция потерь
def combined_loss(
    schedule,
    peak_intervals,
    non_peak_max_wait,
    peak_max_wait,
    drivers_count,
    driver_weight=1.0,
    waiting_weight=1.0,
) -> float:
    waiting_loss = 0
    for day_schedule in schedule:
        for i in range(len(day_schedule) - 1):
            current_time = day_schedule[i].start_time
            next_time = day_schedule[i + 1].start_time
            interval = (
                next_time - current_time
            ).total_seconds() / 60  # Интервал в минутах

            is_peak = any(start <= current_time < end for start, end in peak_intervals)
            max_wait = peak_max_wait if is_peak else non_peak_max_wait

            if interval > max_wait:
                waiting_loss += (interval - max_wait) ** 2

    driver_loss = drivers_count**2
    total_loss = waiting_weight * waiting_loss + driver_weight * driver_loss
    return total_loss


# Brute Force алгоритм
def brute_force_schedule() -> tuple[list[list[Shift]], float]:
    """
    Для сгенерированных комбинаций водителей по дням
    мы составляем расписание на каждый день с учетом того, сколько
    сегодня работает водителей каждого типа.
    Затем считаем функцию потерь и сравниваем оптимальность
    """
    best_loss = 10000000
    best_schedule = None

    def generate_schedule_per_day(drivers: list[Driver], buses: list[Bus]):
        nonlocal best_loss
        nonlocal best_schedule
        schedule = [[] for i in range(7)]
        for day in DAYS:
            """
            Каждые 5 минут мы проверяем состояние
            Если это не час пик, мы ждем, пока не наберется 15 минут
            Если через час начнется час пик, то мы начинаем отправлять автобусы с частотой 5 минут
            """
            current_time = datetime.strptime("06:00", "%H:%M")
            last_bus_time = datetime.strptime("03:00", "%H:%M")

            today_drivers_a, today_drivers_b = [], []
            for driver in drivers:
                # Обнуляем пройденные маршруты для водителя
                driver.route_count = 0
                if (
                    driver.type == "A"
                    and driver.first_day <= day < driver.first_day + 5
                ):
                    today_drivers_a.append(driver)
                if driver.type == "B" and (
                    driver.first_day == day or driver.first_day + 3 == day
                ):
                    today_drivers_b.append(driver)

            """
            Дек содержит свободных водителей, причем в начало
            мы добавляем водителей типа B, а в конец - типа А
            Так мы делаем, потому что нам лучше позже отправлять водителей типа B,
            Чтобы они покрыли больше времени.
            Водителей в пути мы же закидываем в очередь.(но дек)
            А водителей на обеде или перерыве мы закидываем в дек, где
            обед - это конец, а перерыв - начало
            """

            available_drivers = deque()
            busy_drivers = deque()
            break_drivers = deque()
            available_buses = buses.copy()

            # Перемешиваем водителей двух типов
            for i, driver in enumerate(today_drivers_a + today_drivers_b):
                if i % 2 == 0:
                    available_drivers.append(driver)
                else:
                    available_drivers.appendleft(driver)

            while current_time < END_TIME:
                next_time = current_time + timedelta(minutes=PEAK_MAX_WAIT)
                is_peak = any(
                    start <= current_time + timedelta() < end
                    for start, end in PEAK_HOURS
                )
                current_invterval = PEAK_MAX_WAIT if is_peak else NON_PEAK_MAX_WAIT
                # Обновляем состояние водителей
                # Смотрим на водителей в пути
                while (
                    len(busy_drivers) > 0
                    and busy_drivers[0].next_available_time <= current_time
                ):
                    driver = busy_drivers.popleft()
                    available_buses.append(driver.current_bus)
                    # Проверить, нужен ли обед. Иначе - просто перерыв каждые два часа
                    # Логика распределения водителей по обедам, перерывам и работе
                    #
                    if driver.route_count > 4:
                        driver.next_available_time = current_time + LUNCH_DURATION
                        break_drivers.append(driver)
                    elif driver.route_count > 2:
                        driver.next_available_time = current_time + BREAK_DURATION
                        break_drivers.appendleft(driver)
                    else:
                        driver.next_available_time = current_time
                        if len(available_drivers) % 2 == 0:
                            available_drivers.append(driver)
                        else:
                            available_drivers.appendleft(driver)

                while (
                    len(break_drivers) > 0
                    and break_drivers[0].next_available_time <= current_time
                ):
                    driver = break_drivers.popleft()
                    driver.next_available_time = current_time
                    if len(available_drivers) % 2 == 0:
                        available_drivers.append(driver)
                    else:
                        available_drivers.appendleft(driver)

                # Запускаем автобус, прошло достаточно времени с отправки последнего автобуса
                if (
                    current_time - last_bus_time
                ).total_seconds() // 60 > current_invterval:
                    if len(available_drivers) == 0:
                        # Если свободных водителей нет - ждем, когда он появится
                        current_time = next_time
                        continue
                    if len(available_buses) == 0:
                        # Если свободных автобусов нет - ждем, когда он появится
                        current_time = next_time
                        continue
                    driver = available_drivers.popleft()
                    bus = available_buses.pop()
                    if driver.start_time is None:
                        driver.start_time = current_time

                    driver.next_available_time = current_time + ROUTE_DURATION
                    driver.route_count += 1
                    driver.current_bus = bus
                    busy_drivers.append(driver)
                    last_bus_time = current_time
                    if day - 1 >= len(schedule):
                        print(day - 1)
                    schedule[day - 1].append(Shift(driver, bus, current_time))

                current_time = next_time
        """
        Теперь у нас есть сгенерированное на неделю расписание
        Остается только сравнить его эффективность 
        """
        schedule_loss = combined_loss(
            schedule,
            PEAK_HOURS,
            NON_PEAK_MAX_WAIT,
            PEAK_MAX_WAIT,
            len(drivers),
            5.0,
            2.0,
        )
        if schedule_loss < best_loss:
            best_loss = schedule_loss
            best_schedule = schedule

    # Первым делом - составить график водителей на неделю
    def recursive_days(drivers: list[Driver], x: int):
        if x == len(drivers):
            # В это месте мы вызываем generate_schedule_per_day
            # print([(d.id, d.type, d.first_day) for d in drivers])
            generate_schedule_per_day(drivers, buses)
            return
        for i in range(0, 3):
            drivers[x].first_day = DAYS[i]
            recursive_days(drivers, x + 1)

    for count_drivers in range(4, NUM_BUSES + 1):
        for count_drivers_a in range(0, count_drivers + 1):
            count_drivers_b = count_drivers - count_drivers_a
            drivers = [Driver("A", i) for i in range(1, count_drivers_a + 1)] + [
                Driver("B", i + count_drivers_a) for i in range(1, count_drivers_b + 1)
            ]
            recursive_days(drivers, 0)
    return best_schedule, best_loss


schedule, loss = brute_force_schedule()

print(loss)
print(schedule)
for day, day_s in enumerate(schedule):
    print(day)
    print("-----------")
    for s in day_s:
        print(s.driver.id, s.bus.id, s.start_time)
    print("-----------")
