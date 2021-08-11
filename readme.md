# Casper
NPC traffic generator/C2 framework that allows for scripted user actions. 

It's made to provide realistic-ish forensicating experience by not having deterministic PCAPs. 

There is also a beaconing system to facilitate C2 over the agents running on your hosts so you can dynamically introduce new elements to the network traffic or host logs (via `push-op` in near real-time. 

You can script out your scenarios in one or more "operation files" (specified in TOML) 

The agents will run in independent of the C2 server and will load all of the `.toml` files in the `./ops` adjacent to the program. those things can be configured, of course.  

Originally inspired by https://github.com/cmu-sei/GHOSTS

---
# Quickstart
`pip install -r requirements.txt` (if running from source)

`python3 casper_agent.py operate` OR `casper_agent.exe operate` on windows

```
Usage: casper_agent.py [OPTIONS] COMMAND [ARGS]...

Options:
  --config-file PATH    [default: config.toml]
  --debug / --no-debug  [default: True]
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.

  --help                Show this message and exit.

Commands:
  flush-ops
  get-uuid      this returns the uuid of agent on THIS computer (useful for...
  operate       actually fire off the operations defined in the ops.toml...
  push-op       TESTING load an opfile from an arbitrary path.
  random-visit  randomly visit a list of urls
  remote-ops
  run-command   run an arbitrary system command.
  send-email    ONLY PARTIALLY IMPLEMENTED; send an email to multiple...
  visit-page
  wander        randomly follow links on a page upto depth links deep with
                a...
```
---
# Operation Files
An operation file (op file for short) is a list of tasks which may or may not be configured to repeat until interrupted.

Tasks are actions which can be leveraged to achieve some outcome (generating plausible network traffic in most cases) by simulating user activity on a computer.

Actions such as `run`, `visit`, `wander`, and `send_email` can be sequenced to provide a repeatable yet non-deterministic PCAP for traffic analysis and general 'who dun it' investigations.    

For instance, you can have your agents visit a page, download, and ultimately run an exe.
All with random-ish delays between actions and all while having a concurrent, realistic web browsing experience (scrolling and clicking links on reddit).

As mentioned, this provides PCAPs which are dynamic but still have a pattern to witness. 

---
## Common config parameters and their defaults
All actions support these configuration items in the op file
You can override these default values by specifying them in your operation file. 

```toml
start_offset = 0 # wait N seconds after agent startup before starting this task

repeat_every = 0 # Wait N seconds (+/- repeat_jitter) before each cycle; 0 to disable repeating

hours_of_operation = None # when should a task be allowed to run; None (or missing ) means there are no constrained hours of operation for this task. i.e. it will run whenever the agent runs. 
# hours_of_operation = ["11:30:15","15:30:00"] # means that this action 

start_jitter = 0

repeat_jitter = 0 # how much swing (+/- N ) is applied to the jitter 
# repeat_every = 60 and repeat_jitter = 30 means that any two cycles could happen 30 seconds apart or as far apart as 90 seconds (plus the time of execution of the task itself). Over time they will be about 60 seconds average; It will be random each loop. 

target_tags = ['compromised', 'web', 'tag3', 'user4',...] # this can be used to selectively apply tasks to agents.  

target_platform = ['windows', 'linux', ...] # this is for selectively loading tasks from an opfile based upon the agent's self-identified platform; at startup it detects which platform it is running on and beacons that information to the C2 server. 

target_id = ['id1', 'id2', ...] # this can be used to selectively choose an agent to run a task on. This is most useful in combination with the beacon method to push new operation files to agents mid-event. This is akin to having C2 over those agents as you can run remote commands and capture their output

```
### Quick Time Reference
- 3 min is `180` seconds
- 5 min is `300` seconds
- 15 min is `900` seconds 
- 30 min is `1800` seconds
- 1 hour is `3600` seconds
- 6 hours is `21600` seconds
- 12 hours is `43200` seconds
- 1 day is `86400` seconds
- 1 week is `604800` seconds
- 1 month (30 days) is `18144000` seconds

# Example op file
This outlines a narrative where a user visits a website, downloads a file, and runs it. on a any windows-based agent 

```toml
[[tasks]]
  # no platform specific targeting
  action = 'visit'
  url = "https://somesite.com/"
  start_offset = 30 # wait 30 seconds after agent start
  start_jitter = 15


[[tasks]]
  target_tags = [
    'silly_user_1' # all agents with the tag "silly_user_1" should perform this task.
  ] 
  action = 'download'
  url = "https://somesite.com/game.exe"
  download_dir = "C:\users\user1\desktop" # this path would only make sense on windows
  start_offset = 120 # 2 minutes after start
  start_jitter = 10

[[tasks]]
  target_ids = [
    'abcdef0123456789'
  ]
  action = 'run'
  cmd = "C:\users\user1\desktop\game.exe"
  start_offset = 180 # at least 3 minutes in but wait until 1230 to start 
  hours_of_operation = ['12:30:00', '13:00:00'] # this task will only start between these hours

[[tasks]]
  action = 'wander'
  starting_url = 'https://facebook.com'
  wander_depth = 3 # how many pages deep
  wander_dwell = 30 # how long to sit on each page  +/- wander_jitter
  wander_jitter = 15
  repeat_every 300  # repeat this process every 5 minutes; simulate someone visiting facebook every 5 minutes
  
# hopefully all of the targeting works towards narrowing down to a few logical hosts. You could always just be specific and just use the agent UUID with target_ids 

```
Save that example in the `ops` folder as a .toml file and run `casper_agent.exe operate` 



---
# The C2 Server
The agent is configured to beacon to the C2 server (accessible on all IPs at `https://localhost:5000` by default. )

you can push one or more new operations to all beaconing agents via the C2 servers agent.  

```bash
./casper_agent.py push-op op_file1.toml op_file2.toml ...
```
or specify which c2-server to use
```bash
./casper_agent.py --c2-server https://someserver.com push-op op_file1.toml op_file2.toml ...
```

You can disable the beaconing during operation. Obviously, this will prevent you from pushing new ops to the agent.
```bash
./casper_agent.py operate --disable-beacon
```

The `config.toml` adjacent to the agent will also allow you to change c2 servers or disable the beacon.

---
# Dev Quickstart 
if you want to run from source or hack on casper to the following... 
```bash
git clone https://github.com/ShyftXero/casper
cd casper && python3 -m venv venv && source venv/bin/activate
pip install -U -r requirements.txt
```

if you want to build binaries with pyinstaller, you should be able to 
`make build`  on whatever platform is most appropriate. 

