import twisted

from OpenSSL.crypto import FILETYPE_PEM
from twisted.web.iweb import IPolicyForHTTPS
from zope.interface.declarations import implementer
from scrapy.core.downloader.contextfactory import BrowserLikeContextFactory

from twisted.internet.ssl import (
    optionsForClientTLS,
    platformTrust
)

@implementer(IPolicyForHTTPS)
class MazaCertContextFactory(BrowserLikeContextFactory):

    def creatorForNetloc(self, hostname, port):
        with open('ssl_certificate/maza.pem') as cert_file:
            cert = cert_file.read()
        myClientCert = twisted.internet.ssl.PrivateCertificate.loadPEM(
            cert
        )
        return optionsForClientTLS(hostname.decode("ascii"),
                                   trustRoot=platformTrust(),
                                   clientCertificate=myClientCert,
                                   extraCertificateOptions={
                                        'method': self._ssl_method,
                                   })
