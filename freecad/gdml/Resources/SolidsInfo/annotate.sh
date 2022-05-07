for i in `ls a*.png|sed s/\.png//`; do convert $i.png -background transparent -pointsize 15 -size 300x -gravity Center caption:"`cat $i.txt`" -append ${i}_annotated.png;done
