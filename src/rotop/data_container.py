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
import time
import os
import pandas as pd

from .top_runner import TopRunner
from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')


class DataContainer:
  MAX_ROW_CSV = 600
  MAX_NUM_HISTORY = 100

  def __init__(self, write_csv=False):
    now = datetime.datetime.now()
    if write_csv:
      self.csv_dir_name = now.strftime('./rotop_%Y%m%d_%H%M%S')
      os.mkdir(self.csv_dir_name)
    else:
      self.csv_dir_name = None
    self.csv_index = 0
    self.df_cpu = pd.DataFrame()
    self.df_mem = pd.DataFrame()
    self.df_cpu_history = pd.DataFrame()
    self.df_mem_history = pd.DataFrame()

  def run(self, top_runner: TopRunner, lines: list[str], num_process: int):
    if top_runner.col_range_command and top_runner.col_range_command[0] > 0:
      df_cpu_current, df_mem_current = self.create_df_from_top(top_runner, lines, num_process)
      self.df_cpu = pd.concat([self.df_cpu, df_cpu_current], axis=0)
      self.df_mem = pd.concat([self.df_mem, df_mem_current], axis=0)
      self.df_cpu_history = pd.concat([self.df_cpu_history, df_cpu_current], axis=0, ignore_index=True)
      self.df_mem_history = pd.concat([self.df_mem_history, df_mem_current], axis=0, ignore_index=True)
      if self.csv_dir_name:
        self.df_cpu.to_csv(os.path.join(self.csv_dir_name, f'cpu_{self.csv_index:03d}.csv'), index=False)
        self.df_mem.to_csv(os.path.join(self.csv_dir_name, f'mem_{self.csv_index:03d}.csv'), index=False)
        if len(self.df_cpu) >= self.MAX_ROW_CSV:
          self.df_cpu = pd.DataFrame()
          self.df_mem = pd.DataFrame()
          self.csv_index += 1
      if len(self.df_cpu_history) >= self.MAX_NUM_HISTORY:
        self.df_cpu_history = self.df_cpu_history[1:]
        self.df_mem_history = self.df_mem_history[1:]

    self.df_cpu_history = self.sort_df_in_column(self.df_cpu_history)
    self.df_mem_history = self.sort_df_in_column(self.df_mem_history)

    return self.df_cpu_history, self.df_mem_history


  def reset_history(self):
    self.df_cpu_history = pd.DataFrame()
    self.df_mem_history = pd.DataFrame()


  @staticmethod
  def sort_df_in_column(df: pd.DataFrame):
    df = df.sort_values(by=len(df)-1, axis=1, ascending=False)
    return df


  @staticmethod
  def create_df_from_top(top_runner: TopRunner, lines: list[str], num_process: int):
    # now = datetime.datetime.now()
    now = int(time.time())
    for i, line in enumerate(lines):
      if 'PID' in line:
        lines = lines[i + 1:]
        break

    process_list = []
    cpu_list = []
    mem_list = []
    for i, line in enumerate(lines):
      if i >= num_process:
        break
      pid = line[top_runner.col_range_pid[0]:top_runner.col_range_pid[1]].strip()
      command = line[top_runner.col_range_command[0]:].strip()
      process_name = str(f'{command} ({pid})')
      process_list.append(process_name)
      cpu = float(line[top_runner.col_range_CPU[0]:top_runner.col_range_CPU[1]].strip())
      cpu_list.append(cpu)
      mem = float(line[top_runner.col_range_MEM[0]:top_runner.col_range_MEM[1]].strip())
      mem_list.append(mem)

    df_cpu_current = pd.DataFrame([[now] + cpu_list], columns=['datetime'] + process_list)
    df_mem_current = pd.DataFrame([[now] + mem_list], columns=['datetime'] + process_list)

    return df_cpu_current, df_mem_current
