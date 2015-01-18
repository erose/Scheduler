import datetime, calendar, collections

# The datetime object for today.
today = datetime.date.today()

# The datetime object for the currently selected day (starts off at today).
selected = today

# A {date: {time: string}} dictionary which associates dates/times with events.
schedule = collections.defaultdict(dict)

# Horizontal space between objects in Days and Header windows.
space = 4