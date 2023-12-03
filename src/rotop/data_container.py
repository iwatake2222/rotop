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

from .top import Top
from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')


class DataContainer:
  def __init__(self, write_csv: bool, max_row_csv: int=600, max_num_history: int=100):
    self.max_row_csv = max_row_csv
    self.max_num_history = max_num_history
    now = datetime.datetime.now()
    if write_csv:
      self.csv_dir_name = now.strftime('./rotop_%Y%m%d_%H%M%S')
      os.mkdir(self.csv_dir_name)
    else:
      self.csv_dir_name = None
    self.csv_index = 0
    self.df_cpu_csv = pd.DataFrame()
    self.df_mem_csv = pd.DataFrame()
    self.df_cpu_graph = pd.DataFrame()
    self.df_mem_graph = pd.DataFrame()

  def run(self, top: Top):
    df_cpu_current, df_mem_current = self.create_df_from_top(top)

    self.df_cpu_csv = pd.concat([self.df_cpu_csv, df_cpu_current], axis=0)
    self.df_mem_csv = pd.concat([self.df_mem_csv, df_mem_current], axis=0)
    self.df_cpu_graph = pd.concat([self.df_cpu_graph, df_cpu_current], axis=0, ignore_index=True)
    self.df_mem_graph = pd.concat([self.df_mem_graph, df_mem_current], axis=0, ignore_index=True)
    if self.csv_dir_name:
      self.df_cpu_csv.to_csv(os.path.join(self.csv_dir_name, f'cpu_{self.csv_index:03d}.csv'), index=False, float_format='%.1f')
      self.df_mem_csv.to_csv(os.path.join(self.csv_dir_name, f'mem_{self.csv_index:03d}.csv'), index=False, float_format='%.1f')
      if len(self.df_cpu_csv) >= self.max_row_csv:
        self.df_cpu_csv = pd.DataFrame()
        self.df_mem_csv = pd.DataFrame()
        self.csv_index += 1
    if len(self.df_cpu_graph) >= self.max_num_history:
      self.df_cpu_graph = self.df_cpu_graph[1:]
      self.df_mem_graph = self.df_mem_graph[1:]

    self.df_cpu_graph = self.sort_df_in_column(self.df_cpu_graph)
    self.df_mem_graph = self.sort_df_in_column(self.df_mem_graph)

    return self.df_cpu_graph, self.df_mem_graph


  @staticmethod
  def sort_df_in_column(df: pd.DataFrame):
    df = df.sort_values(by=len(df)-1, axis=1, ascending=False)
    columns = list(df)
    columns.remove('time')
    if 'total' in columns:
      columns.remove('total')
      df = df.reindex(columns=['time', 'total'] + columns)
    else:
      df = df.reindex(columns=['time'] + columns)
    return df


  def create_df_from_top(self, top: Top):
    process_info_list = top.process_info_list
    process_list = []
    cpu_list = []
    mem_list = []
    for process_info in process_info_list:
      process_name = str(f'{process_info["command"]} ({process_info["pid"]})')
      process_list.append(process_name)
      cpu_list.append(process_info['cpu_percent'])
      mem_list.append(process_info['memory_percent'])

    total_cpu_usage = sum([100 - each['id'] for each in top.cpu_summary_each])

    now = int(time.time())
    df_cpu_current = pd.DataFrame([[now] + [total_cpu_usage] + cpu_list], columns=['time'] + ['total'] + process_list)
    df_mem_current = pd.DataFrame([[now] + mem_list], columns=['time'] + process_list)

    return df_cpu_current, df_mem_current


  def reset_history(self):
    self.df_cpu_graph = pd.DataFrame()
    self.df_mem_graph = pd.DataFrame()
