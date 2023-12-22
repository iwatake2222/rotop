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
from __future__ import annotations
import argparse
from .main_cui import main_cui
from .main_gui import main_gui
from .utility import create_logger
try:
  from ._version import version
except:
  from .version_dummy import version


logger = create_logger(__name__, log_filename='rotop.log')


def parse_args():
  parser = argparse.ArgumentParser(
    description=f'rotop: top for ROS 2, version {version}')
  parser.add_argument('-d', '--interval', type=float, default=1, help="Update interval in seconds. Similar to the -d option of top.")
  parser.add_argument('--filter', type=str, default='.*', help="Only show processes fitting to this regular expression.")
  parser.add_argument('--csv', action='store_true', default=False, help="Activate saving data to csv file.")
  parser.add_argument('--gui', action='store_true', default=False, help="Use GUI including plotting of CPU loads.")
  parser.add_argument('--num_process', type=int, default=30, help="Maximum number of processes that will be shown.")
  parser.add_argument('--only_ros', action='store_true', default=False, help="List only ROS 2 node processes.")

  args = parser.parse_args()

  logger.debug(f'filter: {args.filter}')
  logger.debug(f'csv: {args.csv}')
  logger.debug(f'gui: {args.gui}')
  logger.debug(f'num_process: {args.num_process}')
  logger.debug(f'only_ros: {args.only_ros}')

  return args


def main():
  args = parse_args()
  if args.gui:
    main_gui(args)
  else:
    main_cui(args)
