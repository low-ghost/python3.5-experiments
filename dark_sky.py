import asyncio
import json
import aiohttp
import time
from aiohttp import web
import geopy
from geopy.geocoders import Nominatim
import argparse
import functools
from typing import List, Dict, Any, Union

def parse_args() -> argparse.Namespace:	
  parser = argparse.ArgumentParser()
  parser.add_argument('-a', '--address', help='enter an address to get long and lat', type=str)
  parser.add_argument('-k', '--key', help='api key for darksky', type=str)
  parser.add_argument('-v', '--verbose', help='verbose hourly and daily reports', action="store_true")
  return parser.parse_args()

def get_location(args: argparse.Namespace) -> geopy.location.Location:
  geolocator = Nominatim()
  return geolocator.geocode(args.address)
  
async def dark_sky(args: argparse.Namespace, client: aiohttp.client.ClientSession, location: geopy.location.Location) -> Any:
   url = 'https://api.forecast.io/forecast/{}/{},{}'.format(args.key, location.latitude, location.longitude)
   async with client.get(url) as response:
     assert response.status == 200
     return await response.read(decode=True)

def pluck(args: List[str], filled_dict: Dict, to_dict = False) -> Union[List, Dict]:
  if to_dict:
    return {arg: filled_dict.get(arg) for arg in args}
  return (filled_dict.get(arg) for arg in args)

def format_header(title: str, summary: str) -> str:
  return '\n{}: \n\t{}'.format(title, summary)

def format_summary_block(title, data: Dict) -> str:
  summary, temp, precipType, precipProb = pluck(['summary', 'temperature', 'precipType', 'precipProbability'], data)
  header = format_header(title, summary)
  return '{} and {} degrees\n\tPossibility of {}: {}'.format(header, temp, precipType if precipType else 'precipitation', precipProb)

def format_minutely(minutely: Dict) -> str:
  return '\t{}'.format(minutely['summary'])


def format_hourly(args: argparse.Namespace, hourly: Dict) -> str:
  summary, data = pluck(['summary', 'data'], hourly)
  header = format_header('Hourly', summary)
  if not args.verbose:
    return header
  return header + functools.reduce(lambda state, next: state + format_summary_block(get_hour(next.get('time')), next), data, '')

def get_local_time(formatStr: str, timestamp) -> str:
  return time.strftime(formatStr, time.localtime(timestamp))

get_clock_time = functools.partial(get_local_time, '%I:%M %p')  
get_hour = functools.partial(get_local_time, '%a %I O\'Clock %p')

def format_daily_verbose(day: Dict) -> str:
  plucked = pluck([
    'time', 'summary', 'temperatureMin',
    'temperatureMax', 'precipType', 'precipProbability',
    'sunriseTime', 'sunsetTime'
  ], day, True)
  return """
        {date}:
                {summary}
                Between {temperatureMin} and {temperatureMax} degrees
                Possibility of {precip}: {precipProbability}
                Sunrise: {sunrise}, Sunset: {sunset} 
  """.format(
    **plucked,
    date = get_local_time("%A %b %d", plucked['time']),
    sunrise = get_clock_time(plucked['sunriseTime']),
    sunset = get_clock_time(plucked['sunsetTime']),
    precip = plucked['precipType'] if plucked['precipType'] is not None else 'precipitation')

def format_daily(args: argparse.Namespace, daily: Dict) -> str:
  summary, data = pluck(['summary', 'data'], daily)
  header = format_header('Daily', summary)
  if not args.verbose:
    return header
  return header + functools.reduce(lambda state, next: state + format_daily_verbose(next), data, '')

def print_utf8(s: str) -> None:
  print(s.encode('ascii', 'replace').decode('ascii'))

def print_to_console(args: argparse.Namespace, currently: Dict, minutely: Dict, hourly: Dict, daily: Dict) -> None:
  return [print_utf8(x) for x in [
    format_summary_block('currently', currently),
    format_minutely(minutely),
    format_hourly(args, hourly),
    format_daily(args, daily)
  ]]

def main() -> None:
  args = parse_args()
  location = get_location(args)
  loop = asyncio.get_event_loop()
  client = aiohttp.ClientSession(loop=loop)
  content = loop.run_until_complete(dark_sky(args, client, location))
  print_to_console(args, *pluck(['currently', 'minutely', 'hourly', 'daily'], content));
  client.close()

if __name__ == '__main__':
  main()
