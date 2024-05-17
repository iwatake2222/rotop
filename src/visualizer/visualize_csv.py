# Copyright 2024 iwatake2222
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
from distutils.util import strtobool
from pathlib import Path
import argparse
import logging
import pandas as pd
import os
import sys
import flask
from bokeh.models import DatetimeTickFormatter, HoverTool, Legend
from bokeh.plotting import figure, save
from bokeh.resources import CDN
from bokeh.palettes import Category10, Category20


logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
app = flask.Flask(__name__)


def parse_args():
  parser = argparse.ArgumentParser(
    description=f'rotop csv visualizer')
  parser.add_argument('csv_path', nargs=1, type=str)
  parser.add_argument('--max_process_num', type=int, default=30, help="Max num to display process.")
  args = parser.parse_args()
  args.csv_path = args.csv_path[0]
  logger.debug(f'csv_path: {args.csv_path}')
  logger.debug(f'max_process_num: {args.max_process_num}')
  return args


def find_csv_files_from_filename(csv_path: Path) -> list[Path]:
  prefix = '_'.join(str(csv_path.stem).split('_')[:-1])
  number_base = str(csv_path.stem).split('_')[-1:][0]
  file_list = []
  for i in range(999):
    number = f'{i:0{len(number_base)}}'
    filename = csv_path.parent.joinpath(prefix + '_' + number + csv_path.suffix)
    file = Path(filename)
    if file.exists():
      file_list.append(file)
    else:
      break
  return file_list


def find_csv_files_from_dir(csv_path: Path) -> dict[str, list[Path]]:
  prefix_name_list = []
  file_list = []
  for file in csv_path.iterdir():
    if file.suffix != '.csv':
      continue
    prefix = '_'.join(str(file.stem).split('_')[:-1])
    if prefix not in prefix_name_list:
      prefix_name_list.append(prefix)
      file_list.append(file)
  file_dict = {}
  for i, prefix_name in enumerate(prefix_name_list):
    file_dict[prefix_name] = find_csv_files_from_filename(file_list[i])
  return file_dict


def find_csv_files_from_path(csv_path: Path) -> dict[str, list[Path]]:
  if csv_path.is_dir():
    return find_csv_files_from_dir(csv_path)
  elif csv_path.is_file():
    if csv_path.suffix != '.csv':
      return None
    prefix = '_'.join(str(csv_path.stem).split('_')[:-1])
    return {prefix: find_csv_files_from_filename(csv_path)}
  else:
    return None


def create_df_from_csv_files(file_list: list[Path]):
  df_total = pd.DataFrame()
  for file in file_list:
    df = pd.read_csv(file, index_col=0)
    df_total = pd.concat([df_total, df], axis=0)
  df_total = df_total.sort_index()

  def unixtime_to_datetime(unix_time):
      return pd.to_datetime(unix_time, unit='s')
  df_total.index = df_total.index.map(unixtime_to_datetime)

  if 'idle' in df_total.columns:
    df_total['idle'] = 100 - df_total['idle']
    df_total = df_total.rename(columns={'idle': 'total'})

  return df_total


def generate_color_from_integer(number):
  index = number % len(generate_color_from_integer.palette)
  return generate_color_from_integer.palette[index]
generate_color_from_integer.palette = Category10[10] + Category20[20]


def create_graph(dest_dir: Path, name: str, unit: str, df: pd.DataFrame, width=1200, height=400) -> Path:
  # workaround: Overwrite date time as UTC with time difference because it looks Bokeh doesn't care time　zone appropriately
  fix_time_zone = pd.Timedelta(hours=9)
  y_axis_label = f'{name} [{unit}]'
  line_plot = figure(width=width, frame_height=height, title=f'{name}', x_axis_label=None, y_axis_label=y_axis_label, x_axis_type='datetime')
  legend_list = []
  for i, col_name in enumerate(df.columns):
    item = line_plot.line(x=df.index + fix_time_zone, y=df[col_name], line_width=2, color=generate_color_from_integer(i), name=col_name, legend_label=col_name)
    legend_list.append((col_name, [item]))
  line_plot.x_range.start = df.index[0] + fix_time_zone
  line_plot.y_range.start = 0

  line_plot.xaxis.formatter = DatetimeTickFormatter(
                                days=f"%m/%d %H:%M",
                                months="%m/%d %H:%M",
                                hours="%m/%d %H:%M",
                                minutes="%m/%d %H:%M:%S",
                                minsec="%m/%d %H:%M:%S",
                                seconds="%m/%d %H:%M:%S")

  legend = Legend(items=legend_list, click_policy='mute', location='left')
  if len(df.columns) > 10:
    line_plot.legend.visible = False
    line_plot.add_layout(legend, 'below')
  hover = HoverTool(tooltips=[('Label', '$name'), ('Value', '@y')])
  line_plot.add_tools(hover)

  graph_file_path = dest_dir.joinpath(dest_dir).joinpath(name.replace(' ', '_').lower() + '.html')
  Path.mkdir(graph_file_path.parent, exist_ok=True)
  save(line_plot, title=name, filename=graph_file_path, resources=CDN)
  return graph_file_path


class Stats:
  def __init__(self, name: str, mean: float, std: float, max: float):
    self.name: str = name
    self.mean: float = mean
    self.std: float = std
    self.max: float = max


def create_page(dest_file: Path, title: str, unit: str, graph_file_path: Path, stats_list: list[Stats]):
  template_path = Path(__file__).parent.joinpath('visualize_csv.html')
  graph_file_path = graph_file_path.relative_to(dest_file.parent)

  with app.app_context():
    with open(template_path, 'r', encoding='utf-8') as f_html:
      template_string = f_html.read()
      rendered = flask.render_template_string(
        template_string,
        title=title,
        unit=unit,
        graph_file_path=str(graph_file_path),
        stats_list=stats_list
      )

    with open(dest_file, 'w', encoding='utf-8') as f_html:
      f_html.write(rendered)


def main():
  args = parse_args()
  csv_path = Path(args.csv_path)
  csv_file_dict = find_csv_files_from_path(csv_path)
  if csv_file_dict is None:
    logger.error('Unable to find csv file')

  rotop_log_dir = csv_path if csv_path.is_dir() else csv_path.parent
  dest_dir = rotop_log_dir

  for prefix, csv_file_list in csv_file_dict.items():
    stats_list: list[Stats] = []
    df = create_df_from_csv_files(csv_file_list)
    graph_file_path = create_graph(dest_dir, prefix, '%', df)
    for col_name in df.columns:
      df_for_item = df[col_name]
      stats_list.append(Stats(col_name, df_for_item.mean(), df_for_item.std(), df_for_item.max()))
    stats_list = sorted(stats_list, key=lambda stats: stats.mean, reverse=True)
    create_page(dest_dir.joinpath(f'index_{prefix}.html'), f'{str(rotop_log_dir.stem)}_{prefix}', '%', graph_file_path, stats_list)


if __name__ == '__main__':
  main()
