# How I used AI on this challenge

Most of my effort went into building [a Claude Code plugin](https://github.com/michaelwayman/mkit) called mkit. Left alone, the AI builders did far more than the challenge asked for, so I built a way to hold them to the requirements.

MKit keeps the scope in a numbered spec: the requirements the challenge needs, each with acceptance bullets, plus an explicit list of what is out of scope. Before each build the builder gets only the requirements it is working on and a "do not build" list, and a requirement counts as done only when its acceptance bullets pass. That kept the work to what was necessary, and no less.

It is not a straitjacket. When I wanted something new, like URL-synced filters or pagination controls, I added it as one feature: logged it, turned it into a requirement with its own acceptance bullets through a change I approved, then built just that. Features go in one at a time, on purpose.

# Why my choices differ

I deliberately used a range of approaches, and I can argue for most of them depending on the real-world scenario or the dev environment. For this take-home I built for dev and demo, so I picked the simplest option that stayed correct. The import reads MariaDB directly because the data was already loaded, where a live site might call the WordPress REST API. The main app verifies tokens locally with a public key, which suits "auth going down must not take the app down"; if instant revocation mattered more, I would call the auth service on each request instead. Average rating is derived, not stored, which is fine at 100 brands and would change at scale. Auth user IDs are UUIDs derived from the WordPress ID, which avoids collisions with other ID sources without adding a lookup table. Each is a trade-off I made on purpose and can reverse if the context changes.

# 3 attempts
1. [My original submission](https://github.com/michaelwayman/ca-challenge) was fine but lacked methodology. AI Builders did a lot and my steering did "too little". AI gone wild.
2. [My next attempt](https://github.com/michaelwayman/ck-dryrun) had full github integration, production quality, parallel workstreams, auto-fix, CI, service boundaries, etc. but that was "too expensive".
3. [This attempt](https://github.com/michaelwayman/ca-code-challenge) has 100% control of what goes in or out of scope, the AI is completely under control. It's a dev build with few tests but it's "just right" and (CHEAPER $ USAGE)
