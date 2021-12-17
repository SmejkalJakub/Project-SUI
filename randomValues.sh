#!/bin/bash

for j in {0..80..1}
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

    random=$(( $RANDOM % 1000 ))
    succ_prob=$(echo "scale=4;$random/1000" | bc)
    random=$(( $RANDOM % 1000 ))
    hold_prob=$(echo "scale=4;$random/1000" | bc)

    echo "player_areas_weight = $v"
    echo "biggest_region_weight = $w"
    echo "weak_borders_weight = $x"
    echo "weak_enemies_weight = $y"

    echo "succ_prob = $succ_prob"
    echo "hold_prob = $hold_prob"

    sed -i "s/            player_areas_weight = .*/            player_areas_weight = $v/" dicewars/ai/xgrunw00.py
    sed -i "s/            biggest_region_weight = .*/            biggest_region_weight = $w/" dicewars/ai/xgrunw00.py
    sed -i "s/            weak_borders_weight = .*/            weak_borders_weight = $x/" dicewars/ai/xgrunw00.py
    sed -i "s/            weak_enemies_weight = .*/            weak_enemies_weight = $y/" dicewars/ai/xgrunw00.py

    sed -i "s/if(hold_prob >= 0\..* and succ_prob >= 0\..*):/if(hold_prob >= $hold_prob and succ_prob >= $succ_prob):/" dicewars/ai/xgrunw00.py

    result=$(python3 ./scripts/dicewars-tournament.py -g 4 -n 100 -b 101 -s 1337)
    tmp=${result#*xgrunw00}
    result_value=${tmp#*xgrunw00}

    echo '------------------------------------------------------------------'
    percentage_wins=$(echo $result_value | awk '{print substr($result_value,0,4)}')
    echo $percentage_wins
    echo '------------------------------------------------------------------'
done