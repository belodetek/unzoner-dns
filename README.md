# unzoner-dns
> [black.box Unzoner](https://unzoner.com) DNS server, inspired by [this](https://stackoverflow.com/a/33531753/1559300) post

This block implements a simple DNS server, which responds to `A` and `AAAA` dns queries,
using responses from [Unzoner API backend](https://github.com/belodetek/unzoner-api). The
format for the DNS query follows `{{alpha-2}}.{{dns_sub_domain}}.{{dns_domain}}`. ISO-3166
country codes are described [here](https://www.iban.com/country-codes) (e.g.)

```sh
$ dig +short CA.blackbox.unzoner.com
174.138.72.255
```

Delegate your `{{dns_sub_domain}}` under `{{dns_domain}}` to the endpoint running the DNS
server and ensure public access to `53/udp` port (e.g.)

```sh
$ dig +short NS blackbox.unzoner.com
ns1.blackbox.unzoner.com.
```

## usage
* ensure the API backend is deployed and configured
* add the latest [unzoner-dns](https://hub.balena.io/organizations/belodetek/blocks) block to your balenaCloud fleet composition (e.g. `amd64`)

```yml
version: '2.4'

services:
  unzoner-api:
    ...

  unzoner-dns:
    # https://www.balena.io/docs/learn/develop/blocks/#using-your-block-in-other-projects
    image: bh.cr/belodetek/unzoner-dns-amd64
    restart: unless-stopped
    ports:
      - "53:53/udp"
    # https://www.balena.io/docs/reference/supervisor/docker-compose/#labels
    labels:
      io.balena.update.strategy: download-then-kill
```

* set `API_SECRET` fleet environment variable to match API backend
