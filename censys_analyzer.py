#!/usr/bin/env python3
from cortexutils.analyzer import Analyzer
from censys.certificates import CensysCertificates
from censys.ipv4 import CensysIPv4
from censys.websites import CensysWebsites
from censys.base import CensysNotFoundException, CensysRateLimitExceededException, CensysUnauthorizedException


class CensysAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)

        self.__uid = self.get_param(
            'config.uid',
            None,
            'No UID for Censys given. Please add it to the cortex configuration.'
        )
        self.__api_key = self.get_param(
            'config.key',
            None,
            'No API-Key for Censys given. Please add it to the cortex configuration.'
        )

    def search_hosts(self, ip):
        """
        Searches for a host using its ipv4 address

        :param ip: ipv4 address as string
        :type ip: str
        :return: dict
        """
        c = CensysIPv4(api_id=self.__uid, api_secret=self.__api_key)
        return c.view(ip)

    def search_certificate(self, hash):
        """
        Searches for a specific certificate using its hash

        :param hash: certificate hash
        :type hash: str
        :return: dict
        """
        c = CensysCertificates(api_id=self.__uid, api_secret=self.__api_key)
        return c.view(hash)

    def search_website(self, dom):
        """
        Searches for a website using the domainname
        :param dom: domain
        :type dom: str
        :return: dict
        """
        c = CensysWebsites(api_id=self.__uid, api_secret=self.__api_key)
        return c.view(dom)

    def run(self):
        try:
            if self.data_type == 'ip':
                self.report({
                    'ip': self.search_hosts(self.get_data())
                })
            elif self.data_type == 'hash':
                self.report({
                    'hash': self.search_certificate(self.get_data())
                })
            elif self.data_type == 'domain' or self.data_type == 'fqdn':
                self.report({
                    'website': self.search_website(self.get_data())
                })
            else:
                self.error('Data type not supported. Please use this analyzer with data types hash, ip or domain.')
        except CensysNotFoundException:
            self.error('{} not found.'.format(self.get_data()))
        except CensysUnauthorizedException:
            self.error('Censys raised NotAuthorizedException. Please check your credentials.')
        except CensysRateLimitExceededException:
            self.error('Rate limit exceeded.')

    def summary(self, raw):
        taxonomies = []
        if 'ip' in raw:
            raw = raw['ip']
            service_count = len(raw.get('protocols', []))
            heartbleed = raw.get('443', {}).get('https', {}).get('heartbleed', {}).get('heartbleed_vulnerable', False)

            taxonomies.append(self.build_taxonomy('info', 'Censys', 'ServiceCount', service_count))
            if heartbleed:
                taxonomies.append(self.build_taxonomy('malicious', 'Censys', 'Heartbleed', 'vulnerable'))
        elif 'website' in raw:
            pass
        elif 'cert' in raw:
            pass

        return {
            'taxonomies': taxonomies
        }


if __name__ == '__main__':
    CensysAnalyzer().run()
