#!/bin/env python
import subprocess
import asyncio
import time
import json
import sys
import os

DEBUG = os.environ.get("DEBUG", False)

HYPRCTL = f'/tmp/hypr/{ os.environ["HYPRLAND_INSTANCE_SIGNATURE"] }/.socket.sock'
EVENTS = f'/tmp/hypr/{ os.environ["HYPRLAND_INSTANCE_SIGNATURE"] }/.socket2.sock'
CONTROL = f'/tmp/hypr/{ os.environ["HYPRLAND_INSTANCE_SIGNATURE"] }/.scratchpads.sock'

CONFIG_FILE = "~/.config/hypr/scratchpads.json"
DEFAULT_MARGIN = 60


async def hyprctlJSON(command):
    if DEBUG:
        print("(JS)>>>", command)
    ctl_reader, ctl_writer = await asyncio.open_unix_connection(HYPRCTL)
    ctl_writer.write(f"-j/{command}".encode())
    await ctl_writer.drain()
    resp = await ctl_reader.read()
    ctl_writer.close()
    await ctl_writer.wait_closed()
    return json.loads(resp)


async def hyprctl(command):
    if DEBUG:
        print(">>>", command)
    ctl_reader, ctl_writer = await asyncio.open_unix_connection(HYPRCTL)
    ctl_writer.write(f"/dispatch {command}".encode())
    await ctl_writer.drain()
    resp = await ctl_reader.read(100)
    ctl_writer.close()
    await ctl_writer.wait_closed()
    if DEBUG:
        print("<<<", resp)
    return resp == b"ok"


async def get_focused_monitor_props():
    for monitor in await hyprctlJSON("monitors"):
        if monitor.get("focused") == True:
            return monitor


async def get_client_props_by_pid(pid: int):
    for client in await hyprctlJSON("clients"):
        if client.get("pid") == pid:
            return client


class Scratch:
    def __init__(self, uid, opts):
        self.uid = uid
        self.pid = 0
        self.conf = opts
        self.visible = False
        self.just_created = True
        self.clientInfo = {}

    def isAlive(self):
        path = f"/proc/{self.pid}"
        if os.path.exists(path):
            for line in open(os.path.join(path, "status"), "r").readlines():
                if line.startswith("State"):
                    state = line.split()[1]
                    return state in "RSDTt"  # not "Z (zombie)"or "X (dead)"
        return False

    def reset(self, pid: int):
        self.pid = pid
        self.visible = False
        self.just_created = True
        self.clientInfo = {}

    @property
    def address(self) -> str:
        return str(self.clientInfo.get("address", ""))[2:]

    async def updateClientInfo(self, clientInfo=None):
        if clientInfo is None:
            clientInfo = await get_client_props_by_pid(self.pid)
        assert clientInfo
        self.clientInfo.update(clientInfo)


