import requests
from time import time, sleep
import random
import logging
import threading
import argparse
import json

class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    END = '\033[0m'

logging.basicConfig(level=logging.INFO, format='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s', datefmt='%H:%M:%S',)
logging.addLevelName(logging.INFO, f'{Colors.BLUE}INFO{Colors.END}')
logging.addLevelName(logging.WARNING, f'{Colors.YELLOW}WARN{Colors.END}')
logging.addLevelName(logging.ERROR, f'{Colors.RED}ERRO{Colors.END}')

class User:
    def __init__(self, name, authorization, min_balance, proxies=None, daily_cipher=None, tap_range=[50, 500]):
        self.name = name
        self.authorization = authorization
        self.min_balance = min_balance
        self.proxies = proxies
        self.daily_cipher = daily_cipher
        self.running = True
        self.tap_range = tap_range
        
        self.upgrade_logger = logging.getLogger(name=f"{self.name} U")
        self.upgrade_thread = threading.Thread(target=self.upgrade_loop)
        self.upgrade_thread.start()

        self.tap_logger = logging.getLogger(name=f"{self.name} T")
        self.tap_thread = threading.Thread(target=self.tap_loop)
        self.tap_thread.start()
    
        self.cipher_logger = logging.getLogger(name=f"{self.name} C")
        self.cipher_thread = threading.Thread(target=self.cipher_loop)
        self.cipher_thread.start()

        self.task_logger = logging.getLogger(name=f"{self.name} D")
        self.task_thread = threading.Thread(target=self.task_loop)
        self.task_thread.start()

    def safe_post(self, url, data=None, logger=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Android 12; Mobile; rv:102.0) Gecko/102.0 Firefox/102.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://hamsterkombatgame.io/',
            'Authorization': self.authorization,
            'Origin': 'https://hamsterkombatgame.io',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
        }

        try:
            return requests.post(url, headers=headers, json=data, timeout=5).json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            if logger:
                logger.error(e)

            return None
    
    def safe_sleep(self, seconds):
        for _ in range(seconds):
            if not self.running:
                break
            sleep(1)

    def task_loop(self):
        self.task_logger.info('Starting ...')
        
        while self.running:
            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/list-tasks", logger=self.task_logger)
            
            if (not response) or 'error_code' in response:
                self.task_logger.error(f"Failed to get tasks.")
                self.task_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue

            for task in response['tasks']:
                if task['isCompleted'] or task['id'] in ('invite_friends'):
                    continue

                inner_response = self.safe_post("https://api.hamsterkombatgame.io/clicker/check-task", data={
                    'taskId': task['id']
                }, logger=self.task_logger)
            
                if (not inner_response) or 'error_code' in inner_response:
                    self.task_logger.error(f"Failed to check task {task['id']}")
                    self.task_logger.warning(f"Waiting {30} seconds...")
                    self.safe_sleep(30)
                    continue
                
                self.task_logger.info(f"Checked task {task['id']} successfully.")
                self.safe_sleep(30)
            
            self.safe_sleep(60 * 5)

    def cipher_loop(self):
        self.cipher_logger.info('Starting ...')
        
        if not self.daily_cipher:
            self.cipher_logger.warning('No cipher, exiting ...')
            return 
        
        while self.running:
            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/claim-daily-cipher", data={
                'cipher': self.daily_cipher,
            }, logger=self.cipher_logger)
            
            if (not response) or 'error_code' in response:
                self.cipher_logger.error(f"Failed to claim cipher.")
                self.cipher_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue
            
            self.cipher_logger.info(f"Claimed cipher successfully.")
            self.daily_cipher = None
            break
        
    def tap_loop(self):
        self.tap_logger.info('Starting ...')

        while self.running:
            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/sync", logger=self.tap_logger)

            if (not response) or 'error_code' in response:
                self.tap_logger.error(f"Failed to sync.")
                self.tap_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue

            current_balance = float(response['clickerUser']['balanceCoins'])
            available_taps = int(response['clickerUser']['availableTaps'])
            self.tap_logger.info(f"Current balance: {current_balance:,}")
            self.tap_logger.info(f"Available taps: {available_taps:,}")

            sleep_between_clicks = random.randint(5, 15)
            taps = random.randint(*self.tap_range)
            
            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/tap", data={
                'availableTaps': available_taps,
                'count': taps,
                'timestamp': int(time() * 1000),
            }, logger=self.tap_logger)
            if (not response) or 'error_code' in response:
                self.tap_logger.error(f"Failed to tap.")
                self.tap_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue
            self.tap_logger.info(f"Tapped for '{taps}' times successfully.")

            self.tap_logger.info(f"Waiting {sleep_between_clicks} seconds before next tap...")

            self.safe_sleep(sleep_between_clicks)


    def upgrade_loop(self):
        self.upgrade_logger.info('Starting ...')

        while self.running:
            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/sync", logger=self.upgrade_logger)

            if (not response) or 'error_code' in response:
                self.upgrade_logger.error(f"Failed to sync.")
                self.upgrade_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue
            
            current_balance = float(response['clickerUser']['balanceCoins'])
            self.upgrade_logger.info(f"Current Balance: {current_balance:,}")
            if current_balance < self.min_balance:
                self.upgrade_logger.error(f"Balance lower than {self.min_balance:,}.")
                self.upgrade_logger.warning(f"Waiting {60 * 5} seconds...")
                self.safe_sleep(60 * 5)
                continue

            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/upgrades-for-buy", logger=self.upgrade_logger)
            if (not response) or 'error_code' in response:
                self.upgrade_logger.error(f"Failed to get upgrades.")
                self.upgrade_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue

            upgrades = []
            for card in response['upgradesForBuy']:
                card['cooldownSeconds'] = card.get('cooldownSeconds', 0)
                
                if card["isExpired"] or not card["isAvailable"]:# or card['cooldownSeconds'] > 60 * 60: # or card['price'] > current_balance:#:
                    continue

                upgrades.append({
                    'ratio': card['profitPerHourDelta'] / card['price'] * 100,
                    'profit': card['profitPerHourDelta'],
                    'price': card['price'],
                    'id': card['id'],
                    'cooldown': card['cooldownSeconds'],
                    'section': card['section']
                })
        

            if len(upgrades) == 0:
                self.upgrade_logger.error(f"No more upgrades to buy.")
                self.upgrade_logger.warning(f"Waiting {60 * 5} seconds...")
                self.safe_sleep(60 * 5)
                continue

            upgrades.sort(key=lambda x: x['ratio'], reverse=True)
            
            for upgrade in upgrades[:5]:
                self.upgrade_logger.info(f"Ratio: {upgrade['ratio']:.2f}% \t Profit: {upgrade['profit']:,} \t Price: {upgrade['price']:,}")
            
            best_item = upgrades[0]

            if current_balance < best_item['price']:
                self.upgrade_logger.error(f"Balance lower than {best_item['price']:,}.")
                self.upgrade_logger.warning(f"Waiting {60 * 5} seconds...")
                self.safe_sleep(60 * 5)
                continue

            response = self.safe_post("https://api.hamsterkombatgame.io/clicker/buy-upgrade", data={
                "upgradeId": best_item['id'],
                "timestamp": int(time() * 1000)
            }, logger=self.upgrade_logger)

            if (not response):
                self.upgrade_logger.error(f"Failed to purchased upgrade.")
                self.upgrade_logger.warning(f"Waiting {30} seconds...")
                self.safe_sleep(30)
                continue

            if 'error_code' in response:
                self.upgrade_logger.error(f"Upgrade is on cooldown.")
                self.upgrade_logger.warning(f"Waiting {best_item['cooldown']} seconds...")
                
                self.safe_sleep(best_item['cooldown'])
            else:
                sleep_secds = 2 + random.randint(0, 5)
                self.upgrade_logger.info(f"Upgrade '{best_item['id']}' purchased successfully.")
                self.upgrade_logger.info(f"Waiting {sleep_secds} seconds before next purchase...")
                
                self.safe_sleep(sleep_secds)

