import curses, calendar, datetime
import shared, days

class Window():
    def __init__(self, height, width, startx, starty):
        self.width, self.height = width, height
        self.startx, self.starty = startx, starty

        #The underlying curses window.
        self.window = curses.newwin(height, width, startx, starty)

    # Redirect to the underlying curses window.
    def __getattr__(self, attr):
        return getattr(self.window, attr)

class EventsWindow(Window):
    def __init__(self, days_window, *args):
        super().__init__(100, 80, *args)

        # The DaysWindow this window is looking at.
        self.days_window = days_window

    """
    Takes a date and returns a pretty string representation.
    """
    def render_date(self, date):
        end_digit = date.day % 10

        if end_digit == 1 and date.day != 11:   end = "st"
        elif end_digit == 2 and date.day != 12: end = "nd"
        elif end_digit == 3 and date.day != 13: end = "rd"
        else:                                   end = "th"

        month_name = calendar.month_name[date.month]
        weekday_name = calendar.day_name[(date.isoweekday() - 1 + 7) % 7]

        return "{}, {} {}{}".format(
            weekday_name, month_name, str(date.day), end)

    """
    Draws the events for the currently selected day_obj onto this window.
    """
    def draw(self):
        self.clear()

        # A line of decoration, then the currently selected day.
        text = self.render_date(shared.selected)
        self.addstr(0, 0, "." * len(text))
        self.addstr(1, 0, text)

        # Draw hours.
        for i in range(1, 16 + 1):
            hour = i + 8
            self.addstr(i*2, 0, str(hour - 12 if hour > 12 else hour))

        # Does this day have events? (Has it been entered into the schedule?)
        if shared.selected in shared.schedule:
            # Yes? Good.
            events = shared.schedule[shared.selected]

            # Draw each event.
            for (start, end), event in sorted(events.items()):
                minutes_length = (
                    (end.hour * 60 + end.minute)
                    -
                    (start.hour * 60 + start.minute)
                    )
                text = ("{} -- {}: {}").format(
                    start.strftime("%I:%M%p"), end.strftime("%I:%M%p"), event
                    )
                start_position = 2 + ((start.hour - 9) * 60 + start.minute) // 30
                self.addstr(start_position, 5, text)

                for i in range(0, round(minutes_length / 30)):
                    self.addstr(start_position + i, 3, "*", curses.A_REVERSE)

        self.refresh()

class HeaderWindow(Window):
    def __init__(self, *args, height):
        super().__init__(height, shared.space * 7, *args)

    """
    Draws the month name and day names onto the window.
    """
    def draw(self):
        self.clear()

        # Draw the month name centered at the top.
        month_name = calendar.month_name[shared.selected.month]
        self.draw_centered(0, month_name + ", " + str(shared.selected.year), curses.A_BOLD)

        # Draw the day names along the top, under the month name.
        for i, day_name in enumerate(("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")):
            self.addstr(1, i * shared.space, day_name)

        self.refresh()

    """
    Draws the given text centered horizontally at the given y-position.
    """
    def draw_centered(self, y, text, options = 0):
        self.addstr(y, (self.width - shared.space) // 2 - len(text) // 2, text, options)

class DaysWindow(Window):
    # The maximum height of any month.
    # It's top + four weeks in the middle + bottom.
    max_month_height = 1 + 4 + 1

    def __init__(self, *args):
        super().__init__(DaysWindow.max_month_height, shared.space * 7, *args)

        # Create a calendar object, with the first day of the week = Sunday (6).
        self.cal = calendar.Calendar(firstweekday = 6)

        # Set up the keyboard for listening.
        self.keypad(1)

    """
    Changes the selected day by amount number of days (+ forward, -backward)
    """
    def change_day(self, amount):
        shared.selected += datetime.timedelta(days = amount)

    """
    Given a date, returns its display options for ncurses (an integer).
    """
    def display_options_for_day(self, date):
        return (
              (curses.color_pair(2) if date == shared.today else 0)
            | (curses.A_BOLD if date.month == shared.selected.month else 0)
            | (curses.A_REVERSE if shared.selected == date else 0)
            )

    """
    Handles the keypress and returns False if we should stop, True otherwise.
    """
    def handle_keypress(self, key):
        from curses import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT

        if key in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT):
            if key == KEY_UP: self.change_day(-7)
            if key == KEY_DOWN: self.change_day(7)
            if key == KEY_LEFT: self.change_day(-1)
            if key == KEY_RIGHT: self.change_day(1)

        # The page and selected day object have changed, so redraw.
        self.draw()

    """
    Draws all of the days in their positions on the window.
    """
    def draw(self):
        self.clear()

        # The iterator over dates that would appear on this calendar page.
        dates_for_month = self.cal.itermonthdates(shared.selected.year, shared.selected.month)

        # Draw the day numbers in their grid.
        for i, date in enumerate(dates_for_month):
            x, y = i % 7, i // 7
            self.addstr(
                y, x * shared.space, str(date.day),
                self.display_options_for_day(date)
                )

        self.refresh()