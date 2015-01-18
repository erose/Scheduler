import re, datetime, calendar, itertools
import shared

class ScannerError(Exception): pass
class Scanner(re.Scanner):
    # Constucts a regex to match full and abbreviated month names.
    months_full = ['January', 'February', 'March',
        'April', 'May', 'June', 'July',
        'August', 'September', 'October',
        'November', 'December']
    months_abbr = ['Jan', 'Feb', 'Mar',
        'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep',
        'Oct', 'Nov', 'Dec']

    # Day names have three levels of abbreviation (and Tues + Thurs).
    weekdays_full = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
    ]
    weekdays_three = [
    "Sun", "Mon", "Tue", "Wed",
    "Thu", "Fri", "Sat"
    ]
    weekdays_one = [
    "U", "M", "T", "W",
    "R", "F", "S"
    ]

    def __init__(self, *args):
        super().__init__(args[0] + [
                # All recognized punctuation.
                (r"--|-|,|:|\.", lambda scanner, token: (token, '')),
                # Ignore spaces.
                (r"\s+", None)
                ])

    def scan(self, string):
        results, remainder = super().scan(string)
        if remainder != '':
            raise ScannerError((string, remainder))

        return results

    """
    Returns a time object for a time string.
    """
    def parse_time(self, time_string):
        if ":" in time_string:
            splits = time_string.split(":")
            hours = int(splits[0])
            minutes = int(splits[1][:2])
        else:
            hours = int(re.match(r"(\d*)", time_string).group(1))
            minutes = 0

        if ("p" in time_string or "P" in time_string) and hours < 12:
            hours += 12

        return 'TIME', datetime.time(hours, minutes)

    """
    Returns an integer day number for a day string.
    """
    def parse_day(self, day_string):
        # September 8, July 4
        if day_string.isdigit():
            return 'DAY', int(day_string)
        # August 1st, April 20th, May 23rd
        if day_string[:-2].isdigit():
            return 'DAY', int(day_string[:-2])

    """
    Returns an integer in the range 1-7 inclusive for a weekday string.
    """
    def parse_weekday(self, weekday_string):
        if weekday_string == "Tues": return 'WEEKDAY', 3
        if weekday_string == "Thurs": return 'WEEKDAY', 5

        for names_list in self.weekdays_full, self.weekdays_three, self.weekdays_one:
            if weekday_string in names_list:
                return 'WEEKDAY', names_list.index(weekday_string) + 1

    """
    Returns an integer in the range 1-12 (inclusive) for a month string.
    """
    def parse_month(self, month_string):
        for names_list in self.months_full, self.months_abbr:
            if month_string in names_list:
                return 'MONTH', names_list.index(month_string) + 1


class ParserError(Exception): pass
class Parser:
    def __init__(self, tokens):
        self.tokens = iter(tokens + [('END', '')])
        self.current = next(self.tokens)

    def accept(self, allowed_kinds):
        return self.expect(allowed_kinds, necessary=False)

    def confirm(self, allowed_kinds):
        return self.expect(allowed_kinds, yesorno=True)

    def check(self, allowed_kinds):
        return self.expect(allowed_kinds, yesorno=True, necessary=False)

    def expect(self, allowed_kinds, yesorno=False, necessary=True):
        kind, value = self.current

        if kind in allowed_kinds:
            try:
                self.current = next(self.tokens)
            except StopIteration:
                pass

            if yesorno:     return True
            if necessary:   return value
            else:           return True, value
        else:
            if necessary:   raise ParserError((self.current, allowed_kinds))
            if yesorno:     return False
            else:           return False, None


class TimeParser(Parser):
    def __init__(self, string):
        scanner = Scanner([
            # Time in hh:mm format, with optional pm or am.
            (r"\d?\d(:\d\d\s*)?\s*([paPA]\.?[mM]\.?)?", Scanner.parse_time)
            ])

        tokens = scanner.scan(string)
        super().__init__(tokens)

    def time_pairs(self):
        while True:
            start = self.expect(["TIME"])
            self.confirm(["-", "--"])
            end = self.expect(["TIME"])
            yield start, end

            if not self.check([',']): break

    def parsed(self):
        yield from self.time_pairs()


