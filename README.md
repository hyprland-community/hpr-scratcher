# Usage

In your `hyprland.conf` add something like this:

```ini

exec-once = hpr-scratcher

# Repeat this for each scratchpad you need
bind = $mainMod,V,exec,$HOME/utils/hpr-scratcher toggle volume
windowrule = float,^(pavucontrol)$
windowrule = workspace special silent,^(pavucontrol)$
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
