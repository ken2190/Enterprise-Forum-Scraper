FROM dperson/torproxy
ENV PASSWORD tor_proxy

RUN echo "forward-socks5 / 127.0.0.1:9050" >> /etc/privoxy/config
