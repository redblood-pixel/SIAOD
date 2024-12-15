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
        self.start_time: datetime = None
        self.route_count = 0
        self.current_bus: Bus = None


class Bus:
    def __init__(self, id):
        self.id = id
        self.schedule = []


class Shift:
    def __init__(self, driver, bus, start_time):
        self.driver: Driver = driver
        self.bus: Bus = bus
        self.start_time: datetime = start_time

    def __str__(self):
        print(self.start_time.strftime("%H:%M:%S"))
        return f"Водитель-{self.driver.id} Автобус-{self.bus.id} Выезд-{self.start_time.strftime("%H:%M:%S")}"


# Параметры задачи
START_TIME = datetime.strptime("06:00", "%H:%M")
END_TIME = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)
PEAK_HOURS = [
    (datetime.strptime("07:00", "%H:%M"), datetime.strptime("09:00", "%H:%M")),
    (datetime.strptime("17:00", "%H:%M"), datetime.strptime("19:00", "%H:%M")),
]

NUM_BUSES = 20
buses = [Bus(i) for i in range(1, NUM_BUSES)]

ROUTE_DURATION = timedelta(minutes=60)
LUNCH_DURATION = timedelta(minutes=60)
BREAK_DURATION = timedelta(minutes=15)

PEAK_MAX_WAIT = 10  # Минуты
NON_PEAK_MAX_WAIT = 20  # Минуты
DAYS = [i for i in range(0, 7)]


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
        if len(day_schedule) == 0:
            waiting_loss += 400000000
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
def brute_force_schedule(
    num_buses: int, route_duration: timedelta
) -> tuple[list[list[Shift]], float, list[int]]:
    """
    Для сгенерированных комбинаций водителей по дням
    мы составляем расписание на каждый день с учетом того, сколько
    сегодня работает водителей каждого типа.
    Затем считаем функцию потерь и сравниваем оптимальность
    """
    best_loss = 10000000
    best_schedule = None
    best_count = []

    def count_per_day(drivers):
        cnt = [0 for i in range(7)]
        for day in DAYS:
            for driver in drivers:
                if (
                    driver.type == "A"
                    and driver.first_day <= day < driver.first_day + 5
                ):
                    cnt[day] += 1
                elif driver.type == "B" and (
                    driver.first_day == day or driver.first_day + 5 == day
                ):
                    cnt[day] += 1
        return cnt

    def generate_schedule_per_day(drivers: list[Driver], buses: list[Bus]):
        nonlocal best_loss
        nonlocal best_schedule
        nonlocal best_count
        schedule = [[] for i in range(7)]
        for day in DAYS:
            """
            Каждые 10 минут мы проверяем состояние
            Если это не час пик, мы ждем, пока не наберется 20 минут
            Если через час начнется час пик, то мы начинаем отправлять автобусы с частотой 10 минут
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
                    driver.first_day == day or driver.first_day + 5 == day
                ):
                    today_drivers_b.append(driver)

            """
            Дек содержит свободных водителей, причем сначала мы равномерно перемешиваем 
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
            l, r = 0, 0
            while l < len(today_drivers_a) or r < len(today_drivers_b):
                if l == len(today_drivers_a):
                    available_drivers.append(today_drivers_b[r])
                    r += 1
                elif r == len(today_drivers_b):
                    available_drivers.append(today_drivers_a[l])
                    l += 1
                else:
                    if (l + r) % 2 == 0:
                        available_drivers.append(today_drivers_a[l])
                        l += 1
                    else:
                        available_drivers.append(today_drivers_b[r])
                        r += 1
            for i, driver in enumerate(today_drivers_a + today_drivers_b):
                if i % 2 == 0:
                    available_drivers.append(driver)
                else:
                    available_drivers.appendleft(driver)

            while current_time < END_TIME:
                next_time = current_time + timedelta(minutes=PEAK_MAX_WAIT)
                is_peak = any(
                    start <= current_time < end
                    or start <= current_time + route_duration < end
                    for start, end in PEAK_HOURS
                )
                current_invterval = PEAK_MAX_WAIT if is_peak else NON_PEAK_MAX_WAIT
                # print(current_time, is_peak, current_invterval)
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
                ).total_seconds() // 60 >= current_invterval:
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

                    driver.next_available_time = current_time + route_duration
                    driver.route_count += 1
                    driver.current_bus = bus
                    busy_drivers.append(driver)
                    last_bus_time = current_time
                    schedule[day].append(Shift(driver, bus, current_time))

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
            100.0,
        )
        if schedule_loss < best_loss:
            best_loss = schedule_loss
            best_schedule = schedule
            best_count = count_per_day(drivers)

    # Первым делом - составить график водителей на неделю
    # def recursive_days(drivers: list[Driver], x: int):
    #     if x == len(drivers):
    #         # В это месте мы вызываем generate_schedule_per_day
    #         # print([(d.id, d.type, d.first_day) for d in drivers])
    #         generate_schedule_per_day(drivers, buses)
    #         return
    #     for i in range(0, 3):
    #         drivers[x].first_day = DAYS[i]
    #         recursive_days(drivers, x + 1)

    for count_drivers in range(4, num_buses + 1):
        for count_drivers_a in range(0, count_drivers + 1):
            count_drivers_b = count_drivers - count_drivers_a
            drivers_a = [Driver("A", i) for i in range(1, count_drivers_a + 1)]
            driver_b = [
                Driver("B", i + count_drivers_a) for i in range(1, count_drivers_b + 1)
            ]
            # Распределяем большую часть на будние, небольшую - на выходные
            distibution = [0.4, 0.3, 0.3]
            sum_d = [int(distibution[0] * count_drivers_a)]
            for i in range(1, 3):
                sum_d.append(int(distibution[i] * count_drivers_a) + sum_d[i - 1])
            sum_d[-1] = count_drivers_a
            pos_d = 0
            for i, da in enumerate(drivers_a):
                if i > sum_d[pos_d]:
                    pos_d += 1
                da.first_day = DAYS[pos_d]
            for i, db in enumerate(driver_b):
                db.first_day = DAYS[i % 2]

            drivers = drivers_a + driver_b
            generate_schedule_per_day(drivers, buses)

            # recursive_days(drivers, 0)
    return best_schedule, best_loss, best_count


def display_one_day(schedule_d) -> str:
    res = ""
    for s in schedule_d:
        res += str(s) + "\n\n"
    return res


if __name__ == "__main__":
    schedule, loss, best_count = brute_force_schedule(NUM_BUSES, ROUTE_DURATION)

    print(loss)
    print(best_count)
    for day, day_s in enumerate(schedule):
        print(day)
        print("-----------")
        for s in day_s:
            print(s.driver.id, s.bus.id, s.start_time)
        print("-----------")
