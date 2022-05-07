for i in `ls a*.png|sed s/\.png//`; do
	if [ -f $i.txt ];then
		convert -background transparent -pointsize 15 -size 300x -gravity Center caption:"`cat $i.txt`" ${i}_annotation.png
	fi
done
