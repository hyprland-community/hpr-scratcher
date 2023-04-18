#!/bin/env python
import subprocess
import asyncio
import json
import sys
import os

DEBUG = os.environ.get("DEBUG", False)

MARGIN = 60  # TODO take it from JSON config
EVENTS = f'/tmp/hypr/{ os.environ["HYPRLAND_INSTANCE_SIGNATURE"] }/.socket2.sock'
CONTROL = f'/tmp/hypr/{ os.environ["HYPRLAND_INSTANCE_SIGNATURE"] }/.scratchpads.sock'

CONFIG_FILE = "~/.config/hypr/scratchpads.json"


def hyprctlJSON(command):
    if DEBUG:
        print(command)
    return json.loads(subprocess.getoutput(f"hyprctl -j {command}"))


def hyprctl(command):
    if DEBUG:
        print(command)
    subprocess.call(
        ["hyprctl", "dispatch", command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get_focused_monitor():
    for monitor in hyprctlJSON("monitors"):
        if monitor.get("focused") == True:
            return monitor


def get_client_by_class(name):
    for client in hyprctlJSON("clients"):
        if client.get("class") == name:
            return client


class Scratch:
    def __init__(self, uid, opts):
        self.uid = uid
        self.conf = opts
        self.visible = False
        self.just_created = True


class ScratchpadManager:
    server: asyncio.Server
    event_reader: asyncio.StreamReader
    stopped = False

    def __init__(self):
        self.procs = {}
        self.scratches = {}
        self.load_config()

    def load_config(self, reload=False):
        config = json.loads(
            open(os.path.expanduser(CONFIG_FILE), encoding="utf-8").read()
        )
        old_scratches = self.scratches
        self.scratches = {k: Scratch(k, v) for k, v in config.items()}
        self.scratches_by_class = {v["class"]: Scratch(k, v) for k, v in config.items()}
        if reload:
            for k in self.scratches:
                self.scratches[k].just_created = False
                if old_scratches.get(k):
                    self.scratches[k].visible = old_scratches[k].visible

    def load_clients(self):
        self.procs = {
            name: subprocess.Popen(
                scratch.conf["command"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
            )
            for name, scratch in self.scratches.items()
        }

    # event handlers:

    async def event_openwindow(self, params):
        addr, wrkspc, kls, title = params.split(",", 3)
        if wrkspc == "special":
            item = self.scratches_by_class.get(kls)
            if item and item.just_created:
                await self.run_hide(item.uid, force=True)
                item.just_created = False

    async def event_activewindowv2(self, params):
        pass

    async def event_activewindow(self, params):
        klass, _ = params.rstrip().split(",", 1)
        item = self.scratches_by_class.get(klass)
        if item:
            if item.just_created:
                await self.run_hide(item.uid)
                item.just_created = False
        else:
            for uid, scratch in self.scratches.items():
                if scratch.visible and scratch.conf.get("unfocus") == "hide":
                    await self.run_hide(uid)

    # command handlers

    async def run_reload(self):
        self.load_config(reload=True)

    async def run_toggle(self, uid):
        uid = uid.strip()
        item = self.scratches.get(uid)
        if not item:
            print(f"{uid} is not configured")
            return
        if item.visible:
            await self.run_hide(uid)
        else:
            await self.run_show(uid)

    async def run_hide(self, uid, force=False):
        uid = uid.strip()
        item = self.scratches.get(uid)
        if not item:
            print(f"{uid} is not configured")
            return
        if not item.visible and not force:
            print(f"{uid} is already hidden")
            return
        item.visible = False
        kls = item.conf["class"]
        hyprctl(f"movewindowpixel 0 -{item.conf['offset']},^({kls})$")
        await asyncio.sleep(0.2)
        hyprctl(f"movetoworkspacesilent special,^({kls})$")

    async def run_show(self, uid, force=False):
        uid = uid.strip()
        item = self.scratches.get(uid)

        if not item:
            print(f"{uid} is not configured")
            return

        if item.visible and not force:
            print(f"{uid} is already visible")
            return

        item.visible = True
        monitor = get_focused_monitor()
        assert monitor
        kls = item.conf["class"]
        client = get_client_by_class(kls)
        assert client
        mon_x = monitor["x"]
        mon_y = monitor["y"]
        mon_width = monitor["width"]

        offset = client["at"][1]
        if offset > -1:
            print(f"Huhu, didn't expect this! offset={offset}")

        client_width = client["size"][0]
        margin_x = int((mon_width - client_width) / 2) + mon_x
        wrkspc = monitor["activeWorkspace"]["id"]
        hyprctl(f"movetoworkspace {wrkspc},^({kls})$")
        hyprctl(f"pin ^({kls})$")
        hyprctl(f"movewindowpixel exact {margin_x} {mon_y + MARGIN},^({kls})$")
        hyprctl(f"focuswindow ^({kls})$")

    # Async loops & handlers (dispatchers):

    async def read_events_loop(self):
        while not self.stopped:
            data = (await self.event_reader.readline()).decode()
            if not data:
                print("Reader starved")
                return
            cmd, params = data.split(">>")
            full_name = f"event_{cmd}"
            if hasattr(self, full_name):
                if DEBUG:
                    print("EVT", full_name, params)
                await getattr(self, full_name)(params)
            else:
                print("unknown event:", cmd, "///", params)

    async def read_command(self, reader, writer):
        data = (await reader.readline()).decode()
        if not data:
            print("Server starved")
            return
        if data == "exit\n":
            self.stopped = True
            writer.close()
            await writer.wait_closed()
            self.server.close()
            return
        args = data.split(None, 1)
        if len(args) == 1:
            cmd = args[0]
            args = []
        else:
            cmd = args[0]
            args = args[1:]
        full_name = f"run_{cmd}"
        if hasattr(self, full_name):
            if DEBUG:
                print("CMD:", full_name, args)
            await getattr(self, full_name)(*args)
        else:
            print("Unknown command:", cmd)

    async def serve(self):
        async with self.server:
            await self.server.serve_forever()

    async def run(self):
        await asyncio.gather(
            asyncio.create_task(self.serve()),
            asyncio.create_task(self.read_events_loop()),
        )


async def run_daemon():
    manager = ScratchpadManager()
    manager.server = await asyncio.start_unix_server(manager.read_command, CONTROL)
    events_reader, events_writer = await asyncio.open_unix_connection(EVENTS)
    manager.event_reader = events_reader

    manager.load_clients()  # ensure sockets are connected first

    try:
        await manager.run()
    except KeyboardInterrupt:
        print("Interrupted")
    except asyncio.CancelledError:
        print("Bye!")

    events_writer.close()
    await events_writer.wait_closed()
    manager.server.close()
    await manager.server.wait_closed()


async def run_client():
    if sys.argv[1] == "--help":
        print(
            """Commands:
  show   <scratchpad name>
  hide   <scratchpad name>
  toggle <scratchpad name>


If arguments are ommited, runs the daemon which will start every configured command.
"""
        )
        return

    _, writer = await asyncio.open_unix_connection(CONTROL)
    writer.write((" ".join(sys.argv[1:])).encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


def main():
    try:
        asyncio.run(run_daemon() if len(sys.argv) <= 1 else run_client())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
