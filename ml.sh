#!/bin/bash
v=0.5
w=0.55
x=0.3
y=0.4

treshold=0.2

hold_prob=0.3
succ_prob=0.5

itterations=10

for j in {0..3..1}
do
    random=$(( $RANDOM % 1000 ))
    v=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    w=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    x=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    y=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))

    treshold=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    succ_prob=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    hold_prob=$(echo "scale=4;$random/1000" | bc)

    iteration_number_of_wins=0

    echo "v = $v"
    echo "w = $w"
    echo "x = $x"
    echo "y = $y"

    echo "treshold = $treshold"

    echo "succ_prob = $succ_prob"
    echo "hold_prob = $hold_prob"

    sed -i "s/            v = .*/            v = $v/" dicewars/ai/xsmejk28.py
    sed -i "s/            w = .*/            w = $w/" dicewars/ai/xsmejk28.py
    sed -i "s/            x = .*/            x = $x/" dicewars/ai/xsmejk28.py
    sed -i "s/            y = .*/            y = $y/" dicewars/ai/xsmejk28.py

    sed -i "s/treshold = .*/treshold = $treshold/" dicewars/ai/xsmejk28.py

    sed -i "s/if(hold_prob >= 0\..* and succ_prob >= 0\..*): #tohle je zatim asi nejlepsi podminka/if(hold_prob >= $hold_prob and succ_prob >= $succ_prob): #tohle je zatim asi nejlepsi podminka/" dicewars/ai/xsmejk28.py


    for i in $(seq 1 $itterations)
    do
        result=$(python3 ./scripts/dicewars-ai-only.py -r -b 11 -o 22 -s 33 -c 44 -n $itterations -l ../logs --ai dt.rand xsmejk28)
        result_value=${result#*\'xsmejk28 \(AI\)\':}

        number_of_wins=$(echo $result_value | awk '{print substr($result_value,0,1)}')
        #echo $result
        #echo $result_value
        #echo $number_of_wins
        iteration_number_of_wins=$((iteration_number_of_wins + number_of_wins))
    done

    echo '------------------------------------------------------------------'
    average_wins=$(echo "scale=4;$iteration_number_of_wins/$itterations" | bc) 
    echo $average_wins
    echo '------------------------------------------------------------------'
done