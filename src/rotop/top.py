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
import datetime
import psutil
import re

from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')

KiB = 1024
MiB = 1024 * 1024


class Top:
  def __init__(self, filter):
    self.filter_re = self.create_filter_re(filter)
    self.ros_re = self.create_filter_re('--ros-arg|/opt/ros')

    # Store process instance
    self.process_dict = {}

    # Store result
    self.process_info_list = []
    self.uptime_summary = {}
    self.task_summary = {}
    self.cpu_summary = {}
    self.cpu_summary_each = []
    self.memory_summary = {}
    self.swap_summary = {}


  def run(self, num_process, show_all_info=False, only_ros=False, each_cpu=False)->list[str]:
    process_info_list = []
    process_info_str_list = []
    status_count_dict = {
      psutil.STATUS_RUNNING: 0,
      psutil.STATUS_SLEEPING: 0,
      psutil.STATUS_STOPPED: 0,
      psutil.STATUS_ZOMBIE: 0,
    }
    self.update_process()
    for pid, process in self.process_dict.items():
      process_info, process_info_str = self.get_process_info(pid, process, self.filter_re, self.ros_re, show_all_info, only_ros)
      if process_info is None:
        continue
      process_info_list.append(process_info)
      process_info_str_list.append(process_info_str)
      status = process_info['status']
      if status in status_count_dict:
        status_count_dict[status] += 1

    process_info_list, process_info_str_list = self.sort_process_info_by_cpu_percent(process_info_list, process_info_str_list)
    process_info_list = process_info_list[:num_process]
    process_info_str_list = process_info_str_list[:num_process]

    uptime_summary, uptime_summary_str = self.get_uptime_summary()
    task_summary, task_summary_str = self.get_task_summary(len(self.process_dict), status_count_dict)
    cpu_summary, cpu_summary_each, cpu_summary_str, summary_each_str = self.get_cpu_summary()
    memory_summary, memory_summary_str = self.get_memory_summary()
    swap_summary, swap_summary_str = self.get_swap_summary()
    process_info_header = self.get_process_info_header(show_all_info)

    # Store result
    self.process_info_list = process_info_list
    self.uptime_summary = uptime_summary
    self.task_summary = task_summary
    self.cpu_summary = cpu_summary
    self.cpu_summary_each = cpu_summary_each
    self.memory_summary = memory_summary
    self.swap_summary = swap_summary

    # Generate string to be displayed
    top_lines = []
    top_lines.append(uptime_summary_str)
    top_lines.append(task_summary_str)
    if each_cpu:
      top_lines += summary_each_str
    else:
      top_lines.append(cpu_summary_str)
    top_lines.append(memory_summary_str)
    top_lines.append(swap_summary_str)
    top_lines.append('')
    top_lines.append(process_info_header)
    top_lines += process_info_str_list

    return top_lines


  def update_process(self):
    current_pids = psutil.pids()
    saved_pids = self.process_dict.keys()
    new_pids = list(set(current_pids) - set(saved_pids))
    deleted_pids = list(set(saved_pids) - set(current_pids))
    for pid in new_pids:
      self.process_dict[pid] = psutil.Process(pid)
    for pid in deleted_pids:
      del self.process_dict[pid]


  @staticmethod
  def get_uptime_summary():
    summary = {}
    load_average = psutil.getloadavg()
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = str(uptime).split('.')[0]
    summary['load_average_0'] = load_average[0]
    summary['load_average_1'] = load_average[1]
    summary['load_average_2'] = load_average[2]
    summary['now'] = datetime.datetime.now().strftime('%H:%M:%S')
    summary['uptime'] = uptime
    load_average_str = f'load average: {summary["load_average_0"]:.2f}, {summary["load_average_1"]:.2f}, {summary["load_average_2"]:.2f}'
    summary_str = f'top - {summary["now"]} up {summary["uptime"]}, {load_average_str}'
    return summary, summary_str


  @staticmethod
  def get_task_summary(process_num, status_count_dict):
    summary = {}
    summary['total'] = process_num
    summary['running'] = status_count_dict[psutil.STATUS_RUNNING]
    summary['sleeping'] = status_count_dict[psutil.STATUS_SLEEPING]
    summary['stopped'] = status_count_dict[psutil.STATUS_STOPPED]
    summary['zombie'] = status_count_dict[psutil.STATUS_ZOMBIE]

    summary_str = 'Tasks:'
    summary_str += f'{summary["total"]:4} total,'
    summary_str += f'{summary["running"]:4} running,'
    summary_str += f'{summary["sleeping"]:4} sleeping,'
    summary_str += f'{summary["stopped"]:4} stopped,'
    summary_str += f'{summary["zombie"]:4} zombie'

    return summary, summary_str


  @staticmethod
  def get_cpu_summary():
    cpu_times_percent = psutil.cpu_times_percent()
    summary = {}
    summary['us'] = cpu_times_percent.user
    summary['sy'] = cpu_times_percent.system
    summary['ni'] = cpu_times_percent.nice
    summary['id'] = cpu_times_percent.idle
    summary['wa'] = cpu_times_percent.iowait
    summary['hi'] = cpu_times_percent.irq
    summary['si'] = cpu_times_percent.softirq
    summary['st'] = cpu_times_percent.steal

    cpu_times_percent_list = psutil.cpu_times_percent(percpu=True)
    cpu_freq_list = psutil.cpu_freq(percpu=True)
    summary_each = []
    for i, cpu_times_percent in enumerate(cpu_times_percent_list):
      each = {}
      each['cpu_freq'] = int(cpu_freq_list[i].current)
      each['us'] = cpu_times_percent.user
      each['sy'] = cpu_times_percent.system
      each['ni'] = cpu_times_percent.nice
      each['id'] = cpu_times_percent.idle
      each['wa'] = cpu_times_percent.iowait
      each['hi'] = cpu_times_percent.irq
      each['si'] = cpu_times_percent.softirq
      each['st'] = cpu_times_percent.steal
      summary_each.append(each)

    summary_str = '%Cpu(s):'
    summary_str += f'{summary["us"]:5.1f} us,'
    summary_str += f'{summary["sy"]:5.1f} sy,'
    summary_str += f'{summary["ni"]:5.1f} ni,'
    summary_str += f'{summary["id"]:5.1f} id,'
    summary_str += f'{summary["wa"]:5.1f} wa,'
    summary_str += f'{summary["hi"]:5.1f} hi,'
    summary_str += f'{summary["si"]:5.1f} si,'
    summary_str += f'{summary["sy"]:5.1f} st'

    summary_each_str = []
    for i, each in enumerate(summary_each):
      each_str = f'%Cpu{i:<3}({each["cpu_freq"]:4.0f}):'
      each_str += f'{each["us"]:5.1f} us,'
      each_str += f'{each["sy"]:5.1f} sy,'
      each_str += f'{each["ni"]:5.1f} ni,'
      each_str += f'{each["id"]:5.1f} id,'
      each_str += f'{each["wa"]:5.1f} wa,'
      each_str += f'{each["hi"]:5.1f} hi,'
      each_str += f'{each["si"]:5.1f} si,'
      each_str += f'{each["sy"]:5.1f} st'
      summary_each_str.append(each_str)

    return summary, summary_each, summary_str, summary_each_str


  @staticmethod
  def get_memory_summary():
    virtual_memory = psutil.virtual_memory()
    summary = {}
    summary['total'] = virtual_memory.total/MiB
    summary['free'] = virtual_memory.free/MiB
    summary['used'] = virtual_memory.used/MiB
    summary['buff/cache'] = (virtual_memory.buffers+virtual_memory.cached)/MiB

    summary_str = 'MiB Mem :'
    summary_str += f'{summary["total"]:9.1f} total,'
    summary_str += f'{summary["free"]:9.1f} free,'
    summary_str += f'{summary["used"]:9.1f} used,'
    summary_str += f'{summary["buff/cache"]:9.1f} buff/cache,'

    return summary, summary_str


  @staticmethod
  def get_swap_summary():
    swap_memory = psutil.swap_memory()
    summary = {}
    summary['total'] = swap_memory.total/MiB
    summary['free'] = swap_memory.free/MiB
    summary['used'] = swap_memory.used/MiB

    summary_str = 'MiB Swap:'
    summary_str += f'{summary["total"]:9.1f} total,'
    summary_str += f'{summary["free"]:9.1f} free,'
    summary_str += f'{summary["used"]:9.1f} used,'

    return summary, summary_str


  @staticmethod
  def get_process_info_header(show_all_info: bool):
    header = ''
    header += f'{"PID":>5} '
    header += f'{"USER":<8} '
    if show_all_info:
      header += f'{"VIRT":>8} '
      header += f'{"RES":>8} '
      header += f'{"SHR":>8} '
      header += 'S '
    header += f'{"%CPU":>5} '
    header += f'{"%MEM":>5} '
    header += f'{"TIME+":>9} '
    header += 'COMMAND'
    return header


  @staticmethod
  def get_process_info(pid: int, p: psutil.Process, filter_re: re, ros_re: re, show_all_info: bool, only_ros: bool):
    try:
      name = p.name()
    except:
      name = str(pid)

    try:
      cmdline = p.cmdline()
    except:
      cmdline = name

    cmd_all = ' '.join(cmdline)
    if not filter_re.match(cmd_all):
      return None, None
    if only_ros and not ros_re.match(cmd_all):
      return None, None
    command = Top.parse_command(name, cmdline)

    try:
      username = p.username()
    except:
      username = ''

    try:
      status = p.status()
      status_char = status[0].upper()
    except:
      status_char = 'X'

    try:
      cpu_percent = p.cpu_percent()
    except:
      cpu_percent = 0

    try:
      memory_info = p.memory_info()
      vms = int(memory_info.vms/KiB)
      rss = int(memory_info.rss/KiB)
      shared = int(memory_info.shared/KiB)
    except:
      vms = rss = shared = 0

    try:
      memory_percent = p.memory_percent()
    except:
      memory_percent = 0

    try:
      ctime = datetime.timedelta(seconds=sum(p.cpu_times()))
      ctime = f'{ctime.seconds // 60 % 60}:{str(ctime.seconds % 60).zfill(2)}.{str(ctime.microseconds)[:2]}'
    except:
      ctime = ''

    process_info = {}
    process_info['pid'] = pid
    process_info['username'] = username
    process_info['vms'] = vms
    process_info['rss'] = rss
    process_info['shared'] = shared
    process_info['status'] = status_char
    process_info['cpu_percent'] = cpu_percent
    process_info['memory_percent'] = memory_percent
    process_info['ctime'] = ctime
    process_info['command'] = command

    process_info_str = ''
    process_info_str += f'{process_info["pid"]:>5} '
    process_info_str += f'{process_info["username"]:<8} '
    if show_all_info:
      process_info_str += f'{process_info["vms"]:>8} '
      process_info_str += f'{process_info["rss"]:>8} '
      process_info_str += f'{process_info["shared"]:>8} '
      process_info_str += f'{process_info["status"]} '
    process_info_str += f'{process_info["cpu_percent"]:5.1f} '
    process_info_str += f'{process_info["memory_percent"]:5.1f} '
    process_info_str += f'{process_info["ctime"]:>9} '
    process_info_str += process_info['command']

    return process_info, process_info_str


  @staticmethod
  def sort_process_info_by_cpu_percent(process_info_list, process_info_str_list):
    process_info_merged_list = [[process_info, process_info_str] for process_info, process_info_str in zip(process_info_list, process_info_str_list)]
    process_info_merged_list = sorted(process_info_merged_list, key=lambda process_info_merged: process_info_merged[0]['cpu_percent'], reverse=True)
    process_info_list = [process_info for process_info, _ in process_info_merged_list]
    process_info_str_list = [process_info_str for _, process_info_str in process_info_merged_list]
    return process_info_list, process_info_str_list


  @staticmethod
  def create_filter_re(filter_str):
    if '.*' not in filter_str:
      filter_str = '.*' + filter_str + '.*'
    filter_re = re.compile(filter_str)
    return filter_re


  @staticmethod
  def parse_command_ros(name, cmdline):
    node = None
    ns = None
    for i, arg in enumerate(cmdline):
      if '__node' in arg:
        node = cmdline[i+1]
      if '__ns' in arg:
        ns = cmdline[i+1]

    if node:
      command = node
    else:
      command = name

    if ns:
      command += ', ' + ns

    return command


  @staticmethod
  def parse_command_arg(name, cmdline):
    """
    e.g.
    '/very/long/path/exe /very/long/path/input_file --option opt' -> 'exe input_file'
    '/very/long/path/exe --option opt /very/long/path/input_file' -> 'exe input_file'
    '/usr/local/bin/python3 /very/long/path/hoge.py' -> 'python3 hoge.py'
    'ros2 bag play ooo' -> 'python3 ros2 bag play ooo'
    """
    arg = ''
    if len(cmdline[1]) > 0 and cmdline[1][0] != '-':
      arg = cmdline[1]
    elif len(cmdline[-1]) > 0 and cmdline[-1][0] != '-':
      arg = cmdline[-1]

    # arg could be very long if it's a file name
    arg = arg.split('/')[-1]

    # For ROS cli
    # e.g. 'ros2 bag play ooo' -> 'python3 ros2 bag play ooo'
    if arg == 'ros2':
      arg += ' ' + ' '.join(cmdline[2:5])

    return name + ' ' + arg


  @staticmethod
  def parse_command(name, cmdline):
    param_for_ros2 = ['__node', '__ns']
    cmd_all = ' '.join(cmdline)
    if len(cmdline) > 1:
      command = Top.parse_command_arg(name, cmdline)
    elif any(item in cmd_all for item in param_for_ros2):
        command = Top.parse_command_ros(name, cmdline)
    else:
        command = name
    return command
