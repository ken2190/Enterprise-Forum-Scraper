from scraper.antichat import AntichatScrapper
from scraper.breachforums import BreachForumsScrapper
from scraper.exploit import ExploitScrapper
from scraper.exploit_private import ExploitPrivateScrapper
from scraper.lolzteam import LolzScrapper
from scraper.verified import VerifiedScScrapper
from scraper.sentryMBA import SentryMBAScrapper
from scraper.bitcointalk import BitCoinTalkScrapper
from scraper.psbdmp import PasteBinScrapper
from scraper.wallstreet import WallStreetScrapper
from scraper.kickass import KickAssScrapper
from scraper.galaxy3 import Galaxy3Scrapper
from scraper.badkarma import BadKarmaScrapper
from scraper.sinister import SinisterScrapper
from scraper.sentryMBA_v2 import SentryMBAv2Scrapper
from scraper.verified_carder import VerifiedCarderScrapper
from scraper.carderme import CarderMeScrapper
from scraper.ccc_mn import CCCMNScrapper
from scraper.cracked_to import CrackedToScrapper
from scraper.sky_fraud import SkyFraudScrapper
from scraper.nulled_to import NulledToScrapper
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
from scraper.nulledbb import NulledBBScrapper
from scraper.russian_carders import RussianCarderScrapper
from scraper.blackhatworld import BlackHatWorldScrapper
from scraper.thecc import TheCCScrapper
from scraper.prtship import PrtShipScrapper
from scraper.carding_school import CardingSchoolScrapper
from scraper.l33t import L33TScrapper
from scraper.lcpcc import LCPScrapper
from scraper.raidforums import RaidForumsScrapper
from scraper.marviher import MarviherScrapper
from scraper.xss import XSSScrapper
from scraper.hackforums import HackForumsScrapper
from scraper.rstforums import RSTForumsScrapper
from scraper.bhf_io import BHFIOScrapper
from scraper.crdclub import CrdClubScrapper
from scraper.carderhub import CarderHubScrapper
from scraper.omerta import OmertaScrapper
from scraper.primeforums import PrimeForumsScrapper
from scraper.leakportal import LeakPortalScrapper
from scraper.hoxforum import HoxForumScrapper
from scraper.scrapeboxforum import ScrapeBoxForumScrapper
from scraper.fraudstercrew import FraudstercrewScrapper
from scraper.crackx import CrackXScrapper
from scraper.Oday import OdayScrapper
from scraper.hashkiller import HashKillerScrapper
from scraper.darkwebs import DarkWebsScrapper
from scraper.fuckav import FuckavScrapper
from scraper.canadahq import CanadaHQScrapper
from scraper.youhack import YouHackScrapper
from scraper.wwhclub import WwhClubScrapper
from scraper.korovka import KorovkaScrapper
from scraper.enclave import EnclaveScrapper
from scraper.crimemarket import CrimeMarketScrapper
from scraper.phreaker import PhreakerScrapper
from scraper.prologic import ProLogicScrapper
from scraper.ogusers import OgUsersScrapper
from scraper.center_club import CenterClubScrapper
from scraper.crackingpro import CrackingProScrapper
from scraper.xrpchat import XrpChatScrapper
from scraper.carding_team import CardingTeamScrapper
from scraper.thebot import TheBotScrapper
from scraper.italian_deep_web import ItalianDeepWebScrapper
from scraper.dnm_avengers import DNMAvengersScrapper
from scraper.oxsec import Ox00SecScrapper
from scraper.rosa_negra import RosaNegraScrapper
from scraper.envoy import EnvoyScrapper
from scraper.bitshacking import BitsHackingScrapper
from scraper.safetyskyhacks import SafetySkyHacksScrapper
from scraper.skynetzone import SkyNetZoneScrapper
from scraper.mashacker import MasHackerScrapper
from scraper.hackthissite import HackThisSiteScrapper
from scraper.devilteam import DevilTeamScrapper
from scraper.devilgroup import DevilGroupScrapper
from scraper.demonforums import DemonForumsScrapper
from scraper.crack_community import CrackCommunityScrapper
from scraper.superbay import SuperBayScrapper
from scraper.chknet import ChkNetScrapper
from scraper.torigon import TorigonScrapper
from scraper.psxhax import PsxhaxScrapper
from scraper.phcracker import PHCrackerScrapper
from scraper.rutor import RutorScrapper
from scraper.freehack import FreeHackScrapper
from scraper.void_to import VoidToScrapper
from scraper.cebulka import CebulkaScrapper
from scraper.dfas import DfasScrapper
from scraper.majestic_garden import MajesticGardenScrapper
from scraper.torum import TorumScrapper
from scraper.ciphers import CiphersScrapper
from scraper.bigmmo import BigmmoScrapper
from scraper.runtime import RunTimeScrapper


