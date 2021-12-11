#!/bin/bash
itterations=10

for j in {0..80..1}
do
    iteration_number_of_wins=0

    for i in $(seq 1 $itterations)
    do
        result=$(python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n $itterations -l ../logs --ai dt.rand xsmejk28)
        result_value=${result#*\'xsmejk28 \(AI\)\':}

        number_of_wins=$(echo $result_value | awk '{print substr($result_value,0,1)}')
        iteration_number_of_wins=$((iteration_number_of_wins + number_of_wins))
    done

    echo '------------------------------------------------------------------'
    average_wins=$(echo "scale=4;$iteration_number_of_wins/$itterations" | bc) 
    echo $average_wins
    echo '------------------------------------------------------------------'
done