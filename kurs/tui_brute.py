from datetime import timedelta

from textual.app import App, ComposeResult
from textual.widgets import (
    Static,
    Button,
    Header,
    Log,
    TabbedContent,
    Markdown,
    TabPane,
    DataTable,
)
from textual.containers import Horizontal, Middle

import brute_force

schedule, _, _ = brute_force.brute_force_schedule(20, timedelta(minutes=60))


class Week(Static):

    days = ["MN", "TUE", "WED", "TH", "FR", "SAT", "SUN"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        content_widget = self.query_one("#content", Log)
        # content_widget.update(self.days[int(event.button.id[1])])
        content_widget.write_line(
            brute_force.display_one_day(schedule[int(event.button.id[1]) - 1])
        )

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
            Log("", id="content"),
        )


class CalendarApp(App):
    """Приложение для отображения TUI-календаря с расписанием автобусов."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.exit()
            return

    def generate_table(self, day):
        table = DataTable()
        table.add_columns("Водитель", "Автобус", "Выезд")
        for s in schedule[day]:
            table.add_row(s.driver.id, s.bus.id, s.start_time.strftime("%H:%M"))
        return table

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Выберите день недели")
        yield Button("Выйти", id="exit")
        with TabbedContent():
            with TabPane("ПН", id="p1"):
                yield self.generate_table(0)
            with TabPane("ВТ", id="p2"):
                yield self.generate_table(1)
            with TabPane("СР", id="p3"):
                yield self.generate_table(2)
            with TabPane("ЧТ", id="p4"):
                yield self.generate_table(3)
            with TabPane("ПТ", id="p5"):
                yield self.generate_table(4)
            with TabPane("СБ", id="p6"):
                yield self.generate_table(5)
            with TabPane("ВС", id="p7"):
                yield self.generate_table(6)
        # yield Horizontal(
        #     Button("ПН", id="p0"),
        #     Button("ВТ", id="p1"),
        #     Button("СР", id="p2"),
        #     Button("ЧТ", id="p3"),
        #     Button("ПТ", id="p4"),
        #     Button("СБ", id="p5"),
        #     Button("ВС", id="p6"),
        # )
        # yield Log("", id="content")

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     """Обработка нажатия кнопки."""
    #     if event.button.id == "show-schedule":
    #         self.query_one("#main-container").mount(ScheduleWidget())


if __name__ == "__main__":
    app = CalendarApp()
    app.run()
