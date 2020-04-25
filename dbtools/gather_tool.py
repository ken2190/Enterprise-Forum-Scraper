import sh

default_ports = [5900, 5901, 5902, 27017, 27018, 27019, 7000, 70001]


def gather_ips(**kwargs):
    # Load ports
    ports = kwargs.get("ports", default_ports)

    # Run scan
    sh.masscan(["-p%s" % ",".join(ports), "0.0.0.0/8"])
