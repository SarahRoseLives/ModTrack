# ModTrack - OpenTTD Moderation Bot

ModTrack is an OpenTTD moderation bot designed to keep your server on track ~~by providing features such as vote kicking, banning, and filtering messages based on predefined word lists. It is configurable via a simple INI file.~~

## What Happened to The Code?

I have decided to take a new approch to this, I scrubbed the old code and am now attempting to write a Discord / OpenTTD Administration bot to manage your servers, chat, abuse reports and much more.

Due to issues with threading and concurrency as well as the additional complications of trying to mix pyOpenTTDAdmin with the Discord.py library (and my lack of skill) Cross-Communication between the discord and admin port sections of the code will be facilitated over a set of UDP ports on the local host.

This allows me to send command data back and forth on the loopback address and enables us to both continuously receieve packets and also send them on the fly. We'll use a thread in admin.py and async in bot.py due to Discord.py's already async nature.

## Currently Implemented but lacking refinement

- Rcon Packets directly available in discord with !rcon 'rcon_command'
- That's it lol, I spent 12+ hours figuring out how to get these libraries to talk together before settling on the UDP method. I'll be adding more very soon.

## Dependencies

ModTrack utilizes the pyOpenTTDAdmin library, available at [liki-mc/pyOpenTTDAdmin](https://github.com/liki-mc/pyOpenTTDAdmin). Ensure you have this submodule included in your repository.

## Contributing

Contributions to ModTrack are welcome! Feel free to submit bug reports, feature requests, or pull requests via GitHub.
