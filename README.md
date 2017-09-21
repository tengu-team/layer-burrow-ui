# layer-burrow-ui
Burrow is a monitoring companion for [Apache Kafka](https://jujucharms.com/kafka) that provides consumer lag checking as a service without the need for specifying thresholds. It monitors committed offsets for all consumers and calculates the status of those consumers on demand. An HTTP endpoint is provided to request status on demand, as well as provide other Kafka cluster information.

Burrow is a LinkedIn project and can be found [here](https://github.com/linkedin/Burrow).

# Usage
```
juju deploy burrow
juju add-relation burrow kafka
juju deploy burrow-ui
juju add-relation burrow-ui burrow
juju expose burrow-ui
```

## Authors

This software was created in the [IDLab research group](https://www.ugent.be/ea/idlab) of [Ghent University](https://www.ugent.be) in Belgium. This software is used in [Tengu](https://tengu.io), a project that aims to make experimenting with data frameworks and tools as easy as possible.

 - Sander Borny <sander.borny@ugent.be>