class DateParser(Parser):
    def __init__(self, string):
        valid_month_names = r"|".join(Scanner.months_full + Scanner.months_abbr)
        valid_day_names = r"|".join(Scanner.weekdays_full + ["Tues", "Thurs"]
            + Scanner.weekdays_three + Scanner.weekdays_one)

        scanner = Scanner([
            (valid_month_names, Scanner.parse_month),
            (valid_day_names, Scanner.parse_weekday),
            # Parse day numbers.
            (r"\d\d?[a-zA-z]*", Scanner.parse_day)
            ])

        tokens = scanner.scan(string)
        super().__init__(tokens)

    """
    Reads in an interval of dates, like August -- September or January 18-21.
    Returns a list of Date objects.
    """
    def I(self):
        start_month = self.expect(['MONTH'])
        is_numeric, start_day = self.accept(['DAY'])

        if is_numeric:
            if self.check(["-", "--"]):
                does_span_months, end_month = self.accept(['MONTH'])
                if not does_span_months: end_month = start_month
                end_day = self.expect(['DAY'])
            else:
                end_day, end_month = start_day, start_month

        else:
            start_day = 1

            if self.check(["-", "--"]):
                end_month = self.expect(['MONTH'])
            else:
                end_month = start_month

            end_day = last_day(end_month)

        result = []
        start = datetime.date(shared.today.year, start_month, start_day)
        end = datetime.date(shared.today.year, end_month, end_day)

        while start <= end:
            result.append(start)
            start += datetime.timedelta(days=1)

        return result

    """
    Reads <day> - <day> | <day>, where <day> is a number or a weekday name.
    Returns a (date -> boolean) lambda.
    """
    def D(self):
        is_numeric, start = self.accept(['DAY'])

        if is_numeric:
            if self.check(["-", "--"]):
                end = self.expect(['DAY'])
                return lambda date: start <= date.day <= end

            else:
                return lambda date: date.day == start

        else:
            is_weekday, start_weekday_num = self.accept(['WEEKDAY'])

            if is_weekday:
                included_weekdays = set()
                if self.check(["-", "--"]):
                    end_weekday_num = self.expect(['WEEKDAY'])

                    while start_weekday_num != end_weekday_num:
                        included_weekdays.add(start_weekday_num)
                        start_weekday_num += 1
                        start_weekday_num %= 7
                    included_weekdays.add(end_weekday_num)

                else:
                    included_weekdays.add(start_weekday_num)

                return lambda date: (date.isoweekday() + 1 + 7) % 7 in included_weekdays

            else:
                return lambda date: True

    def dates(self):
        while True:
            interval = self.I()
            lambdas = []

            while True:
                lambdas.append(self.D())
                if self.check([',', 'END']): break

            for date in interval:
                for l in lambdas:
                    if l(date): yield date; break

            if self.check(['END']): break

    def parsed(self):
        yield from self.dates()


def last_day(month_num):
    """
    Utility method. Returns the number of the last day in the given month.
    """
    for day in 31, 30, 29, 28:
        try:
            datetime.date(shared.today.year, month_num, day)
            return day
        except ValueError: continue


def read_line(line):
    """
    Enters a single line of schedule.txt into the schedule dictionary.
    """
    dates, times, event = line.split("|")
    try:
        dates = DateParser(dates).parsed()
        times = TimeParser(times).parsed()

        for date, time_pair in itertools.product(dates, times):
            start, end = time_pair
            shared.schedule[date][start, end] = event

    except ScannerError as e:
        print("Error scanning text file.")
        print("Beginning in this section: \n\t", e.args[0][1])
        print("the following line: \n\t", e.args[0][0])
        print("could not be understood.")
        exit(0)

    except ParserError as e:
        print("Error parsing text file.")
        print("Expected something in: \n\t", e.args[0][1])
        print("But found this instead: \n\t", e.args[0][0])
        exit(0)


def read_file(filename):
    with open(filename, "r") as f:
        for line in f:
            if line.strip() != "": read_line(line.strip())

if __name__ == "__main__":
    read_line("September 1 | 7:00pm - 8:30pm | Algorithms Office Hours")