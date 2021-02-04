#!/usr/bin/env bash
set -e
HOST="172.30.0.112"
USERNAME="adminastoria"
PASSWORD="qZtJjrZgJ7NR"
DATABASE="ratec496_ratechecker"
if [ -z "$HOST" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ] || [ -z $DATABASE ]; then
    echo "Usage: chunked-mysqldump <host> <username> <password> <database>"
    exit 1
fi
BATCH_SIZE=200000
TABLES=(lead_autoInsurance lead_autoLoanRefinance lead_autoRefinance lead_edu lead_edu_direct lead_finalInsurance lead_healthInsurance lead_homeImprovement lead_homeInsurance lead_installmentLoan lead_legal lead_lifeInsurance lead_mortgage lead_mortgagePP lead_newcar lead_payday lead_paydayDebtHelp lead_payday_recover lead_personalLoan lead_rentersInsurance lead_send_using_script lead_shortform_edu lead_shortform_payday lead_titleLoans)
for TABLE in ${TABLES[@]}; do
    NUMBER_OF_RECORDS=$(mysql --batch --silent -h "$HOST" -u "$USERNAME" -p"$PASSWORD" "$DATABASE" -e "select count(*) from $TABLE;")
    NUMBER_OF_DUMPS=$(perl -e "print int($NUMBER_OF_RECORDS / $BATCH_SIZE) + 1")
    echo "Dumping $NUMBER_OF_DUMPS file(s) with $NUMBER_OF_RECORDS record(s) from $DATABASE.$TABLE:"
    for DUMP_INDEX in $(seq 0 $((NUMBER_OF_DUMPS - 1))); do
        OFFSET=$((DUMP_INDEX * BATCH_SIZE))
        NAME="${DATABASE}_${TABLE}_${DUMP_INDEX}_$(date +%s).sql"
        echo -e "\t$NAME"
        mysqldump -h "$HOST" -u "$USERNAME" -p"$PASSWORD" --no-create-info --where="1 limit $OFFSET, $BATCH_SIZE" "$DATABASE" "$TABLE" > "$NAME"
    done;
    echo
done
