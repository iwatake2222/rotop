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
from setuptools import setup, find_packages
from os import path
import re

package_name = 'rotop'
root_dir = path.abspath(path.dirname(__file__))

with open(path.join(root_dir, package_name, '__init__.py')) as f:
  init_text = f.read()
  version = re.search(r'__version__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
  license = re.search(r'__license__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
  author = re.search(r'__author__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
  author_email = re.search(r'__author_email__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)
  url = re.search(r'__url__\s*=\s*[\'\"](.+?)[\'\"]', init_text).group(1)

assert version
assert license
assert author
assert author_email
assert url

with open("README.md", encoding='utf8') as f:
  long_description = f.read()

setup(
  name="rotop",
  version=version,
  description='top command for ROS 2',
  long_description=long_description,
  long_description_content_type="text/markdown",
  keywords='ros ros2 top cpu usage',
  author=author,
  author_email=author_email,
  url=url,
  project_urls={
    "Source":
    "https://github.com/iwatake2222/rotop",
    "Tracker":
    "https://github.com/iwatake2222/rotop/issues",
  },
classifiers=[
    'Development Status :: 2 - Pre-Alpha',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Topic :: Utilities',
    'Topic :: Scientific/Engineering :: Visualization',
    'Framework :: Robot Framework :: Tool',
  ],
  license=license,
  python_requires=">=3.7",
  install_requires=[
    "dearpygui>=1.10.1",
    "numpy",
    "pandas",
    "pexpect",
  ],
  # tests_require=['pytest'],
  packages=find_packages(),
  platforms=["linux", "unix"],
  # package_data={"rotop": ["setting.json", "font/*/*.ttf"]},
  entry_points="""
    [console_scripts]
    rotop=rotop.__main__:main
  """,
)