SCRAPER_MAP = {
    'antichat': AntichatScrapper,
    'breachforums': BreachForumsScrapper,
    'exploit': ExploitScrapper,
    'exploitprivate': ExploitPrivateScrapper,
    'lolzteam': LolzScrapper,
    'verified': VerifiedScScrapper,
    'sentrymba': SentryMBAScrapper,
    'bitcointalk': BitCoinTalkScrapper,
    'psbdmp': PasteBinScrapper,
    'wallstreet': WallStreetScrapper,
    'kickass': KickAssScrapper,
    'galaxy3': Galaxy3Scrapper,
    'badkarma': BadKarmaScrapper,
    'sinister': SinisterScrapper,
    'sentrymba_v2': SentryMBAv2Scrapper,
    'verified_carder': VerifiedCarderScrapper,
    'carder': CarderMeScrapper,
    'ccc_mn': CCCMNScrapper,
    'cracked_to': CrackedToScrapper,
    'sky_fraud': SkyFraudScrapper,
    'nulled_to': NulledToScrapper,
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
    'l33t': L33TScrapper,
    'lcpcc': LCPScrapper,
    'raidforums': RaidForumsScrapper,
    'marviher': MarviherScrapper,
    'xss': XSSScrapper,
    'hackforums': HackForumsScrapper,
    'rstforums': RSTForumsScrapper,
    'bhfio': BHFIOScrapper,
    'crdclub': CrdClubScrapper,
    'carderhub': CarderHubScrapper,
    'omerta': OmertaScrapper,
    'primeforums': PrimeForumsScrapper,
    'leakportal': LeakPortalScrapper,
    'hoxforum': HoxForumScrapper,
    'scrapeboxforum': ScrapeBoxForumScrapper,
    'fraudstercrew': FraudstercrewScrapper,
    'crackx': CrackXScrapper,
    '0day': OdayScrapper,
    'hashkiller': HashKillerScrapper,
    'darkwebs': DarkWebsScrapper,
    'fuckav': FuckavScrapper,
    'canadahq': CanadaHQScrapper,
    'youhack': YouHackScrapper,
    'wwhclub': WwhClubScrapper,
    'korovka': KorovkaScrapper,
    'enclave': EnclaveScrapper,
    'crimemarket': CrimeMarketScrapper,
    'phreaker': PhreakerScrapper,
    'prologic': ProLogicScrapper,
    'ogusers': OgUsersScrapper,
    'center_club': CenterClubScrapper,
    'crackingpro': CrackingProScrapper,
    'xrpchat': XrpChatScrapper,
    'carding_team': CardingTeamScrapper,
    'thebot': TheBotScrapper,
    'italiandeepweb': ItalianDeepWebScrapper,
    'dnmavengers': DNMAvengersScrapper,
    'oxsec': Ox00SecScrapper,
    'rosanegra': RosaNegraScrapper,
    'envoy': EnvoyScrapper,
    'bitshacking': BitsHackingScrapper,
    'safetyskyhacks': SafetySkyHacksScrapper,
    'skynetzone': SkyNetZoneScrapper,
    'mashacker': MasHackerScrapper,
    'hackthissite': HackThisSiteScrapper,
    'devilteam': DevilTeamScrapper,
    'devilgroup': DevilGroupScrapper,
    'demonforums': DemonForumsScrapper,
    'crackcommunity': CrackCommunityScrapper,
    'superbay': SuperBayScrapper,
    'chknet': ChkNetScrapper,
    'torigon': TorigonScrapper,
    'psxhax': PsxhaxScrapper,
    'phcracker': PHCrackerScrapper,
    'rutor': RutorScrapper,
    'freehack': FreeHackScrapper,
    'void_to': VoidToScrapper,
    'cebulka': CebulkaScrapper,
    'dfas': DfasScrapper,
    'majestic_garden': MajesticGardenScrapper,
    'torum': TorumScrapper,
    'ciphers': CiphersScrapper,
    'bigmmo': BigmmoScrapper,
    'runtime': RunTimeScrapper,
}
