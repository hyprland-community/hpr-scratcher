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
