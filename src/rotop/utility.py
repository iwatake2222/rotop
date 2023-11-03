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
import logging


def create_logger(name, level: int=logging.DEBUG, log_filename: str=None) -> logging.Logger:
  handler_format = logging.Formatter('[%(asctime)s][%(levelname)-7s][%(filename)s:%(lineno)s] %(message)s')
  # stream_handler = logging .StreamHandler()
  # stream_handler.setLevel(level)
  # stream_handler.setFormatter(handler_format)
  logger = logging.getLogger(name)
  logger.propagate = False
  logger.setLevel(level)
  # logger.addHandler(stream_handler)
  # if log_filename:
    # file_handler = logging.FileHandler(log_filename)
    # file_handler.setLevel(level)
    # file_handler.setFormatter(handler_format)
    # logger.addHandler(file_handler)
  return logger
