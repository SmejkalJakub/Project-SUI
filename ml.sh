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

    echo "v = $v"
    echo "w = $w"
    echo "x = $x"
    echo "y = $y"

    echo "succ_prob = $succ_prob"
    echo "hold_prob = $hold_prob"

    sed -i "s/            v = .*/            v = $v/" dicewars/ai/xsmejk28_ste.py
    sed -i "s/            w = .*/            w = $w/" dicewars/ai/xsmejk28_ste.py
    sed -i "s/            x = .*/            x = $x/" dicewars/ai/xsmejk28_ste.py
    sed -i "s/            y = .*/            y = $y/" dicewars/ai/xsmejk28_ste.py

    sed -i "s/if(hold_prob >= 0\..* and succ_prob >= 0\..*): #tohle je zatim asi nejlepsi podminka/if(hold_prob >= $hold_prob and succ_prob >= $succ_prob): #tohle je zatim asi nejlepsi podminka/" dicewars/ai/xsmejk28_ste.py

    result=$(python3 ./scripts/dicewars-tournament.py -g 4 -n 100 -b 101 -s 1337)
    tmp=${result#*xsmejk28_ste}
    result_value=${tmp#*xsmejk28_ste}
    echo $result_value

    echo $percentage_wins

    echo '------------------------------------------------------------------'
    percentage_wins=$(echo $result_value | awk '{print substr($result_value,0,4)}')
    echo $percentage_wins
    echo '------------------------------------------------------------------'
done