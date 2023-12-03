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
import curses
import time
from .data_container import DataContainer
from .top import Top
from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')


def main_curses(stdscr, args):
  if stdscr:
    curses.use_default_colors()
    curses.curs_set(0)
    stdscr.timeout(args.interval * 1000)

  top = Top(args.filter)
  data_container = DataContainer(args.csv)

  each_cpu = False

  while True:
    if stdscr:
      max_y, max_x = stdscr.getmaxyx()
    else:
      max_y, max_x = 1000, 1000

    top_lines = top.run(num_process=args.num_process, show_all_info=max_x>160, only_ros=args.only_ros, each_cpu=each_cpu)
    _ = data_container.run(top)

    if stdscr:
      stdscr.clear()
      for i, line in enumerate(top_lines):
        if i >= max_y - 1:
          break
        stdscr.addstr(i, 0, line[:max_x])

      stdscr.refresh()
      key = stdscr.getch()
      if key == ord('q'):
        break
      elif key == ord('1'):
        each_cpu = not each_cpu

    else:
      print('\n'.join(top_lines))
      time.sleep(args.interval)


def main_cui(args):
  curses.wrapper(main_curses, args)
  # main_curses(None, args)  # For debug
