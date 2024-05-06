# ModTrack - OpenTTD Moderation Bot

ModTrack is an OpenTTD moderation bot designed to keep your server on track by providing features such as vote kicking, banning, and filtering messages based on predefined word lists. It is configurable via a simple INI file.

## Features

- **Vote kicking and banning:** Users can initiate votes to kick or ban other players from the server.
- **Word list filtering:** Messages containing words stored in predefined word lists can trigger warnings or actions.
- **Logging:** Keep track of bot activities and user interactions for moderation purposes.
- **Rate Limiting:** Kick users for spamming the server's chat. 
- **Configuration:** Easily configurable using a straightforward INI file format.

## Commands

- `!vote kick user #1` - Type full username as seen on the server
- `!vote ban user #4` - Type full username as seen on the server
- `!admin enable/disable` - Enables or Disables bot in-game, only responds to admin ip

## Configuration

The `config.cfg` file contains various sections and keys to configure ModTrack.

### ModRail Section

- `server`: IP address of the OpenTTD server.
- `adminpass`: Admin password for connecting to the OpenTTD server.
- `port`: Port number for the OpenTTD admin interface.
- `welcome`: Welcome message displayed when the bot starts.
- `prefix`: Prefix for bot commands in chat (e.g., `!`).
- `logging`: Enable/disable logging (e.g., `enabled` or `disabled`).
- `botadminip`: IP address of the bot administrator.
- `ratelimiting`: Enable/disable rate limiting.
- `ratelimit_messages`: Number of messages triggering rate limiting.
- `ratelimit_seconds`: Time window for rate limiting in seconds.

### Wordlists Section

Each key in this section represents a word list, and its value determines if the list is enabled or disabled.

- `profanity`: Enable/disable the profanity word list.
- `politics`: Enable/disable the politics word list.
- `slurs`: Enable/disable the slurs word list.
- `custom`: Enable/disable a custom word list.

### Warnings Section

- `warning1`: First warning message displayed to users for violating word list rules.
- `warning2`: Final warning message before potential kick for repeated violations.
- `votedwarning`: Message displayed when a user has already voted against another user.

### Votes Section

- `votestokick`: Number of votes required to initiate a kick.
- `votestoban`: Number of votes required to initiate a ban.

## Dependencies

ModTrack utilizes the pyOpenTTDAdmin library, available at [liki-mc/pyOpenTTDAdmin](https://github.com/liki-mc/pyOpenTTDAdmin). Ensure you have this submodule included in your repository.

## Contributing

Contributions to ModTrack are welcome! Feel free to submit bug reports, feature requests, or pull requests via GitHub.
