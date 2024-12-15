import random
from datetime import datetime, timedelta


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

    def __str__(self):
        return (
            f"Водитель-{self.driver.id} Автобус-{self.bus.id} Выезд-{self.start_time}"
        )


# Параметры задачи
START_TIME = datetime.strptime("06:00", "%H:%M")
END_TIME = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)
PEAK_HOURS = [
    (datetime.strptime("07:00", "%H:%M"), datetime.strptime("09:00", "%H:%M")),
    (datetime.strptime("17:00", "%H:%M"), datetime.strptime("19:00", "%H:%M")),
]

NUM_BUSES = 15
buses = [Bus(i) for i in range(1, NUM_BUSES)]

ROUTE_DURATION = timedelta(minutes=60)
LUNCH_DURATION = timedelta(minutes=60)
BREAK_DURATION = timedelta(minutes=15)

PEAK_MAX_WAIT = 10  # Минуты
NON_PEAK_MAX_WAIT = 20  # Минуты
DAYS = [i for i in range(0, 7)]

POPULATION_SIZE = 20
GENERATIONS = 100
MUTATION_RATE = 0.1


def generate_one_schedule(drivers: list[Driver]) -> list[tuple[int, datetime]]:
    schedule = []
    driver_next_available = {driver.id: START_TIME for driver in drivers}
    current_time = START_TIME
    while current_time < END_TIME:
        available_drivers = [
            driver
            for driver in drivers
            if driver_next_available[driver.id] <= current_time
        ]
        if not available_drivers:
            break
        driver = random.choice(available_drivers)

        schedule.append((driver.id, current_time))
        driver_next_available[driver.id] += ROUTE_DURATION
        current_time += timedelta(minutes=random.choice([5, 10, 15, 20]))  # Интервалы
    return schedule


# Генерация начальной популяции
def initialize_population(drivers: list[Driver]) -> list[list[tuple[int, datetime]]]:
    population = []
    for _ in range(POPULATION_SIZE):
        schedule = generate_one_schedule(drivers)
        population.append(schedule)
    return population


# Оценка расписания (функция потерь)
def fitness(schedule: list[tuple[int, datetime]]) -> float:
    waiting_loss = 0
    driver_usage = {}
    if not schedule:
        return 2000000000

    for i in range(len(schedule) - 1):
        _, time1 = schedule[i]
        _, time2 = schedule[i + 1]
        interval = (time2 - time1).total_seconds() / 60

        # Проверка на пики
        is_peak = any(start <= time1 < end for start, end in PEAK_HOURS)
        max_wait = 5 if is_peak else 15
        if interval > max_wait:
            waiting_loss += (interval - max_wait) ** 2

        # Учет использования водителей
        driver_id, _ = schedule[i]
        if driver_id not in driver_usage:
            driver_usage[driver_id] = 0
        driver_usage[driver_id] += 1

    # Штраф за использование большого числа водителей
    driver_loss = len(driver_usage) ** 2

    # Итоговая функция потерь
    return waiting_loss + driver_loss


def is_schedule_valid(schedule: list[tuple[int, datetime]]) -> bool:
    """
    Проверяет, что водители не выезжают чаще, чем раз в час.
    """
    if not schedule:
        return False

    driver_last_departure = {}
    for driver_id, departure_time in schedule:
        if driver_id in driver_last_departure:
            last_time = driver_last_departure[driver_id]
            if (
                departure_time - last_time
            ).total_seconds() < 3600:  # Проверяем разницу в часах
                return False  # Некорректное расписание
        driver_last_departure[driver_id] = departure_time

    return True


# Очистка популяции от некорректных расписаний
def clean_population(
    population: list[list[tuple[int, datetime]]],
    drivers: list[Driver],
    max_invalid=10,
) -> list[list[tuple[int, datetime]]]:
    """
    Удаляет некорректные особи из популяции и заменяет их новыми.
    """
    valid_population = []
    invalid_count = 0

    for individual in population:
        if is_schedule_valid(individual):
            valid_population.append(individual)
        elif invalid_count < max_invalid:
            # Генерируем новую особь вместо некорректной
            # Берем первую особь из нового поколения
            new_individual = generate_one_schedule(drivers)
            valid_population.append(new_individual)
            invalid_count += 1

    return valid_population


# Селекция (турнирный отбор)
def selection(population: list[tuple[int, datetime]]) -> list[tuple[int, datetime]]:
    if not population or len(population) < 3:
        return None
    tournament = random.sample(population, k=3)
    return min(tournament, key=fitness)


# Кроссовер (обмен расписаниями между родителями)
def crossover(
    parent1: list[tuple[int, datetime]], parent2: list[tuple[int, datetime]]
) -> list[tuple[int, datetime]]:
    split_point = random.randint(1, len(parent1) - 1)
    child = parent1[:split_point] + parent2[split_point:]
    return child


# Мутация (изменение времени отправления или водителя)
def mutate(drivers: list[Driver], schedule: list[tuple[int, datetime]]) -> None:
    if random.random() < MUTATION_RATE:
        index = random.randint(0, len(schedule) - 1)
        driver = random.choice(drivers)
        new_time = schedule[index][1] + timedelta(minutes=random.choice([-5, 5, 10]))
        schedule[index] = (driver.id, new_time)


# Основной генетический алгоритм
def genetic_algorithm(num_buses: int, route_duration: timedelta):
    # Водители
    # drivers = [
    #     {"id": i + 1, "type": "A" if i < NUM_DRIVERS_A else "B"}
    #     for i in range(NUM_DRIVERS_A + NUM_DRIVERS_B)
    # ]
    best_loss = 100000000
    total_schedule = []
    for count_drivers in range(num_buses // 2, num_buses + 1):
        drivers = [Driver("B", i) for i in range(1, count_drivers)]

        population = initialize_population(drivers)
        best_schedule = None
        best_fitness = float("inf")
        print(count_drivers, len(population))

        for generation in range(GENERATIONS):
            new_population = []
            for _ in range(POPULATION_SIZE):
                parent1 = selection(population)
                parent2 = selection(population)
                if not parent1 or not parent2:
                    continue
                child = crossover(parent1, parent2)
                mutate(drivers, child)
                new_population.append(child)

            # Удаляем некорректные особи и заменяем их новыми
            population = clean_population(new_population, drivers)

            # Обновление лучшего решения
            if not population:
                break
            current_best = min(population, key=fitness)
            current_fitness = fitness(current_best)
            if current_fitness < best_fitness:
                best_schedule = current_best
                best_fitness = current_fitness

            # print(f"Generation {generation + 1}, Best Fitness: {best_fitness}")
        if best_fitness < best_loss:
            best_loss = best_fitness
            total_schedule = best_schedule

    return total_schedule


def run_genetic_algo(num_buses: int, route_duration: timedelta):
    # Запуск алгоритма
    best_schedule = genetic_algorithm(num_buses, route_duration)
    print(is_schedule_valid(best_schedule))
    print("Лучшее расписание:")
    for driver_id, time in best_schedule:
        print(f"Водитель {driver_id} отправляется в {time.strftime('%H:%M')}")


if __name__ == "__main__":
    run_genetic_algo(NUM_BUSES, ROUTE_DURATION)
