import datetime, calendar, collections

# The datetime object for today.
today = datetime.date.today()

# The datetime object for the currently selected day (starts off at today).
selected = today

# A {date: {time: string}} dictionary which associates dates/times with events.
schedule = collections.defaultdict(dict)

# Horizontal space between objects in Days and Header windows.
space = 4

### Utility Methods ###
def render_date(date):
    end_digit = date.day % 10

    if end_digit == 1 and date.day != 11:   end = "st"
    elif end_digit == 2 and date.day != 12: end = "nd"
    elif end_digit == 3 and date.day != 13: end = "rd"
    else:                                   end = "th"

    month_name = calendar.month_name[date.month]
    weekday_name = calendar.day_name[(date.isoweekday() - 1 + 7) % 7]

    return "{}, {} {}{}".format(
        weekday_name, month_name, str(date.day), end)