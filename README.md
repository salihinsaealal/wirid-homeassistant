# Wirid for Home Assistant

Dhikr statistics from the Wirid Android app, one device per phone. Full instructions coming soon.

## Connecting a phone

Settings → Devices & services → Add integration → Wirid: phone name → who uses it → (first phone
only, when old YAML sensors are found) take them over → the phone's address. Copy that address into
Wirid on the phone (Settings → Home Assistant). The integration's options show the address again or
make a new one.

The address step has no "open in Wirid" (`wirid://`) link. Home Assistant renders config-flow text
with `ha-markdown`, which sanitises it with js-xss; js-xss keeps an `href` only when it starts with
`http://`, `https://`, `mailto:`, `tel:`, `ftp://`, `data:image/`, `/`, `./`, `../` or `#`, so a
`wirid://` link would render with an empty address. Copy is the only way in.
