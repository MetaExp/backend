# MetaExp: Interactive Explanation and Exploration of Large Knowledge Graphs
[![Build Status](https://travis-ci.org/KDD-OpenSource/32de-python.svg?branch=master)](https://travis-ci.org/KDD-OpenSource/32de-python)
[![Coverage Status](https://coveralls.io/repos/github/KDD-OpenSource/32de-python/badge.svg?branch=master)](https://coveralls.io/github/KDD-OpenSource/32de-python?branch=master)

MetaExp is an open-source, interactive framework for graph exploration that can automatically discover hidden knowledge in large graph databases.
It incorporates the domain knowledge of the user to define a unique and personalized view on the graph.

## Contact and citation
> Behrens, F., Bischoff, S., Ladenburger, P., Rückin, J., Seidel, L., Stolp, F., Vaichenker, M.,  Ziegler, A., Mottin, D., Aghaei, F., Müller, E., Preusse, M., Müller, N. & Hunger, M. (2018). MetaExp: Interactive Explanation and Exploration of Large Knowledge Graphs. *WWW*

## Description
We present MetaExp, a system that assists the user during the exploration of large knowledge graphs, given two sets of initial nodes.
At its core, MetaExp presents a small set of meta-paths to the user, which are sequences of relationships among node types.
Such meta-paths do not overwhelm the user with complex structures, yet they preserve semantically-rich relationships in a graph.
MetaExp engages the user in an interactive procedure, which involves simple meta-paths evaluations to infer a user-specific similarity measure.
This similarity measure incorporates the domain knowledge and the preferences of the user, overcoming the fundamental limitations of previous methods based on local node neighborhoods or statically determined similarity scores.
Our system provides a user-friendly interface for searching initial nodes and guides the user towards progressive refinements of the meta-paths.
The system is demonstrated on three datasets, Freebase, a movie database, and a biological network.

## Installation
To deploy our system including neo4j, the neo4j graph algorithm component, the UI and our server install docker on your system and run `deployment/docker-deployment.sh`.
This will install a clean version from the alpha-dev and the master branches and doesn't include your local code changes.
If the API should be served ssl encrypted, set the environment variable `METAEXP_HTTPS` to `true` and provide `api.crt` and `api.key` in the `https` folder.

# Development
We have a collection of some helpful scripts you might want to use when developing for this project.

## Scripts

### Build and run
To build your own local code use `deployment/build-*.sh /path/to/code` (e.g. `deployment/build-server.sh .`) and to
run a single container `deployment/run-*.sh [PORT]`.
By default Neo4j browser is listening on port `7474`, bolt is available on port `7687` and
our server is listening on port `8000` for all hosts.
If you start the additional neo4j containers with `run-neo4j-helmholtz.sh` and `run-neo4j-commerzbank.sh`,
they are listening on the ports +10 for Helmholtz and +20 for the Commerzbank data.
All the neo4j containers are based on the `neo4j-graph-algorithms` image.
To change the default port simply specify the `PORT` parameter when running `deployment/run-*.sh [PORT]`.
We use redis for our meta paths. Start the container by executing deployment/run-redis.sh.
After startup of the redis container simply execute localhost:8000/test-import in your browser. This command fills the
redis store with Helmholtz meta paths.

### Updating files in containers
If you want to update any files in your container you can use the
`deployment/copy-to-container.sh [CONTAINER] [PATH/IN/CONTAINER]` command.
All you have to do is specify the container name or id you want to copy your updated files to.
The second parameter is optional.
If you have changed the path to the project files *in the container* you need to specify this path here.
**WARNING** This will overwrite any changes made in the container.

Tutorials for installing Docker: [Mac](https://docs.docker.com/docker-for-mac/install/), [Windows](https://docs.docker.com/docker-for-windows/install/) and [Ubuntu](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/).

## Usage
This is the server component of the MetaExp system.

# Development
## Logging Guideline
Use MetaExp-Logger. For example if you wanted to equip the module Example with a logger, you would simply create a child logger by `logging.getLogger('MetaExp.Example')`. If you wanted to use a logger for
each class, you would define it as `self.logger = logging.getLogger('MetaExp.{}'.format(__class__.__name__))`.

## Contributors
Freya Behrens, Sebastian Bischoff, Pius Ladenburger, Julius Rückin, Laurenz Seidel, Fabian Stolp, Michael Vaichenker and Adrian Ziegler.

## License
This work is licensed under [MIT License](LICENSE.md).
