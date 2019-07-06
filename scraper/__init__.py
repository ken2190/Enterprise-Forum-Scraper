from scraper.antichat import AntichatScrapper
from scraper.breachforums import BreachForumsScrapper
from scraper.exploit import ExploitScrapper
from scraper.exploit_private import ExploitPrivateScrapper
from scraper.lolzteam import LolzScrapper
from scraper.verified import VerifiedScrapper
from scraper.sentryMBA import SentryMBAScrapper
from scraper.bitcointalk import BitCoinTalkScrapper
from scraper.psbdmp import PasteBinScrapper
from scraper.wallstreet import WallStreetScrapper
from scraper.kickass import KickAssScrapper
from scraper.galaxy3 import Galaxy3Scrapper
from scraper.badkarma import BadKarmaScrapper
from scraper.antichat_v2 import Antichatv2Scrapper
from scraper.sinister import SinisterScrapper
from scraper.sentryMBA_v2 import SentryMBAv2Scrapper
from scraper.verified_carder import VerifiedCarderScrapper
from scraper.carder import CarderScrapper
from scraper.ccc_mn import CCCMNScrapper
from scraper.cracked_to import CrackedToScrapper
from scraper.sky_fraud import SkyFraudScrapper
from scraper.nulled import NulledScrapper
from scraper.dark_skies import DarkSkiesScrapper
from scraper.procrd import ProcrdScrapper
from scraper.hydra import HydraScrapper
from scraper.blackbox import BlackBoxScrapper
from scraper.v3rmillion import V3RMillionScrapper
from scraper.thehub import TheHubScrapper
from scraper.justpasteit import JustPasteItScrapper
from scraper.silk_road3 import SilkRoad3Scrapper
from scraper.hiddenhand import HiddenHandScrapper
from scraper.prvtzone import PrvtZoneScrapper
from scraper.runion import RUnionScrapper
from scraper.nulledbb_selenium import NulledBBScrapper
from scraper.russian_carders import RussianCarderScrapper
from scraper.blackhatworld import BlackHatWorldScrapper
from scraper.thecc import TheCCScrapper
from scraper.prtship import PrtShipScrapper
from scraper.carding_school import CardingSchoolScrapper
from scraper.darknet import DarknetScrapper
from scraper.verified_v2 import Verifiedv2Scrapper

SCRAPER_MAP = {
    'antichat': AntichatScrapper,
    'breachforums': BreachForumsScrapper,
    'exploit': ExploitScrapper,
    'exploitprivate': ExploitPrivateScrapper,
    'lolzteam': LolzScrapper,
    'verified': VerifiedScrapper,
    'verified1': VerifiedScrapper,
    'sentrymba': SentryMBAScrapper,
    'bitcointalk': BitCoinTalkScrapper,
    'psbdmp': PasteBinScrapper,
    'wallstreet': WallStreetScrapper,
    'kickass': KickAssScrapper,
    'galaxy3': Galaxy3Scrapper,
    'badkarma': BadKarmaScrapper,
    'antichat_v2': Antichatv2Scrapper,
    'sinister': SinisterScrapper,
    'sentrymba_v2': SentryMBAv2Scrapper,
    'verified_carder': VerifiedCarderScrapper,
    'carder': CarderScrapper,
    'ccc_mn': CCCMNScrapper,
    'cracked_to': CrackedToScrapper,
    'sky_fraud': SkyFraudScrapper,
    'nulled': NulledScrapper,
    'dark_skies': DarkSkiesScrapper,
    'procrd': ProcrdScrapper,
    'hydra': HydraScrapper,
    'blackbox': BlackBoxScrapper,
    'v3rmillion': V3RMillionScrapper,
    'thehub': TheHubScrapper,
    'justpasteit': JustPasteItScrapper,
    'silk_road3': SilkRoad3Scrapper,
    'hiddenhand': HiddenHandScrapper,
    'prvtzone': PrvtZoneScrapper,
    'runion': RUnionScrapper,
    'nulledbb': NulledBBScrapper,
    'russian_carders': RussianCarderScrapper,
    'blackhatworld': BlackHatWorldScrapper,
    'thecc': TheCCScrapper,
    'prtship': PrtShipScrapper,
    'carding_school': CardingSchoolScrapper,
    'darknet': DarknetScrapper,
    'verifiedv2': Verifiedv2Scrapper,
}
