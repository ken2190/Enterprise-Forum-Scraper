import sh

default_ports = [5900, 5901, 5902, 27017, 27018, 27019, 7000, 70001]


class ShodanGatherer:

    token = "k2ibdtThKh6HU6E2uWCP7VhJDPfjUTTq"

    def scan(sample):
        
        



def gather_ips(**kwargs):
    # Load ports
    ports = kwargs.get("ports", default_ports)

    # Run scan
    sh.masscan(["-p%s" % ",".join(ports), "0.0.0.0/8"])

