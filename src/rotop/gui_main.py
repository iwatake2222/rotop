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
import pandas as pd
import threading
import time
import dearpygui.dearpygui as dpg

from .data_container import DataContainer
from .top_runner import TopRunner
from .utility import create_logger


logger = create_logger(__name__, log_filename='rotop.log')

g_reset_history_df = False  # todo: add lock

COLOR_MAP = (
  # matplotlib.cm.tab20
  (31, 119, 180),
  (174, 199, 232),
  (256, 127, 14),
  (256, 187, 120),
  (44, 160, 44),
  (152, 223, 138),
  (214, 39, 40),
  (256, 152, 150),
  (148, 103, 189),
  (197, 176, 213),
  (140, 86, 75),
  (196, 156, 148),
  (227, 119, 194),
  (247, 182, 210),
  (127, 127, 127),
  (199, 199, 199),
  (188, 189, 34),
  (219, 219, 141),
  (23, 190, 207),
  (158, 218, 229),
  # matplotlib.cm.tab20b
  (57, 59, 121),
  (82, 84, 163),
  (107, 110, 207),
  (156, 158, 222),
  (99, 121, 57),
  (140, 162, 82),
  (181, 207, 107),
  (206, 219, 156),
  (140, 109, 49),
  (189, 158, 57),
  (231, 186, 82),
  (231, 203, 148),
  (132, 60, 57),
  (173, 73, 74),
  (214, 97, 107),
  (231, 150, 156),
  (123, 65, 115),
  (165, 81, 148),
  (206, 109, 189),
  (222, 158, 214),
)


class GuiView:
  def __init__(self):
    self.is_exit = False
    self.pause = False  # todo: add lock
    self.plot_is_cpu = True
    self.dpg_plot_axis_x_id = None
    self.dpg_plot_axis_y_id = None
    self.color_dict = {}
    self.theme_dict = {}


  def exit(self):
    self.is_exit = True


  def start_dpg(self):
    dpg.create_context()
    dpg.create_viewport(title='rotop', width=800, height=600)
    dpg.setup_dearpygui()

    with dpg.window(label='window', no_collapse=True, no_title_bar=True, no_move=True, no_resize=True) as self.dpg_window_id:
      with dpg.group(horizontal=True):
        self.dpg_button_cpumem = dpg.add_button(label='CPU/MEM', callback=self.cb_button_cpumem)
        self.dpg_button_reset = dpg.add_button(label='RESET', callback=self.cb_button_reset)
        self.dpg_button_pause = dpg.add_button(label='PAUSE', callback=self.cb_button_pause)
        dpg.add_text('Help(?)')
      with dpg.tooltip(dpg.last_item()):
        dpg.add_text('- CLick "Reset" to clear graph and history.')
      with dpg.plot(label=self.get_plot_title(), use_local_time=True, no_title=True) as self.dpg_plot_id:
        self.dpg_plot_axis_x_id =  dpg.add_plot_axis(dpg.mvXAxis, label='datetime', time=True)
      self.dpg_text = dpg.add_text()

    dpg.set_viewport_resize_callback(self.cb_resize)
    self.cb_resize(None, [None, None, dpg.get_viewport_width(), dpg.get_viewport_height()])
    dpg.show_viewport()
    
    # Manually control FPS (10fps), otherwise FPS becomes very high, which causes high CPU load
    # dpg.start_dearpygui()
    while dpg.is_dearpygui_running() and not self.is_exit:
      time.sleep(0.1)
      dpg.render_dearpygui_frame()

    dpg.destroy_context()


  def get_plot_title(self):
    return 'CPU [%]' if self.plot_is_cpu else 'MEM [%]'


  def cb_button_cpumem(self, sender, app_data, user_data):
    self.plot_is_cpu = not self.plot_is_cpu
    dpg.set_item_label(self.dpg_plot_id, self.get_plot_title())


  def cb_button_reset(self, sender, app_data, user_data):
    global g_reset_history_df
    g_reset_history_df = True
    self.color_dict = {}
    self.theme_dict = {}


  def cb_button_pause(self, sender, app_data, user_data):
    self.pause = not self.pause


  def cb_resize(self, sender, app_data):
    window_width = app_data[2]
    window_height = app_data[3]
    dpg.set_item_width(self.dpg_window_id, window_width)
    dpg.set_item_height(self.dpg_window_id, window_height)
    dpg.set_item_width(self.dpg_plot_id, window_width)
    dpg.set_item_height(self.dpg_plot_id, window_height / 2)


  def update_gui(self, result_lines:list[str], df_cpu_history:pd.DataFrame, df_mem_history:pd.DataFrame):
    if self.pause:
      return
    if self.dpg_plot_axis_y_id:
      dpg.delete_item(self.dpg_plot_axis_y_id)
    self.dpg_plot_axis_y_id =  dpg.add_plot_axis(dpg.mvYAxis, label=self.get_plot_title(), lock_min=True, parent=self.dpg_plot_id)

    df = df_cpu_history if self.plot_is_cpu else df_mem_history
    col_x = df.columns[0]
    cols_y = df.columns[1:]

    x = df[col_x].to_list()
    for col_y in cols_y:
      y = df[col_y].to_list()
      line_series = dpg.add_line_series(x, y, label=col_y[:min(40, len(col_y))].ljust(40), parent=self.dpg_plot_axis_y_id)
      theme = self.get_theme(col_y)
      dpg.bind_item_theme(line_series, theme)


    if  self.plot_is_cpu:
      dpg.add_line_series([x[0]], [110], label='', parent=self.dpg_plot_axis_y_id)  # dummy for ymax>=100
    dpg.add_plot_legend(parent=self.dpg_plot_id, outside=True, location=dpg.mvPlot_Location_NorthEast)
    dpg.fit_axis_data(self.dpg_plot_axis_x_id)
    dpg.fit_axis_data(self.dpg_plot_axis_y_id)

    dpg.set_value(self.dpg_text, '\n'.join(result_lines))


  def get_color(self, process_name)->tuple[int]:
    # return (0, 0, 0)
    if process_name in self.color_dict:
      return self.color_dict[process_name]
    else:
      color = COLOR_MAP[len(self.color_dict)%len(COLOR_MAP)]
      self.color_dict[process_name] = color
      return color

  def get_theme(self, process_name):
    if process_name in self.theme_dict:
      return self.theme_dict[process_name]
    else:
      with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, self.get_color(process_name), category=dpg.mvThemeCat_Plots)
      self.theme_dict[process_name] = theme
      return theme


def gui_loop(view: GuiView):
  view.start_dpg()


def gui_main(args):
  global g_reset_history_df
  top_runner = TopRunner(args.interval, args.filter)
  data_container = DataContainer(args.csv)

  view = GuiView()
  gui_thread = threading.Thread(target=gui_loop, args=(view,))
  gui_thread.start()

  try:
    while True:
      if g_reset_history_df:
        data_container.reset_history()
        g_reset_history_df = False

      result_lines, result_show_all_lines = top_runner.run(args.num_process, True, args.only_ros)
      if result_show_all_lines is None:
        time.sleep(0.1)
        continue

      df_cpu_history, df_mem_history = data_container.run(top_runner, result_show_all_lines, args.num_process)
      df_cpu_history = df_cpu_history.iloc[:, :min(args.num_process, len(df_cpu_history.columns))]
      df_mem_history = df_mem_history.iloc[:, :min(args.num_process, len(df_mem_history.columns))]

      if gui_thread.is_alive():
        view.update_gui(result_lines, df_cpu_history, df_mem_history)
      else:
        break

  except KeyboardInterrupt:
    pass

  view.exit()
  gui_thread.join()
