# rotop

## About

top command for ROS 2

## Features

- Replace long ROS 2 command and Python command, especially for component container
  - :sob: normal `top` command : "`component_container`"
  - :cold_sweat: normal `top -c` or `htop` : "`/very/long/path/component_container` `very-long-options`"
  - :grin: `rotop` : "`{node_name} {name_space}`"
- Filter function
- csv file logger
- Graph plotter

## How to use

```sh
pip3 install rotop

rotop
rotop --gui


# usage: rotop [-h] [--interval INTERVAL] [--filter FILTER] [--csv] [--gui] [--num_process NUM_PROCESS]
# options:
#   -h, --help            show this help message and exit
#   --interval INTERVAL
#   --filter FILTER
#   --csv
#   --gui
#   --num_process NUM_PROCESS
```

```sh
cd rotop
python3 main.py
```

## Screen Shot

- cui mode
  - ![](./00_doc/capture_00.png)
- gui mode
  - ![](./00_doc/capture_01.png)
