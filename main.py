import curses, calendar, datetime, os
import windows, days, shared, events

def initialize_colors():
    curses.use_default_colors()

    # Pair 2 is green on black.
    curses.init_pair(2, 2, -1)

def main(stdscr):
    initialize_colors()

    # Get rid of the cursor.
    curses.curs_set(False)

    # Create the calendar header (month name + day names) window.
    header_win = windows.HeaderWindow(0, 0, height = 3)

    # Create the calendar days window.
    days_win = windows.DaysWindow(3, 0)

    # Create the events window.
    events_win = windows.EventsWindow(days_win, days_win.height + 3, 0)

    # Draw everything once: redraws will be handled by the windows themselves.
    days_win.draw()
    header_win.draw()
    events_win.draw()

    while True:
        # Wait for input.
        key = days_win.getch()

        # Send the input to the day and events windows for handling.
        days_win.handle_keypress(key)
        events_win.handle_keypress(key)

if __name__ == "__main__":
    # Read the events in.
    filename = "schedule.txt"
    events.read_file(filename)
    
    curses.wrapper(main)