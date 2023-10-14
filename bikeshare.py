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

INDICATOR = '\u20d7'

def get_months():
    selection = pick(
        ['January', 'February', 'March', 'April', 'May', 'June'],
        'Filter by month(s):',
        INDICATOR,
        multiselect=True,
        min_selection_count=1
    )

    return [m for m, _ in selection]

def get_days():
    selection = pick(
        ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'Filter by day(s):',
        INDICATOR,
        multiselect=True,
        min_selection_count=1
    )

    return [d for d, _ in selection]

def get_filters():

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

    def inner1(*args, **kwargs):

        from time import time

        begin = time()
        func(*args, **kwargs)
        end = time()
        
        # print('-'*45)
        # LOGGER.info('Time Taken to %s -- %.2fs', func.__doc__, end - begin)

    return inner1

FORMAT_TIME = lambda x: f'{x} PM' if x > 11 else f'{x} AM'

@calculate_time
def time_stats(df: pd.DataFrame, buffer: list):
    """Display statistics on the most frequent times of travel."""

    # most popular month
    month = df.Month.mode()[0]

    # most popular day
    day = df.Day.mode()[0]

    # most popular hour
    hour = df.Hour.mode()[0]

    buffer.append('Time Statistics')
    buffer.append('---------------')
    buffer.append(f'Busiest Month: {month}')
    buffer.append(f'Busiet Day: {day}')
    buffer.append(f'Rush Hour: {FORMAT_TIME(hour)}')


@calculate_time
def station_stats(df: pd.DataFrame, buffer: list):
    """Display statistics on the most popular stations and trip."""

    from collections import Counter
    
    # most popular start station
    start = df['Start Station'].value_counts()

    # most popular end station
    end = df['End Station'].value_counts()

    # most frequent route
    route = Counter(zip(df['Start Station'], df['End Station'])).most_common(1)

    buffer.append('Station Statictics')
    buffer.append('------------------')
    buffer.append(f'Most popular start station: {start.index[0]}, Count: {start.iloc[0]}')
    buffer.append(f'Most popular end station: {end.index[0]}, Count: {end.iloc[0]}')
    buffer.append(f'Most frequent route: {route[0][0][0]} -> {route[0][0][1]}, Count: {route[0][1]}')


@calculate_time
def trip_duration_stats(df: pd.DataFrame, buffer: list):
    """Display statistics on the total and average trip duration."""
    from datetime import timedelta
    
    total, average, max_ = df['Trip Duration'].agg(['sum', 'mean', 'max'])

    # display total travel time
    dt_total = timedelta(seconds=total)

    # display average trip duration
    dt_avg = timedelta(seconds=average)

    # display longest trip
    dt_max = timedelta(seconds=max_)

    buffer.append('Trip Duration Statistics')
    buffer.append('------------------------')
    buffer.append(f'Total trip time: {dt_total}')
    buffer.append(f'Average trip duration: {dt_avg}')
    buffer.append(f'Longest trip: {dt_max}')


@calculate_time
def user_stats(df: pd.DataFrame, buffer: list):
    """Display statistics on bikeshare users."""

    buffer.append('Users Breakdown')
    buffer.append('---------------')

    if 'User Type' in df:
       user_types_count = df['User Type'].value_counts()
       buffer.append('Type:')
       for typ, count in user_types_count.items():
           buffer.append(f'\t{typ}: {count}')

    if 'Gender' in df:
        gender_count = df['Gender'].value_counts()
        buffer.append('Gender:')
        for gender, count in gender_count.items():
            buffer.append(f'\t{gender}: {count}')

    if 'Birth Year' in df:
        by = df['Birth Year']
        by_max, by_min = by.agg(['max', 'min'])
        by_common = by.mode()[0]
        buffer.append('Birth Year:')
        buffer.append(f'\tOldest: {by_min:.0f}')
        buffer.append(f'\tYoungest: {by_max:.0f}')
        buffer.append(f'\tMost Common: {by_common:.0f}')


if __name__ == '__main__':

    while True:
        data = []
        city, months, days = get_filters()

        df = load_data(city, months, days)

        print(f'\nCalulating Statistics ... filters({city = }, {months = }, {days = })\n')

        time_stats(df, data)
        station_stats(df, data)
        trip_duration_stats(df, data)
        user_stats(df, data)

        current_line = 0
        while current_line < len(data):
            for i in range(current_line, min(current_line + 5, len(data))):
                print(data[i])

            inp = input("\nPress 'Enter' to view next 5 lines > ")
            if inp:
                break

            print(' ')
            current_line += 5

        restart = input('restart program [y/n]? ').strip().lower()

        if restart != 'y':
            break

    print('Program End')