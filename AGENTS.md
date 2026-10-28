# Agent instructions

## Git identity

- Commit as `Elad Ben-Haim <elad12390@gmail.com>` and push as the `elad12390` GitHub account,
  which owns this repository. This overrides the global `elad@othello.ai` identity.
- The active `gh` account may be a work account with no push access here. Push with the owner's
  token for that one command: `GH_TOKEN="$(gh auth token --user elad12390)" git push`.

## Public repository

- `searxng-config/settings.yml` holds the local SearXNG proxy credentials. Never commit them.
