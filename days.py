import curses, calendar
import shared

class Day:
    def __init__(self, datetime):
        # The underlying datetime object.
        self.datetime = datetime

        # Make it easier to access some things from the datetime.
        self.year_num = datetime.year
        self.month_num = datetime.month
        self.day_num = datetime.day

        # Events on this day, as a dict time => string.
        self.events = {}

    def __repr__(self):
        end_digit = self.day_num % 10

        if end_digit == 1 and self.day_num != 11:   end = "st"
        elif end_digit == 2 and self.day_num != 12: end = "nd"
        elif end_digit == 3 and self.day_num != 13: end = "rd"
        else:                                       end = "th"

        month_name = calendar.month_name[self.month_num]

        return "{} {}{}".format(
            month_name, str(self.day_num), end)