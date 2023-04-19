# Installation

```
pip install hpr-scratcher
```

_OR_

- copy and rename the `__init__.py` file to some accessible path, do not forget to add +x to it

# Features

- Allow showing & hiding sliding scratchpads
- Allow auto-hide when the focus is lost

# Usage

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
    "class": "kitty-dropterm",
    "offset": 800,
    "animation": "fromTop",
    "unfocus": "hide"
  },
  "volume": {
    "command": "pavucontrol",
    "class": "pavucontrol",
    "animation": "fromTop",
    "offset": 1200
  }
}
```

And you'll be able to toggle pavucontrol with MOD + V.

## Options

### animation

Type of animation to use

- `null` / `""`
- `"fromTop"`

_TODO_:

- `fromBottom`
- `fromLeft`
- `fromRight`

### offset

number of pixels for the animation.

### class

class of the created window

### unfocus

allow to hide the window when the focus is lost when set to "hide"

# Changelog

# WIP

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

# TODO

- Make the margin/padding configurable per app
- Better handling of fast repetitions
- Allow different "poles" for scratchpads instead of always sliding from the top
- Make the usage of an explicit offset not needed
- Allow auto-restart of applications (if closed)
  - Allow closing the app on unfocus
- Move to socket instead of hyprctl when possible
