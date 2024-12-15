from datetime import timedelta

from textual.app import App, ComposeResult
from textual.widgets import (
    Static,
    Button,
    Header,
    Input,
    DataTable,
    Label,
)
from textual.containers import Horizontal, Middle, Vertical, Container

import brute_force

from genetic import genetic_algorithm


class CalendarApp(App):
    """Приложение для отображения TUI-календаря с расписанием автобусов."""

    CSS = """
    #main-container {
        height: 100%;
        width: 100%;
        layout: vertical;
        overflow-y: auto;
    }
    """

    def on_button_pressed(self, event: Button.Pressed):
        container = self.query_one("#main-container", Vertical)
        if event.button.id == "exit":
            self.exit()
            return
        elif event.button.id == "calc":
            content = self.query_one("#content", DataTable).clear()
            self.update_table()

    def generate_table(self):
        table = DataTable(id="content")
        table.add_columns("Водитель", "Выезд")
        return table

    def update_table(self):
        table = self.query_one("#content", DataTable)
        num_buses = self.query_one("#nb", Input).value
        route_duration = self.query_one("#rd", Input).value
        schedule = genetic_algorithm(
            int(num_buses), timedelta(minutes=int(route_duration))
        )
        if not schedule:
            return table
        for s in schedule:
            table.add_row(s[0], s[1].strftime("%H:%M"))
        return table

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Number of buses", value="15", type="integer", id="nb")
        yield Input(placeholder="Route duration", value="60", type="integer", id="rd")
        yield Container(
            Vertical(
                Button("Рассчитать", id="calc"),
                Button("Выйти", id="exit"),
                self.generate_table(),
                id="main-container",
            )
        )


if __name__ == "__main__":
    app = CalendarApp()
    app.run()