class ScratchpadManager:
    server: asyncio.Server
    event_reader: asyncio.StreamReader
    stopped = False

    def __init__(self):
        self.procs = {}
        self.scratches = {}
        self.transitioning_scratches = set()
        self.startedAt = time.time()
        self._respawned_scratches = set()
        self.load_config()

    def load_config(self):
        config = json.loads(
            open(os.path.expanduser(CONFIG_FILE), encoding="utf-8").read()
        )
        scratches = {k: Scratch(k, v) for k, v in config.items()}

        is_updating = not bool(self.scratches)

        for name in scratches:
            if name not in self.scratches:
                self.scratches[name] = scratches[name]
            else:
                self.scratches[name].conf = scratches[name].conf

        if is_updating:
            for name in self.scratches:
                if name not in scratches:
                    del self.scratches[name]

        # not known yet
        self.scratches_by_address = {}
        self.scratches_by_pid = {}

    def start_scratch_command(self, name: str):
        self._respawned_scratches.add(name)
        scratch = self.scratches[name]
        old_pid = self.procs[name].pid if name in self.procs else 0
        self.procs[name] = subprocess.Popen(
            scratch.conf["command"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        pid = self.procs[name].pid
        self.scratches[name].reset(pid)
        self.scratches_by_pid[self.procs[name].pid] = scratch
        if old_pid:
            del self.scratches_by_pid[old_pid]

    def load_clients(self):
        self.procs = {}
        for name in self.scratches:
            self.start_scratch_command(name)

    # event handlers:

    async def event_moveworkspace(self, params):
        pass

    async def event_openlayer(self, params):
        pass

    async def event_closelayer(self, params):
        pass

    async def event_changefloatingmode(self, params):
        pass

    async def event_activelayout(self, params):
        pass

    async def event_urgent(self, params):
        pass

    async def event_closewindow(self, params):  # winid
        pass

    async def event_fullscreen(self, params):
        pass

    async def event_workspace(self, params):
        pass

    async def event_destroyworkspace(self, params):
        pass

    async def event_createworkspace(self, params):
        pass

    async def event_focusedmon(self, params):
        pass

    async def event_activewindowv2(self, addr):
        addr = addr.strip()
        scratch = self.scratches_by_address.get(addr)
        if scratch:
            if scratch.just_created:
                await self.run_hide(scratch.uid, force=True)
                scratch.just_created = False
        else:
            for uid, scratch in self.scratches.items():
                if scratch.clientInfo and scratch.address != addr:
                    if (
                        scratch.visible
                        and scratch.conf.get("unfocus") == "hide"
                        and scratch.uid not in self.transitioning_scratches
                    ):
                        await self.run_hide(uid)

    async def event_openwindow(self, params):
        addr, wrkspc, kls, title = params.split(",", 3)
        if wrkspc == "special":
            item = self.scratches_by_address.get(addr)
            if not item and self._respawned_scratches:
                await self.updateScratchInfo()
                item = self.scratches_by_address.get(addr)
            if item and item.just_created:
                self._respawned_scratches.discard(item.uid)
                await self.run_hide(item.uid, force=True)
                item.just_created = False

    async def event_activewindow(self, params):  # XXX: do not use
        return

    # command handlers

    async def run_reload(self):
        self.load_config()

    async def run_toggle(self, uid: str):
        uid = uid.strip()
        item = self.scratches.get(uid)
        if not item:
            print(f"{uid} is not configured")
            return
        if item.visible:
            await self.run_hide(uid)
        else:
            await self.run_show(uid)

    async def updateScratchInfo(self, scratch: Scratch | None = None):
        if scratch is None:
            for client in await hyprctlJSON("clients"):
                scratch = self.scratches_by_pid.get(client["pid"])
                if scratch:
                    await scratch.updateClientInfo(client)
                    self.scratches_by_address[
                        scratch.clientInfo["address"][2:]
                    ] = scratch
        else:
            add_to_address_book = ("address" not in scratch.clientInfo) or (
                scratch.address not in self.scratches_by_address
            )
            await scratch.updateClientInfo()
            if add_to_address_book:
                self.scratches_by_address[scratch.clientInfo["address"][2:]] = scratch

    async def run_hide(self, uid: str, force=False):
        uid = uid.strip()
        item = self.scratches.get(uid)
        if not item:
            print(f"{uid} is not configured")
            return
        if not item.visible and not force:
            print(f"{uid} is already hidden")
            return
        item.visible = False
        pid = "pid:%d" % item.pid
        animation_type = item.conf.get("animation", "").lower()
        if animation_type:
            offset = item.conf.get("offset")
            if offset is None:
                if "size" not in item.clientInfo:
                    await self.updateScratchInfo(item)

                offset = int(1.3 * item.clientInfo["size"][1])

            if animation_type == "fromtop":
                await hyprctl(f"movewindowpixel 0 -{offset},{pid}")
            elif animation_type == "frombottom":
                await hyprctl(f"movewindowpixel 0 {offset},{pid}")
            elif animation_type == "fromleft":
                await hyprctl(f"movewindowpixel -{offset} 0,{pid}")
            elif animation_type == "fromright":
                await hyprctl(f"movewindowpixel {offset} 0,{pid}")

            if uid in self.transitioning_scratches:
                return  # abort sequence
            await asyncio.sleep(0.2)  # await for animation to finish
        if uid not in self.transitioning_scratches:
            await hyprctl(f"movetoworkspacesilent special,{pid}")

    async def _animation_fromtop(self, monitor, client, client_uid, margin):
        mon_x = monitor["x"]
        mon_y = monitor["y"]
        mon_width = monitor["width"]

        client_width = client["size"][0]
        margin_x = int((mon_width - client_width) / 2) + mon_x
        await hyprctl(f"movewindowpixel exact {margin_x} {mon_y + margin},{client_uid}")

    async def _animation_frombottom(self, monitor, client, client_uid, margin):
        mon_x = monitor["x"]
        mon_y = monitor["y"]
        mon_width = monitor["width"]
        mon_height = monitor["height"]

        client_width = client["size"][0]
        client_height = client["size"][1]
        margin_x = int((mon_width - client_width) / 2) + mon_x
        await hyprctl(
            f"movewindowpixel exact {margin_x} {mon_y + mon_height - client_height - margin},{client_uid}"
        )

    async def _animation_fromleft(self, monitor, client, client_uid, margin):
        mon_y = monitor["y"]
        mon_height = monitor["height"]

        client_height = client["size"][1]
        margin_y = int((mon_height - client_height) / 2) + mon_y

        await hyprctl(f"movewindowpixel exact {margin} {margin_y},{client_uid}")

    async def _animation_fromright(self, monitor, client, client_uid, margin):
        mon_y = monitor["y"]
        mon_width = monitor["width"]
        mon_height = monitor["height"]

        client_width = client["size"][0]
        client_height = client["size"][1]
        margin_y = int((mon_height - client_height) / 2) + mon_y
        await hyprctl(
            f"movewindowpixel exact {mon_width - client_width - margin} {margin_y},{client_uid}"
        )

    async def run_show(self, uid, force=False):
        uid = uid.strip()
        item = self.scratches.get(uid)

        if not item:
            print(f"{uid} is not configured")
            return

        if item.visible and not force:
            print(f"{uid} is already visible")
            return

        if not item.isAlive():
            print(f"{uid} is not running, restarting...")
            self.procs[uid].kill()
            self.start_scratch_command(uid)
            while uid in self._respawned_scratches:
                await asyncio.sleep(0.05)

        item.visible = True
        monitor = await get_focused_monitor_props()
        assert monitor

        await self.updateScratchInfo(item)

        pid = "pid:%d" % item.pid

        animation_type = item.conf.get("animation", "").lower()

        wrkspc = monitor["activeWorkspace"]["id"]
        self.transitioning_scratches.add(uid)
        await hyprctl(f"movetoworkspacesilent {wrkspc},{pid}")
        if animation_type:
            margin = item.conf.get("margin", DEFAULT_MARGIN)
            fn = getattr(self, "_animation_%s" % animation_type)
            await fn(monitor, item.clientInfo, pid, margin)

        # FIXME: pin doesn't always work
        # await hyprctl(f"pin {pid}")
        await hyprctl(f"focuswindow {pid}")
        await asyncio.sleep(0.2)  # ensure some time for events to propagate
        self.transitioning_scratches.discard(uid)

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
                    print(f"EVT {full_name}({params.strip()})")
                await getattr(self, full_name)(params)
            else:
                print(f"unknown event: {cmd} ({params.strip()})")

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
                print(f"CMD: {full_name}({args})")
            await getattr(self, full_name)(*args)
        else:
            print("Unknown command:", cmd)

    async def serve(self):
        try:
            async with self.server:
                await self.server.serve_forever()
        finally:

            async def die_in_piece(scratch: Scratch):
                proc = self.procs[scratch.uid]
                proc.terminate()
                for n in range(10):
                    if not scratch.isAlive():
                        break
                    await asyncio.sleep(0.1)
                if scratch.isAlive():
                    proc.kill()
                proc.wait()

            await asyncio.gather(
                *(die_in_piece(scratch) for scratch in self.scratches.values())
            )

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
    finally:
        events_writer.close()
        await events_writer.wait_closed()
        manager.server.close()
        await manager.server.wait_closed()


async def run_client():
    if sys.argv[1] == "--help":
        print(
            """Commands:
  reload
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
