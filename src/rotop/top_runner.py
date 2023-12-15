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
import atexit
import pexpect
import re
import signal

from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')


class TopRunner:
  def __init__(self, interval, filter):
    self.child = pexpect.spawn(f'top -cb -d {interval} -o %CPU -w 512')
    self.filter_re = self.create_filter_re(filter)
    self.ros_re = self.create_filter_re('--ros-arg|/opt/ros')
    self.col_range_list_to_display = None
    self.col_range_pid = None
    self.col_range_CPU = None
    self.col_range_MEM = None
    self.col_range_command = None
    self.next_after = ''


  def __del__(self):
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # ignore ctrl-c while closing
    self.child.close()


  def run(self, max_num_process, show_all=False, only_ros=False):
    # get the result string of top command
    self.child.expect(r'top - .*load average:')
    before = self.child.before
    previous_after = self.next_after
    self.next_after = self.child.after
    if before == '' or previous_after == '' or self.next_after == '':
      return None, None
    top_str = (previous_after + before).decode('utf-8')
    orgial_lines = top_str.splitlines()

    result_lines = []
    result_show_all_lines = []
    row_process_info = 0

    # System Information
    for line in orgial_lines:
      result_lines.append(line)
      result_show_all_lines.append(line)
      if 'PID' in line:
        break

    # get layout information from process header line
    row_process_info = len(result_lines)
    process_header_org = result_lines[-1]
    self.analyze_cols(process_header_org, show_all)

    process_header = ''
    for range in self.col_range_list_to_display:
      process_header += process_header_org[range[0]:range[1]]
    result_lines[-1] = process_header

    # Process Information
    for line in orgial_lines[row_process_info:]:
      if self.col_range_command and self.col_range_command[0] > 0 and len(line) > self.col_range_command[0]:
        process_info_org = line[:self.col_range_command[0]]
        process_info = ''
        for range in self.col_range_list_to_display:
          process_info += process_info_org[range[0]:range[1]]
        command_str = line[self.col_range_command[0]:]
        if not self.filter_re.match(command_str):
          continue
        if only_ros and not self.ros_re.match(command_str):
          continue
        command_str = self.parse_command_str(command_str)

        line = process_info + command_str
        show_all_line = process_info_org + command_str

        result_lines.append(line)
        result_show_all_lines.append(show_all_line)
        if len(result_lines) >= row_process_info + max_num_process:
          break

    return result_lines, result_show_all_lines


  def analyze_cols(self, process_header: str, show_all: bool):
    if self.col_range_command is None or self.col_range_command[0] == -1:
      self.col_range_list_to_display = self.get_col_range_list_to_display(process_header, show_all)
      self.col_range_pid = TopRunner.get_col_range_PID(process_header)
      self.col_range_CPU = TopRunner.get_col_range_CPU(process_header)
      self.col_range_MEM = TopRunner.get_col_range_MEM(process_header)
      self.col_range_command = TopRunner.get_col_range_command(process_header)
    return



  @staticmethod
  def create_filter_re(filter_str):
    if '.*' not in filter_str:
      filter_str = '.*' + filter_str + '.*'
    filter_re = re.compile(filter_str)
    return filter_re


  @staticmethod
  def get_row_start_list(lines: list[str])->list[int]:
    row_list = []
    for i, line in enumerate(lines):
      if 'top' in line and 'load average' in line:
        row_list.append(i)
    return row_list


  @staticmethod
  def get_col_range_command(process_info_header_line: str):
    start_col = process_info_header_line.find('COMMAND')
    end_col = len(process_info_header_line) - 1
    return (start_col, end_col)


  @staticmethod
  def get_col_range_PID(process_info_header_line: str):
    start_col = 0
    end_col = process_info_header_line.find('PID') + len('PID')
    return (start_col, end_col)


  @staticmethod
  def get_col_range_CPU(process_info_header_line: str):
    start_col = process_info_header_line.find('SHR S') + len('SHR S')
    end_col = process_info_header_line.find('%CPU') + len('%CPU')
    return (start_col, end_col)


  @staticmethod
  def get_col_range_MEM(process_info_header_line: str):
    start_col = process_info_header_line.find('%CPU') + len('%CPU')
    end_col = process_info_header_line.find('%MEM') + len('%MEM')
    return (start_col, end_col)


  @staticmethod
  def get_col_range_list_to_display(process_info_header_line: str, show_all=False):
    range_list = []

    if show_all:
      range_list.append((0, len(process_info_header_line)))
    else:
      start_col = 0
      end_col = process_info_header_line.find('PID') + len('PID')
      range_list.append((start_col, end_col))

      start_col = process_info_header_line.find('NI') + len('NI')
      end_col = process_info_header_line.find('%MEM') + len('%MEM')
      range_list.append((start_col, end_col))

      start_col = process_info_header_line.find('COMMAND') - 1
      end_col = len(process_info_header_line)
      range_list.append((start_col, end_col))

    return range_list


  @staticmethod
  def parse_component_container_command(command):
    cmd = command.split()[0].split('/')[-1]
    idx_node = command.find('__node')
    if idx_node > 0:
      node = command[idx_node:].split()[0].split('=')[-1]
      cmd = node
    idx_ns = command.find('__ns')
    if idx_ns > 0:
      ns = command[idx_ns:].split()[0].split('=')[-1]
      # cmd = cmd + ', ' + node + ', ' + ns
      cmd += ', ' + ns
    return cmd


  @staticmethod
  def parse_python_command(command):
    cmd_list = command.split()
    cmd = cmd_list[0].split('/')[-1]
    if len(cmd_list) > 1:
      if cmd_list[1][0] == '-':
          python_file = cmd_list[-1]
      else:
          python_file = cmd_list[1]
      python_file = python_file.split('/')[-1]

      ros2_option = ''
      if 'ros2' == python_file:
          ros2_option = ' '.join(cmd_list[2:5])

      cmd = cmd + ' ' + python_file + ' ' + ros2_option
    return cmd


  @staticmethod
  def parse_command_str(command):
    param_for_ros2 = ['__node', '__ns']
    if '[' == command[0]:
        # kernel process
        command = command
    elif any(item in command for item in param_for_ros2):
        command = TopRunner.parse_component_container_command(command)
    elif 'python' in command:
        command = TopRunner.parse_python_command(command)
    else:
        # normal process
        command = command.split()[0].split('/')[-1]
    return command