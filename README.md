# CHECK https://github.com/fdev31/pyprland for more maintained code

The goal of this project was to keep it single file. I'm now using **pyprland** which is doing the same and more and I'm not maintaining _hpr-scratcher_ anymore.
Please move to _pyprland_ if you are not interested in the single file feature.
The configuration file is compatible, just add your hpr-scratcher configuration under the "scratchpad" JSON key.

# Installation

```
pip install hpr-scratcher
```

_OR_

- copy and rename the `__init__.py` file to some accessible path, do not forget to add +x to it

# Features

- Allow showing & hiding sliding scratchpads
- Allow auto-hide when the focus is lost
- Supports optional animation from top, bottom, left or right
- Reload config without restart

# Usage

As an example, defining two scratchpads:

- _term_ which would be a kitty terminal on upper part of the screen
- _volume_ which would be a pavucontrol window on the right part of the screen

In your `hyprland.conf` add something like this:

```ini
exec-once = hpr-scratcher

# Repeat this for each scratchpad you need
bind = $mainMod,V,exec,hpr-scratcher toggle volume
windowrule = float,^(pavucontrol)$
windowrule = workspace special silent,^(pavucontrol)$

bind = $mainMod,A,exec,hpr-scratcher toggle term
$dropterm  = ^(kitty-dropterm)$
windowrule = float,$dropterm
windowrule = workspace special silent,$dropterm
windowrule = size 75% 60%,$dropterm
```

Then in $HOME/.config/hypr/scratchpads.json add:

```json
{
  "term": {
    "command": "kitty --class kitty-dropterm",
    "animation": "fromTop",
    "margin": 50,
    "unfocus": "hide"
  },
  "volume": {
    "command": "pavucontrol",
    "animation": "fromRight"
  }
}
```

And you'll be able to toggle pavucontrol with MOD + V.

# Nix / Home Manager

1. Add the flake input `hpr-scratcher.url = "github:hyprland-community/hpr-scratcher?dir=nix";`
2. Add the home manager module `inputs.hpr-scratcher.homeManagerModules.default`
3. Enable it `programs.hpr-scratcher.enable = true;` (Also adds it to your config, no need to add `exec-once`)
4. Configure it `programs.hpr-scratcher.scratchpads = {};` (same as `scratchpads.json`, but in nix)
5. Optionally use it for binds
```nix
{
    binds = {
        term = { mods = "SUPER"; key = "T"; type = "show"; };
    };
}
```
6. Add window rules if you need them, they not manageed by the hm module

## Command-line options

- `reload` : reloads the configuration file
- `toggle <scratchpad name>` : toggle the given scratchpad
- `show <scratchpad name>` : show the given scratchpad
- `hide <scratchpad name>` : hide the given scratchpad

Note: with no argument it runs the daemon (doesn't fork in the background)

## Scratchpad Options

### command

This is the command you wish to run in the scratchpad.
For a nice startup you need to be able to identify this window in `hyprland.conf`, using `--class` is often a good idea.

### animation

Type of animation to use

- `null` / `""` / not defined
- "fromTop"
- "fromBottom"
- "fromLeft"
- "fromRight"

### offset (optional)

number of pixels for the animation.

### unfocus (optional)

allow to hide the window when the focus is lost when set to "hide"

### margin (optional)

number of pixels for the margin

# Changelog

# 0.6.0

- animation names are case-insensitive now
- drop `hyprctl` dependency
- auto-restarts applications when needed

# 0.5.0

- windows can slide from any direction now (values for "animation" property):
  - `fromTop`
  - `fromBottom`
  - `fromLeft`
  - `fromRight`
- make "class" option obsolete
- FIX: code reloading
- FIX: misc improvements

# 0.4.0

- the offset is now optional
- the margin can be configured now
- FIX: fast repetition of show/hide sequences
- FIX: automatic hide on focus lost doesn't trigger before the window takes the focus

# 0.3.0

- add animation (only "fromTop" now, but can be switched off)
- pid used in most commands (more reliable)
- FIX: stop pinning the windows
- FIX: debug traces
- FIX: close processes on exit (should be configurable ?)

# 0.2.0

- add a "reload" command re-reading the configuration
- allow automatic hiding on focus

# 0.1.0

- first version, close to no options
