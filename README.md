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
    "unfocus": "hide"
  },
  "volume": {
    "command": "pavucontrol",
    "class": "pavucontrol",
    "offset": 1200
  }
}
```

And you'll be able to toggle pavucontrol with MOD + V.

# TODO

- Better handling of fast repetitions
- Allow different "poles" for scratchpads instead of always sliding from the top
- Make the usage of an explicit offset not needed
- study avoiding the usage of classes to track the windows (once registered)
- Allow auto-restart of applications (if closed)
  - Allow closing the app on unfocus
- Move to socket instead of hyprctl when possible
