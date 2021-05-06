# Casper
NPC traffic generator/C2 framework... 

originally inspired by https://github.com/cmu-sei/GHOSTS


# Quickstart
`pip install -r requirements.txt`

`python casper_agent operate` OR `casper_agent.exe operate` on windows

```
Usage: casper_agent.py [OPTIONS] COMMAND [ARGS]...

Options:
  --config-file PATH              [default: config.toml]
  --debug / --no-debug            [default: True]
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.

Commands:
  flush-ops
  get-uuid      this returns the uuid of agent on THIS computer (useful for...
  operate       actually fire off the operations defined in the ops.toml...
  push-op       TESTING load an opfile from an arbitrary path.
  random-visit  randomly visit a list of urls
  remote-ops
  run-command   run an arbitrary system command.
  send-email    ONLY PARTIALLY IMPLEMENTED; send an email to multiple...
  visit-page    visit an arbitrary url.
  wander        randomly follow links on a page upto depth links deep with
                a...
```

---
## Operation Files
scripted events. may or may not be repeated.

tasks

actions

