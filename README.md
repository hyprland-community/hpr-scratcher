# Installation

```
pip install hpr-scratcher
```

_OR_

- copy and rename the `__init__.py` file to some accessible path, do not forget to add +x to it

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
    "offset": 800
  },
  "volume": {
    "command": "pavucontrol",
    "class": "pavucontrol",
    "offset": 1200,
    "unfocus": "TODO: hide"
  }
}
```

And you'll be able to toggle pavucontrol with MOD + V.

# TODO

- Allow auto-hide when the focus is lost
- Better handling of fast repetitions
