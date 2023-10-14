import logging
import pandas as pd
from pick import pick

logging.basicConfig(format='\n%(levelname)s: %(message)s\n', level=logging.INFO)
LOGGER = logging.getLogger()

CITY_DATA = {
    'Chicago': 'chicago.csv',
    'Washington': 'washington.csv',
    'New York City': 'new_york_city.csv'
}

INDICATOR = '-> '

def get_months():
    """Select month(s) to filter by"""

    selection = pick(
        ['January', 'February', 'March', 'April', 'May', 'June'],
        'Filter by month(s):',
        INDICATOR,
        multiselect=True,
        min_selection_count=1
    )

    return [m for m, _ in selection]

def get_days():
    """Select day(s) to filter by"""
    
    selection = pick(
        ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'Filter by day(s):',
        INDICATOR,
        multiselect=True,
        min_selection_count=1
    )

    return [d for d, _ in selection]

def get_filters():
    """
    Ask user to specify city, month(s) and day(s) to analyze

    Return
    ------
        - `str` - `city`: choosen city
        - `list[str] | None` - `months`: month(s) to filter by
        - `list[str] | None` - `days`: day(s) to filter by
    """

    city, _ = pick(
        ['Chicago', 'Washington', 'New York City'],
        'Please choose a city:',
        INDICATOR,
    )

    months, days = None, None
    filt = input('Would you like to apply a filter? [month, day, both] enter to continue > ').strip().lower()
    match filt:
        case 'month':
            months = get_months()
        case 'day':
            days = get_days()
        case 'both':
            months = get_months()
            days = get_days()
        case _: None

    return city, months, days


def load_data(city: str, months: list | None, days: list | None):
    """
    Loads data for the specified city and filters by month and day if applicable.

    Args
    ----
        * (str) `city` - name of the city to analyze
        * (list) `months` - name of the month(s) to filter by, or 'None' to apply no month filter
        * (list) `days` - name of the day(s) of week to filter by, or 'None to apply no day filter

    Returns
    -------
        `df` - Pandas DataFrame containing city data filtered by month(s) and day(s)
    """

    from pathlib import Path

    file = Path('bike_share', CITY_DATA[city])
    if not file.exists():
        raise FileNotFoundError('No file found: %s' %(file))

    df = pd.read_csv(file, parse_dates=[1,2], index_col=0)
    start = df['Start Time'].dt
    df['Month'] = start.month_name()
    df['Day'] = start.day_name()
    df['Hour'] = start.hour

    if months:
        df = df[df.Month.isin(months)]
    
    if days:
        df = df[df.Day.isin(days)]

    return df

def calculate_time(func):
    """Time calculation decorator"""

    def inner1(*args, **kwargs):

        from time import time

        print('-'*45)

        begin = time()

        func(*args, **kwargs)

        end = time()
        
        LOGGER.info('Time Taken to %s -- %.2fs', func.__doc__, end - begin)

    return inner1

FORMAT_TIME = lambda x: f'{x} PM' if x > 11 else f'{x} AM'

@calculate_time
def time_stats(df: pd.DataFrame):
    """Display statistics on the most frequent times of travel."""

    # most popular month
    month = df.Month.mode()[0]

    # most popular day
    day = df.Day.mode()[0]

    # most popular hour
    hour = df.Hour.mode()[0]

    print('Busiest Month: ', month)
    print('Busiest Day: ', day)
    print('Rush Hour: ', FORMAT_TIME(hour))


@calculate_time
def station_stats(df: pd.DataFrame):
    """Display statistics on the most popular stations and trip."""

    from collections import Counter
    
    # most popular start station
    start = df['Start Station'].value_counts()

    # most popular end station
    end = df['End Station'].value_counts()

    # most frequent route
    route = Counter(zip(df['Start Station'], df['End Station'])).most_common(1)

    print(f'Most popular start station: {start.index[0]}, Count: {start.iloc[0]}')
    print(f'Most popular end station: {end.index[0]}, Count: {end.iloc[0]}')
    print(f'Most frequent route: {route[0][0][0]} -> {route[0][0][1]}, Count: {route[0][1]}')


@calculate_time
def trip_duration_stats(df: pd.DataFrame):
    """Display statistics on the total and average trip duration."""
    
    total, average = df['Trip Duration'].agg(['sum', 'mean'])

    # display total travel time
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    print('Total travel time: ', f'{hrs:02.0f}h {mins:02.0f}m {secs:02.0f}s')

    # display average trip duration
    a_mins, a_secs = divmod(average, 60)
    print('Average trip duration: ', f'{a_mins:02.0f}m {a_secs:02.0f}s')


@calculate_time
def user_stats(df: pd.DataFrame):
    """Display statistics on bikeshare users."""

    if 'User Type' in df:
       user_types_count = df['User Type'].value_counts()
       print('User Types:')
       for typ, count in user_types_count.items():
           print(f'\t{typ}: {count}')

    if 'Gender' in df:
        gender_count = df['Gender'].value_counts()
        print('Gender Count:')
        for gender, count in gender_count.items():
            print(f'\t{gender}: {count}')

    if 'Birth Year' in df:
        by = df['Birth Year']
        by_max, by_min = by.agg(['max', 'min'])
        by_common = by.mode()[0]
        print(f'Birth Year:\n\tOldest: {by_min:.0f}\n\tYoungest: {by_max:.0f}\n\tMost Common: {by_common:.0f}', )


if __name__ == '__main__':

    while True:
        city, months, days = get_filters()

        df = load_data(city, months, days)

        print(f'\nCalulating Statistics ... filters({city = }, {months = }, {days = })\n')

        time_stats(df)
        station_stats(df)
        trip_duration_stats(df)
        user_stats(df)

        raw_data = input('Would you like to view raw data [y/n]? ').strip().lower()
        if raw_data == 'y':
            rows_per_page = 5
            pd.set_option('display.max_columns', None)
            for i in range(0, len(df), rows_per_page):
                chunk = df.iloc[i:i + rows_per_page, 0:-3]
                print('\n',chunk)

                user_input = input("\nWould you like to view the next 5 rows [y/n]? ").strip().lower()
                if user_input != 'y':
                    break

        restart = input('restart program [y/n]? ').strip().lower()

        if restart != 'y':
            break

    print('Program End')