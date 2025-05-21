# uav-guidance-system

A guidance and automatic target engagement system for FPV drones.
At this stage, the system has been developed to operate within a **simulator**.

## Requirements

- Linux
- Python 3.13
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [uv](https://github.com/astral-sh/uv)

Make sure you have an FPV drone simulator installed (such as Liftoff), your controller configured,
and a tool like OBS set up to stream the simulator window via UDP.
If necessary, adjust the configuration settings in `config.py`.

## Usage

Install the dependencies:

```
uv sync
```

Run the system using the following command:

```
cd src && sudo ../.venv/bin/python main.py
```

Next, launch the simulator and start streaming its window.
