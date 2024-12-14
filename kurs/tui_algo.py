from datetime import datetime, timedelta
import calendar
from textual.app import App, ComposeResult
from textual.widgets import Static, Button, Header
from textual.containers import Horizontal, Middle
from textual.widget import Widget


class CalendarWidget(Widget):
    """Динамический виджет для отображения одной недели календаря."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_week = self.get_current_week()

    def get_current_week(self):
        """Возвращает список дней текущей недели."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return [
            (start_of_week + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)
        ]

    def compose(self) -> ComposeResult:
        yield self.render()
        yield Button("Показать расписание автобусов", id="show-schedule")


class Week(Static):

    days = ["MN", "TUE", "WED", "TH", "FR", "SAT", "SUN"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        content_widget = self.query_one("#content", Static)
        content_widget.update(self.days[int(event.button.id[1])])
        if event.button.id == "p1":
            content_widget.update("Это текст 1. Добро пожаловать!")
        elif event.button.id == "p2":
            content_widget.update("Это текст 2. Здесь может быть другая информация.")
        elif event.button.id == "p3":
            content_widget.update("Это текст 3. Переключайтесь между вариантами!")

    def compose(self):
        yield Middle(
            Static("Выберите день недели", id="systext"),
            Horizontal(
                Button("ПН", id="p0"),
                Button("ВТ", id="p1"),
                Button("СР", id="p2"),
                Button("ЧТ", id="p3"),
                Button("ПТ", id="p4"),
                Button("СБ", id="p5"),
                Button("ВС", id="p6"),
            ),
            Static("", id="content"),
        )


class CalendarApp(App):
    """Приложение для отображения TUI-календаря с расписанием автобусов."""

    def compose(self) -> ComposeResult:
        yield Header()
        # yield Button("ПН", id="mn")
        yield Horizontal(Week())

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     """Обработка нажатия кнопки."""
    #     if event.button.id == "show-schedule":
    #         self.query_one("#main-container").mount(ScheduleWidget())


if __name__ == "__main__":
    app = CalendarApp()
    app.run()
