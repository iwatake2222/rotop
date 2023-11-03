# Copyright 2023 iwatake2222
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import curses
import time

from .data_container import DataContainer
from .top_runner import TopRunner
from .gui_main import gui_main
from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')


def main_curses(stdscr, args):
  curses.use_default_colors()
  # curses.init_color(0, 0, 0, 0)
  curses.curs_set(0)
  stdscr.timeout(100)

  top_runner = TopRunner(args.filter, args.interval)
  data_container = DataContainer(args.csv)

  try:
    while True:
      max_y, max_x = stdscr.getmaxyx()
      result_lines, result_show_all_lines = top_runner.run(max(max_y, args.num_process), max_x>160)
      if result_show_all_lines is None:
        time.sleep(0.1)
        continue

      _ = data_container.run(top_runner, result_show_all_lines, args.num_process)

      stdscr.clear()
      for i, line in enumerate(result_lines):
        if i >= max_y - 1:
          break
        stdscr.addstr(i, 0, line[:max_x])

      stdscr.refresh()
      key = stdscr.getch()
      if key == ord('q'):
        break
  except KeyboardInterrupt:
    exit(0)


def parse_args():
  parser = argparse.ArgumentParser(
    description='rotop: top for ROS 2')
  parser.add_argument('--interval', type=float, default=2)
  parser.add_argument('--filter', type=str, default='.*')
  parser.add_argument('--csv', action='store_true', default=False)
  parser.add_argument('--gui', action='store_true', default=False)
  parser.add_argument('--num_process', type=int, default=30)
  args = parser.parse_args()

  logger.debug(f'filter: {args.filter}')
  logger.debug(f'csv: {args.csv}')
  logger.debug(f'gui: {args.gui}')
  logger.debug(f'num_process: {args.num_process}')

  return args


def main():
  args = parse_args()
  if args.gui:
    gui_main(args)
  else:
    curses.wrapper(main_curses, args)