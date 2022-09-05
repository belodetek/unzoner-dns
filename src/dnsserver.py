#!/usr/bin/env python3

import sys
import json
import threading

from time import sleep, strftime, gmtime
from datetime import datetime
from dnslib.server import DNSServer
from dnslib import DNSRecord, CNAME, A,AAAA, RR, SOA, NS, QTYPE

from config import *
from utils import *


cache_ipv = {
    4: {
        "ip": get_ipv(),
        "ts": datetime.utcnow()
    },
    6: {
        "ip": get_ipv(6),
        "ts": datetime.utcnow()
    }
}

cache_node = {
    4: dict(), 6: dict()
}

class DomainName(str):
    def __getattr__(self, item):
        return DomainName(item + '.' + self)

    
class BlackboxResolver:
    def resolve(self, request, handler):
        if DEBUG: print(request, handler, handler.__dict__)
        domain = DomainName(DNS_DOMAIN)
        reply = request.reply()
        host = str(request.q.qname).lower()

        ttl = (datetime.utcnow() - cache_ipv[4]['ts']).total_seconds()
        if ttl > DNS_TTL:
            cache_ipv[4]['ts'] = datetime.utcnow()
            cache_ipv[4]['ip'] = get_ipv()
            if DEBUG: print('cache(miss): ip={} ttl={}'.format(
                cache_ipv[4]['ip'],
                ttl
            ))
        ipv4 = cache_ipv[4]['ip']

        ttl = (datetime.utcnow() - cache_ipv[6]['ts']).total_seconds()
        if ttl > DNS_TTL:
            cache_ipv[6]['ts'] = datetime.utcnow()
            cache_ipv[6]['ip'] = get_ipv(6)
            if DEBUG: print('cache(miss): ip={} ttl={}'.format(
                cache_ipv[6]['ip'],
                ttl
            ))
        ipv6 = cache_ipv[6]['ip']
        
        if ipv4 == ipv6: ipv6 = None
        t = int(strftime('%Y%m%d01', gmtime()))
        c_ip = handler.client_address[0]
        
        soa_record = SOA(
            mname=domain.ns1,
            rname=domain.admin,
            times=(
                t,
                60 * 60 * 1,
                60 * 60 * 3,
                60 * 60 * 24,
                60 * 60 * 1
            )
        )
        
        ns_record = NS(domain.ns1)
        records = [A(ipv4.decode()), soa_record, ns_record]
        if ipv6: records.append(AAAA(ipv6.decode()))
        
        records = {
            domain: records,
            domain.ns1: [A(ipv4.decode())],
            domain.admin: [CNAME(domain)],
        }

        print(
            'client={} c_ip={} qtype={} qname={} ipv4={} ipv6={}'.format(
                handler.client_address,
                c_ip,
                request.q.qtype,
                host,
                ipv4,
                ipv6
            )
        )

        if request.q.qtype in [6]: # SOA
            reply.add_answer(
                RR(
                    rname=domain,
                    rtype=QTYPE.SOA,
                    rclass=1,
                    ttl=DNS_TTL*5,
                    rdata=soa_record
                )
            )
            return reply
            
        if request.q.qtype in [2]: # NS
            if str(request.q.qname) == domain:
                reply.add_answer(
                    RR(
                        rname=domain,
                        rtype=QTYPE.NS,
                        rclass=1,
                        ttl=DNS_TTL*5,
                        rdata=ns_record
                    )
                )
            else:
                reply.add_answer(
                    RR(
                        rname=domain,
                        rtype=QTYPE.SOA,
                        rclass=1,
                        ttl=DNS_TTL*5,
                        rdata=soa_record
                    )
                )
            return reply

        if str(request.q.qname) in [str(NS(domain.ns1)), domain]:
            if request.q.qtype in [1]: # A
                if ipv4: reply.add_answer(
                    *RR.fromZone(
                        '{} {} A {}'.format(
                            host,
                            DNS_TTL*5,
                            ipv4
                        )
                    )
                )
            
            if request.q.qtype in [28]: # AAAA
                if ipv6: reply.add_answer(
                    *RR.fromZone(
                        '{} {} AAAA {}'.format(
                            host,
                            DNS_TTL*5,
                            ipv6
                        )
                    )
                )
            return reply

        try:
            country = ISO_MAP[host.split('.')[0].upper()]
        except KeyError:
            if request.q.qtype in [1]: # A
                reply.add_answer(
                    *RR.fromZone(
                        '{} {} A {}'.format(
                            host,
                            0,
                            DEFAULT_A
                        )
                    )
                )
                return reply
            elif request.q.qtype in [28]: # AAAA
                reply.add_answer(
                    *RR.fromZone(
                        '{} {} AAAA {}'.format(
                            host,
                            0,
                            DEFAULT_AAAA
                        )
                    )
                )
            else:
                return reply    
        
        if request.q.qtype in [1]: # A
            af = 4
            try:
                try:
                    ttl = (datetime.utcnow() - cache_node[af][country]['ts']).total_seconds()
                except:
                    cache_node[af][country] = dict()
                    cache_node[af][country]['ts'] = datetime.utcnow()
                    cache_node[af][country]['ip'] = None
                    ttl = DNS_TTL + 1

                if ttl > DNS_TTL:
                    cache_node[af][country]['ts'] = datetime.utcnow()
                    cache_node[af][country]['ip'] = get_node(
                        client_ip=c_ip,
                        country=country
                    )
                    if DEBUG: print('cache(miss): ip={} ttl={} country={}'.format(
                        cache_node[af][country]['ip'],
                        ttl,
                        country
                    ))
                ip = cache_node[af][country]['ip'].decode()
                if DEBUG: print('cache={} ip={}'.format(cache_node, ip))
                assert ip
            except:
                reply.add_answer(
                    *RR.fromZone(
                        '{} {} A {}'.format(
                            host,
                            0,
                            DEFAULT_A
                        )
                    )
                )
                return reply

            reply.add_answer(
                *RR.fromZone(
                    '{} {} A {}'.format(
                        host,
                        DNS_TTL,
                        ip
                    )
                )
            )
        
        elif request.q.qtype in [28]: # AAAA
            af = 6
            try:
                try:
                    ttl = (datetime.utcnow() - cache_node[af][country]['ts']).total_seconds()
                except:
                    cache_node[af][country] = dict()
                    cache_node[af][country]['ts'] = datetime.utcnow()
                    cache_node[af][country]['ip'] = None
                    ttl = DNS_TTL + 1

                if ttl > DNS_TTL:
                    cache_node[af][country]['ts'] = datetime.utcnow()
                    cache_node[af][country]['ip'] = get_node(
                        proto=af,
                        client_ip=c_ip,
                        country=country
                    )
                    if DEBUG: print('cache(miss): ip={} ttl={} country={}'.format(
                        cache_node[af][country]['ip'],
                        ttl,
                        country
                    ))
                ip = cache_node[af][country]['ip'].decode()
                if DEBUG: print('cache={} ip={}'.format(cache_node, ip))
                assert ip
            except:
                reply.add_answer(
                    *RR.fromZone(
                        '{} {} AAAA {}'.format(
                            host,
                            0,
                            DEFAULT_AAAA
                        )
                    )
                )
                return reply

            reply.add_answer(
                *RR.fromZone(
                    '{} {} AAAA {}'.format(
                        host,
                        DNS_TTL,
                        ip
                    )
                )
            )            

        else: print(request.q.qtype, country, host)
        return reply


if __name__ == '__main__':
    try:
        countries = json.loads(get_countries())
        ISO_MAP = {v: k for k, v in countries.items()}
    except AssertionError:
        sys.exit(1)
    
    resolver = BlackboxResolver()
    
    server = DNSServer(
        resolver,
        port=PORT,
        address=LISTEN_ADDR,
        logger=None,
        tcp=False
    )
    
    thread = threading.Thread(target=server.start_thread())
    thread.daemon = True
    thread.start()
    
    print(
        'server running in thread: {} ({}:{})'.format(
            thread.name,
            LISTEN_ADDR,
            PORT
        )
    )

    try:
        while True:
            sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
