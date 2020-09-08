import re
import sys
import json
import string
import random
from faker import Faker


DEFAULT_COUNT = 1
BUFFER_SIZE = 10
OUTPUT_FILE = 'fakedata.json'
HELP_MESSAGE = """
    Usage: python fakedata.py --breach_name=[breach_name] --date=[date] --count=[value]

    Example:
        python fakedata.py --breach_name="dubsmash_breach" --date="2016-08-10" --count=1000

    Optional:
        --fields=field1,field2
            Field lists:
                name,address,phone_number,email,company,date_of_birth,ip_address,
                password,password_hash,password_salt,social_id,btc_wallet

        --output
            Specifies output file

"""

def random_alphanumeric(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

def phone_number(fake):
    phone_number = re.sub(r'\D', '',fake.phone_number())
    return phone_number

def password(fake):

    def change_case(x):
        if random.randint(1,3)==3:
            return x.upper()
        return x

    rand = random.randint(1,3)
    number = random.randint(0,50000)
    words = ''.join([change_case(x) for x in fake.words(rand)])
    name = re.sub(r' ', '', fake.name())
    specials = '#@$%&^'

    value = name if number%6==0 or number%11==0 else words
    array = [value, str(number), specials[int(random.random()*len(specials))]]
    random.shuffle(array)
    result = ''.join(array)
    return result



def get_data(fake, args):
    data = {}
    data['name'] = fake.name()
    data['address'] = fake.address().replace('\n', ' ')
    data['phone_number'] = phone_number(fake)
    data['email'] = fake.email()
    data['company'] = fake.company()
    data['date_of_birth'] = fake.date_of_birth().strftime("%Y-%m-%d")
    data['ip_address'] = fake.ipv4()
    data['password'] = password(fake)
    data['password_hash'] = fake.sha256()
    data['password_salt'] = random_alphanumeric(random.randint(8,15))
    data['social_id'] = str(fake.random_number(digits=15))
    data['btc_wallet'] = random_alphanumeric(random.randint(26,36))

    result = {}
    result['breach_name'] = args['breach_name']
    result['imported_date'] = args['date']
    if 'fields' in args.keys():
        for key in args['fields']:
            try:
                result[key] = data[key]
            except:
                print(f"Invalid field: {key}")
                print(HELP_MESSAGE)
                exit()
    else:
        result = data

    return result

def write_data(jar):
    with open(OUTPUT_FILE, 'a') as fp:
        fp.write(jar)       
        print(f'JSON Written in {OUTPUT_FILE}')
        print('++++++++++++++++++++++++++++++++')

def main(args):
    count = 1
    string_jar = ''
    for i in range(0, int(args['count'])):
        Faker.seed(random.randint(0,9000))
        data = json.dumps(get_data(Faker(), args))
        string_jar += str(data) + '\n'
        print(data)
        if count%BUFFER_SIZE == 0:
            write_data(string_jar)
            string_jar = ''
            count = 1
        else:
            count += 1
            print('-----------------------')
    if string_jar:
        write_data(string_jar)

if __name__ == '__main__':
    args = {}
    for arg in sys.argv[1:]:
        try:
            key = arg.split('=')[0].split('--')[-1]
            value = arg.split('=')[1]
        except:
            print('Missing values.')
            print(HELP_MESSAGE)
            exit()

        if key == 'count':
            try:
                args[key] = int(value)
            except:
                print('Count should be integer.')
                print(HELP_MESSAGE)
                exit()
        elif key == 'fields':
            fields = []
            values = value.split(',')
            for val in values:
                fields.append(val)
            args[key] = tuple(fields)

        elif key == 'output':
            OUTPUT_FILE = value
        else:
            args[key] = value

    required = ['breach_name', 'date']
    for arg in required:
        if arg not in args:
            print(f'{arg} is required.')
            print(HELP_MESSAGE)
            exit()

        if not args[arg]:
            print(HELP_MESSAGE)
            exit()

    if not 'count' in list(args.keys()):
        args['count'] = DEFAULT_COUNT
    main(args)

