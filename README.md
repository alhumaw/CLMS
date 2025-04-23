## ♻️ Cluster Lifecycle Management System ♻️
This research introduces the Cluster Lifecycle Management System (CLMS), 
a preemptive approach to container lifecycle management in Kubernetes.

### Running the program
In order to run this program, you will need to set your `KUBECONFIG` directory as an environment variable:
```shell
export KUBECONFIG=/etc/kubernetes/admin.conf
```
### Execution syntax
This example accepts the following input parameters.
| Parameter | Purpose |
| :--- | :--- |
| `-d`, `--debug` | Enable API debugging. |
| `-n`, `--namespaces` | Namespaces for the program to target. |
| `-e`, `--exclude` | Deployments to exclude from the program. |


Targets the namespace `martian-bank`, cycles all deployments within that namespace.
```shell
python3 clms.py -n martian-bank
```

Targets the namespace `martian-bank`, excludes any deployment containing the string `mongodb`.
```shell
python3 clms.py -n martian-bank -e mongodb
```

Targets the namespaces `martian-bank` and `sock-shop`. Excludes any deployment containing the strings `mongodb`, `sql`, `database`.
```shell
python3 clms.py -n 'martian-bank,sock-shop' -e 'mongodb,sql,database'
```

#### Command-line help
Command-line help is available using the `-h` or `--help` parameters.

```shell
usage: clms.py [-h] -n NAMESPACES [-e EXCLUDE] [-d]



███████ ██     ██ ██    ██      ██████ ██    ██ ██████  ███████ ██████
██      ██     ██ ██    ██     ██       ██  ██  ██   ██ ██      ██   ██
█████   ██  █  ██ ██    ██     ██        ████   ██████  █████   ██████
██      ██ ███ ██ ██    ██     ██         ██    ██   ██ ██      ██   ██
███████  ███ ███   ██████       ██████    ██    ██████  ███████ ██   ██


                                         Eastern Washington University

   ____ _    _   _ ____ _____ _____ ____
  / ___| |  | | | / ___|_   _| ____|  _ \
 | |   | |  | | | \___ \ | | |  _| | |_) |
 | |___| |__| |_| |___) || | | |___|  _ <
  \____|_____\___/|____/ |_| |_____|_| \_\
  _     ___ _____ _____ ______   ______ _     _____
 | |   |_ _|  ___| ____/ ___\ \ / / ___| |   | ____|
 | |    | || |_  |  _|| |    \ V / |   | |   |  _|
 | |___ | ||  _| | |__| |___  | || |___| |___| |___
 |_____|___|_|   |_____\____| |_| \____|_____|_____|
  __  __    _    _   _    _    ____ _____ __  __ _____ _   _ _____
 |  \/  |  / \  | \ | |  / \  / ___| ____|  \/  | ____| \ | |_   _|
 | |\/| | / _ \ |  \| | / _ \| |  _|  _| | |\/| |  _| |  \| | | |
 | |  | |/ ___ \| |\  |/ ___ \ |_| | |___| |  | | |___| |\  | | |
 |_|  |_/_/   \_\_| \_/_/   \_\____|_____|_|  |_|_____|_| \_| |_|
  ______   ______ _____ _____ __  __
 / ___\ \ / / ___|_   _| ____|  \/  |
 \___ \\ V /\___ \ | | |  _| | |\/| |
  ___) || |  ___) || | | |___| |  | |
 |____/ |_| |____/ |_| |_____|_|  |_|


This research introduces the Cluster Lifecycle Management System (CLMS),
a preemptive approach to container lifecycle management in Kubernetes.

Creation date: 04.23.25 - alhumaw

options:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        Comma separated list of deployments to exclude
  -d, --debug           Enable API debugging

required arguments:
  -n NAMESPACES, --namespaces NAMESPACES
                        Selected namespaces for CLMS to monitor
```

### Example source code
The source code for this program can be found [here](clms.py).