# Alireza2: "Bearer 1719243290374SGie0tA9HXkE0iBpzCWwHFr1gIM5j1W5AC5iR06DTKMIp4zDqIHedv5uYwVbSQe66354562785"
# Alireza1: "Bearer 1718985498182T6BiVqy1koSDDSICjCW2Yk1DfXUiWXpY5ecXln1NsW5W9xgtoPwGfBAoEH6CQrYX866940060"

parser = argparse.ArgumentParser(description='HamsterKombat Automation Tool')
parser.add_argument('--config', required=True, help='Config file address', default="config.json")
args = parser.parse_args()

old_config = None
new_config = None
first_time = True
users = []

main_logger = logging.getLogger(name="Main")
main_logger.info("Starting ...")

while True:
    try:
        with open(args.config, 'r') as f:
            new_config = json.load(f)
    except (FileNotFoundError, OSError, json.decoder.JSONDecodeError) as e:
        main_logger.error(f'Error reading config: {e}')

    if new_config == old_config:
        sleep(60)
        continue
    
    old_config = new_config

    for user in users:
        user.running = False

    if not first_time:
        main_logger.info(f'Config changed, stopping services and waiting {60} seconds ...')
        sleep(60)

    users = []

    for account in new_config['accounts']:
        users.append(User(name=account['name'], 
                        authorization=account['token'], 
                        daily_cipher=new_config['daily_cipher'], 
                        min_balance=float(account['min_balance']), 
                        proxies=account['proxies'],
                        tap_range=account['tap_range']))
    
    first_time = False
